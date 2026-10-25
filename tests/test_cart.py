import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from conftest import (
    INVENTORY_URL,
    get_error_message,
    login_to_saucedemo,
    logout_from_saucedemo,
)
from data.products import BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT
from data.users import BROKEN_CART_USERS

# Products the BROKEN_CART_USERS can't add to the cart
BROKEN_ADD_PRODUCTS = [BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT]

def test_add_to_cart(page: Page):
    login_to_saucedemo(page)

    # Selector for the first "Add to cart" button
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    # Verify cart badge update
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")

    # Navigate to cart and verify item is there
    page.click(".shopping_cart_link")
    expect(page).to_have_url("https://www.saucedemo.com/cart.html")
    # Scope to .cart_item: the inventory list is still in the DOM for a moment after the URL changes
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Backpack")

def test_add_to_cart_from_product_page(page: Page):
    # Positive: add an item from its own product page instead of the products list
    login_to_saucedemo(page)

    page.click("text=Sauce Labs Bike Light")
    expect(page).to_have_url(f"{BASE_URL}/inventory-item.html?id=0")

    page.click("button[data-test='add-to-cart']")
    expect(page.locator("button[data-test='remove']")).to_be_visible()
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")

    page.click(".shopping_cart_link")
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Bike Light")

def test_remove_item_from_products_page(page: Page):
    # Positive: the Remove button on the products page takes the item out of the cart
    login_to_saucedemo(page)

    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    page.click("button[data-test='add-to-cart-sauce-labs-bike-light']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("2")

    page.click("button[data-test='remove-sauce-labs-backpack']")
    expect(cart_badge).to_have_text("1")
    expect(page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

    page.click(".shopping_cart_link")
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Bike Light")

def test_cart_shows_item_details(page: Page):
    # Positive: the cart row shows quantity, name and the same price as the products page
    login_to_saucedemo(page)

    backpack = page.locator(".inventory_item").filter(has_text="Sauce Labs Backpack")
    price = backpack.locator(".inventory_item_price").inner_text()
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    page.click(".shopping_cart_link")
    cart_item = page.locator(".cart_item")
    expect(cart_item).to_have_count(1)
    expect(cart_item.locator(".cart_quantity")).to_have_text("1")
    expect(cart_item.locator(".inventory_item_name")).to_have_text("Sauce Labs Backpack")
    expect(cart_item.locator(".inventory_item_price")).to_have_text(price)

def test_cart_navigation(page: Page):
    # Positive: Continue Shopping and Checkout buttons on the cart page
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    # Continue Shopping goes back to the products page and keeps the cart
    page.click(".shopping_cart_link")
    page.click("button[data-test='continue-shopping']")
    expect(page).to_have_url(INVENTORY_URL)
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")

    # Checkout opens the first checkout step
    page.click(".shopping_cart_link")
    page.click("button[data-test='checkout']")
    expect(page).to_have_url(f"{BASE_URL}/checkout-step-one.html")

def test_cart_requires_login(page: Page):
    # Negative: the cart page can't be opened without logging in
    page.goto(f"{BASE_URL}/cart.html")

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(get_error_message(page)).to_have_text(
        "Epic sadface: You can only access '/cart.html' when you are logged in."
    )

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_add_to_cart_buttons(page: Page, username: str):
    # Negative: some "Add to cart" buttons do nothing for these users
    login_to_saucedemo(page, username=username)

    for product in BROKEN_ADD_PRODUCTS:
        add_button = page.locator(f"button[data-test='add-to-cart-{product.slug}']")
        add_button.click()
        expect(add_button).to_be_visible()
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_be_hidden()

    # A working product still adds, and the badge counts only that one
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    expect(cart_badge).to_have_text("1")

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_remove_button(page: Page, username: str):
    # Negative: "Remove" on the products page does nothing for these users
    login_to_saucedemo(page, username=username)

    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")

    remove_button = page.locator("button[data-test='remove-sauce-labs-backpack']")
    remove_button.click()
    expect(remove_button).to_be_visible()
    expect(cart_badge).to_have_text("1")

    # Adding another product proves the Remove click was handled and ignored
    page.click("button[data-test='add-to-cart-sauce-labs-bike-light']")
    expect(cart_badge).to_have_text("2")

@pytest.mark.xfail(reason="saucedemo bug: checkout is allowed with an empty cart", strict=True)
def test_checkout_disabled_for_empty_cart(page: Page):
    # Negative: Checkout should be blocked when the cart is empty
    login_to_saucedemo(page)

    page.click(".shopping_cart_link")
    expect(page).to_have_url(f"{BASE_URL}/cart.html")
    expect(page.locator(".cart_item")).to_have_count(0)
    expect(page.locator("button[data-test='checkout']")).to_be_disabled()

def test_add_all_items_to_cart(page: Page):
    # Edge case: fill the cart with every product in the store
    login_to_saucedemo(page)

    # all_inner_texts() doesn't auto-wait, so wait for the products to render first
    product_locator = page.locator(".inventory_item_name")
    expect(product_locator).to_have_count(6)
    product_names = product_locator.all_inner_texts()

    # Each click turns that button into "Remove", so always click the first remaining "Add to cart"
    add_buttons = page.locator("button[data-test^='add-to-cart']")
    for _ in product_names:
        add_buttons.first.click()

    expect(add_buttons).to_have_count(0)
    expect(page.locator(".shopping_cart_badge")).to_have_text("6")

    # Cart lists every product, in the same order as the inventory page
    page.click(".shopping_cart_link")
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text(product_names)

def test_remove_last_item_empties_cart(page: Page):
    # Edge case: removing the only item hides the badge entirely (it never shows "0")
    login_to_saucedemo(page)

    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")

    page.click(".shopping_cart_link")
    page.click("button[data-test='remove-sauce-labs-backpack']")

    expect(page.locator(".cart_item")).to_have_count(0)
    expect(cart_badge).to_be_hidden()

    # Back on the inventory page the button is "Add to cart" again
    page.click("button[data-test='continue-shopping']")
    expect(page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

def test_cart_persists_after_logout(page: Page):
    # Edge case: the cart lives in the browser's localStorage, so it survives logging out and back in
    login_to_saucedemo(page)

    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    expect(page.locator(".shopping_cart_badge")).to_have_text("1")

    logout_from_saucedemo(page)
    expect(page).to_have_url(f"{BASE_URL}/")

    login_to_saucedemo(page)

    expect(page.locator(".shopping_cart_badge")).to_have_text("1")
    page.click(".shopping_cart_link")
    expect(page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Backpack")
