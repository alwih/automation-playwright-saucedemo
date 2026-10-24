import asyncio
import re

import pytest
from playwright.async_api import Browser, Page, expect
from conftest import (
    ACCEPTED_USERS,
    BASE_URL,
    PASSWORD,
    expect_inventory_page_async,
    get_error_message,
    login_to_saucedemo_async,
    logout_from_saucedemo_async,
)

# Async mirror of test_login.py: same cases, written with the async API (`async def` + `await`)

# Every test in this file runs on the session-wide event loop shared with the async fixtures
pytestmark = pytest.mark.asyncio(loop_scope="session")

# Every accepted user except locked_out_user can log in
LOGIN_USERS = [user for user in ACCEPTED_USERS if user != "locked_out_user"]

async def test_accepted_users_listed_on_login_page(async_page: Page):
    # Fails if SauceDemo adds/removes a user, so this suite stays in sync
    await async_page.goto(BASE_URL)

    credentials = async_page.locator("[data-test='login-credentials']")
    for user in ACCEPTED_USERS:
        await expect(credentials).to_contain_text(user)

async def test_valid_login(async_page: Page):
    await login_to_saucedemo_async(async_page, username="standard_user", password=PASSWORD)

    await expect_inventory_page_async(async_page)

async def test_locked_out_user(async_page: Page):
    await login_to_saucedemo_async(async_page, username="locked_out_user", password=PASSWORD)

    error_message = get_error_message(async_page)
    await expect(error_message).to_be_visible()
    await expect(error_message).to_contain_text("Epic sadface: Sorry, this user has been locked out.")
    await expect(async_page).to_have_url(f"{BASE_URL}/")

async def test_problem_user(async_page: Page):
    await login_to_saucedemo_async(async_page, username="problem_user", password=PASSWORD)

    await expect_inventory_page_async(async_page)

    # problem_user sees the same broken "sl-404" image for every product
    images = async_page.locator(".inventory_item img")
    await expect(images).to_have_count(6)
    for image in await images.all():
        await expect(image).to_have_attribute("src", re.compile(r"sl-404"))

async def test_performance_glitch_user(async_page: Page):
    await login_to_saucedemo_async(async_page, username="performance_glitch_user", password=PASSWORD)

    # Login is delayed ~5s, longer than the default 5s expect timeout
    await expect_inventory_page_async(async_page, timeout=15000)

async def test_error_user(async_page: Page):
    # error_user logs in normally; its bugs appear later in cart/checkout
    await login_to_saucedemo_async(async_page, username="error_user", password=PASSWORD)

    await expect_inventory_page_async(async_page)

async def test_visual_user(async_page: Page):
    await login_to_saucedemo_async(async_page, username="visual_user", password=PASSWORD)

    await expect_inventory_page_async(async_page)

    # visual_user gets a misplaced cart icon
    await expect(async_page.locator(".shopping_cart_container")).to_have_class(re.compile(r"visual_failure"))

@pytest.mark.parametrize("username", LOGIN_USERS)
async def test_login_then_logout(async_page: Page, username: str):
    await login_to_saucedemo_async(async_page, username=username, password=PASSWORD)
    await expect_inventory_page_async(async_page, timeout=15000)

    await logout_from_saucedemo_async(async_page)

    await expect(async_page).to_have_url(f"{BASE_URL}/")
    await expect(async_page.locator("input#login-button")).to_be_visible()

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
async def test_invalid_login(async_page: Page, username: str, password: str, expected_error: str):
    await login_to_saucedemo_async(async_page, username=username, password=password)

    error_message = get_error_message(async_page)
    await expect(error_message).to_be_visible()
    await expect(error_message).to_have_text(expected_error)
    await expect(async_page).to_have_url(f"{BASE_URL}/")

async def test_close_error_message(async_page: Page):
    await login_to_saucedemo_async(async_page, username="locked_out_user", password=PASSWORD)

    error_message = get_error_message(async_page)
    await expect(error_message).to_be_visible()

    await async_page.click("[data-test='error-button']")

    await expect(error_message).to_be_hidden()

async def test_inventory_requires_login(async_page: Page):
    await async_page.goto(f"{BASE_URL}/inventory.html")

    await expect(async_page).to_have_url(f"{BASE_URL}/")
    await expect(get_error_message(async_page)).to_have_text(
        "Epic sadface: You can only access '/inventory.html' when you are logged in."
    )

async def test_concurrent_logins(async_browser: Browser):
    # Async-only: log every user in at the same time, each in its own isolated context.
    # Total time ~= the slowest login (performance_glitch_user), not the sum of all logins.
    async def login_as(username: str):
        context = await async_browser.new_context()
        try:
            page = await context.new_page()
            await login_to_saucedemo_async(page, username=username, password=PASSWORD)
            await expect_inventory_page_async(page, timeout=15000)
        finally:
            await context.close()

    await asyncio.gather(*(login_as(user) for user in LOGIN_USERS))
