"""ADMET / drug-likeness connector — ChEMBL molecule_properties."""
from typing import Optional

import httpx

from connectors.utils import retryable_get

BASE = "https://www.ebi.ac.uk/chembl/api/data"


async def fetch(entity_ids: dict, params: dict) -> dict:
    """Return physicochemical and drug-likeness descriptors for a compound."""
    chembl_id = entity_ids.get("drug_chembl")
    entity = entity_ids.get("entity", "")

    if not chembl_id:
        chembl_id = await _lookup_chembl_id(entity)
    if not chembl_id:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await retryable_get(client, f"{BASE}/molecule/{chembl_id}.json", timeout=10)
            return _parse_molecule(response.json(), chembl_id)
    except Exception as exc:
        return {"molecule_chembl_id": chembl_id, "error": str(exc)}


async def _lookup_chembl_id(name: str) -> Optional[str]:
    if not name:
        return None
    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            response = await retryable_get(
                client,
                f"{BASE}/molecule/search",
                params={"q": name, "format": "json", "limit": 1},
                timeout=8,
            )
            molecules = response.json().get("molecules", [])
            return molecules[0]["molecule_chembl_id"] if molecules else None
    except Exception:
        return None


def _to_float(value):
    try:
        return float(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _to_int(value):
    try:
        return int(value) if value is not None else None
    except (TypeError, ValueError):
        return None


def _parse_molecule(data: dict, chembl_id: str) -> dict:
    molecule_properties = data.get("molecule_properties") or {}
    ro5 = _to_int(molecule_properties.get("num_ro5_violations"))
    return {
        "molecule_chembl_id": chembl_id,
        "pref_name": data.get("pref_name") or "",
        "max_phase": _to_float(data.get("max_phase")),
        "molecular_weight": _to_float(molecule_properties.get("full_mwt")),
        "alogp": _to_float(molecule_properties.get("alogp")),
        "psa": _to_float(molecule_properties.get("psa")),
        "hba": _to_int(molecule_properties.get("hba")),
        "hbd": _to_int(molecule_properties.get("hbd")),
        "rotatable_bonds": _to_int(molecule_properties.get("rtb")),
        "aromatic_rings": _to_int(molecule_properties.get("aromatic_rings")),
        "num_ro5_violations": ro5,
        "qed_weighted": _to_float(molecule_properties.get("qed_weighted")),
        "ro3_pass": (molecule_properties.get("ro3_pass") == "Y") if molecule_properties.get("ro3_pass") is not None else None,
        "molecular_formula": molecule_properties.get("full_molformula") or "",
        "lipinski_pass": (ro5 == 0) if ro5 is not None else None,
    }
