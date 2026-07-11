"""Shared fixtures for backend and E2E tests."""
import os
import sys
import pytest
from pathlib import Path
from dotenv import load_dotenv

# Load .env so all tests have API keys
load_dotenv(Path(__file__).parent.parent / ".env")

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent))

# Real IDs for imatinib/ABL1 — used across all tests
DEMO_IDS = {
    "entity": "imatinib",
    "target": "ABL1",
    "drug_pubchem": "5291",
    "drug_chembl": "CHEMBL941",
    "target_uniprot": "P00519",
    "target_chembl": "CHEMBL1862",
}

# Sample queries per persona (from the developer guide)
PERSONA_QUERIES = {
    "medicinal_chemist": (
        "I'm optimizing imatinib analogues against ABL1 — "
        "what's the SAR, and are there co-crystal structures of the ABL1 complex I can use?"
    ),
    "pathologist": (
        "This CML patient stopped responding to imatinib — "
        "is there an ABL1 mutation that explains resistance, and what's its clinical significance?"
    ),
    "cell_molecular_biologist": (
        "How does imatinib blocking ABL1 change downstream signaling — "
        "which pathways and partner proteins are involved?"
    ),
    "computational_biologist": (
        "I need structural and sequence inputs to model imatinib–ABL1 binding — "
        "what experimental/predicted structures, sequences, and bioactivity datasets exist?"
    ),
}

SHARED_QUERY = "What do I need to know about imatinib and its target ABL1?"
BASE_URL = "http://localhost:8000"
