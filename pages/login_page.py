from playwright.sync_api import Page, expect
from config import BASE_URL
from data.users import PASSWORD
from pages.base_page import BasePage

class LoginPage(BasePage):
    URL = f"{BASE_URL}/"

    def __init__(self, page: Page):
        super().__init__(page)
        self.username_input = page.get_by_test_id("username")
        self.password_input = page.get_by_test_id("password")
        self.login_button = page.get_by_test_id("login-button")
        # The list of accepted usernames under the form
        self.credentials = page.get_by_test_id("login-credentials")

    def login(self, username: str = "standard_user", password: str = PASSWORD):
        """Open the login page and submit the form"""
        self.open()
        self.username_input.fill(username)
        self.password_input.fill(password)
        self.login_button.click()

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.login_button).to_be_visible()

    def expect_access_denied(self, path: str):
        """Assert a logged-out visit to path (e.g. '/cart.html') was sent back here with an error"""
        expect(self.page).to_have_url(self.URL)
        expect(self.error).to_have_text(f"Epic sadface: You can only access '{path}' when you are logged in.")
