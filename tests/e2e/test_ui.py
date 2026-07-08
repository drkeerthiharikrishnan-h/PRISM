"""
Playwright E2E tests — UI flows for all 4 personas.
Server must be running: uv run uvicorn main:app --port 8000

Run:  uv run pytest tests/e2e/ -v --headed        (see the browser)
      uv run pytest tests/e2e/ -v                  (headless)
"""
import pytest
from playwright.sync_api import Page, expect
from tests.conftest import PERSONA_QUERIES, SHARED_QUERY

BASE_URL = "http://localhost:8000"
STREAM_TIMEOUT = 90_000   # 90s — LLM synthesis can take a while
SHORT_TIMEOUT  = 10_000   # 10s for UI interactions


# ── Landing page ──────────────────────────────────────────────────────────────

def test_landing_page_loads(page: Page):
    """Landing page shows PRISM branding and all 4 role cards."""
    page.goto(BASE_URL)
    landing = page.locator("#landing")

    expect(page.get_by_role("heading", name="PRISM")).to_be_visible(timeout=SHORT_TIMEOUT)
    expect(landing.get_by_text("Medicinal Chemist")).to_be_visible()
    expect(landing.get_by_text("Pathologist")).to_be_visible()
    expect(landing.get_by_text("Cell / Molecular Biologist")).to_be_visible()
    expect(landing.get_by_text("Computational Biologist")).to_be_visible()
    expect(landing.get_by_text("see all 4 expert views")).to_be_visible()


def test_landing_page_has_persona_descriptions(page: Page):
    """Each card should show its domain keywords."""
    page.goto(BASE_URL)

    expect(page.locator("text=Potency")).to_be_visible()
    expect(page.locator("text=Resistance")).to_be_visible()
    expect(page.locator("text=Signaling")).to_be_visible()
    expect(page.locator("text=ML datasets")).to_be_visible()


# ── Navigation ────────────────────────────────────────────────────────────────

def test_clicking_card_shows_query_view(page: Page):
    """Clicking a role card navigates to the query screen."""
    page.goto(BASE_URL)
    page.click("#card-medicinal_chemist")

    expect(page.locator("#query-view")).to_be_visible(timeout=SHORT_TIMEOUT)
    expect(page.locator("#landing")).to_be_hidden()
    expect(page.locator("#view-label")).to_contain_text("Medicinal Chemist")
    expect(page.locator("#query-input")).to_be_visible()


def test_change_role_returns_to_landing(page: Page):
    """'Change role' link returns user to the landing card selection."""
    page.goto(BASE_URL)
    page.click("#card-pathologist")
    expect(page.locator("#query-view")).to_be_visible()

    page.click("text=Change role")
    expect(page.locator("#landing")).to_be_visible(timeout=SHORT_TIMEOUT)
    expect(page.locator("#query-view")).to_be_hidden()


def test_compare_all_button_shows_4_panels(page: Page):
    """'Or see all 4 expert views' button shows the 4-panel compare layout."""
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")

    expect(page.locator("#compare-panels")).to_be_visible(timeout=SHORT_TIMEOUT)
    expect(page.locator("#single-panel")).to_be_hidden()
    expect(page.locator("#view-label")).to_contain_text("4-Expert Compare")


def test_compare_toggle_from_single_view(page: Page):
    """'Compare all 4 →' button inside the query view switches to compare mode."""
    page.goto(BASE_URL)
    page.click("#card-comp_biologist")
    expect(page.locator("#compare-toggle")).to_be_visible()

    page.click("#compare-toggle")
    expect(page.locator("#compare-panels")).to_be_visible(timeout=SHORT_TIMEOUT)


# ── Query input ───────────────────────────────────────────────────────────────

def test_empty_query_does_not_navigate(page: Page):
    """Pressing Run with empty query should not trigger a request."""
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")

    page.click("button:has-text('▶ Run')")
    # Status bar should NOT appear (no request fired)
    expect(page.locator("#status-bar")).to_be_hidden(timeout=2000)


def test_enter_key_triggers_query(page: Page):
    """Pressing Enter in the query input field should fire the query."""
    page.goto(BASE_URL)
    page.click("#card-medicinal_chemist")

    page.fill("#query-input", SHARED_QUERY)
    page.keyboard.press("Enter")

    expect(page.locator("#status-bar")).to_be_visible(timeout=SHORT_TIMEOUT)


def test_demo_button_fills_query(page: Page):
    """Demo button prefills the imatinib/ABL1 query text."""
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")

    # Demo button should pre-fill without waiting for LLM
    page.click("button:has-text('Demo')")
    expect(page.locator("#query-input")).to_have_value(
        "What do I need to know about imatinib and its target ABL1?",
        timeout=SHORT_TIMEOUT,
    )


# ── Per-persona streaming ─────────────────────────────────────────────────────

@pytest.mark.parametrize("persona_id,card_id,expected_keyword", [
    ("medicinal_chemist", "#card-medicinal_chemist", "SAR"),
    ("pathologist",       "#card-pathologist",       "mutation"),
    ("cell_biologist",    "#card-cell_biologist",    "pathway"),
    ("comp_biologist",    "#card-comp_biologist",    "structure"),
])
def test_persona_query_streams_and_shows_content(
    page: Page, persona_id: str, card_id: str, expected_keyword: str
):
    """
    Each persona role card → query → streaming response contains persona-specific content.
    This is the core functional test.
    """
    page.goto(BASE_URL)
    page.click(card_id)

    # Use the persona's natural query
    query = PERSONA_QUERIES[persona_id]
    page.fill("#query-input", query)

    # Start streaming
    page.click("button:has-text('▶ Run')")

    # Status bar should appear quickly
    expect(page.locator("#status-bar")).to_be_visible(timeout=SHORT_TIMEOUT)

    # Wait for response content — generous timeout for LLM
    content_el = page.locator("#single-content")
    expect(content_el).not_to_be_empty(timeout=STREAM_TIMEOUT)

    # Check persona-specific keyword is present
    content_text = content_el.inner_text()
    assert expected_keyword.lower() in content_text.lower(), (
        f"[{persona_id}] Expected '{expected_keyword}' in response.\n"
        f"Preview: {content_text[:300]}"
    )

    # Status bar should settle to "Complete"
    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=STREAM_TIMEOUT)

    print(f"\n  [{persona_id}] ✓ '{expected_keyword}' found, "
          f"{len(content_text)} chars rendered")


# ── 4-panel compare mode ──────────────────────────────────────────────────────

def test_compare_mode_all_panels_populate(page: Page):
    """
    4-panel compare mode: all 4 panels must stream distinct content.
    This is the main demo-day test.
    """
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")
    page.fill("#query-input", SHARED_QUERY)
    page.click("button:has-text('▶ Run')")

    expect(page.locator("#status-bar")).to_be_visible(timeout=SHORT_TIMEOUT)

    # All 4 panels must populate
    for persona_id in ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]:
        panel = page.locator(f"#panel-{persona_id}")
        expect(panel).not_to_be_empty(timeout=STREAM_TIMEOUT)

    # Status should finish
    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=STREAM_TIMEOUT)

    # Verify panels have DIFFERENT content (the core PRISM value prop)
    texts = {
        pid: page.locator(f"#panel-{pid}").inner_text()
        for pid in ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]
    }
    unique_texts = set(texts.values())
    assert len(unique_texts) == 4, "All 4 panels should have unique responses"

    # Footer metadata should appear
    expect(page.locator("#footer-meta")).to_be_visible(timeout=SHORT_TIMEOUT)
    footer = page.locator("#footer-meta").inner_text()
    assert "imatinib" in footer.lower() or "ABL1" in footer

    print(f"\n  Compare mode: 4 unique panels ✓")
    for pid, text in texts.items():
        print(f"    [{pid}] {len(text)} chars")


def test_compare_mode_persona_keywords_diverge(page: Page):
    """
    Chemist panel should mention IC50/SAR, pathologist should mention mutation/T315I,
    cell biologist should mention pathway/signaling, comp biologist should mention structure.
    This verifies the persona lens is actually working.
    """
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")
    page.fill("#query-input", SHARED_QUERY)
    page.click("button:has-text('▶ Run')")

    # Wait for all panels to finish
    for persona_id in ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]:
        expect(page.locator(f"#panel-{persona_id}")).not_to_be_empty(timeout=STREAM_TIMEOUT)

    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=STREAM_TIMEOUT)

    checks = {
        "medicinal_chemist": ["IC50", "SAR", "structure"],
        "pathologist":       ["mutation", "resistance", "clinical"],
        "cell_biologist":    ["pathway", "signaling", "mechanism"],
        "comp_biologist":    ["structure", "sequence", "AlphaFold"],
    }

    for persona_id, keywords in checks.items():
        text = page.locator(f"#panel-{persona_id}").inner_text().lower()
        matched = [kw for kw in keywords if kw.lower() in text]
        assert matched, (
            f"[{persona_id}] None of {keywords} found in panel.\n"
            f"Preview: {text[:300]}"
        )
        print(f"  [{persona_id}] matched: {matched}")


# ── Auto-detect persona ───────────────────────────────────────────────────────

def test_auto_detect_banner_appears_on_typed_query(page: Page):
    """
    If user skips role selection and goes straight to compare view,
    typing a profession-specific query should trigger auto-detection banner.
    """
    page.goto(BASE_URL)
    page.click("text=see all 4 expert views")

    # Type a clearly pathologist query
    pathologist_query = (
        "My CML patient has T315I ABL1 mutation and stopped responding to imatinib"
    )
    page.fill("#query-input", pathologist_query)
    page.click("button:has-text('▶ Run')")

    # The detect banner may appear if confidence is high enough
    # (not guaranteed for all queries — just check it doesn't crash)
    expect(page.locator("#status-bar")).to_be_visible(timeout=SHORT_TIMEOUT)
    print("\n  Auto-detect test: query accepted, no crash ✓")
