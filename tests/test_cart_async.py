import pytest
from playwright.async_api import Page, expect
from config import BASE_URL
from conftest import (
    INVENTORY_URL,
    get_error_message,
    login_to_saucedemo_async,
    logout_from_saucedemo_async,
)
from data.products import BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT
from data.users import BROKEN_CART_USERS

# Async mirror of test_cart.py: same cases, written with the async API (`async def` + `await`)

# Every test in this file runs on the session-wide event loop shared with the async fixtures
pytestmark = pytest.mark.asyncio(loop_scope="session")

# Products the BROKEN_CART_USERS can't add to the cart
BROKEN_ADD_PRODUCTS = [BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT]

async def test_add_to_cart(async_page: Page):
    await login_to_saucedemo_async(async_page)

    # Selector for the first "Add to cart" button
    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    # Verify cart badge update
    cart_badge = async_page.locator(".shopping_cart_badge")
    await expect(cart_badge).to_have_text("1")

    # Navigate to cart and verify item is there
    await async_page.click(".shopping_cart_link")
    await expect(async_page).to_have_url(f"{BASE_URL}/cart.html")
    # Scope to .cart_item: the inventory list is still in the DOM for a moment after the URL changes
    await expect(async_page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Backpack")

async def test_add_to_cart_from_product_page(async_page: Page):
    # Positive: add an item from its own product page instead of the products list
    await login_to_saucedemo_async(async_page)

    await async_page.click("text=Sauce Labs Bike Light")
    await expect(async_page).to_have_url(f"{BASE_URL}/inventory-item.html?id=0")

    await async_page.click("button[data-test='add-to-cart']")
    await expect(async_page.locator("button[data-test='remove']")).to_be_visible()
    await expect(async_page.locator(".shopping_cart_badge")).to_have_text("1")

    await async_page.click(".shopping_cart_link")
    await expect(async_page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Bike Light")

async def test_remove_item_from_products_page(async_page: Page):
    # Positive: the Remove button on the products page takes the item out of the cart
    await login_to_saucedemo_async(async_page)

    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    await async_page.click("button[data-test='add-to-cart-sauce-labs-bike-light']")
    cart_badge = async_page.locator(".shopping_cart_badge")
    await expect(cart_badge).to_have_text("2")

    await async_page.click("button[data-test='remove-sauce-labs-backpack']")
    await expect(cart_badge).to_have_text("1")
    await expect(async_page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

    await async_page.click(".shopping_cart_link")
    await expect(async_page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Bike Light")

async def test_cart_shows_item_details(async_page: Page):
    # Positive: the cart row shows quantity, name and the same price as the products page
    await login_to_saucedemo_async(async_page)

    backpack = async_page.locator(".inventory_item").filter(has_text="Sauce Labs Backpack")
    price = await backpack.locator(".inventory_item_price").inner_text()
    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    await async_page.click(".shopping_cart_link")
    cart_item = async_page.locator(".cart_item")
    await expect(cart_item).to_have_count(1)
    await expect(cart_item.locator(".cart_quantity")).to_have_text("1")
    await expect(cart_item.locator(".inventory_item_name")).to_have_text("Sauce Labs Backpack")
    await expect(cart_item.locator(".inventory_item_price")).to_have_text(price)

async def test_cart_navigation(async_page: Page):
    # Positive: Continue Shopping and Checkout buttons on the cart page
    await login_to_saucedemo_async(async_page)
    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")

    # Continue Shopping goes back to the products page and keeps the cart
    await async_page.click(".shopping_cart_link")
    await async_page.click("button[data-test='continue-shopping']")
    await expect(async_page).to_have_url(INVENTORY_URL)
    await expect(async_page.locator(".shopping_cart_badge")).to_have_text("1")

    # Checkout opens the first checkout step
    await async_page.click(".shopping_cart_link")
    await async_page.click("button[data-test='checkout']")
    await expect(async_page).to_have_url(f"{BASE_URL}/checkout-step-one.html")

async def test_cart_requires_login(async_page: Page):
    # Negative: the cart page can't be opened without logging in
    await async_page.goto(f"{BASE_URL}/cart.html")

    await expect(async_page).to_have_url(f"{BASE_URL}/")
    await expect(get_error_message(async_page)).to_have_text(
        "Epic sadface: You can only access '/cart.html' when you are logged in."
    )

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
async def test_broken_add_to_cart_buttons(async_page: Page, username: str):
    # Negative: some "Add to cart" buttons do nothing for these users
    await login_to_saucedemo_async(async_page, username=username)

    for product in BROKEN_ADD_PRODUCTS:
        add_button = async_page.locator(f"button[data-test='add-to-cart-{product.slug}']")
        await add_button.click()
        await expect(add_button).to_be_visible()
    cart_badge = async_page.locator(".shopping_cart_badge")
    await expect(cart_badge).to_be_hidden()

    # A working product still adds, and the badge counts only that one
    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    await expect(cart_badge).to_have_text("1")

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
async def test_broken_remove_button(async_page: Page, username: str):
    # Negative: "Remove" on the products page does nothing for these users
    await login_to_saucedemo_async(async_page, username=username)

    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = async_page.locator(".shopping_cart_badge")
    await expect(cart_badge).to_have_text("1")

    remove_button = async_page.locator("button[data-test='remove-sauce-labs-backpack']")
    await remove_button.click()
    await expect(remove_button).to_be_visible()
    await expect(cart_badge).to_have_text("1")

    # Adding another product proves the Remove click was handled and ignored
    await async_page.click("button[data-test='add-to-cart-sauce-labs-bike-light']")
    await expect(cart_badge).to_have_text("2")

@pytest.mark.xfail(reason="saucedemo bug: checkout is allowed with an empty cart", strict=True)
async def test_checkout_disabled_for_empty_cart(async_page: Page):
    # Negative: Checkout should be blocked when the cart is empty
    await login_to_saucedemo_async(async_page)

    await async_page.click(".shopping_cart_link")
    await expect(async_page).to_have_url(f"{BASE_URL}/cart.html")
    await expect(async_page.locator(".cart_item")).to_have_count(0)
    await expect(async_page.locator("button[data-test='checkout']")).to_be_disabled()

async def test_add_all_items_to_cart(async_page: Page):
    # Edge case: fill the cart with every product in the store
    await login_to_saucedemo_async(async_page)

    # all_inner_texts() doesn't auto-wait, so wait for the products to render first
    product_locator = async_page.locator(".inventory_item_name")
    await expect(product_locator).to_have_count(6)
    product_names = await product_locator.all_inner_texts()

    # Each click turns that button into "Remove", so always click the first remaining "Add to cart"
    add_buttons = async_page.locator("button[data-test^='add-to-cart']")
    for _ in product_names:
        await add_buttons.first.click()

    await expect(add_buttons).to_have_count(0)
    await expect(async_page.locator(".shopping_cart_badge")).to_have_text("6")

    # Cart lists every product, in the same order as the inventory page
    await async_page.click(".shopping_cart_link")
    await expect(async_page.locator(".cart_item .inventory_item_name")).to_have_text(product_names)

async def test_remove_last_item_empties_cart(async_page: Page):
    # Edge case: removing the only item hides the badge entirely (it never shows "0")
    await login_to_saucedemo_async(async_page)

    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = async_page.locator(".shopping_cart_badge")
    await expect(cart_badge).to_have_text("1")

    await async_page.click(".shopping_cart_link")
    await async_page.click("button[data-test='remove-sauce-labs-backpack']")

    await expect(async_page.locator(".cart_item")).to_have_count(0)
    await expect(cart_badge).to_be_hidden()

    # Back on the inventory page the button is "Add to cart" again
    await async_page.click("button[data-test='continue-shopping']")
    await expect(async_page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

async def test_cart_persists_after_logout(async_page: Page):
    # Edge case: the cart lives in the browser's localStorage, so it survives logging out and back in
    await login_to_saucedemo_async(async_page)

    await async_page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    await expect(async_page.locator(".shopping_cart_badge")).to_have_text("1")

    await logout_from_saucedemo_async(async_page)
    await expect(async_page).to_have_url(f"{BASE_URL}/")

    await login_to_saucedemo_async(async_page)

    await expect(async_page.locator(".shopping_cart_badge")).to_have_text("1")
    await async_page.click(".shopping_cart_link")
    await expect(async_page.locator(".cart_item .inventory_item_name")).to_have_text("Sauce Labs Backpack")
