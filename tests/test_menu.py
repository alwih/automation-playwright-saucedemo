import re
import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from conftest import (
    INVENTORY_URL,
    expect_inventory_page,
    get_error_message,
    login_to_saucedemo,
    logout_from_saucedemo,
)

# Click the buttons, not [data-test='open-menu'] / [data-test='close-menu']: those are icon images under the buttons
MENU_BUTTON = "#react-burger-menu-btn"
CLOSE_BUTTON = "#react-burger-cross-btn"
# The closed menu is moved off-screen, not hidden, so open/closed is checked with to_be_in_viewport()
MENU = ".bm-menu-wrap"
# Only the 5 top-level items: submenu links end in "-link", not "-sidebar-link"
MENU_ITEMS = "[data-test$='-sidebar-link']"
MENU_LABELS = ["All Items", "Dynamic Catalog", "About", "Logout", "Reset App State"]
DYNAMIC_CATALOG_LINK = "[data-test='dynamic-catalog-sidebar-link']"
DYNAMIC_CATALOG_SUBMENU = "[data-test='dynamic-catalog-submenu']"
# Dynamic Catalog page slug -> label (page URL is /dynamic-catalog-<slug>.html)
DYNAMIC_PAGES = {
    "lazy-load": "Lazy Load",
    "spinner": "Spinner",
    "slider": "Slider",
}
ABOUT_URL = "https://saucelabs.com/"
ABOUT_404_URL = "https://saucelabs.com/error/404"
# (data-test, link text, href) of each footer link
SOCIAL_LINKS = [
    ("social-x", "X", "https://x.com/saucelabs"),
    ("social-facebook", "Facebook", "https://www.facebook.com/saucelabs"),
    ("social-linkedin", "LinkedIn", "https://www.linkedin.com/company/sauce-labs/"),
]
FOOTER_COPY = "[data-test='footer-copy']"
COPYRIGHT = re.compile(r"^© (\d{4}) Sauce Labs\. All Rights Reserved\. Terms of Service \| Privacy Policy$")

def open_menu(page: Page):
    """Open the burger menu and wait until it has slid into view"""
    page.click(MENU_BUTTON)
    expect(page.locator(MENU)).to_be_in_viewport()

def test_menu_items(page: Page):
    # Positive: the menu starts closed and opens with the 5 items in order
    login_to_saucedemo(page)
    expect_inventory_page(page)
    expect(page.locator(MENU)).not_to_be_in_viewport()

    open_menu(page)

    expect(page.locator(MENU_ITEMS)).to_have_text(MENU_LABELS)

@pytest.mark.parametrize("close_with", ["close_button", "escape"])
def test_close_menu(page: Page, close_with: str):
    # Positive: the ✕ button and the Escape key both close the menu
    login_to_saucedemo(page)
    open_menu(page)

    if close_with == "close_button":
        page.click(CLOSE_BUTTON)
    else:
        page.keyboard.press("Escape")

    expect(page.locator(MENU)).not_to_be_in_viewport()

@pytest.mark.parametrize(
    "path",
    ["/cart.html", "/inventory-item.html?id=4", "/checkout-step-one.html", "/checkout-complete.html"],
    ids=["cart", "product_detail", "checkout_step_one", "checkout_complete"],
)
def test_all_items_from_other_pages(page: Page, path: str):
    # Positive: All Items goes back to the products page from anywhere, and keeps the cart
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("1")
    page.goto(f"{BASE_URL}{path}")

    open_menu(page)
    page.click("[data-test='inventory-sidebar-link']")

    expect_inventory_page(page)
    expect(page.locator(MENU)).not_to_be_in_viewport()
    expect(cart_badge).to_have_text("1")

def test_dynamic_catalog_submenu(page: Page):
    # Positive: Dynamic Catalog opens and closes its submenu
    login_to_saucedemo(page)
    open_menu(page)
    dynamic_catalog = page.locator(DYNAMIC_CATALOG_LINK)
    submenu = page.locator(DYNAMIC_CATALOG_SUBMENU)

    dynamic_catalog.click()
    expect(dynamic_catalog).to_have_attribute("aria-expanded", "true")
    expect(submenu.locator("a")).to_have_text(list(DYNAMIC_PAGES.values()))

    # Closing removes the submenu from the page instead of hiding it
    dynamic_catalog.click()
    expect(dynamic_catalog).to_have_attribute("aria-expanded", "false")
    expect(submenu).to_have_count(0)

@pytest.mark.parametrize("slug, label", DYNAMIC_PAGES.items(), ids=["lazy_load", "spinner", "slider"])
def test_dynamic_catalog_links(page: Page, slug: str, label: str):
    # Positive: each submenu link opens its Dynamic Catalog page (what the pages do is tested elsewhere)
    login_to_saucedemo(page)
    open_menu(page)
    page.click(DYNAMIC_CATALOG_LINK)

    page.click(f"[data-test='dynamic-catalog-{slug}-link']")

    expect(page).to_have_url(f"{BASE_URL}/dynamic-catalog-{slug}.html")
    expect(page.locator("[data-test='title']")).to_have_text(f"Dynamic Catalog - {label}")
    expect(page.locator(MENU)).not_to_be_in_viewport()

def test_about_link(page: Page):
    # Positive: About links to the Sauce Labs site (only the href is checked, clicking would leave saucedemo)
    login_to_saucedemo(page)
    open_menu(page)

    expect(page.locator("[data-test='about-sidebar-link']")).to_have_attribute("href", ABOUT_URL)

def test_problem_user_about_link_is_404(page: Page):
    # Negative: for problem_user, About links to a 404 page
    login_to_saucedemo(page, username="problem_user")
    open_menu(page)

    expect(page.locator("[data-test='about-sidebar-link']")).to_have_attribute("href", ABOUT_404_URL)

def test_reset_app_state_empties_cart(page: Page):
    # Positive: Reset App State empties the cart
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    page.click("button[data-test='add-to-cart-sauce-labs-onesie']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("2")

    open_menu(page)
    page.click("[data-test='reset-sidebar-link']")

    expect(cart_badge).to_be_hidden()
    page.click(".shopping_cart_link")
    expect(page.locator("[data-test='title']")).to_have_text("Your Cart")
    expect(page.locator(".cart_item")).to_have_count(0)

    # Back on the products page every button is "Add to cart" again
    page.click("button[data-test='continue-shopping']")
    expect_inventory_page(page)
    expect(page.locator("button[data-test^='add-to-cart']")).to_have_count(6)

@pytest.mark.xfail(reason="saucedemo bug: Reset App State leaves stale Remove buttons on the page", strict=True)
def test_reset_app_state_updates_buttons(page: Page):
    # Negative: right after Reset, the products page shouldn't show any Remove buttons
    login_to_saucedemo(page)
    page.click("button[data-test='add-to-cart-sauce-labs-backpack']")
    page.click("button[data-test='add-to-cart-sauce-labs-onesie']")
    cart_badge = page.locator(".shopping_cart_badge")
    expect(cart_badge).to_have_text("2")

    open_menu(page)
    page.click("[data-test='reset-sidebar-link']")

    # The hidden badge proves the Reset was handled; today both buttons still say Remove until the page re-renders
    expect(cart_badge).to_be_hidden()
    expect(page.locator("button[data-test^='remove']")).to_have_count(0)

def test_back_after_logout_is_blocked(page: Page):
    # Negative: the browser's Back button can't reopen the products page after logging out
    login_to_saucedemo(page)
    expect_inventory_page(page)
    logout_from_saucedemo(page)
    expect(page).to_have_url(f"{BASE_URL}/")

    page.go_back()

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(get_error_message(page)).to_have_text(
        "Epic sadface: You can only access '/inventory.html' when you are logged in."
    )

@pytest.mark.parametrize("data_test, text, href", SOCIAL_LINKS, ids=["x", "facebook", "linkedin"])
def test_footer_social_links(page: Page, data_test: str, text: str, href: str):
    # Positive: each footer link points to Sauce Labs' page and opens in a new tab
    login_to_saucedemo(page)

    link = page.locator(f"[data-test='{data_test}']")
    expect(link).to_have_text(text)
    expect(link).to_have_attribute("href", href)
    expect(link).to_have_attribute("target", "_blank")
    expect(link).to_have_attribute("rel", "noreferrer")

def test_social_link_opens_new_tab(page: Page):
    # Positive: clicking a footer link opens a new tab and leaves the products page where it is
    login_to_saucedemo(page)
    # Answer with a stub page so the test never loads x.com. The route goes on the context, because page routes skip popups
    page.context.route("https://x.com/**", lambda route: route.fulfill(body="<p>stub</p>", content_type="text/html"))

    with page.expect_popup() as popup_info:
        page.click("[data-test='social-x']")

    expect(popup_info.value).to_have_url("https://x.com/saucelabs")
    expect(page).to_have_url(INVENTORY_URL)

def test_footer_copyright(page: Page):
    # Positive: the footer shows the copyright line
    login_to_saucedemo(page)

    expect(page.locator(FOOTER_COPY)).to_have_text(COPYRIGHT)

def test_copyright_year_follows_browser_clock(page: Page):
    # Edge case: the copyright year comes from the browser's clock, not from a fixed string
    # The clock must be set before the page loads, because the footer reads the year when it renders
    page.clock.set_fixed_time("2030-06-01")
    login_to_saucedemo(page)

    expect(page.locator(FOOTER_COPY)).to_have_text(re.compile(r"^© 2030 Sauce Labs\."))
