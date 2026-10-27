import re

import pytest
from playwright.sync_api import expect
from data.users import ACCEPTED_USERS, LOGIN_USERS, PASSWORD
from pages.components import Menu
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

def test_accepted_users_listed_on_login_page(login_page: LoginPage):
    # Fails if SauceDemo adds/removes a user, so this suite stays in sync
    login_page.open()

    for user in ACCEPTED_USERS:
        expect(login_page.credentials).to_contain_text(user)

def test_valid_login(login_page: LoginPage, inventory_page: InventoryPage):
    login_page.login("standard_user")

    inventory_page.expect_loaded()

def test_locked_out_user(login_page: LoginPage):
    login_page.login("locked_out_user")

    expect(login_page.error).to_be_visible()
    expect(login_page.error).to_contain_text("Epic sadface: Sorry, this user has been locked out.")
    login_page.expect_loaded()

def test_problem_user(login_page: LoginPage, inventory_page: InventoryPage):
    login_page.login("problem_user")

    inventory_page.expect_loaded()

    # problem_user sees the same broken "sl-404" image for every product
    expect(inventory_page.images).to_have_count(6)
    for image in inventory_page.images.all():
        expect(image).to_have_attribute("src", re.compile(r"sl-404"))

def test_performance_glitch_user(login_page: LoginPage, inventory_page: InventoryPage):
    login_page.login("performance_glitch_user")

    # Login is delayed ~5s, longer than the default 5s expect timeout
    inventory_page.expect_loaded(timeout=15000)

def test_error_user(login_page: LoginPage, inventory_page: InventoryPage):
    # error_user logs in normally; its bugs appear later in cart/checkout
    login_page.login("error_user")

    inventory_page.expect_loaded()

def test_visual_user(login_page: LoginPage, inventory_page: InventoryPage):
    login_page.login("visual_user")

    inventory_page.expect_loaded()

    # visual_user gets a misplaced cart icon
    expect(inventory_page.cart_container).to_have_class(re.compile(r"visual_failure"))

@pytest.mark.parametrize("username", LOGIN_USERS)
def test_login_then_logout(login_page: LoginPage, inventory_page: InventoryPage, menu: Menu, username: str):
    login_page.login(username)
    inventory_page.expect_loaded(timeout=15000)

    menu.logout()

    login_page.expect_loaded()

@pytest.mark.parametrize(
    "username, password, expected_error",
    [
        ("", "", "Epic sadface: Username is required"),
        ("", PASSWORD, "Epic sadface: Username is required"),
        ("standard_user", "", "Epic sadface: Password is required"),
        ("standard_user", "wrong_password", "Epic sadface: Username and password do not match any user in this service"),
        ("unknown_user", PASSWORD, "Epic sadface: Username and password do not match any user in this service"),
        ("STANDARD_USER", PASSWORD, "Epic sadface: Username and password do not match any user in this service"),
    ],
    ids=["empty_both", "empty_username", "empty_password", "wrong_password", "unknown_user", "username_case_sensitive"],
)
def test_invalid_login(login_page: LoginPage, username: str, password: str, expected_error: str):
    login_page.login(username, password)

    expect(login_page.error).to_be_visible()
    expect(login_page.error).to_have_text(expected_error)
    login_page.expect_loaded()

def test_close_error_message(login_page: LoginPage):
    login_page.login("locked_out_user")

    expect(login_page.error).to_be_visible()

    login_page.close_error()

    expect(login_page.error).to_be_hidden()

def test_inventory_requires_login(login_page: LoginPage, inventory_page: InventoryPage):
    inventory_page.open()

    login_page.expect_access_denied("/inventory.html")
