from assistant.browser import BrowserPage
from typing import List


def setup_HEB_search_location(page: BrowserPage, zip_code: int = 78209) -> None:
    """Sets up HEB store location for web scraping session.

    Navigates to HEB website and configures the store location based on provided
    zip code by selecting the first available store in that area.

    Args:
        page (BrowserPage): Playwright browser page object for web interaction
        zip_code (int): ZIP code to search for nearby HEB stores

    Returns:
        None

    Example:
        >>> setup_HEB_search_location(page, 78701)
    """
    url = "https://www.heb.com/"
    page.goto(url, wait_until="networkidle")

    # Set Pickup fulfillment for store nearest zip code
    change_store_button = page.get_by_test_id("header_change_store")
    change_store_button.wait_for()
    change_store_button.click()

    address_input = page.locator('#address-input')
    address_input.wait_for()
    address_input.fill(str(zip_code))

    search_button = page.locator('button:has-text("Search")')
    search_button.wait_for()
    search_button.click()

    page.locator('p:has-text(" stores near ")').wait_for()

    store_card = page.locator('[data-qe-id="storeCard"]').first
    store_card.wait_for()
    select_store_btn = store_card.locator(
        'button:has-text("Store")'
        )
    select_store_btn.click()
    return None


def find_product_at_HEB(product_query: str,
                        browser_page: BrowserPage) -> List[str]:
    """
    Search for available products at HEB grocery store's website.

    Args:
        product_query (str): Search term for the product
        browser_page (BrowserPage): Browser page object for web interaction

    Returns:
        List[str]: List of product titles that are in stock. Empty list if no products
                  found or in case of errors

    Raises:
        Exception: For any errors during web scraping or page navigation

    Example:
        >>> browser = BrowserPage()
        >>> products = find_product_at_HEB("milk", browser, 78209)
        >>> print(products)
        ['H-E-B Select Ingredients Whole Milk', 'H-E-B Select 2% Reduced Fat Milk']
    """
    try:
        # Navigate to the search URL for the desired product
        product_encoded = product_query.replace(' ', '%20')
        search_url = f"https://www.heb.com/search?esc=true&q={product_encoded}"
        browser_page.goto(search_url, wait_until="networkidle")

        # Extract product cards, filtering out out-of-stock items
        product_cards = browser_page.locator('div[data-qe-id="productCard"]')
        count = product_cards.count()

        results = []
        for i in range(count):
            card = product_cards.nth(i)
            out_of_stock = card.locator(
                'button[data-qe-id="addToCart"] span:has-text("Out of stock")'
            ).count() > 0

            if not out_of_stock:
                title = card.locator(
                    'div[data-qe-id="productTitle"] span'
                ).get_attribute('title')
                results.append(title)

        return results

    except Exception as e:
        print(f"Error searching for products: {e}")
        return []
