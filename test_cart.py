from playwright.sync_api import Page, expect
from conftest import BASE_URL, login_to_saucedemo, logout_from_saucedemo

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
