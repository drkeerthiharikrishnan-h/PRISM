"""Record Facet demo videos for Daraxonrasib vs Sotorasib.

This script generates one video for the 4-panel compare view and one video for
each persona-specific run. Videos are saved as .webm files inside the chosen
output directory, which defaults to Downloads.

Run:
  uv run python scripts/record_daraxonrasib_demo.py \
    --output-dir /Users/keerthi/Downloads/facet-demo-recordings
"""

from __future__ import annotations

import argparse
import time
from pathlib import Path

from playwright.sync_api import expect, sync_playwright


BASE_URL = "http://127.0.0.1:8000"
QUERY = "**Compare Daraxonrasib with Sotorasib"

PERSONA_RUNS = [
    ("medicinal_chemist", "#card-medicinal_chemist", QUERY),
    ("pathologist", "#card-pathologist", QUERY),
    ("cell_biologist", "#card-cell_biologist", QUERY),
    ("comp_biologist", "#card-comp_biologist", QUERY),
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.home() / "Downloads" / "facet-demo-recordings",
        help="Directory where the .webm files will be written.",
    )
    parser.add_argument(
        "--slowmo",
        type=int,
        default=500,
        help="Milliseconds to slow down interactions for a more watchable recording.",
    )
    parser.add_argument(
        "--headless",
        action="store_true",
        help="Run Chromium headless while still recording video.",
    )
    parser.add_argument(
        "--timeout-ms",
        type=int,
        default=120_000,
        help="Timeout for waiting on streamed responses.",
    )
    return parser.parse_args()


def _wait_for_response(page, selector: str, timeout_ms: int) -> str:
    content = page.locator(selector)
    expect(content).not_to_be_empty(timeout=timeout_ms)
    expect(page.locator("#status-bar")).to_contain_text("Complete", timeout=timeout_ms)
    return content.inner_text()


def _run_compare(page, timeout_ms: int) -> str:
    page.goto(BASE_URL)
    page.get_by_role("button", name="Compare all 4 expert views side-by-side").click()
    expect(page.locator("#query-input")).to_be_visible(timeout=10_000)
    page.fill("#query-input", QUERY)
    time.sleep(0.4)
    page.click("button:has-text('▶ Run')")
    expect(page.locator("#status-bar")).to_be_visible(timeout=10_000)
    for pid in ["medicinal_chemist", "pathologist", "cell_biologist", "comp_biologist"]:
        expect(page.locator(f"#panel-{pid}")).not_to_be_empty(timeout=timeout_ms)
    expect(page.locator("#footer-meta")).to_be_visible(timeout=timeout_ms)
    return page.locator("#compare-panels").inner_text()


def _run_persona(page, card_selector: str, query: str, timeout_ms: int) -> str:
    page.goto(BASE_URL)
    page.click(card_selector)
    expect(page.locator("#query-view")).to_be_visible(timeout=10_000)
    page.fill("#query-input", query)
    time.sleep(0.4)
    page.click("button:has-text('▶ Run')")
    expect(page.locator("#status-bar")).to_be_visible(timeout=10_000)
    return _wait_for_response(page, "#single-content", timeout_ms)


def _rename_video(session_dir: Path, target_name: str) -> Path:
    videos = sorted(session_dir.glob("**/*.webm"))
    if not videos:
        raise FileNotFoundError(f"No .webm video found in {session_dir}")
    target = session_dir / target_name
    videos[0].rename(target)
    return target


def main() -> None:
    args = parse_args()
    args.output_dir.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=args.headless, slow_mo=args.slowmo)

        # 4-panel compare recording.
        compare_dir = args.output_dir / "compare_all_4"
        compare_dir.mkdir(parents=True, exist_ok=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(compare_dir), record_video_size={"width": 1440, "height": 900})
        page = context.new_page()
        compare_text = _run_compare(page, args.timeout_ms)
        page.wait_for_timeout(1500)
        context.close()
        compare_video = _rename_video(compare_dir, "compare_all_4.webm")
        print(f"saved {compare_video}")
        print(f"compare preview: {compare_text[:250]}\n")

        # Persona-specific recordings.
        for persona_id, card_selector, persona_query in PERSONA_RUNS:
            persona_dir = args.output_dir / persona_id
            persona_dir.mkdir(parents=True, exist_ok=True)
            context = browser.new_context(viewport={"width": 1440, "height": 900}, record_video_dir=str(persona_dir), record_video_size={"width": 1440, "height": 900})
            page = context.new_page()
            response = _run_persona(page, card_selector, persona_query, args.timeout_ms)
            page.wait_for_timeout(1500)
            context.close()
            video_path = _rename_video(persona_dir, f"{persona_id}.webm")
            print(f"saved {video_path}")
            print(f"{persona_id} preview: {response[:250]}\n")

        browser.close()


if __name__ == "__main__":
    main()