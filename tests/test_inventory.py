"""
Inventory / product listing tests for SauceDemo.
Covers: page load, sorting, product detail navigation.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def login(page: Page, base_url, valid_credentials):
    """Log in before every test in this module."""
    page.goto(base_url)
    page.fill("#user-name", valid_credentials["username"])
    page.fill("#password", valid_credentials["password"])
    page.click("#login-button")
    expect(page).to_have_url(f"{base_url}/inventory.html")


class TestInventory:

    def test_inventory_loads(self, page: Page):
        """Inventory page displays at least one product."""
        items = page.locator(".inventory_item")
        expect(items.first).to_be_visible()
        assert items.count() > 0

    def test_product_count(self, page: Page):
        """Exactly 6 products are shown on the default inventory page."""
        assert page.locator(".inventory_item").count() == 6

    def test_sort_price_low_to_high(self, page: Page):
        """Price sort (low→high) orders products correctly."""
        page.select_option(".product_sort_container", "lohi")
        prices = [
            float(el.inner_text().replace("$", ""))
            for el in page.locator(".inventory_item_price").all()
        ]
        assert prices == sorted(prices), "Prices are not in ascending order"

    def test_sort_price_high_to_low(self, page: Page):
        """Price sort (high→low) orders products correctly."""
        page.select_option(".product_sort_container", "hilo")
        prices = [
            float(el.inner_text().replace("$", ""))
            for el in page.locator(".inventory_item_price").all()
        ]
        assert prices == sorted(prices, reverse=True)

    def test_sort_name_a_to_z(self, page: Page):
        """Name sort (A→Z) orders products alphabetically."""
        page.select_option(".product_sort_container", "az")
        names = [el.inner_text() for el in page.locator(".inventory_item_name").all()]
        assert names == sorted(names)

    def test_product_detail_navigation(self, page: Page, base_url):
        """Clicking a product name opens its detail page."""
        first_product = page.locator(".inventory_item_name").first
        product_name = first_product.inner_text()
        first_product.click()
        expect(page).to_have_url(f"{base_url}/inventory-item.html?id=4")
        expect(page.locator(".inventory_details_name")).to_contain_text(product_name)

    def test_back_to_products(self, page: Page):
        """Back button on detail page returns to inventory."""
        page.locator(".inventory_item_name").first.click()
        page.click("#back-to-products")
        expect(page.locator(".inventory_list")).to_be_visible()
