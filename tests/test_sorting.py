import pytest
from playwright.sync_api import Page, expect
from data.products import BACKPACK, ONESIE
from pages.cart_page import CartPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

SORT_OPTIONS = InventoryPage.SORT_OPTIONS
SORTING_BROKEN_ALERT = "Sorting is broken! This error has been reported to Backtrace."

def test_sort_options(login_page: LoginPage, inventory_page: InventoryPage):
    # Positive: the dropdown offers exactly the 4 sort options
    login_page.login()

    expect(inventory_page.sort_dropdown_options).to_have_text(list(SORT_OPTIONS.values()))

def test_default_sort_is_name_a_to_z(login_page: LoginPage, inventory_page: InventoryPage):
    # Positive: products start sorted by name, A to Z
    login_page.login()

    expect(inventory_page.sort_dropdown).to_have_value("az")
    expect(inventory_page.active_sort).to_have_text(SORT_OPTIONS["az"])
    names = inventory_page.get_names()
    assert names == sorted(names)

def test_sort_by_name(login_page: LoginPage, inventory_page: InventoryPage):
    # Positive: Z to A reverses the names and A to Z puts them back
    login_page.login()
    names = inventory_page.get_names()

    inventory_page.sort_by("za")
    expect(inventory_page.names).to_have_text(sorted(names, reverse=True))

    # A to Z is the default, so it only proves something after switching away from it
    inventory_page.sort_by("az")
    expect(inventory_page.names).to_have_text(sorted(names))

@pytest.mark.parametrize("option, reverse", [("lohi", False), ("hilo", True)], ids=["lohi", "hilo"])
def test_sort_by_price(login_page: LoginPage, inventory_page: InventoryPage, option: str, reverse: bool):
    # Positive: price sorting matches Python's sorted() on the prices read off the page
    login_page.login()
    prices = inventory_page.get_prices()

    inventory_page.sort_by(option)

    # Only prices are compared: two shirts both cost $15.99, so the order of their names isn't defined
    assert inventory_page.get_prices() == sorted(prices, reverse=reverse)

@pytest.mark.parametrize("option", ["za", "hilo"])
def test_problem_user_sort_does_nothing(login_page: LoginPage, inventory_page: InventoryPage, option: str):
    # Negative: for problem_user, picking a sort option changes nothing
    login_page.login("problem_user")
    names = inventory_page.get_names()

    # select_option fires the change event synchronously, so the site has already handled it here
    inventory_page.sort_dropdown.select_option(option)

    expect(inventory_page.active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(inventory_page.names).to_have_text(names)

def test_error_user_sort_shows_alert(page: Page, login_page: LoginPage, inventory_page: InventoryPage):
    # Negative: for error_user, sorting shows a "Sorting is broken!" alert and the list stays A to Z
    login_page.login("error_user")
    names = inventory_page.get_names()

    # The alert blocks the page until it is closed, so accept it; waiting for it proves the change was handled
    page.once("dialog", lambda dialog: dialog.accept())
    with page.expect_event("dialog") as dialog_info:
        inventory_page.sort_dropdown.select_option("za")

    assert dialog_info.value.type == "alert"
    assert dialog_info.value.message == SORTING_BROKEN_ALERT
    expect(inventory_page.active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(inventory_page.names).to_have_text(names)

def test_sort_keeps_cart(login_page: LoginPage, inventory_page: InventoryPage):
    # Edge case: re-sorting the list doesn't touch the cart
    login_page.login()
    inventory_page.add_to_cart(BACKPACK)
    inventory_page.add_to_cart(ONESIE)
    expect(inventory_page.cart_badge).to_have_text("2")

    inventory_page.sort_by("hilo")

    expect(inventory_page.cart_badge).to_have_text("2")
    expect(inventory_page.remove_buttons).to_have_count(2)
    expect(inventory_page.remove_button(BACKPACK)).to_be_visible()
    expect(inventory_page.remove_button(ONESIE)).to_be_visible()

def test_sort_moves_whole_cards(login_page: LoginPage, inventory_page: InventoryPage):
    # Edge case: sorting moves each product card as a whole, so every name keeps its own price
    login_page.login()
    price_by_name = dict(zip(inventory_page.get_names(), inventory_page.get_prices()))

    inventory_page.sort_by("hilo")

    assert dict(zip(inventory_page.get_names(), inventory_page.get_prices())) == price_by_name

def test_sort_resets_after_leaving_page(page: Page, login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    # Edge case: the chosen sort isn't remembered, so leaving the page or reloading brings back A to Z
    login_page.login()
    names = inventory_page.get_names()

    # To the cart and back with Continue Shopping
    inventory_page.sort_by("za")
    inventory_page.open_cart()
    cart_page.continue_shopping()
    inventory_page.expect_loaded()
    expect(inventory_page.active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(inventory_page.names).to_have_text(names)

    # Reload the page
    inventory_page.sort_by("za")
    page.reload()
    expect(inventory_page.active_sort).to_have_text(SORT_OPTIONS["az"])
    expect(inventory_page.names).to_have_text(names)
