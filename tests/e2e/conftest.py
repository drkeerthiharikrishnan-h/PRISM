"""
E2E conftest — configures Playwright for headed, video-recorded test runs.
Videos + traces saved to: test-recordings/<test-name>/
"""
import pytest


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure viewport and recording for all E2E tests."""
    return {
        **browser_context_args,
        "viewport": {"width": 1440, "height": 900},
        "record_video_size": {"width": 1440, "height": 900},
    }
