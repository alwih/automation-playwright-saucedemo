from playwright.sync_api import Page, expect
from conftest import login_to_saucedemo

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
    expect(page.locator(".inventory_item_name")).to_have_text("Sauce Labs Backpack")