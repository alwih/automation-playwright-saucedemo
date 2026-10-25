import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from conftest import (
    INVENTORY_URL,
    get_error_message,
    login_to_saucedemo,
)

CART_URL = f"{BASE_URL}/cart.html"
CHECKOUT_STEP_ONE_URL = f"{BASE_URL}/checkout-step-one.html"
CHECKOUT_STEP_TWO_URL = f"{BASE_URL}/checkout-step-two.html"
CHECKOUT_COMPLETE_URL = f"{BASE_URL}/checkout-complete.html"
TAX_RATE = 0.08

def go_to_checkout(page: Page, products: tuple[str, ...] = ("sauce-labs-backpack",), username: str = "standard_user"):
    """Log in, add the products to the cart and open the first checkout step"""
    login_to_saucedemo(page, username=username)
    for product in products:
        page.click(f"button[data-test='add-to-cart-{product}']")
    page.click(".shopping_cart_link")
    page.click("button[data-test='checkout']")
    expect(page).to_have_url(CHECKOUT_STEP_ONE_URL)

def fill_checkout_info(page: Page, first_name: str = "John", last_name: str = "Doe", postal_code: str = "12345"):
    """Fill the "Your Information" form and press Continue"""
    page.fill("[data-test='firstName']", first_name)
    page.fill("[data-test='lastName']", last_name)
    page.fill("[data-test='postalCode']", postal_code)
    page.click("[data-test='continue']")

def expect_overview_page(page: Page):
    """Assert the user is on checkout step two (Overview)"""
    expect(page).to_have_url(CHECKOUT_STEP_TWO_URL)
    # The URL changes before the page re-renders, so also wait for the new title
    expect(page.locator("[data-test='title']")).to_have_text("Checkout: Overview")

def to_amount(text: str) -> float:
    """'$29.99' or 'Item total: $29.99' -> 29.99"""
    return float(text.split("$")[1])

def test_complete_checkout(page: Page):
    # Positive: the whole flow, from the cart to "Thank you for your order!"
    go_to_checkout(page)

    fill_checkout_info(page)
    expect_overview_page(page)

    page.click("button[data-test='finish']")
    expect(page).to_have_url(CHECKOUT_COMPLETE_URL)
    expect(page.locator("[data-test='complete-header']")).to_have_text("Thank you for your order!")
    expect(page.locator(".shopping_cart_badge")).to_be_hidden()

    # Back Home returns to the products page with an empty cart
    page.click("button[data-test='back-to-products']")
    expect(page).to_have_url(INVENTORY_URL)
    expect(page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

    page.click(".shopping_cart_link")
    expect(page.locator("[data-test='title']")).to_have_text("Your Cart")
    expect(page.locator(".cart_item")).to_have_count(0)

def test_checkout_overview_totals(page: Page):
    # Positive: Item total is the sum of the prices, tax is 8% and Total adds them up
    go_to_checkout(page, products=("sauce-labs-backpack", "sauce-labs-bike-light"))
    fill_checkout_info(page)
    expect_overview_page(page)

    # all_inner_texts() doesn't auto-wait, so wait for both rows first
    prices = page.locator(".cart_item .inventory_item_price")
    expect(prices).to_have_count(2)
    subtotal = sum(to_amount(price) for price in prices.all_inner_texts())
    tax = round(subtotal * TAX_RATE, 2)

    expect(page.locator("[data-test='subtotal-label']")).to_have_text(f"Item total: ${subtotal:.2f}")
    expect(page.locator("[data-test='tax-label']")).to_have_text(f"Tax: ${tax:.2f}")
    expect(page.locator("[data-test='total-label']")).to_have_text(f"Total: ${subtotal + tax:.2f}")

    expect(page.locator("[data-test='payment-info-value']")).to_have_text("SauceCard #31337")
    expect(page.locator("[data-test='shipping-info-value']")).to_have_text("Free Pony Express Delivery!")

def test_checkout_overview_lists_items(page: Page):
    # Positive: the overview lists the same items as the cart
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    page.click("button[data-test='add-to-cart-sauce-labs-bike-light']")
    page.click(".shopping_cart_link")

    cart_items = page.locator(".cart_item")
    expect(cart_items).to_have_count(2)
    names = cart_items.locator(".inventory_item_name").all_inner_texts()
    quantities = cart_items.locator(".cart_quantity").all_inner_texts()
    prices = cart_items.locator(".inventory_item_price").all_inner_texts()

    page.click("button[data-test='checkout']")
    fill_checkout_info(page)
    expect_overview_page(page)

    expect(cart_items.locator(".inventory_item_name")).to_have_text(names)
    expect(cart_items.locator(".cart_quantity")).to_have_text(quantities)
    expect(cart_items.locator(".inventory_item_price")).to_have_text(prices)

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
def test_checkout_required_fields(page: Page, first_name: str, last_name: str, postal_code: str, expected_error: str):
    # Negative: every field on the form is required
    go_to_checkout(page)

    fill_checkout_info(page, first_name=first_name, last_name=last_name, postal_code=postal_code)

    error_message = get_error_message(page)
    expect(error_message).to_be_visible()
    expect(error_message).to_have_text(expected_error)
    expect(page).to_have_url(CHECKOUT_STEP_ONE_URL)

def test_close_checkout_error(page: Page):
    # Negative: the ✕ button hides the form's error banner
    go_to_checkout(page)

    page.click("[data-test='continue']")
    error_message = get_error_message(page)
    expect(error_message).to_be_visible()

    page.click("[data-test='error-button']")

    expect(error_message).to_be_hidden()

@pytest.mark.parametrize("path", ["checkout-step-one.html", "checkout-step-two.html", "checkout-complete.html"])
def test_checkout_requires_login(page: Page, path: str):
    # Negative: no checkout page can be opened without logging in
    page.goto(f"{BASE_URL}/{path}")

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(get_error_message(page)).to_have_text(
        f"Epic sadface: You can only access '/{path}' when you are logged in."
    )

def test_problem_user_last_name_overwrites_first_name(page: Page):
    # Negative: for problem_user, typing in Last Name replaces First Name instead
    go_to_checkout(page, username="problem_user")

    fill_checkout_info(page, first_name="John", last_name="Doe")

    expect(page.locator("[data-test='firstName']")).to_have_value("Doe")
    expect(page.locator("[data-test='lastName']")).to_have_value("")
    expect(get_error_message(page)).to_have_text("Error: Last Name is required")
    expect(page).to_have_url(CHECKOUT_STEP_ONE_URL)

def test_error_user_cannot_finish(page: Page):
    # Negative: error_user's Last Name field ignores typing, yet the form still lets them continue
    go_to_checkout(page, username="error_user")

    page.fill("[data-test='lastName']", "Doe")
    expect(page.locator("[data-test='lastName']")).to_have_value("")

    fill_checkout_info(page)
    expect_overview_page(page)

    # Finish crashes in the site's JavaScript; waiting for that error proves the click was handled
    with page.expect_event("pageerror"):
        page.click("button[data-test='finish']")

    # The order never goes through: still on the overview and the item is still in the cart
    expect(page).to_have_url(CHECKOUT_STEP_TWO_URL)
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")

def test_checkout_cancel_buttons(page: Page):
    # Edge case: Cancel on either step leaves checkout but keeps the cart
    go_to_checkout(page)

    # Cancel on "Your Information" goes back to the cart
    page.click("button[data-test='cancel']")
    expect(page).to_have_url(CART_URL)
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Backpack")

    # Cancel on the Overview goes back to the products page
    page.click("button[data-test='checkout']")
    fill_checkout_info(page)
    expect_overview_page(page)
    page.click("button[data-test='cancel']")
    expect(page).to_have_url(INVENTORY_URL)
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")
