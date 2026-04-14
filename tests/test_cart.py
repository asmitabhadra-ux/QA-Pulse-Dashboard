"""
Shopping cart tests for SauceDemo.
Covers: add item, remove item, cart badge count, empty cart.
"""
import pytest
from playwright.sync_api import Page, expect


@pytest.fixture(autouse=True)
def login(page: Page, base_url, valid_credentials):
    page.goto(base_url)
    page.fill("#user-name", valid_credentials["username"])
    page.fill("#password", valid_credentials["password"])
    page.click("#login-button")


class TestCart:

    def test_add_item_to_cart(self, page: Page):
        """Adding a product increments the cart badge to 1."""
        page.locator(".btn_inventory").first.click()
        expect(page.locator(".shopping_cart_badge")).to_have_text("1")

    def test_add_multiple_items(self, page: Page):
        """Adding two products shows badge count of 2."""
        buttons = page.locator(".btn_inventory").all()
        buttons[0].click()
        buttons[1].click()
        expect(page.locator(".shopping_cart_badge")).to_have_text("2")

    def test_remove_item_from_inventory(self, page: Page):
        """Removing an item from the inventory page clears the badge."""
        page.locator(".btn_inventory").first.click()
        page.locator(".btn_inventory").first.click()  # toggles to Remove → clicks Remove
        badge = page.locator(".shopping_cart_badge")
        expect(badge).not_to_be_visible()

    def test_cart_page_shows_added_item(self, page: Page, base_url):
        """Cart page lists the item that was added."""
        first_name = page.locator(".inventory_item_name").first.inner_text()
        page.locator(".btn_inventory").first.click()
        page.click(".shopping_cart_link")
        expect(page).to_have_url(f"{base_url}/cart.html")
        expect(page.locator(".cart_item_label")).to_contain_text(first_name)

    def test_empty_cart(self, page: Page, base_url):
        """Navigating to cart with no items shows no cart items."""
        page.click(".shopping_cart_link")
        expect(page).to_have_url(f"{base_url}/cart.html")
        assert page.locator(".cart_item").count() == 0
