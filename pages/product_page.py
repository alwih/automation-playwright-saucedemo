import re

from playwright.sync_api import Page, expect
from config import BASE_URL
from pages.base_page import BasePage

class ProductPage(BasePage):
    """A product's detail page: /inventory-item.html?id=<id>"""

    URL = f"{BASE_URL}/inventory-item.html"

    def __init__(self, page: Page):
        super().__init__(page)
        # The detail page reuses the products page's data-test names (even "inventory-item" on this container),
        # so every read is scoped to it, through a class only the detail page has
        self.details = page.locator(".inventory_details_container")
        self.name = self.details.get_by_test_id("inventory-item-name")
        self.description = self.details.get_by_test_id("inventory-item-desc")
        self.price = self.details.get_by_test_id("inventory-item-price")
        self.image = self.details.get_by_test_id(re.compile(r"^item-.+-img$"))
        # No product suffix on the detail page's buttons
        self.add_button = page.get_by_test_id("add-to-cart")
        self.remove_button = page.get_by_test_id("remove")
        self.back_button = page.get_by_test_id("back-to-products")

    def open(self, query: str = ""):
        """Open the detail page URL directly (query is e.g. '?id=4')"""
        self.page.goto(f"{self.URL}{query}")

    def expect_loaded(self):
        expect(self.page).to_have_url(re.compile(rf"^{re.escape(self.URL)}"))
        expect(self.details).to_be_visible()

    def expect_product(self, product_id: int, name: str):
        """Assert the user is on the detail page of this product"""
        expect(self.page).to_have_url(f"{self.URL}?id={product_id}")
        expect(self.name).to_have_text(name)

    def add_to_cart(self):
        self.add_button.click()

    def remove(self):
        self.remove_button.click()

    def back_to_products(self):
        self.back_button.click()
