import pytest
from playwright.sync_api import Page, expect
from conftest import (
    BASE_URL,
    expect_inventory_page,
    get_error_message,
    login_to_saucedemo,
)

ITEM_URL = f"{BASE_URL}/inventory-item.html"
# The detail page reuses the products page's data-test names, so every read is scoped to this container
DETAILS = ".inventory_details_container"
DETAIL_NAME = f"{DETAILS} [data-test='inventory-item-name']"
NOT_FOUND_NAME = "ITEM NOT FOUND"
# Product name -> id in its detail page URL (taken from the cards' item-<id>-title-link)
PRODUCT_IDS = {
    "Sauce Labs Backpack": 4,
    "Sauce Labs Bike Light": 0,
    "Sauce Labs Bolt T-Shirt": 1,
    "Sauce Labs Fleece Jacket": 5,
    "Sauce Labs Onesie": 2,
    "Test.allTheThings() T-Shirt (Red)": 3,
}
# Users whose cart buttons are broken on purpose
BROKEN_CART_USERS = ["problem_user", "error_user"]

def get_product_card(page: Page, name: str):
    """Locator for one product's card on the products page"""
    return page.locator("[data-test='inventory-item']").filter(has_text=name)

def go_to_product(page: Page, query: str, username: str = "standard_user"):
    """Log in, then open the detail page URL directly (query is e.g. '?id=4')"""
    login_to_saucedemo(page, username=username)
    # Wait for the login to finish first, so the goto can't race it
    expect_inventory_page(page)
    page.goto(f"{ITEM_URL}{query}")

def expect_product_page(page: Page, product_id: int, name: str):
    """Assert the user is on the detail page of this product"""
    expect(page).to_have_url(f"{ITEM_URL}?id={product_id}")
    expect(page.locator(DETAIL_NAME)).to_have_text(name)

@pytest.mark.parametrize("name, product_id", PRODUCT_IDS.items())
def test_detail_matches_inventory_card(page: Page, name: str, product_id: int):
    # Positive: the detail page shows the same description, price and image as the product's card
    login_to_saucedemo(page)
    card = get_product_card(page, name)
    description = card.locator("[data-test='inventory-item-desc']").inner_text()
    price = card.locator("[data-test='inventory-item-price']").inner_text()
    image = card.locator("img").get_attribute("src")

    card.locator("[data-test='inventory-item-name']").click()

    expect_product_page(page, product_id, name)
    details = page.locator(DETAILS)
    expect(details.locator("[data-test='inventory-item-desc']")).to_have_text(description)
    expect(details.locator("[data-test='inventory-item-price']")).to_have_text(price)
    expect(details.locator(".inventory_details_img")).to_have_attribute("src", image)

def test_open_product_from_image(page: Page):
    # Positive: the product image opens the same detail page as the name
    login_to_saucedemo(page)

    page.click("[data-test='item-4-img-link']")

    expect_product_page(page, 4, "Sauce Labs Backpack")

def test_back_to_products(page: Page):
    # Positive: Back to Products returns to the products page
    login_to_saucedemo(page)
    page.click("[data-test='item-4-title-link']")
    expect_product_page(page, 4, "Sauce Labs Backpack")

    page.click("button[data-test='back-to-products']")

    expect_inventory_page(page)

def test_remove_from_detail_page(page: Page):
    # Positive: an item already in the cart shows Remove on its detail page, and Remove works there
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")

    page.click("[data-test='item-4-title-link']")
    expect_product_page(page, 4, "Sauce Labs Backpack")
    page.click("button[data-test='remove']")

    expect(cart_badge).to_be_hidden()
    expect(page.locator("button[data-test='add-to-cart']")).to_be_visible()

    # The products page shows "Add to cart" for it again
    page.click("button[data-test='back-to-products']")
    expect_inventory_page(page)
    expect(page.locator("button[data-test='add-to-cart-sauce-labs-backpack']")).to_be_visible()

@pytest.mark.parametrize("query", ["?id=6", "?id=99", "?id=abc", ""], ids=["id_6", "id_99", "id_abc", "no_id"])
def test_unknown_product_id(page: Page, query: str):
    # Negative: an id that matches no product (6 is one past the last) shows ITEM NOT FOUND
    go_to_product(page, query)

    expect(page).to_have_url(f"{ITEM_URL}{query}")
    expect(page.locator(DETAIL_NAME)).to_have_text(NOT_FOUND_NAME)

@pytest.mark.xfail(reason="saucedemo bug: the ITEM NOT FOUND page adds an item the cart can't show", strict=True)
def test_not_found_item_cannot_be_added_to_cart(page: Page):
    # Negative: Add to cart on ITEM NOT FOUND shouldn't put anything in the cart
    go_to_product(page, "?id=99")
    expect(page.locator(DETAIL_NAME)).to_have_text(NOT_FOUND_NAME)

    page.click("button[data-test='add-to-cart']")

    # Opening the cart proves the click was handled; today it lists nothing but the badge says "1"
    page.click(".shopping_cart_link")
    expect(page.locator("[data-test='title']")).to_have_text("Your Cart")
    expect(page.locator(".cart_item")).to_have_count(0)
    expect(page.locator(".shopping_cart_badge")).to_be_hidden()

def test_product_detail_requires_login(page: Page):
    # Negative: a detail page can't be opened without logging in
    page.goto(f"{ITEM_URL}?id=4")

    expect(page).to_have_url(f"{BASE_URL}/")
    # The error names the page without its ?id=4 query
    expect(get_error_message(page)).to_have_text(
        "Epic sadface: You can only access '/inventory-item.html' when you are logged in."
    )

@pytest.mark.parametrize(
    "name, opened_name",
    [
        ("Sauce Labs Backpack", "Sauce Labs Fleece Jacket"),
        ("Sauce Labs Fleece Jacket", NOT_FOUND_NAME),
    ],
    ids=["backpack", "fleece_jacket"],
)
def test_problem_user_opens_wrong_product(page: Page, name: str, opened_name: str):
    # Negative: for problem_user, every product links to the next id, so another page opens
    login_to_saucedemo(page, username="problem_user")

    get_product_card(page, name).locator("[data-test='inventory-item-name']").click()

    expect_product_page(page, PRODUCT_IDS[name] + 1, opened_name)

@pytest.mark.parametrize("username", BROKEN_CART_USERS)
def test_broken_cart_buttons_on_detail_page(page: Page, username: str):
    # Negative: the detail page has the same broken Add / Remove buttons as the products page
    go_to_product(page, "?id=1", username=username)
    expect_product_page(page, 1, "Sauce Labs Bolt T-Shirt")
    add_button = page.locator("button[data-test='add-to-cart']")
    cart_badge = page.locator(".shopping_cart_badge")

    # Bolt T-Shirt can't be added
    add_button.click()
    expect(add_button).to_be_visible()
    expect(cart_badge).to_be_hidden()

    # Backpack can, and the badge counts only that one
    page.goto(f"{ITEM_URL}?id=4")
    expect_product_page(page, 4, "Sauce Labs Backpack")
    add_button.click()
    expect(cart_badge).to_have_text("1")

    # ...but Remove does nothing
    remove_button = page.locator("button[data-test='remove']")
    remove_button.click()
    expect(remove_button).to_be_visible()

    # Leaving the page proves the Remove click was handled and ignored
    page.click("button[data-test='back-to-products']")
    expect_inventory_page(page)
    expect(cart_badge).to_have_text("1")
    expect(page.locator("button[data-test='remove-sauce-labs-backpack']")).to_be_visible()

def test_detail_page_survives_reload(page: Page):
    # Edge case: reloading a detail page keeps the product and the cart (the cart lives in localStorage)
    go_to_product(page, "?id=4")
    expect_product_page(page, 4, "Sauce Labs Backpack")
    page.click("button[data-test='add-to-cart']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")

    page.reload()

    expect_product_page(page, 4, "Sauce Labs Backpack")
    expect(page.locator("button[data-test='remove']")).to_be_visible()
    expect(cart_badge).to_have_text("1")
