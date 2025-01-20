import pytest
from unittest.mock import MagicMock, patch
from assistant.browser import BrowserManager, BrowserPage


@pytest.fixture
def mock_playwright():
    with patch("assistant.browser.sync_playwright") as mock_sync_playwright:
        mock_playwright_instance = MagicMock()
        mock_sync_playwright.return_value.__enter__.return_value = mock_playwright_instance
        yield mock_playwright_instance


def test_browser_manager_initialization():
    manager = BrowserManager(user_data_dir="test_data", debug=True)
    assert manager.user_data_dir.name == "test_data"
    assert manager.debug is True
    assert manager.playwright is None
    assert manager.browser_context is None


def test_browser_manager_start(mock_playwright):
    manager = BrowserManager(user_data_dir="test_data", debug=True)
    mock_context = MagicMock()
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context

    page = manager.start()

    assert manager.browser_context == mock_context
    assert isinstance(page, BrowserPage)
    mock_playwright.chromium.launch_persistent_context.assert_called_once()


def test_browser_manager_stop(mock_playwright):
    manager = BrowserManager(user_data_dir="test_data", debug=True)
    mock_context = MagicMock()
    mock_playwright.chromium.launch_persistent_context.return_value = mock_context

    manager.start()
    manager.stop()

    assert manager.browser_context is None
    assert manager.playwright is None
    mock_context.close.assert_called_once()
    mock_playwright.stop.assert_called_once()


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
