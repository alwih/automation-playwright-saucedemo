import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import Page, Playwright, expect
from config import BASE_URL
from data.users import PASSWORD
from pages.cart_page import CartPage
from pages.components import Menu
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

INVENTORY_URL = f"{BASE_URL}/inventory.html"

def login_to_saucedemo(page: Page, username: str = "standard_user", password: str = PASSWORD):
    page.goto(BASE_URL)
    page.fill("input#user-name", username)
    page.fill("input#password", password)
    page.click("input#login-button")

def logout_from_saucedemo(page: Page):
    """Logout through the burger menu"""
    page.click("#react-burger-menu-btn")
    page.click("#logout_sidebar_link")

def get_error_message(page: Page):
    """Locator for the error banner on the login page"""
    return page.locator("[data-test='error']")

def expect_inventory_page(page: Page, timeout: float = 5000):
    """Assert the user landed on the Products (inventory) page"""
    expect(page).to_have_url(INVENTORY_URL, timeout=timeout)
    expect(page.locator(".inventory_list")).to_be_visible(timeout=timeout)
    expect(page.locator("[data-test='title']")).to_have_text("Products", timeout=timeout)

# ---------------------------------------------------------------------------
# Page objects: each fixture wraps the test's `page`, so they all drive the same tab
# ---------------------------------------------------------------------------

@pytest.fixture(scope="session")
def browser_context_args(browser_context_args: dict, playwright: Playwright) -> dict:
    # Extends pytest-playwright's fixture so get_by_test_id("x") matches data-test="x", the attribute SauceDemo uses.
    # Only sync tests request it, so sync Playwright still starts after the async tests (see the sort hook below)
    playwright.selectors.set_test_id_attribute("data-test")
    return browser_context_args

@pytest.fixture
def login_page(page: Page) -> LoginPage:
    return LoginPage(page)

@pytest.fixture
def inventory_page(page: Page) -> InventoryPage:
    return InventoryPage(page)

@pytest.fixture
def cart_page(page: Page) -> CartPage:
    return CartPage(page)

@pytest.fixture
def menu(page: Page) -> Menu:
    return Menu(page)

# ---------------------------------------------------------------------------
# Async API: only test_concurrency_async.py uses it
# ---------------------------------------------------------------------------

@pytest.hookimpl(trylast=True)
def pytest_collection_modifyitems(items):
    # Once sync Playwright starts it keeps its event loop marked as "running" until the session ends,
    # which breaks any async test after it. So run async tests first (stable sort keeps the rest in order).
    items.sort(key=lambda item: item.get_closest_marker("asyncio") is None)

# pytest-playwright's built-in fixtures are sync-only, so async tests get their own browser.
# It runs on one session-wide event loop (loop_scope="session") so every async test can share it.
@pytest_asyncio.fixture(scope="session", loop_scope="session")
async def async_browser(browser_name: str, browser_type_launch_args: dict):
    """One browser for the whole run; honours --browser, --headed and --slowmo like the sync fixtures"""
    async with async_playwright() as playwright:
        # get_by_test_id("x") matches data-test="x", the attribute SauceDemo uses
        playwright.selectors.set_test_id_attribute("data-test")
        browser = await getattr(playwright, browser_name).launch(**browser_type_launch_args)
        yield browser
        await browser.close()
