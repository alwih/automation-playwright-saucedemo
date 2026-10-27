import re

from playwright.sync_api import Locator, Page, expect
from config import BASE_URL
from data.products import PRODUCTS, Product
from pages.base_page import BasePage

class ProductCard:
    """One product's card on the Products page"""

    def __init__(self, root: Locator):
        self.root = root
        self.name = root.get_by_test_id("inventory-item-name")
        self.description = root.get_by_test_id("inventory-item-desc")
        self.price = root.get_by_test_id("inventory-item-price")
        self.image = root.get_by_test_id(re.compile(r"^inventory-item-.+-img$"))

class InventoryPage(BasePage):
    """The Products page, where a logged-in user lands"""

    URL = f"{BASE_URL}/inventory.html"
    # Option value -> label shown on the dropdown, in the order the dropdown lists them
    SORT_OPTIONS = {
        "az": "Name (A to Z)",
        "za": "Name (Z to A)",
        "lohi": "Price (low to high)",
        "hilo": "Price (high to low)",
    }

    def __init__(self, page: Page):
        super().__init__(page)
        self.list = page.get_by_test_id("inventory-list")
        self.cards = page.get_by_test_id("inventory-item")
        self.names = page.get_by_test_id("inventory-item-name")
        self.prices = page.get_by_test_id("inventory-item-price")
        self.images = page.get_by_test_id(re.compile(r"^inventory-item-.+-img$"))
        self.add_buttons = page.get_by_test_id(re.compile(r"^add-to-cart-"))
        self.remove_buttons = page.get_by_test_id(re.compile(r"^remove-"))
        self.sort_dropdown = page.get_by_test_id("product-sort-container")
        self.sort_dropdown_options = self.sort_dropdown.locator("option")
        self.active_sort = page.get_by_test_id("active-option")

    def expect_loaded(self, timeout: float = 5000):
        """Assert the user landed on the Products page (performance_glitch_user needs a longer timeout)"""
        expect(self.page).to_have_url(self.URL, timeout=timeout)
        expect(self.list).to_be_visible(timeout=timeout)
        expect(self.title).to_have_text("Products", timeout=timeout)

    def card(self, product: Product) -> ProductCard:
        return ProductCard(self.cards.filter(has_text=product.name))

    def add_button(self, product: Product) -> Locator:
        return self.page.get_by_test_id(f"add-to-cart-{product.slug}")

    def remove_button(self, product: Product) -> Locator:
        return self.page.get_by_test_id(f"remove-{product.slug}")

    def add_to_cart(self, product: Product):
        self.add_button(product).click()

    def remove(self, product: Product):
        self.remove_button(product).click()

    def sort_by(self, option: str):
        """Pick a sort option and wait until the dropdown shows it (the list re-renders together with the label)"""
        self.sort_dropdown.select_option(option)
        expect(self.active_sort).to_have_text(self.SORT_OPTIONS[option])

    def get_names(self) -> list[str]:
        """Product names in the order the page shows them"""
        # all_inner_texts() doesn't auto-wait, so wait for every product to render first
        expect(self.names).to_have_count(len(PRODUCTS))
        return self.names.all_inner_texts()

    def get_prices(self) -> list[float]:
        """Product prices in the order the page shows them ('$29.99' -> 29.99)"""
        expect(self.prices).to_have_count(len(PRODUCTS))
        return [float(price.removeprefix("$")) for price in self.prices.all_inner_texts()]
