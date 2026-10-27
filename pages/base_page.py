from playwright.sync_api import Page
from config import BASE_URL

class BasePage:
    """One SauceDemo page: its URL, plus the header that every logged-in page shares"""

    URL = BASE_URL

    def __init__(self, page: Page):
        self.page = page
        # Locators are lazy: nothing is looked up until a test or method uses them
        self.title = page.get_by_test_id("title")
        self.cart_badge = page.get_by_test_id("shopping-cart-badge")
        self.cart_link = page.get_by_test_id("shopping-cart-link")
        # No data-test here; visual_user's misplaced cart icon shows up as a class on it
        self.cart_container = page.locator(".shopping_cart_container")

    def open(self):
        self.page.goto(self.URL)

    def open_cart(self):
        self.cart_link.click()

    def expect_loaded(self):
        """Assert the user is on this page"""
        raise NotImplementedError
