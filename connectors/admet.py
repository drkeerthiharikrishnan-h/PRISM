"""ADMET connector — drug-likeness and ADMET properties from ChEMBL molecule_properties."""
import httpx
from connectors.utils import retryable_get

BASE = "https://www.ebi.ac.uk/chembl/api/data"


async def fetch(entity_ids: dict, params: dict) -> dict:
    drug_chembl = entity_ids.get("drug_chembl")
    entity = entity_ids.get("entity", "")

    if not drug_chembl:
        return {}

    try:
        async with httpx.AsyncClient(follow_redirects=True) as client:
            r = await retryable_get(
                client, f"{BASE}/molecule/{drug_chembl}.json",
                timeout=10,
            )
            if r.status_code != 200:
                return {}
            mol = r.json()
            props = mol.get("molecule_properties") or {}
            return {
                "molecule_chembl_id": drug_chembl,
                "pref_name": mol.get("pref_name", entity),
                "max_phase": mol.get("max_phase"),
                "molecular_weight": props.get("full_mwt"),
                "alogp": props.get("alogp"),
                "psa": props.get("psa"),
                "hba": props.get("hba"),
                "hbd": props.get("hbd"),
                "rotatable_bonds": props.get("rtb"),
                "aromatic_rings": props.get("aromatic_rings"),
                "num_ro5_violations": props.get("num_lipinski_ro5_violations"),
                "qed_weighted": props.get("qed_weighted"),
                "ro3_pass": props.get("ro3_pass"),
                "molecular_formula": props.get("full_molformula"),
                "lipinski_pass": (props.get("num_lipinski_ro5_violations") or 0) <= 1,
            }
    except Exception as e:
        return {"error": str(e)}
