import pytest
import pytest_asyncio
from playwright.async_api import async_playwright
from playwright.sync_api import Page, Playwright
from config import BASE_URL
from pages.cart_page import CartPage
from pages.checkout_pages import CheckoutCompletePage, CheckoutInfoPage, CheckoutOverviewPage
from pages.components import Footer, Menu
from pages.dynamic_catalog import LazyLoadPage, SliderPage, SpinnerPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage
from pages.product_page import ProductPage

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
def product_page(page: Page) -> ProductPage:
    return ProductPage(page)

@pytest.fixture
def cart_page(page: Page) -> CartPage:
    return CartPage(page)

@pytest.fixture
def checkout_info_page(page: Page) -> CheckoutInfoPage:
    return CheckoutInfoPage(page)

@pytest.fixture
def checkout_overview_page(page: Page) -> CheckoutOverviewPage:
    return CheckoutOverviewPage(page)

@pytest.fixture
def checkout_complete_page(page: Page) -> CheckoutCompletePage:
    return CheckoutCompletePage(page)

@pytest.fixture
def lazy_load_page(page: Page) -> LazyLoadPage:
    return LazyLoadPage(page)

@pytest.fixture
def spinner_page(page: Page) -> SpinnerPage:
    return SpinnerPage(page)

@pytest.fixture
def slider_page(page: Page) -> SliderPage:
    return SliderPage(page)

@pytest.fixture
def menu(page: Page) -> Menu:
    return Menu(page)

@pytest.fixture
def footer(page: Page) -> Footer:
    return Footer(page)

# ---------------------------------------------------------------------------
# Cookie login: tests that aren't about logging in skip the login form
# ---------------------------------------------------------------------------

@pytest.fixture
def login_as(page: Page, inventory_page: InventoryPage):
    """Log in without the form, then land on the Products page: login_as() or login_as("problem_user")"""
    # SauceDemo keeps the whole session in one cookie, session-username=<user>, and each page reads it on load
    # (the per-user bugs come from it too). Setting it directly skips the login page and its form.
    def login(username: str = "standard_user"):
        page.context.add_cookies([{"name": "session-username", "value": username, "url": BASE_URL}])
        inventory_page.open()
        inventory_page.expect_loaded()
    return login

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
