import pytest
from unittest.mock import MagicMock
from assistant.tools.grocery import find_product_at_HEB


@pytest.fixture
def mock_browser_page():
    return MagicMock()


def test_find_product_in_stock(mock_browser_page):
    product_cards = MagicMock()
    product_cards.count.return_value = 2
    card_in_stock = MagicMock()
    card_in_stock.locator.return_value.count.return_value = 0
    card_in_stock.locator.return_value.get_attribute.return_value = (
        "Test Product"
    )
    product_cards.nth.side_effect = [card_in_stock, card_in_stock]
    mock_browser_page.locator.return_value = product_cards
    results = find_product_at_HEB("milk", mock_browser_page)
    assert results == ["Test Product", "Test Product"]


def test_find_product_out_of_stock(mock_browser_page):
    product_cards = MagicMock()
    product_cards.count.return_value = 1
    card_out_of_stock = MagicMock()
    # Simulate the out-of-stock button text
    card_out_of_stock.locator.return_value.count.return_value = 1
    product_cards.nth.return_value = card_out_of_stock
    mock_browser_page.locator.return_value = product_cards
    results = find_product_at_HEB("milk", mock_browser_page)
    assert results == []


def test_find_product_no_cards(mock_browser_page):
    product_cards = MagicMock()
    product_cards.count.return_value = 0
    mock_browser_page.locator.return_value = product_cards
    results = find_product_at_HEB("milk", mock_browser_page)
    assert results == []


def test_find_product_exception(mock_browser_page):
    mock_browser_page.goto.side_effect = Exception("Network error")
    results = find_product_at_HEB("milk", mock_browser_page)
    assert results == []
