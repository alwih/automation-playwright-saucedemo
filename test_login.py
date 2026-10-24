import re

import pytest
from playwright.sync_api import Page, expect
from conftest import (
    ACCEPTED_USERS,
    BASE_URL,
    PASSWORD,
    expect_inventory_page,
    get_error_message,
    login_to_saucedemo,
    logout_from_saucedemo,
)

# Every accepted user except locked_out_user can log in
LOGIN_USERS = [user for user in ACCEPTED_USERS if user != "locked_out_user"]

def test_accepted_users_listed_on_login_page(page: Page):
    # Fails if SauceDemo adds/removes a user, so this suite stays in sync
    page.goto(BASE_URL)

    credentials = page.locator("[data-test='login-credentials']")
    for user in ACCEPTED_USERS:
        expect(credentials).to_contain_text(user)

def test_valid_login(page: Page):
    login_to_saucedemo(page, username="standard_user", password=PASSWORD)

    expect_inventory_page(page)

def test_locked_out_user(page: Page):
    login_to_saucedemo(page, username="locked_out_user", password=PASSWORD)

    error_message = get_error_message(page)
    expect(error_message).to_be_visible()
    expect(error_message).to_contain_text("Epic sadface: Sorry, this user has been locked out.")
    expect(page).to_have_url(f"{BASE_URL}/")

def test_problem_user(page: Page):
    login_to_saucedemo(page, username="problem_user", password=PASSWORD)

    expect_inventory_page(page)

    # problem_user sees the same broken "sl-404" image for every product
    images = page.locator(".inventory_item img")
    expect(images).to_have_count(6)
    for image in images.all():
        expect(image).to_have_attribute("src", re.compile(r"sl-404"))

def test_performance_glitch_user(page: Page):
    login_to_saucedemo(page, username="performance_glitch_user", password=PASSWORD)

    # Login is delayed ~5s, longer than the default 5s expect timeout
    expect_inventory_page(page, timeout=15000)

def test_error_user(page: Page):
    # error_user logs in normally; its bugs appear later in cart/checkout
    login_to_saucedemo(page, username="error_user", password=PASSWORD)

    expect_inventory_page(page)

def test_visual_user(page: Page):
    login_to_saucedemo(page, username="visual_user", password=PASSWORD)

    expect_inventory_page(page)

    # visual_user gets a misplaced cart icon
    expect(page.locator(".shopping_cart_container")).to_have_class(re.compile(r"visual_failure"))

@pytest.mark.parametrize("username", LOGIN_USERS)
def test_login_then_logout(page: Page, username: str):
    login_to_saucedemo(page, username=username, password=PASSWORD)
    expect_inventory_page(page, timeout=15000)

    logout_from_saucedemo(page)

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(page.locator("input#login-button")).to_be_visible()

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
def test_invalid_login(page: Page, username: str, password: str, expected_error: str):
    login_to_saucedemo(page, username=username, password=password)

    error_message = get_error_message(page)
    expect(error_message).to_be_visible()
    expect(error_message).to_have_text(expected_error)
    expect(page).to_have_url(f"{BASE_URL}/")

def test_close_error_message(page: Page):
    login_to_saucedemo(page, username="locked_out_user", password=PASSWORD)

    error_message = get_error_message(page)
    expect(error_message).to_be_visible()

    page.click("[data-test='error-button']")

    expect(error_message).to_be_hidden()

def test_inventory_requires_login(page: Page):
    page.goto(f"{BASE_URL}/inventory.html")

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(get_error_message(page)).to_have_text(
        "Epic sadface: You can only access '/inventory.html' when you are logged in."
    )
