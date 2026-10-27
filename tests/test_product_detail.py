import pytest
from playwright.sync_api import Page, expect
from data.products import BACKPACK, BOLT_T_SHIRT, FLEECE_JACKET, PRODUCTS, Product
from data.users import BROKEN_CART_USERS
from pages.cart_page import CartPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage

NOT_FOUND_NAME = "ITEM NOT FOUND"

@pytest.fixture
def go_to_product(login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage):
    """Log in, then open a detail page URL directly (query is e.g. '?id=4')"""
    def go(query: str, username: str = "standard_user"):
        login_page.login(username)
        # Wait for the login to finish first, so the goto can't race it
        inventory_page.expect_loaded()
        product_page.open(query)
    return go

@pytest.mark.parametrize("product", PRODUCTS, ids=lambda product: product.slug)
def test_detail_matches_inventory_card(
    login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage, product: Product
):
    # Positive: the detail page shows the same description, price and image as the product's card
    login_page.login()
    card = inventory_page.card(product)
    description = card.description.inner_text()
    price = card.price.inner_text()
    image = card.image.get_attribute("src")

    card.name.click()

    product_page.expect_product(product.id, product.name)
    expect(product_page.description).to_have_text(description)
    expect(product_page.price).to_have_text(price)
    expect(product_page.image).to_have_attribute("src", image)

def test_open_product_from_image(login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage):
    # Positive: the product image opens the same detail page as the name
    login_page.login()

    inventory_page.card(BACKPACK).image.click()

    product_page.expect_product(BACKPACK.id, BACKPACK.name)

def test_back_to_products(login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage):
    # Positive: Back to Products returns to the products page
    login_page.login()
    inventory_page.card(BACKPACK).name.click()
    product_page.expect_product(BACKPACK.id, BACKPACK.name)

    product_page.back_to_products()

    inventory_page.expect_loaded()

def test_remove_from_detail_page(login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage):
    # Positive: an item already in the cart shows Remove on its detail page, and Remove works there
    login_page.login()
    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.card(BACKPACK).name.click()
    product_page.expect_product(BACKPACK.id, BACKPACK.name)
    product_page.remove()

    expect(product_page.cart_badge).to_be_hidden()
    expect(product_page.add_button).to_be_visible()

    # The products page shows "Add to cart" for it again
    product_page.back_to_products()
    inventory_page.expect_loaded()
    expect(inventory_page.add_button(BACKPACK)).to_be_visible()

@pytest.mark.parametrize("query", ["?id=6", "?id=99", "?id=abc", ""], ids=["id_6", "id_99", "id_abc", "no_id"])
def test_unknown_product_id(page: Page, go_to_product, product_page: ProductPage, query: str):
    # Negative: an id that matches no product (6 is one past the last) shows ITEM NOT FOUND
    go_to_product(query)

    expect(page).to_have_url(f"{ProductPage.URL}{query}")
    expect(product_page.name).to_have_text(NOT_FOUND_NAME)

@pytest.mark.xfail(reason="saucedemo bug: the ITEM NOT FOUND page adds an item the cart can't show", strict=True)
def test_not_found_item_cannot_be_added_to_cart(go_to_product, product_page: ProductPage, cart_page: CartPage):
    # Negative: Add to cart on ITEM NOT FOUND shouldn't put anything in the cart
    go_to_product("?id=99")
    expect(product_page.name).to_have_text(NOT_FOUND_NAME)

    product_page.add_to_cart()

    # Opening the cart proves the click was handled; today it lists nothing but the badge says "1"
    product_page.open_cart()
    expect(cart_page.title).to_have_text("Your Cart")
    expect(cart_page.items).to_have_count(0)
    expect(cart_page.cart_badge).to_be_hidden()

def test_product_detail_requires_login(login_page: LoginPage, product_page: ProductPage):
    # Negative: a detail page can't be opened without logging in
    product_page.open(f"?id={BACKPACK.id}")

    # The error names the page without its ?id=4 query
    login_page.expect_access_denied("/inventory-item.html")

@pytest.mark.parametrize(
    "product, opened_name",
    [
        (BACKPACK, FLEECE_JACKET.name),
        (FLEECE_JACKET, NOT_FOUND_NAME),
    ],
    ids=["backpack", "fleece_jacket"],
)
def test_problem_user_opens_wrong_product(
    login_page: LoginPage, inventory_page: InventoryPage, product_page: ProductPage, product: Product, opened_name: str
):
    # Negative: for problem_user, every product links to the next id, so another page opens
    login_page.login("problem_user")

    inventory_page.card(product).name.click()

    product_page.expect_product(product.id + 1, opened_name)

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_cart_buttons_on_detail_page(
    go_to_product, inventory_page: InventoryPage, product_page: ProductPage, username: str
):
    # Negative: the detail page has the same broken Add / Remove buttons as the products page
    go_to_product(f"?id={BOLT_T_SHIRT.id}", username=username)
    product_page.expect_product(BOLT_T_SHIRT.id, BOLT_T_SHIRT.name)

    # Bolt T-Shirt can't be added
    product_page.add_to_cart()
    expect(product_page.add_button).to_be_visible()
    expect(product_page.cart_badge).to_be_hidden()

    # Backpack can, and the badge counts only that one
    product_page.open(f"?id={BACKPACK.id}")
    product_page.expect_product(BACKPACK.id, BACKPACK.name)
    product_page.add_to_cart()
    expect(product_page.cart_badge).to_have_text("1")

    # ...but Remove does nothing
    product_page.remove()
    expect(product_page.remove_button).to_be_visible()

    # Leaving the page proves the Remove click was handled and ignored
    product_page.back_to_products()
    inventory_page.expect_loaded()
    expect(inventory_page.cart_badge).to_have_text("1")
    expect(inventory_page.remove_button(BACKPACK)).to_be_visible()

def test_detail_page_survives_reload(page: Page, go_to_product, product_page: ProductPage):
    # Edge case: reloading a detail page keeps the product and the cart (the cart lives in localStorage)
    go_to_product(f"?id={BACKPACK.id}")
    product_page.expect_product(BACKPACK.id, BACKPACK.name)
    product_page.add_to_cart()
    expect(product_page.cart_badge).to_have_text("1")

    page.reload()

    product_page.expect_product(BACKPACK.id, BACKPACK.name)
    expect(product_page.remove_button).to_be_visible()
    expect(product_page.cart_badge).to_have_text("1")
