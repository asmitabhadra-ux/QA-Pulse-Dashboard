"""
Login flow tests for SauceDemo.
Covers: valid login, locked user, empty fields, invalid credentials.
"""
import pytest
from playwright.sync_api import Page, expect


class TestLogin:

    def test_valid_login(self, page: Page, base_url, valid_credentials):
        """Standard user can log in and reach the inventory page."""
        page.goto(base_url)
        page.fill("#user-name", valid_credentials["username"])
        page.fill("#password", valid_credentials["password"])
        page.click("#login-button")
        expect(page).to_have_url(f"{base_url}/inventory.html")
        expect(page.locator(".inventory_list")).to_be_visible()

    def test_locked_out_user(self, page: Page, base_url, locked_credentials):
        """Locked user sees a descriptive error message."""
        page.goto(base_url)
        page.fill("#user-name", locked_credentials["username"])
        page.fill("#password", locked_credentials["password"])
        page.click("#login-button")
        error = page.locator("[data-test='error']")
        expect(error).to_be_visible()
        expect(error).to_contain_text("locked out")

    def test_empty_username(self, page: Page, base_url):
        """Submitting with no username shows a validation error."""
        page.goto(base_url)
        page.fill("#password", "secret_sauce")
        page.click("#login-button")
        expect(page.locator("[data-test='error']")).to_contain_text("Username is required")

    def test_empty_password(self, page: Page, base_url):
        """Submitting with no password shows a validation error."""
        page.goto(base_url)
        page.fill("#user-name", "standard_user")
        page.click("#login-button")
        expect(page.locator("[data-test='error']")).to_contain_text("Password is required")

    def test_invalid_credentials(self, page: Page, base_url):
        """Wrong credentials show a generic error — no credential hints."""
        page.goto(base_url)
        page.fill("#user-name", "wrong_user")
        page.fill("#password", "wrong_pass")
        page.click("#login-button")
        expect(page.locator("[data-test='error']")).to_contain_text(
            "Username and password do not match"
        )

    def test_logout(self, page: Page, base_url, valid_credentials):
        """Logged-in user can log out and is returned to the login page."""
        page.goto(base_url)
        page.fill("#user-name", valid_credentials["username"])
        page.fill("#password", valid_credentials["password"])
        page.click("#login-button")
        page.click("#react-burger-menu-btn")
        page.click("#logout_sidebar_link")
        expect(page).to_have_url(base_url + "/")
        expect(page.locator("#login-button")).to_be_visible()
