"""
Backend tests — each connector against the real APIs.
These are integration tests: they hit live endpoints, so they need
NCBI_API_KEY and network access.

Run:  uv run pytest tests/test_connectors.py -v
"""
import pytest
from tests.conftest import DEMO_IDS


# ── PubChem ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pubchem_returns_imatinib_cid():
    from connectors.pubchem import fetch
    result = await fetch(DEMO_IDS, {"query_type": "scaffold"})

    assert result.get("cid") == "5291", f"Expected CID 5291, got {result.get('cid')}"
    assert result.get("molecular_formula") == "C29H31N7O"
    assert result.get("molecular_weight") is not None
    assert result.get("canonical_smiles"), "SMILES should not be empty"
    print(f"\n  PubChem: {result['molecular_formula']} MW={result['molecular_weight']}")


@pytest.mark.asyncio
async def test_pubchem_graceful_on_bad_name():
    from connectors.pubchem import fetch
    result = await fetch({"entity": "notadrugxyz999", "drug_pubchem": None}, {})
    # Should return empty dict, not raise
    assert isinstance(result, dict)


# ── ChEMBL ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_chembl_activity_returns_ic50():
    from connectors.chembl import fetch
    result = await fetch(DEMO_IDS, {"query_type": "activity", "standard_types": ["IC50", "Ki"]})

    assert "activities" in result
    assert result.get("count", 0) > 0, "Expected >0 ChEMBL activities"
    activities = result["activities"]
    assert len(activities) > 0
    # At least one should have a numeric value
    has_value = any(a.get("standard_value") for a in activities)
    assert has_value, "At least one activity should have a numeric value"
    print(f"\n  ChEMBL: {result['count']} total activities, {len(activities)} returned")


@pytest.mark.asyncio
async def test_chembl_dataset_returns_count():
    from connectors.chembl import fetch
    result = await fetch(DEMO_IDS, {"query_type": "dataset", "limit": 20})

    assert "dataset_count" in result
    assert result["dataset_count"] > 0
    print(f"\n  ChEMBL dataset: {result['dataset_count']} bioactivities vs ABL1")


# ── PDB ───────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pdb_returns_structures():
    from connectors.pdb import fetch
    result = await fetch(DEMO_IDS, {"query_type": "ligand_search"})

    assert "structures" in result
    assert len(result["structures"]) > 0, "Expected at least 1 PDB structure"
    first = result["structures"][0]
    assert first.get("pdb_id"), "Structure should have a PDB ID"
    print(f"\n  PDB: {len(result['structures'])} structures, first={first['pdb_id']}")


# ── UniProt ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_uniprot_returns_abl1_function():
    from connectors.uniprot import fetch
    result = await fetch(DEMO_IDS, {"fields": ["cc_function", "go"]})

    assert result.get("accession") == "P00519", f"Expected P00519, got {result.get('accession')}"
    assert result.get("gene") == "ABL1", f"Expected ABL1, got {result.get('gene')}"
    assert result.get("function"), "Function text should not be empty"
    assert len(result.get("go_terms", [])) > 0, "Should have GO terms"
    print(f"\n  UniProt: gene={result['gene']} go_terms={len(result['go_terms'])}")


@pytest.mark.asyncio
async def test_uniprot_returns_sequence_features():
    from connectors.uniprot import fetch
    result = await fetch(DEMO_IDS, {"fields": ["sequence", "ft_binding", "ft_domain"]})

    assert result.get("sequence_length") is not None
    assert result["sequence_length"] > 0
    print(f"\n  UniProt sequence: {result['sequence_length']} aa, "
          f"binding_sites={len(result.get('binding_sites', []))}, "
          f"domains={len(result.get('domains', []))}")


# ── PubMed ────────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_pubmed_returns_abstracts():
    from connectors.pubmed import fetch
    result = await fetch(DEMO_IDS, {"keywords": ["SAR", "IC50", "co-crystal"]})

    assert "abstracts" in result
    assert len(result["abstracts"]) > 0, "Expected at least 1 PubMed abstract"
    first = result["abstracts"][0]
    assert first.get("title"), "Abstract should have a title"
    assert first.get("pmid"), "Abstract should have a PMID"
    print(f"\n  PubMed: {len(result['abstracts'])} abstracts, first PMID={first['pmid']}")


@pytest.mark.asyncio
async def test_pubmed_pathologist_keywords():
    from connectors.pubmed import fetch
    result = await fetch(DEMO_IDS, {"keywords": ["resistance mutation", "T315I", "clinical significance"]})

    assert len(result.get("abstracts", [])) > 0
    print(f"\n  PubMed (pathologist): {len(result['abstracts'])} abstracts on resistance")


# ── ClinVar ───────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_clinvar_returns_abl1_variants():
    from connectors.clinvar import fetch
    result = await fetch(DEMO_IDS, {"query_type": "resistance_variants"})

    assert "variants" in result
    # ClinVar may return 0 if query yields no matches — acceptable, but log it
    print(f"\n  ClinVar: {len(result['variants'])} variants for ABL1 + imatinib resistance")
    if result["variants"]:
        first = result["variants"][0]
        assert first.get("variant_id"), "Variant should have an ID"
        assert first.get("title"), "Variant should have a title"


# ── Reactome ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_reactome_returns_abl1_pathways():
    from connectors.reactome import fetch
    result = await fetch(DEMO_IDS, {"query_type": "pathways"})

    assert "pathways" in result
    assert len(result["pathways"]) > 0, "Expected at least 1 Reactome pathway for ABL1"
    first = result["pathways"][0]
    assert first.get("display_name"), "Pathway should have a name"
    print(f"\n  Reactome: {len(result['pathways'])} pathways, first='{first['display_name']}'")


# ── AlphaFold ─────────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_alphafold_returns_abl1_prediction():
    from connectors.alphafold import fetch
    result = await fetch(DEMO_IDS, {"query_type": "prediction", "include_images": True})

    assert result.get("accession") == "P00519"
    assert result.get("available") is True, "AlphaFold entry should be available for P00519"
    assert result.get("entry_id"), "Should have an entry ID"
    assert result.get("model_url"), "Should have a model URL"
    print(f"\n  AlphaFold: {result['entry_id']} pLDDT={result.get('plddt_global')} "
          f"seq_len={result.get('sequence_length')}")
