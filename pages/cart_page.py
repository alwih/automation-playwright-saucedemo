from playwright.sync_api import Page, expect
from config import BASE_URL
from data.products import Product
from pages.base_page import BasePage

class CartPage(BasePage):
    URL = f"{BASE_URL}/cart.html"

    def __init__(self, page: Page):
        super().__init__(page)
        # Scoped to the cart list: the inventory list is still in the DOM for a moment after the URL changes
        self.items = page.get_by_test_id("cart-list").get_by_test_id("inventory-item")
        self.item_names = self.items.get_by_test_id("inventory-item-name")
        self.item_quantities = self.items.get_by_test_id("item-quantity")
        self.item_prices = self.items.get_by_test_id("inventory-item-price")
        self.continue_shopping_button = page.get_by_test_id("continue-shopping")
        self.checkout_button = page.get_by_test_id("checkout")

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_have_text("Your Cart")

    def remove(self, product: Product):
        self.items.get_by_test_id(f"remove-{product.slug}").click()

    def continue_shopping(self):
        self.continue_shopping_button.click()

    def checkout(self):
        self.checkout_button.click()
