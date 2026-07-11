"""Unit tests for answer-scope behavior in the orchestrator."""

import json

from orchestrator import (
    _build_synthesis_prompt,
    _classify_query_scope,
    _classify_question_type,
    _question_scope_from_type,
)


def test_classify_question_type_factual_short_queries():
    lookup_queries = [
        "What is the receptor for Fibulin-1?",
        "Which gene does imatinib target?",
        "Does EGFR bind gefitinib?",
    ]

    for query in lookup_queries:
        assert _classify_question_type(query) == "factual"


def test_classify_question_type_flags_dossier_and_broad_tiers():
    dossier_queries = [
        "Build the reference profile for imatinib and ABL1.",
        "Give me a dossier on Fibulin-1.",
    ]
    exploratory_queries = [
        "What is known about EGFR and resistance?",
    ]
    synthesis_queries = [
        "Connect the findings for ABL1 inhibition.",
    ]

    for query in dossier_queries:
        assert _classify_question_type(query) == "dossier"
    for query in exploratory_queries:
        assert _classify_question_type(query) == "exploratory"
    for query in synthesis_queries:
        assert _classify_question_type(query) == "synthesis"


def test_compare_single_entity_property_query_stays_detail():
    assert _classify_question_type("compare molecular properties of cetuximab") == "detail"


def test_scope_mapping_compatibility_from_question_type():
    assert _question_scope_from_type("factual") == "lookup"
    assert _question_scope_from_type("detail") == "broad"
    assert _question_scope_from_type("comparison") == "broad"


def test_classify_query_scope_remains_compatibility_shim():
    assert _classify_query_scope("What is the receptor for Fibulin-1?") == "lookup"
    assert _classify_query_scope("Build the reference profile for imatinib and ABL1.") == "broad"


def test_lookup_scope_compacts_evidence_and_carries_scope_flag():
    persona_cfg = {"system_prompt": "Persona prompt"}
    entity_ids = {"entity": "fibulin-1", "target": "EGFR"}
    evidence = {
        "uniprot": {
            "accession": "P00533",
            "gene_name": "EGFR",
            "protein_name": "Epidermal growth factor receptor",
        },
        "pubmed": {
            "abstracts": [
                {
                    "pmid": "32719793",
                    "title": "Fibulin-1 and EGFR",
                    "abstract": "Fibulin-1 is linked to EGFR in this study.",
                }
            ]
        },
    }

    system, user, max_idx = _build_synthesis_prompt(
        persona_cfg,
        entity_ids,
        evidence,
        original_query="What is the receptor for Fibulin-1?",
        question_type="factual",
        query_scope="lookup",
    )

    assert "question_scope = lookup" in system
    assert "question_type = factual" in system
    assert "Answer only the directly asked fact" in system
    assert max_idx == 2

    payload = json.loads(user)
    assert payload["question_type"] == "factual"
    assert payload["question_scope"] == "lookup"
    assert "P00533 · EGFR" in payload["structured_evidence"]
    assert "protein_name" not in payload["structured_evidence"]