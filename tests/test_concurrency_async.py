import asyncio
from contextlib import asynccontextmanager

import pytest
from playwright.async_api import Browser, Page, expect
from config import BASE_URL
from data.products import BACKPACK, BIKE_LIGHT
from data.users import LOGIN_USERS, PASSWORD

# The only async tests in the suite: each one drives several browser sessions at the same time.
# Everything else is sync, because pytest runs async tests one at a time anyway (use -n for speed).

# Every test in this file runs on the session-wide event loop shared with the async fixtures
pytestmark = pytest.mark.asyncio(loop_scope="session")

INVENTORY_URL = f"{BASE_URL}/inventory.html"

# Users who can place an order: problem_user's form loses the last name, and error_user's Finish crashes
CHECKOUT_USERS = ["standard_user", "performance_glitch_user", "visual_user"]

@asynccontextmanager
async def new_session(browser: Browser):
    """A page in a fresh context: its own cookies and localStorage, like a separate browser"""
    context = await browser.new_context()
    try:
        yield await context.new_page()
    finally:
        await context.close()

async def login(page: Page, username: str = "standard_user"):
    await page.goto(BASE_URL)
    await page.get_by_test_id("username").fill(username)
    await page.get_by_test_id("password").fill(PASSWORD)
    await page.get_by_test_id("login-button").click()

async def expect_inventory_page(page: Page, timeout: float = 5000):
    """Assert the user landed on the Products (inventory) page"""
    await expect(page).to_have_url(INVENTORY_URL, timeout=timeout)
    await expect(page.get_by_test_id("inventory-list")).to_be_visible(timeout=timeout)
    await expect(page.get_by_test_id("title")).to_have_text("Products", timeout=timeout)

async def test_concurrent_logins(async_browser: Browser):
    # Positive: log every user in at the same time, each in its own isolated context.
    # Total time ~= the slowest login (performance_glitch_user), not the sum of all logins.
    async def login_user(username: str):
        async with new_session(async_browser) as page:
            await login(page, username)
            await expect_inventory_page(page, timeout=15000)

    await asyncio.gather(*(login_user(user) for user in LOGIN_USERS))

async def test_same_user_has_separate_carts_per_browser(async_browser: Browser):
    # Edge case: standard_user is logged in on two browsers at once, and each adds a different product.
    # Each cart lists only its own product: the cart lives in the browser's localStorage, not on the account
    async with new_session(async_browser) as page_a, new_session(async_browser) as page_b:
        await asyncio.gather(login(page_a), login(page_b))
        await asyncio.gather(expect_inventory_page(page_a), expect_inventory_page(page_b))

        # Both products are added before either cart is opened
        await asyncio.gather(
            page_a.get_by_test_id(f"add-to-cart-{BACKPACK.slug}").click(),
            page_b.get_by_test_id(f"add-to-cart-{BIKE_LIGHT.slug}").click(),
        )

        for page, product in ((page_a, BACKPACK), (page_b, BIKE_LIGHT)):
            await expect(page.get_by_test_id("shopping-cart-badge")).to_have_text("1")
            await page.get_by_test_id("shopping-cart-link").click()
            # Scope to the cart list: the inventory list is still in the DOM for a moment after the URL changes
            await expect(page.get_by_test_id("cart-list").get_by_test_id("inventory-item-name")).to_have_text([product.name])

async def test_concurrent_checkouts(async_browser: Browser):
    # Positive: every user who can place an order checks out at the same time, each in its own session
    async def checkout(username: str):
        async with new_session(async_browser) as page:
            await login(page, username)
            # performance_glitch_user's login takes ~5s, longer than the default 5s expect timeout
            await expect_inventory_page(page, timeout=15000)

            await page.get_by_test_id(f"add-to-cart-{BACKPACK.slug}").click()
            await page.get_by_test_id("shopping-cart-link").click()
            await page.get_by_test_id("checkout").click()
            await page.get_by_test_id("firstName").fill("John")
            await page.get_by_test_id("lastName").fill("Doe")
            await page.get_by_test_id("postalCode").fill("12345")
            await page.get_by_test_id("continue").click()
            await page.get_by_test_id("finish").click()

            await expect(page).to_have_url(f"{BASE_URL}/checkout-complete.html")
            await expect(page.get_by_test_id("complete-header")).to_have_text("Thank you for your order!")
            await expect(page.get_by_test_id("shopping-cart-badge")).to_be_hidden()

    await asyncio.gather(*(checkout(user) for user in CHECKOUT_USERS))
