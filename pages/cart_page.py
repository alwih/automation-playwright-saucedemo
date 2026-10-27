from playwright.sync_api import Page, expect
from config import BASE_URL
from pages.base_page import BasePage

class CartPage(BasePage):
    URL = f"{BASE_URL}/cart.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_have_text("Your Cart")

    def continue_shopping(self):
        self.continue_shopping_button.click()
