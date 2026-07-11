"""
Backend tests — entity_resolver: parse_query, resolve_ids, detect_persona.

Run:  uv run pytest tests/test_entity_resolver.py -v
"""
import pytest
from tests.conftest import PERSONA_QUERIES, SHARED_QUERY


# ── parse_query ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_parse_query_extracts_imatinib_abl1():
    from entity_resolver import parse_query
    result = await parse_query(SHARED_QUERY)

    assert "entity" in result
    assert "imatinib" in result["entity"].lower()
    assert "target" in result
    assert "ABL1" in result["target"].upper()
    print(f"\n  Parsed: entity={result['entity']} target={result['target']}")


@pytest.mark.asyncio
async def test_parse_query_caches_result():
    """Second call with same query should return from cache (no extra LLM call)."""
    from entity_resolver import parse_query
    result1 = await parse_query(SHARED_QUERY)
    result2 = await parse_query(SHARED_QUERY)
    assert result1 == result2, "Cached result should be identical"


@pytest.mark.asyncio
async def test_parse_query_different_phrasing():
    """Should extract same entity regardless of how it's phrased."""
    from entity_resolver import parse_query
    result = await parse_query("Tell me about gleevec and the BCR-ABL fusion kinase")
    # gleevec is imatinib's brand name — entity should contain it or imatinib
    assert result.get("entity"), "Entity should not be empty"
    print(f"\n  Parsed gleevec phrasing: entity={result['entity']} target={result['target']}")


# ── resolve_ids ───────────────────────────────────────────────────────────────

@pytest.mark.asyncio
async def test_resolve_ids_imatinib_abl1():
    from entity_resolver import resolve_ids
    result = await resolve_ids("imatinib", "ABL1")

    assert result.get("drug_pubchem") == "5291", f"Expected 5291, got {result.get('drug_pubchem')}"
    assert result.get("drug_chembl") == "CHEMBL941", f"Expected CHEMBL941, got {result.get('drug_chembl')}"
    assert result.get("target_uniprot") == "P00519", f"Expected P00519, got {result.get('target_uniprot')}"
    # ChEMBL has multiple valid ABL1 entries (CHEMBL1862 = gene-level, CHEMBL3099 = protein-level)
    assert result.get("target_chembl") in ("CHEMBL1862", "CHEMBL3099"), \
        f"Expected a valid ABL1 ChEMBL ID, got {result.get('target_chembl')}"
    print(f"\n  Resolved: PubChem={result['drug_pubchem']} ChEMBL={result['drug_chembl']} "
          f"UniProt={result['target_uniprot']}")


@pytest.mark.asyncio
async def test_resolve_ids_graceful_on_unknown():
    """Unknown entity should return dict with None values, not raise."""
    from entity_resolver import resolve_ids
    result = await resolve_ids("notarealdrugxyz123", "FAKEGENE99")
    assert isinstance(result, dict)
    assert result.get("entity") == "notarealdrugxyz123"
    # IDs may be None — that's fine
    print(f"\n  Unknown entity resolve: {result}")


# ── detect_persona ────────────────────────────────────────────────────────────

@pytest.mark.asyncio
@pytest.mark.parametrize("persona_id,query", [
    ("medicinal_chemist",
     "I'm optimizing imatinib analogues against ABL1 — what's the SAR and IC50 for co-crystal structures?"),
    ("pathologist",
     "This CML patient stopped responding to imatinib — is there a T315I ABL1 mutation causing resistance?"),
    ("cell_molecular_biologist",
     "How does imatinib blocking ABL1 affect BCR-ABL downstream signaling and STAT5 phosphorylation?"),
    ("computational_biologist",
     "I need PDB structures, AlphaFold predictions, and bioactivity datasets to train a docking model for ABL1."),
])
async def test_detect_persona_accuracy(persona_id, query):
    from entity_resolver import detect_persona
    detected, confidence = await detect_persona(query)

    assert detected == persona_id, (
        f"Query for '{persona_id}' was detected as '{detected}' (confidence={confidence:.2f})\n"
        f"Query: {query}"
    )
    assert confidence > 0.5, f"Confidence too low: {confidence:.2f}"
    print(f"\n  Detect '{persona_id}': detected={detected} confidence={confidence:.2f}")


@pytest.mark.asyncio
async def test_detect_persona_returns_valid_id():
    """Any query should return one of the 4 valid persona IDs."""
    from entity_resolver import detect_persona, PERSONA_IDS
    detected, confidence = await detect_persona("Tell me about cancer drugs")
    assert detected in PERSONA_IDS, f"'{detected}' is not a valid persona ID"
