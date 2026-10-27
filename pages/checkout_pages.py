from playwright.sync_api import Page, expect
from config import BASE_URL
from pages.base_page import BasePage

class CheckoutInfoPage(BasePage):
    """Checkout step one: Your Information"""

    URL = f"{BASE_URL}/checkout-step-one.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.first_name_input = page.get_by_test_id("firstName")
        self.last_name_input = page.get_by_test_id("lastName")
        self.postal_code_input = page.get_by_test_id("postalCode")
        self.continue_button = page.get_by_test_id("continue")
        self.cancel_button = page.get_by_test_id("cancel")

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_have_text("Checkout: Your Information")

    def fill_and_continue(self, first_name: str = "John", last_name: str = "Doe", postal_code: str = "12345"):
        """Fill the form and press Continue"""
        self.first_name_input.fill(first_name)
        self.last_name_input.fill(last_name)
        self.postal_code_input.fill(postal_code)
        self.continue_button.click()

    def cancel(self):
        self.cancel_button.click()

class CheckoutOverviewPage(BasePage):
    """Checkout step two: Overview"""

    URL = f"{BASE_URL}/checkout-step-two.html"

    def __init__(self, page: Page):
        super().__init__(page)
        # Scoped to the item list, the same way as on the cart page
        self.items = page.get_by_test_id("cart-list").get_by_test_id("inventory-item")
        self.item_names = self.items.get_by_test_id("inventory-item-name")
        self.item_quantities = self.items.get_by_test_id("item-quantity")
        self.item_prices = self.items.get_by_test_id("inventory-item-price")
        self.subtotal = page.get_by_test_id("subtotal-label")
        self.tax = page.get_by_test_id("tax-label")
        self.total = page.get_by_test_id("total-label")
        self.payment_info = page.get_by_test_id("payment-info-value")
        self.shipping_info = page.get_by_test_id("shipping-info-value")
        self.finish_button = page.get_by_test_id("finish")
        self.cancel_button = page.get_by_test_id("cancel")

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        # The URL changes before the page re-renders, so also wait for the new title
        expect(self.title).to_have_text("Checkout: Overview")

    def finish(self):
        self.finish_button.click()

    def cancel(self):
        self.cancel_button.click()

class CheckoutCompletePage(BasePage):
    """Checkout complete: the order confirmation"""

    URL = f"{BASE_URL}/checkout-complete.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.header = page.get_by_test_id("complete-header")
        self.back_home_button = page.get_by_test_id("back-to-products")

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.title).to_have_text("Checkout: Complete!")

    def back_home(self):
        self.back_home_button.click()
