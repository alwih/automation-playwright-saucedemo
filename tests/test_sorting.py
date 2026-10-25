import pytest
from playwright.sync_api import Page, expect
from conftest import expect_inventory_page, login_to_saucedemo

SORT_DROPDOWN = "[data-test='product-sort-container']"
ACTIVE_SORT = "[data-test='active-option']"
PRODUCT_NAMES = "[data-test='inventory-item-name']"
PRODUCT_PRICES = "[data-test='inventory-item-price']"
# Option value -> label shown on the dropdown, in the order the dropdown lists them
SORT_OPTIONS = {
    "az": "Name (A to Z)",
    "za": "Name (Z to A)",
    "lohi": "Price (low to high)",
    "hilo": "Price (high to low)",
}
SORTING_BROKEN_ALERT = "Sorting is broken! This error has been reported to Backtrace."

def get_product_names(page: Page) -> list[str]:
    """Product names in the order the products page shows them"""
    names = page.locator(PRODUCT_NAMES)
    # all_inner_texts() doesn't auto-wait, so wait for all 6 products to render first
    expect(names).to_have_count(6)
    return names.all_inner_texts()

def get_product_prices(page: Page) -> list[float]:
    """Product prices in the order the products page shows them ('$29.99' -> 29.99)"""
    prices = page.locator(PRODUCT_PRICES)
    expect(prices).to_have_count(6)
    return [float(price.removeprefix("$")) for price in prices.all_inner_texts()]

def sort_products(page: Page, option: str):
    """Pick a sort option and wait until the dropdown shows it (the list re-renders together with the label)"""
    page.select_option(SORT_DROPDOWN, option)
    expect(page.locator(ACTIVE_SORT)).to_have_text(SORT_OPTIONS[option])

def test_sort_options(page: Page):
    # Positive: the dropdown offers exactly the 4 sort options
    login_to_saucedemo(page)

    expect(page.locator(f"{SORT_DROPDOWN} option")).to_have_text(list(SORT_OPTIONS.values()))

def test_default_sort_is_name_a_to_z(page: Page):
    # Positive: products start sorted by name, A to Z
    login_to_saucedemo(page)

    expect(page.locator(SORT_DROPDOWN)).to_have_value("az")
    expect(page.locator(ACTIVE_SORT)).to_have_text(SORT_OPTIONS["az"])
    names = get_product_names(page)
    assert names == sorted(names)

def test_sort_by_name(page: Page):
    # Positive: Z to A reverses the names and A to Z puts them back
    login_to_saucedemo(page)
    names = get_product_names(page)
    name_locator = page.locator(PRODUCT_NAMES)

    sort_products(page, "za")
    expect(name_locator).to_have_text(sorted(names, reverse=True))

    # A to Z is the default, so it only proves something after switching away from it
    sort_products(page, "az")
    expect(name_locator).to_have_text(sorted(names))

@pytest.mark.parametrize("option, reverse", [("lohi", False), ("hilo", True)], ids=["lohi", "hilo"])
def test_sort_by_price(page: Page, option: str, reverse: bool):
    # Positive: price sorting matches Python's sorted() on the prices read off the page
    login_to_saucedemo(page)
    prices = get_product_prices(page)

    sort_products(page, option)

    # Only prices are compared: two shirts both cost $15.99, so the order of their names isn't defined
    assert get_product_prices(page) == sorted(prices, reverse=reverse)

@pytest.mark.parametrize("option", ["za", "hilo"])
def test_problem_user_sort_does_nothing(page: Page, option: str):
    # Negative: for problem_user, picking a sort option changes nothing
    login_to_saucedemo(page, username="problem_user")
    names = get_product_names(page)

    # select_option fires the change event synchronously, so the site has already handled it here
    page.select_option(SORT_DROPDOWN, option)

    expect(page.locator(ACTIVE_SORT)).to_have_text(SORT_OPTIONS["az"])
    expect(page.locator(PRODUCT_NAMES)).to_have_text(names)

def test_error_user_sort_shows_alert(page: Page):
    # Negative: for error_user, sorting shows a "Sorting is broken!" alert and the list stays A to Z
    login_to_saucedemo(page, username="error_user")
    names = get_product_names(page)

    # The alert blocks the page until it is closed, so accept it; waiting for it proves the change was handled
    page.once("dialog", lambda dialog: dialog.accept())
    with page.expect_event("dialog") as dialog_info:
        page.select_option(SORT_DROPDOWN, "za")

    assert dialog_info.value.type == "alert"
    assert dialog_info.value.message == SORTING_BROKEN_ALERT
    expect(page.locator(ACTIVE_SORT)).to_have_text(SORT_OPTIONS["az"])
    expect(page.locator(PRODUCT_NAMES)).to_have_text(names)

def test_sort_keeps_cart(page: Page):
    # Edge case: re-sorting the list doesn't touch the cart
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    page.click("button[data-test='add-to-cart-sauce-labs-onesie']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("2")

    sort_products(page, "hilo")

    expect(cart_badge).to_have_text("2")
    expect(page.locator("button[data-test^='remove']")).to_have_count(2)
    expect(page.locator("button[data-test='remove-sauce-labs-backpack']")).to_be_visible()
    expect(page.locator("button[data-test='remove-sauce-labs-onesie']")).to_be_visible()

def test_sort_moves_whole_cards(page: Page):
    # Edge case: sorting moves each product card as a whole, so every name keeps its own price
    login_to_saucedemo(page)
    price_by_name = dict(zip(get_product_names(page), get_product_prices(page)))

    sort_products(page, "hilo")

    assert dict(zip(get_product_names(page), get_product_prices(page))) == price_by_name

def test_sort_resets_after_leaving_page(page: Page):
    # Edge case: the chosen sort isn't remembered, so leaving the page or reloading brings back A to Z
    login_to_saucedemo(page)
    names = get_product_names(page)
    name_locator = page.locator(PRODUCT_NAMES)
    active_sort = page.locator(ACTIVE_SORT)

    # To the cart and back with Continue Shopping
    sort_products(page, "za")
    page.click(".shopping_cart_link")
    page.click("button[data-test='continue-shopping']")
    expect_inventory_page(page)
    expect(active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(name_locator).to_have_text(names)

    # Reload the page
    sort_products(page, "za")
    page.reload()
    expect(active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(name_locator).to_have_text(names)
