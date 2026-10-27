import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from data.products import BACKPACK, BIKE_LIGHT, Product
from pages.cart_page import CartPage
from pages.checkout_pages import CheckoutCompletePage, CheckoutInfoPage, CheckoutOverviewPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

TAX_RATE = 0.08

@pytest.fixture
def go_to_checkout(
    login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage, checkout_info_page: CheckoutInfoPage
):
    """Log in, add the products to the cart and open the first checkout step"""
    def go(products: tuple[Product, ...] = (BACKPACK,), username: str = "standard_user"):
        login_page.login(username)
        for product in products:
            inventory_page.add_to_cart(product)
        inventory_page.open_cart()
        cart_page.checkout()
        checkout_info_page.expect_loaded()
    return go

def to_amount(text: str) -> float:
    """'$29.99' or 'Item total: $29.99' -> 29.99"""
    return float(text.split("$")[1])

def test_complete_checkout(
    go_to_checkout,
    checkout_info_page: CheckoutInfoPage,
    checkout_overview_page: CheckoutOverviewPage,
    checkout_complete_page: CheckoutCompletePage,
    inventory_page: InventoryPage,
    cart_page: CartPage,
):
    # Positive: the whole flow, from the cart to "Thank you for your order!"
    go_to_checkout()

    checkout_info_page.fill_and_continue()
    checkout_overview_page.expect_loaded()

    checkout_overview_page.finish()
    checkout_complete_page.expect_loaded()
    expect(checkout_complete_page.header).to_have_text("Thank you for your order!")
    expect(checkout_complete_page.cart_badge).to_be_hidden()

    # Back Home returns to the products page with an empty cart
    checkout_complete_page.back_home()
    inventory_page.expect_loaded()
    expect(inventory_page.add_button(BACKPACK)).to_be_visible()

    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.items).to_have_count(0)

def test_checkout_overview_totals(
    go_to_checkout, checkout_info_page: CheckoutInfoPage, checkout_overview_page: CheckoutOverviewPage
):
    # Positive: Item total is the sum of the prices, tax is 8% and Total adds them up
    go_to_checkout(products=(BACKPACK, BIKE_LIGHT))
    checkout_info_page.fill_and_continue()
    checkout_overview_page.expect_loaded()

    # all_inner_texts() doesn't auto-wait, so wait for both rows first
    prices = checkout_overview_page.item_prices
    expect(prices).to_have_count(2)
    subtotal = sum(to_amount(price) for price in prices.all_inner_texts())
    tax = round(subtotal * TAX_RATE, 2)

    expect(checkout_overview_page.subtotal).to_have_text(f"Item total: ${subtotal:.2f}")
    expect(checkout_overview_page.tax).to_have_text(f"Tax: ${tax:.2f}")
    expect(checkout_overview_page.total).to_have_text(f"Total: ${subtotal + tax:.2f}")

    expect(checkout_overview_page.payment_info).to_have_text("SauceCard #31337")
    expect(checkout_overview_page.shipping_info).to_have_text("Free Pony Express Delivery!")

def test_checkout_overview_lists_items(
    login_page: LoginPage,
    inventory_page: InventoryPage,
    cart_page: CartPage,
    checkout_info_page: CheckoutInfoPage,
    checkout_overview_page: CheckoutOverviewPage,
):
    # Positive: the overview lists the same items as the cart
    login_page.login()
    inventory_page.add_to_cart(BACKPACK)
    inventory_page.add_to_cart(BIKE_LIGHT)
    inventory_page.open_cart()

    expect(cart_page.items).to_have_count(2)
    names = cart_page.item_names.all_inner_texts()
    quantities = cart_page.item_quantities.all_inner_texts()
    prices = cart_page.item_prices.all_inner_texts()

    cart_page.checkout()
    checkout_info_page.fill_and_continue()
    checkout_overview_page.expect_loaded()

    expect(checkout_overview_page.item_names).to_have_text(names)
    expect(checkout_overview_page.item_quantities).to_have_text(quantities)
    expect(checkout_overview_page.item_prices).to_have_text(prices)

@pytest.mark.parametrize(
    "first_name, last_name, postal_code, expected_error",
    [
        ("", "", "", "Error: First Name is required"),
        ("", "Doe", "12345", "Error: First Name is required"),
        ("John", "", "12345", "Error: Last Name is required"),
        ("John", "Doe", "", "Error: Postal Code is required"),
    ],
    ids=["empty_all", "empty_first_name", "empty_last_name", "empty_postal_code"],
)
def test_checkout_required_fields(
    go_to_checkout, checkout_info_page: CheckoutInfoPage, first_name: str, last_name: str, postal_code: str, expected_error: str
):
    # Negative: every field on the form is required
    go_to_checkout()

    checkout_info_page.fill_and_continue(first_name=first_name, last_name=last_name, postal_code=postal_code)

    expect(checkout_info_page.error).to_be_visible()
    expect(checkout_info_page.error).to_have_text(expected_error)
    checkout_info_page.expect_loaded()

def test_close_checkout_error(go_to_checkout, checkout_info_page: CheckoutInfoPage):
    # Negative: the ✕ button hides the form's error banner
    go_to_checkout()

    checkout_info_page.continue_button.click()
    expect(checkout_info_page.error).to_be_visible()

    checkout_info_page.close_error()

    expect(checkout_info_page.error).to_be_hidden()

@pytest.mark.parametrize("path", ["checkout-step-one.html", "checkout-step-two.html", "checkout-complete.html"])
def test_checkout_requires_login(page: Page, login_page: LoginPage, path: str):
    # Negative: no checkout page can be opened without logging in
    page.goto(f"{BASE_URL}/{path}")

    login_page.expect_access_denied(f"/{path}")

def test_problem_user_last_name_overwrites_first_name(go_to_checkout, checkout_info_page: CheckoutInfoPage):
    # Negative: for problem_user, typing in Last Name replaces First Name instead
    go_to_checkout(username="problem_user")

    checkout_info_page.fill_and_continue(first_name="John", last_name="Doe")

    expect(checkout_info_page.first_name_input).to_have_value("Doe")
    expect(checkout_info_page.last_name_input).to_have_value("")
    expect(checkout_info_page.error).to_have_text("Error: Last Name is required")
    checkout_info_page.expect_loaded()

def test_error_user_cannot_finish(
    page: Page, go_to_checkout, checkout_info_page: CheckoutInfoPage, checkout_overview_page: CheckoutOverviewPage
):
    # Negative: error_user's Last Name field ignores typing, yet the form still lets them continue
    go_to_checkout(username="error_user")

    checkout_info_page.last_name_input.fill("Doe")
    expect(checkout_info_page.last_name_input).to_have_value("")

    checkout_info_page.fill_and_continue()
    checkout_overview_page.expect_loaded()

    # Finish crashes in the site's JavaScript; waiting for that error proves the click was handled
    with page.expect_event("pageerror"):
        checkout_overview_page.finish()

    # The order never goes through: still on the overview and the item is still in the cart
    checkout_overview_page.expect_loaded()
    expect(checkout_overview_page.cart_badge).to_have_text("1")

def test_checkout_cancel_buttons(
    go_to_checkout,
    inventory_page: InventoryPage,
    cart_page: CartPage,
    checkout_info_page: CheckoutInfoPage,
    checkout_overview_page: CheckoutOverviewPage,
):
    # Edge case: Cancel on either step leaves checkout but keeps the cart
    go_to_checkout()

    # Cancel on "Your Information" goes back to the cart
    checkout_info_page.cancel()
    cart_page.expect_loaded()
    expect(cart_page.item_names).to_have_text(BACKPACK.name)

    # Cancel on the Overview goes back to the products page
    cart_page.checkout()
    checkout_info_page.fill_and_continue()
    checkout_overview_page.expect_loaded()
    checkout_overview_page.cancel()
    inventory_page.expect_loaded()
    expect(inventory_page.cart_badge).to_have_text("1")
