"""PDB/RCSB connector — 3D structures, metadata, and per-residue ligand-binding contacts.

Query modes (params["query_type"]):
  "ligand_search"  (default) — full-text/UniProt search → entry metadata list
  "all_structures"           — same search, more rows
  "contacts"                 — download a specific entry, locate the bound ligand,
                               and compute every protein-atom → ligand-atom contact
                               within a distance cutoff (Biopython), returned as a
                               per-residue min-distance table with a geometric
                               interaction class and a legacy→modern residue offset.

Image / 3D policy: assembly JPEGs, the interactive 3D viewer URL, and the downloadable
coordinate file are returned ONLY when params["include_images"] is true. By default the
connector returns text/metadata/geometry so nothing renders unless explicitly requested.
"""
from typing import Optional
import io

import httpx

from connectors.utils import retryable_get, retryable_post

SEARCH_URL = "https://search.rcsb.org/rcsbsearch/v2/query"
ENTRY_URL = "https://data.rcsb.org/rest/v1/core/entry"
DOWNLOAD_URL = "https://files.rcsb.org/download"

# Water / common buffer & cryo components to skip when auto-detecting the ligand.
_NON_LIGAND = {
    "HOH", "WAT", "DOD", "SO4", "PO4", "GOL", "EDO", "PEG", "MPD", "ACT",
    "CL", "NA", "MG", "K", "CA", "ZN", "MN", "DMS", "TRS", "BME", "IOD",
}


async def fetch(entity_ids: dict, params: dict) -> dict:
    query_type = params.get("query_type", "ligand_search")
    include_images = bool(params.get("include_images", False))

    if query_type == "contacts":
        return await _fetch_contacts(entity_ids, params, include_images)

    entity = entity_ids.get("entity", "")
    target_uniprot = entity_ids.get("target_uniprot")
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            pdb_ids = await _search_structures(client, entity, target_uniprot)
            if not pdb_ids:
                return {"structures": []}
            n = 8 if query_type == "all_structures" else 5
            details = []
            for pdb_id in pdb_ids[:n]:
                detail = await _fetch_entry(client, pdb_id, include_images)
                if detail:
                    details.append(detail)
            return {"structures": details}
    except Exception as e:
        return {"structures": [], "error": str(e)}


# --------------------------------------------------------------------------- #
# Contact analysis
# --------------------------------------------------------------------------- #
async def _fetch_contacts(entity_ids: dict, params: dict, include_images: bool) -> dict:
    """Compute ligand–protein contacts for a specific PDB entry."""
    pdb_id = (params.get("pdb_id") or entity_ids.get("pdb_id") or "").upper()
    if not pdb_id:
        return {"error": "contacts mode requires params['pdb_id'] (e.g. '1M17')"}

    # Structural specifics come from the resolved entity map first (query-driven),
    # falling back to explicit params only if a caller overrides them. This keeps
    # personas free of any hardcoded PDB/ligand/offset for a particular drug.
    ligand_code = params.get("ligand_code") or entity_ids.get("ligand_code")  # auto-detected if None
    cutoff = float(params.get("cutoff", 4.5))
    numbering_offset = params.get("numbering_offset")
    if numbering_offset is None:
        numbering_offset = entity_ids.get("numbering_offset")  # legacy→modern, from SIFTS

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(client, f"{DOWNLOAD_URL}/{pdb_id}.pdb", timeout=30)
            if r.status_code != 200:
                return {"pdb_id": pdb_id, "error": f"download failed ({r.status_code})"}
            pdb_text = r.text
    except Exception as e:
        return {"pdb_id": pdb_id, "error": str(e)}

    try:
        from Bio.PDB import PDBParser, NeighborSearch
    except Exception as e:
        return {"pdb_id": pdb_id, "error": f"Biopython unavailable: {e}"}

    parser = PDBParser(QUIET=True)
    structure = parser.get_structure(pdb_id, io.StringIO(pdb_text))
    model = next(iter(structure))

    # Locate ligand residue(s).
    hetero = []
    for chain in model:
        for res in chain:
            hetflag = res.id[0]
            resname = res.resname.strip()
            if hetflag != " " and resname not in _NON_LIGAND:
                hetero.append(res)
    if ligand_code:
        ligand_res = [r for r in hetero if r.resname.strip() == ligand_code.upper()]
    else:
        # choose the hetero residue with the most atoms (the drug, not an ion)
        ligand_res = sorted(hetero, key=lambda r: sum(1 for _ in r.get_atoms()), reverse=True)[:1]

    if not ligand_res:
        return {"pdb_id": pdb_id, "error": "no ligand residue found",
                "hetero_candidates": sorted({r.resname.strip() for r in hetero})}

    lig = ligand_res[0]
    lig_code = lig.resname.strip()
    lig_atoms = list(lig.get_atoms())

    protein_atoms = [a for chain in model for res in chain
                     for a in res if res.id[0] == " "]
    ns = NeighborSearch(protein_atoms)

    # Per-residue minimum distance within cutoff.
    best: dict = {}
    for la in lig_atoms:
        for pa in ns.search(la.coord, cutoff):
            res = pa.get_parent()
            key = (res.get_parent().id, res.id[1], res.resname.strip())
            d = la - pa
            if key not in best or d < best[key]["min_dist"]:
                best[key] = {
                    "min_dist": d,
                    "lig_atom": la.get_name(),
                    "prot_atom": pa.get_name(),
                }

    contacts = []
    for (chain_id, resnum, resname), info in best.items():
        d = round(float(info["min_dist"]), 2)
        contact = {
            "residue": f"{resname}{resnum}",
            "resname": resname,
            "seq_id": resnum,
            "chain": chain_id,
            "min_dist_angstrom": d,
            "lig_atom": info["lig_atom"],
            "prot_atom": info["prot_atom"],
            "interaction": _classify(info["lig_atom"], info["prot_atom"], d),
        }
        if numbering_offset is not None:
            contact["modern_seq_id"] = resnum + int(numbering_offset)
        contacts.append(contact)
    contacts.sort(key=lambda c: c["min_dist_angstrom"])

    out = {
        "pdb_id": pdb_id,
        "ligand_code": lig_code,
        "cutoff_angstrom": cutoff,
        "contact_count": len(contacts),
        "contacts": contacts,
    }
    if numbering_offset is not None:
        out["numbering_note"] = f"modern (UniProt) numbering = legacy + {int(numbering_offset)}"
    if include_images:
        pid = pdb_id.lower()
        out["structure_file_url"] = f"{DOWNLOAD_URL}/{pdb_id}.pdb"
        out["image_url"] = f"https://cdn.rcsb.org/images/structures/{pid}_assembly-1.jpeg"
        out["viewer_url"] = f"https://www.rcsb.org/3d-view/{pdb_id}"
    return out


def _classify(lig_atom: str, prot_atom: str, dist: float) -> str:
    """Transparent geometric interaction class from atom elements + distance.

    Not a force-field assignment — a distance/polarity heuristic. Directionality and
    biological role (hinge H-bond vs. incidental vdW packing) are annotation the caller
    adds; here we only report what the geometry supports.
    """
    def is_polar(atom_name: str) -> bool:
        el = atom_name.strip()[:1].upper()
        return el in ("N", "O", "S")

    lp, pp = is_polar(lig_atom), is_polar(prot_atom)
    if lp and pp and dist <= 3.5:
        return "H-bond / polar"
    if (lp or pp) and dist <= 3.5:
        return "Polar contact"
    return "Hydrophobic / vdW"


# --------------------------------------------------------------------------- #
# Structure search + entry metadata
# --------------------------------------------------------------------------- #
async def _search_structures(client: httpx.AsyncClient, entity: str, uniprot_id: Optional[str]) -> list[str]:
    """Search RCSB for structures containing the entity as a ligand."""
    query: dict = {
        "query": {
            "type": "terminal",
            "service": "full_text",
            "parameters": {"value": entity},
        },
        "return_type": "entry",
        "request_options": {"paginate": {"start": 0, "rows": 8}},
    }
    if uniprot_id:
        query = {
            "query": {
                "type": "terminal",
                "service": "text",
                "parameters": {
                    "attribute": "rcsb_polymer_entity_container_identifiers.reference_sequence_identifiers.database_accession",
                    "operator": "exact_match",
                    "value": uniprot_id,
                },
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 8}},
        }

    r = await retryable_post(client, SEARCH_URL, json=query, timeout=12)
    if r.status_code != 200:
        fallback = {
            "query": {
                "type": "terminal",
                "service": "full_text",
                "parameters": {"value": f"{entity}"},
            },
            "return_type": "entry",
            "request_options": {"paginate": {"start": 0, "rows": 8}},
        }
        r = await retryable_post(client, SEARCH_URL, json=fallback, timeout=12)

    data = r.json()
    return [hit["identifier"] for hit in data.get("result_set", [])]


async def _fetch_entry(client: httpx.AsyncClient, pdb_id: str, include_images: bool) -> Optional[dict]:
    """Fetch title, resolution, and experimental method for a PDB entry."""
    try:
        r = await retryable_get(client, f"{ENTRY_URL}/{pdb_id}", timeout=8)
        d = r.json()
        struct = d.get("struct", {})
        refine = d.get("refine", [{}])
        exptl = d.get("exptl", [{}])
        resolution = None
        if refine and isinstance(refine, list):
            resolution = refine[0].get("ls_d_res_high")
        pid = pdb_id.lower()
        out = {
            "pdb_id": pdb_id,
            "title": struct.get("title", ""),
            "resolution_angstrom": resolution,
            "method": exptl[0].get("method", "") if exptl else "",
        }
        if include_images:
            out["image_url"] = f"https://cdn.rcsb.org/images/structures/{pid}_assembly-1.jpeg"
            out["viewer_url"] = f"https://www.rcsb.org/3d-view/{pdb_id}"
            out["structure_file_url"] = f"{DOWNLOAD_URL}/{pdb_id}.pdb"
        return out
    except Exception:
        return None
