"""
Full E2E persona tests — 4 personas × multiple real biomedical questions.
Each test is recorded as a video.

Run with recording + headed browser:
  uv run pytest tests/e2e/test_full_personas.py -v \\
    --headed --video=on --output=test-recordings --slowmo=600

View videos:
  open test-recordings/   (macOS)

Each test generates: test-recordings/<test-name>/video.webm
"""
import time
import pytest
from playwright.sync_api import Page, expect

BASE_URL    = "http://localhost:8000"
LLM_TIMEOUT = 120_000   # 2 min — full synthesis + streaming
UI_TIMEOUT  = 10_000

# ── Question sets per persona ─────────────────────────────────────────────────
#
# 3 questions per persona, increasing complexity:
#   Q1 — demo classic (imatinib/ABL1)
#   Q2 — same class, different drug/target
#   Q3 — different disease area entirely
#
QUESTIONS = {
    "medicinal_chemist": [
        {
            "query": "What do I need to know about imatinib and its target ABL1?",
            "label": "imatinib-ABL1-classic",
            "expect_keywords": ["IC50", "SAR", "crystal", "scaffold"],
        },
        {
            "query": "What is the binding affinity profile of dasatinib against BCR-ABL "
                     "and what 3D structures explain its broader kinase selectivity?",
            "label": "dasatinib-BCR-ABL-selectivity",
            "expect_keywords": ["dasatinib", "binding", "structure", "kinase"],
        },
        {
            "query": "What SAR data exists for EGFR inhibitors like gefitinib "
                     "and how does the quinazoline scaffold contribute to potency?",
            "label": "gefitinib-EGFR-SAR",
            "expect_keywords": ["EGFR", "gefitinib", "scaffold", "potency"],
        },
    ],
    "pathologist": [
        {
            "query": "This CML patient stopped responding to imatinib — "
                     "is there an ABL1 mutation that explains resistance?",
            "label": "ABL1-imatinib-resistance",
            "expect_keywords": ["mutation", "resistance", "T315I", "clinical"],
        },
        {
            "query": "Which BRCA1 and BRCA2 variants are classified as pathogenic "
                     "and what is their clinical significance for hereditary breast cancer?",
            "label": "BRCA1-BRCA2-variants",
            "expect_keywords": ["BRCA", "variant", "pathogenic", "clinical"],
        },
        {
            "query": "Which KRAS mutations drive resistance to anti-EGFR therapy "
                     "in colorectal cancer patients and how should treatment be adjusted?",
            "label": "KRAS-EGFR-resistance",
            "expect_keywords": ["KRAS", "mutation", "resistance", "treatment"],
        },
    ],
    "cell_biologist": [
        {
            "query": "How does imatinib blocking ABL1 change downstream signaling — "
                     "which pathways and partner proteins are involved?",
            "label": "imatinib-ABL1-signaling",
            "expect_keywords": ["pathway", "signaling", "mechanism", "phosphorylation"],
        },
        {
            "query": "How does vemurafenib inhibit BRAF V600E and what downstream "
                     "MAPK pathway effects does it produce in melanoma cells?",
            "label": "vemurafenib-BRAF-MAPK",
            "expect_keywords": ["BRAF", "MAPK", "pathway", "signaling"],
        },
        {
            "query": "What is the role of the PI3K AKT mTOR signaling axis in cancer "
                     "cell survival and how do PI3K inhibitors disrupt this pathway?",
            "label": "PI3K-AKT-mTOR-pathway",
            "expect_keywords": ["PI3K", "AKT", "mTOR", "pathway"],
        },
    ],
    "comp_biologist": [
        {
            "query": "I need structural and sequence inputs to model imatinib-ABL1 binding — "
                     "what experimental and predicted structures and datasets exist?",
            "label": "ABL1-structures-datasets",
            "expect_keywords": ["structure", "sequence", "dataset", "AlphaFold"],
        },
        {
            "query": "What PDB structures, AlphaFold predictions and bioactivity datasets "
                     "exist for EGFR kinase to train a molecular docking model?",
            "label": "EGFR-docking-data",
            "expect_keywords": ["EGFR", "structure", "sequence", "dataset"],
        },
        {
            "query": "What structural data and ML-ready datasets are available "
                     "for TP53 to study its interaction with small molecule reactivators?",
            "label": "TP53-structural-data",
            "expect_keywords": ["TP53", "structure", "sequence", "dataset"],
        },
    ],
}

CARD_IDS = {
    "medicinal_chemist": "#card-medicinal_chemist",
    "pathologist":       "#card-pathologist",
    "cell_biologist":    "#card-cell_biologist",
    "comp_biologist":    "#card-comp_biologist",
}

PERSONA_COLORS = {
    "medicinal_chemist": "sky",
    "pathologist":       "amber",
    "cell_biologist":    "emerald",
    "comp_biologist":    "violet",
}


# ── Helpers ───────────────────────────────────────────────────────────────────

def _wait_for_streaming_complete(page: Page, selector: str, timeout: int = LLM_TIMEOUT) -> str:
    """Wait until the panel has content AND the status bar shows Complete."""
    content_el = page.locator(selector)
    expect(content_el).not_to_be_empty(timeout=timeout)

    # Wait for "Complete" in status bar
    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=timeout)

    return content_el.inner_text()


def _select_persona_and_navigate(page: Page, persona_id: str) -> None:
    """Go to landing and click the persona card."""
    page.goto(BASE_URL)
    page.wait_for_load_state("networkidle", timeout=UI_TIMEOUT)
    page.click(CARD_IDS[persona_id])
    expect(page.locator("#query-view")).to_be_visible(timeout=UI_TIMEOUT)


def _run_query_and_wait(page: Page, query: str, selector: str) -> str:
    """Fill query, click Run, wait for streaming to finish, return response text."""
    page.fill("#query-input", query)
    time.sleep(0.4)   # brief pause so the slowmo recording shows typing
    page.click("button:has-text('▶ Run')")
    expect(page.locator("#status-bar")).to_be_visible(timeout=UI_TIMEOUT)
    return _wait_for_streaming_complete(page, selector)


# ── Medicinal Chemist — 3 questions ──────────────────────────────────────────

@pytest.mark.parametrize("q", QUESTIONS["medicinal_chemist"],
                         ids=[q["label"] for q in QUESTIONS["medicinal_chemist"]])
def test_medicinal_chemist(page: Page, q: dict):
    """
    Medicinal Chemist persona: verify SAR/potency/structure content
    appears for each query.
    """
    _select_persona_and_navigate(page, "medicinal_chemist")

    text = _run_query_and_wait(page, q["query"], "#single-content")

    assert len(text) > 150, f"Response too short ({len(text)} chars)"

    matched = [kw for kw in q["expect_keywords"] if kw.lower() in text.lower()]
    assert matched, (
        f"[medicinal_chemist / {q['label']}] "
        f"None of {q['expect_keywords']} found.\n"
        f"Preview: {text[:400]}"
    )
    print(f"\n  ✓ medicinal_chemist / {q['label']}: "
          f"{len(text)} chars, matched={matched}")


# ── Pathologist — 3 questions ─────────────────────────────────────────────────

@pytest.mark.parametrize("q", QUESTIONS["pathologist"],
                         ids=[q["label"] for q in QUESTIONS["pathologist"]])
def test_pathologist(page: Page, q: dict):
    """
    Pathologist persona: verify mutation/resistance/clinical content
    appears for each query.
    """
    _select_persona_and_navigate(page, "pathologist")

    text = _run_query_and_wait(page, q["query"], "#single-content")

    assert len(text) > 150
    matched = [kw for kw in q["expect_keywords"] if kw.lower() in text.lower()]
    assert matched, (
        f"[pathologist / {q['label']}] "
        f"None of {q['expect_keywords']} found.\n"
        f"Preview: {text[:400]}"
    )
    print(f"\n  ✓ pathologist / {q['label']}: {len(text)} chars, matched={matched}")


# ── Cell Biologist — 3 questions ──────────────────────────────────────────────

@pytest.mark.parametrize("q", QUESTIONS["cell_biologist"],
                         ids=[q["label"] for q in QUESTIONS["cell_biologist"]])
def test_cell_biologist(page: Page, q: dict):
    """
    Cell Biologist persona: verify pathway/signaling/mechanism content
    appears for each query.
    """
    _select_persona_and_navigate(page, "cell_biologist")

    text = _run_query_and_wait(page, q["query"], "#single-content")

    assert len(text) > 150
    matched = [kw for kw in q["expect_keywords"] if kw.lower() in text.lower()]
    assert matched, (
        f"[cell_biologist / {q['label']}] "
        f"None of {q['expect_keywords']} found.\n"
        f"Preview: {text[:400]}"
    )
    print(f"\n  ✓ cell_biologist / {q['label']}: {len(text)} chars, matched={matched}")


# ── Computational Biologist — 3 questions ─────────────────────────────────────

@pytest.mark.parametrize("q", QUESTIONS["comp_biologist"],
                         ids=[q["label"] for q in QUESTIONS["comp_biologist"]])
def test_comp_biologist(page: Page, q: dict):
    """
    Computational Biologist persona: verify structure/sequence/dataset content
    appears for each query.
    """
    _select_persona_and_navigate(page, "comp_biologist")

    text = _run_query_and_wait(page, q["query"], "#single-content")

    assert len(text) > 150
    matched = [kw for kw in q["expect_keywords"] if kw.lower() in text.lower()]
    assert matched, (
        f"[comp_biologist / {q['label']}] "
        f"None of {q['expect_keywords']} found.\n"
        f"Preview: {text[:400]}"
    )
    print(f"\n  ✓ comp_biologist / {q['label']}: {len(text)} chars, matched={matched}")


# ── 4-panel compare — 2 shared queries ────────────────────────────────────────

@pytest.mark.parametrize("query,label", [
    (
        "What do I need to know about imatinib and its target ABL1?",
        "compare-imatinib-ABL1",
    ),
    (
        "What do I need to know about gefitinib and its target EGFR?",
        "compare-gefitinib-EGFR",
    ),
])
def test_compare_mode_all_panels(page: Page, query: str, label: str):
    """
    4-panel compare mode: all 4 personas respond with distinct content
    for the same query. This is the main demo-day test.
    """
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")
    expect(page.locator("#compare-panels")).to_be_visible(timeout=UI_TIMEOUT)

    page.fill("#query-input", query)
    time.sleep(0.4)
    page.click("button:has-text('▶ Run')")
    expect(page.locator("#status-bar")).to_be_visible(timeout=UI_TIMEOUT)

    # Wait for all 4 panels to populate
    panels = ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]
    for pid in panels:
        expect(page.locator(f"#panel-{pid}")).not_to_be_empty(timeout=LLM_TIMEOUT)

    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=LLM_TIMEOUT)

    # Collect and compare texts
    texts = {pid: page.locator(f"#panel-{pid}").inner_text() for pid in panels}

    for pid, text in texts.items():
        assert len(text) > 100, f"[{label}] Panel {pid} too short: {len(text)} chars"

    # All 4 panels must be DIFFERENT (the whole point of PRISM)
    assert len(set(texts.values())) == 4, \
        f"[{label}] Some panels have identical responses — persona routing may be broken"

    # Footer must show entity info
    expect(page.locator("#footer-meta")).to_be_visible(timeout=UI_TIMEOUT)

    print(f"\n  ✓ compare / {label}:")
    for pid, text in texts.items():
        print(f"    [{pid}] {len(text)} chars")


# ── Auto-detect persona — natural language ────────────────────────────────────

@pytest.mark.parametrize("query,expected_persona,description", [
    (
        "I want to optimize the N-methylpiperazine tail of imatinib to improve "
        "aqueous solubility while maintaining IC50 below 10nM against ABL1",
        "medicinal_chemist",
        "chemistry-optimization-language",
    ),
    (
        "My CML patient has a T315I gatekeeper mutation and is no longer "
        "responding to imatinib — what are the clinical options?",
        "pathologist",
        "clinical-patient-language",
    ),
    (
        "How does constitutively active BCR-ABL drive RAS-MAPK and STAT5 "
        "signaling and what happens to downstream effectors when imatinib binds?",
        "cell_biologist",
        "mechanism-signaling-language",
    ),
    (
        "I need to run molecular dynamics on ABL1 — what experimental PDB entries "
        "have the highest resolution and what pLDDT score does the AlphaFold model have?",
        "comp_biologist",
        "computational-modeling-language",
    ),
])
def test_auto_detect_persona_from_query_language(
    page: Page, query: str, expected_persona: str, description: str
):
    """
    Skip role selection — type a domain-specific query.
    The system should detect the persona from language and show the detect banner.
    """
    page.goto(BASE_URL)
    # Go directly to compare mode (no role selected)
    page.click("text=see all 4 expert views")
    expect(page.locator("#compare-panels")).to_be_visible(timeout=UI_TIMEOUT)

    page.fill("#query-input", query)
    time.sleep(0.4)
    page.click("button:has-text('▶ Run')")

    # Status bar must appear (query fired)
    expect(page.locator("#status-bar")).to_be_visible(timeout=UI_TIMEOUT)

    # All 4 panels should stream since we're in compare mode
    for pid in ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]:
        expect(page.locator(f"#panel-{pid}")).not_to_be_empty(timeout=LLM_TIMEOUT)

    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=LLM_TIMEOUT)

    print(f"\n  ✓ auto-detect / {description}: all 4 panels populated")
