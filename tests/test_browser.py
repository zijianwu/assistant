from pathlib import Path
import pytest
from unittest.mock import MagicMock
from assistant.browser import BrowserManager, BrowserPage
import shutil


def test_browser_manager_initialization():
    manager = BrowserManager(user_data_dir="test_data", debug=True)
    try:
        assert manager.user_data_dir.name == "test_data"
        assert manager.debug is True
        assert manager.playwright is None
        assert manager.browser_context is None
    finally:
        # Clean up test data directory
        if manager.user_data_dir.exists():
            shutil.rmtree(manager.user_data_dir)


def test_browser_page_attribute_delegation():
    mock_playwright_page = MagicMock()
    page = BrowserPage(mock_playwright_page)

    mock_playwright_page.title.return_value = "Test Title"
    assert page.title() == "Test Title"
    mock_playwright_page.title.assert_called_once()


def test_browser_page_representation():
    mock_playwright_page = MagicMock()
    page = BrowserPage(mock_playwright_page)

    assert repr(page) == "<BrowserPage wrapper of Playwright Page"


@pytest.fixture
def temp_browser_data_dir(tmp_path):
    """
    Create a temporary directory for browser user data.
    Pytest will clean it up automatically after each test.
    """
    return tmp_path / "browser_data"


@pytest.fixture
def manager(temp_browser_data_dir):
    """
    Provide a fresh BrowserManager instance per test.
    """
    # Initialize with debug=False to run in headless mode (faster, no UI).
    # If you want to see the actual browser for debugging, set debug=True.
    return BrowserManager(user_data_dir=str(temp_browser_data_dir),
                          debug=False)


def test_init_creates_user_data_dir(manager, temp_browser_data_dir):
    """
    Test that the user_data_dir is created upon initialization.
    """
    # Check that the directory exists
    assert Path(temp_browser_data_dir).exists(), (
            "The user_data_dir was not created."
    )
    # Check the manager's internal attribute
    assert manager.user_data_dir == Path(temp_browser_data_dir)


def test_start_creates_browser_context_and_page(manager):
    """
    Test that calling start() creates a new browser context and
    returns a BrowserPage.
    """
    page = manager.start()
    # Assert the browser_context is not None
    assert manager.browser_context is not None, (
        "Browser context should be initialized."
    )
    # Assert we got a BrowserPage wrapper back
    assert page is not None, "Expected a BrowserPage instance."
    assert page.__class__.__name__ == "BrowserPage", (
        "Returned object should be a BrowserPage."
    )


def test_start_does_not_reinitialize_browser_if_already_started(manager):
    """
    Test that calling start() again uses the existing browser
    context rather than creating a new one.
    """
    manager.start()
    first_context = manager.browser_context
    manager.start()
    second_context = manager.browser_context

    # They should be the same object
    assert first_context == second_context, (
        "Browser context should be reused for subsequent starts."
    )


def test_stop_closes_browser_context(manager):
    """
    Test that stop() closes the browser context and sets it to None.
    """
    manager.start()
    manager.stop()
    assert manager.browser_context is None, (
        "Browser context should be None after stop()"
    )
    assert manager.playwright is None, (
        "Playwright instance should be None after stop()"
    )


def test_stop_without_start(manager):
    """
    Stopping without having started should not raise an error.
    """
    try:
        manager.stop()
    except Exception as e:
        pytest.fail(
            f"stop() raised an exception when stopping "
            f"an uninitialized browser: {e}")
