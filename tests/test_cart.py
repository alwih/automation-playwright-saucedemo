import pytest
from playwright.sync_api import expect
from data.products import BACKPACK, BIKE_LIGHT, BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT
from data.users import BROKEN_CART_USERS
from pages.cart_page import CartPage
from pages.checkout_pages import CheckoutInfoPage
from pages.components import Menu
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage

# Products the BROKEN_CART_USERS can't add to the cart
BROKEN_ADD_PRODUCTS = [BOLT_T_SHIRT, FLEECE_JACKET, RED_T_SHIRT]

def test_add_to_cart(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Positive: an item added on the products page shows on the badge and in the cart
    login_page.login()

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.item_names).to_have_text(BACKPACK.name)

def test_add_to_cart_from_product_page(
    login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage, cart_page: CartPage
):
    # Positive: add an item from its own product page instead of the products list
    login_page.login()

    inventory_page.card(BIKE_LIGHT).name.click()
    product_page.expect_product(BIKE_LIGHT.id, BIKE_LIGHT.name)

    product_page.add_to_cart()
    expect(product_page.remove_button).to_be_visible()
    expect(product_page.cart_badge).to_have_text("1")

    product_page.open_cart()
    expect(cart_page.item_names).to_have_text(BIKE_LIGHT.name)

def test_remove_item_from_products_page(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Positive: the Remove button on the products page takes the item out of the cart
    login_page.login()

    inventory_page.add_to_cart(BACKPACK)
    inventory_page.add_to_cart(BIKE_LIGHT)
    expect(inventory_page.cart_badge).to_have_text("2")

    inventory_page.remove(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")
    expect(inventory_page.add_button(BACKPACK)).to_be_visible()

    inventory_page.open_cart()
    expect(cart_page.item_names).to_have_text(BIKE_LIGHT.name)

def test_cart_shows_item_details(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Positive: the cart row shows quantity, name and the same price as the products page
    login_page.login()

    price = inventory_page.card(BACKPACK).price.inner_text()
    inventory_page.add_to_cart(BACKPACK)

    inventory_page.open_cart()
    expect(cart_page.items).to_have_count(1)
    expect(cart_page.item_quantities).to_have_text("1")
    expect(cart_page.item_names).to_have_text(BACKPACK.name)
    expect(cart_page.item_prices).to_have_text(price)

def test_cart_navigation(
    login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage, checkout_info_page: CheckoutInfoPage
):
    # Positive: Continue Shopping and Checkout buttons on the cart page
    login_page.login()
    inventory_page.add_to_cart(BACKPACK)

    # Continue Shopping goes back to the products page and keeps the cart
    inventory_page.open_cart()
    cart_page.continue_shopping()
    inventory_page.expect_loaded()
    expect(inventory_page.cart_badge).to_have_text("1")

    # Checkout opens the first checkout step
    inventory_page.open_cart()
    cart_page.checkout()
    checkout_info_page.expect_loaded()

def test_cart_requires_login(login_page: LoginPage, cart_page: CartPage):
    # Negative: the cart page can't be opened without logging in
    cart_page.open()

    login_page.expect_access_denied("/cart.html")

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_add_to_cart_buttons(login_page: LoginPage, inventory_page: InventoryPage, username: str):
    # Negative: some "Add to cart" buttons do nothing for these users
    login_page.login(username)

    for product in BROKEN_ADD_PRODUCTS:
        inventory_page.add_to_cart(product)
        expect(inventory_page.add_button(product)).to_be_visible()
    expect(inventory_page.cart_badge).to_be_hidden()

    # A working product still adds, and the badge counts only that one
    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_remove_button(login_page: LoginPage, inventory_page: InventoryPage, username: str):
    # Negative: "Remove" on the products page does nothing for these users
    login_page.login(username)

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.remove(BACKPACK)
    expect(inventory_page.remove_button(BACKPACK)).to_be_visible()
    expect(inventory_page.cart_badge).to_have_text("1")

    # Adding another product proves the Remove click was handled and ignored
    inventory_page.add_to_cart(BIKE_LIGHT)
    expect(inventory_page.cart_badge).to_have_text("2")

@pytest.mark.xfail(reason="saucedemo bug: checkout is allowed with an empty cart", strict=True)
def test_checkout_disabled_for_empty_cart(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Negative: Checkout should be blocked when the cart is empty
    login_page.login()

    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.items).to_have_count(0)
    expect(cart_page.checkout_button).to_be_disabled()

def test_add_all_items_to_cart(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Edge case: fill the cart with every product in the store
    login_page.login()
    product_names = inventory_page.get_names()

    # Each click turns that button into "Remove", so always click the first remaining "Add to cart"
    for _ in product_names:
        inventory_page.add_buttons.first.click()

    expect(inventory_page.add_buttons).to_have_count(0)
    expect(inventory_page.cart_badge).to_have_text("6")

    # Cart lists every product, in the same order as the inventory page
    inventory_page.open_cart()
    expect(cart_page.item_names).to_have_text(product_names)

def test_remove_last_item_empties_cart(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Edge case: removing the only item hides the badge entirely (it never shows "0")
    login_page.login()

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.open_cart()
    cart_page.remove(BACKPACK)

    expect(cart_page.items).to_have_count(0)
    expect(cart_page.cart_badge).to_be_hidden()

    # Back on the inventory page the button is "Add to cart" again
    cart_page.continue_shopping()
    expect(inventory_page.add_button(BACKPACK)).to_be_visible()

def test_cart_persists_after_logout(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage, menu: Menu):
    # Edge case: the cart lives in the browser's localStorage, so it survives logging out and back in
    login_page.login()

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    menu.logout()
    login_page.expect_loaded()

    login_page.login()

    expect(inventory_page.cart_badge).to_have_text("1")
    inventory_page.open_cart()
    expect(cart_page.item_names).to_have_text(BACKPACK.name)
