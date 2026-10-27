import re
import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from data.products import BACKPACK, ONESIE
from pages.cart_page import CartPage
from pages.components import Footer, Menu
from pages.dynamic_catalog import DynamicCatalogPage, LazyLoadPage, SliderPage, SpinnerPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

MENU_LABELS = ["All Items", "Dynamic Catalog", "About", "Logout", "Reset App State"]
# Dynamic Catalog page -> its label in the submenu
DYNAMIC_PAGES = {
    LazyLoadPage: "Lazy Load",
    SpinnerPage: "Spinner",
    SliderPage: "Slider",
}
ABOUT_URL = "https://saucelabs.com/"
ABOUT_404_URL = "https://saucelabs.com/error/404"
# (network, link text, href) of each footer link
SOCIAL_LINKS = [
    ("x", "X", "https://x.com/saucelabs"),
    ("facebook", "Facebook", "https://www.facebook.com/saucelabs"),
    ("linkedin", "LinkedIn", "https://www.linkedin.com/company/sauce-labs/"),
]
COPYRIGHT = re.compile(r"^© (\d{4}) Sauce Labs\. All Rights Reserved\. Terms of Service \| Privacy Policy$")

def test_menu_items(login_as, menu: Menu):
    # Positive: the menu starts closed and opens with the 5 items in order
    login_as()
    expect(menu.panel).not_to_be_in_viewport()

    menu.open()

    expect(menu.items).to_have_text(MENU_LABELS)

@pytest.mark.parametrize("close_with", ["close_button", "escape"])
def test_close_menu(page: Page, login_as, menu: Menu, close_with: str):
    # Positive: the ✕ button and the Escape key both close the menu
    login_as()
    menu.open()

    if close_with == "close_button":
        menu.close()
    else:
        page.keyboard.press("Escape")

    expect(menu.panel).not_to_be_in_viewport()

@pytest.mark.parametrize(
    "path",
    ["/cart.html", "/inventory-item.html?id=4", "/checkout-step-one.html", "/checkout-complete.html"],
    ids=["cart", "product_detail", "checkout_step_one", "checkout_complete"],
)
def test_all_items_from_other_pages(page: Page, login_as, inventory_page: InventoryPage, menu: Menu, path: str):
    # Positive: All Items goes back to the products page from anywhere, and keeps the cart
    login_as()
    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")
    page.goto(f"{BASE_URL}{path}")

    menu.all_items()

    inventory_page.expect_loaded()
    expect(menu.panel).not_to_be_in_viewport()
    expect(inventory_page.cart_badge).to_have_text("1")

def test_dynamic_catalog_submenu(login_as, menu: Menu):
    # Positive: Dynamic Catalog opens and closes its submenu
    login_as()
    menu.open()

    menu.toggle_dynamic_catalog()
    expect(menu.dynamic_catalog_link).to_have_attribute("aria-expanded", "true")
    expect(menu.dynamic_catalog_submenu_links).to_have_text(list(DYNAMIC_PAGES.values()))

    # Closing removes the submenu from the page instead of hiding it
    menu.toggle_dynamic_catalog()
    expect(menu.dynamic_catalog_link).to_have_attribute("aria-expanded", "false")
    expect(menu.dynamic_catalog_submenu).to_have_count(0)

@pytest.mark.parametrize("page_class, label", DYNAMIC_PAGES.items(), ids=["lazy_load", "spinner", "slider"])
def test_dynamic_catalog_links(page: Page, login_as, menu: Menu, page_class: type[DynamicCatalogPage], label: str):
    # Positive: each submenu link opens its Dynamic Catalog page (what the pages do is tested elsewhere)
    login_as()

    menu.open_dynamic_catalog_page(page_class.SLUG)

    dynamic_page = page_class(page)
    dynamic_page.expect_loaded()
    expect(dynamic_page.title).to_have_text(f"Dynamic Catalog - {label}")
    expect(menu.panel).not_to_be_in_viewport()

def test_about_link(login_as, menu: Menu):
    # Positive: About links to the Sauce Labs site (only the href is checked, clicking would leave saucedemo)
    login_as()
    menu.open()

    expect(menu.about_link).to_have_attribute("href", ABOUT_URL)

def test_problem_user_about_link_is_404(login_as, menu: Menu):
    # Negative: for problem_user, About links to a 404 page
    login_as("problem_user")
    menu.open()

    expect(menu.about_link).to_have_attribute("href", ABOUT_404_URL)

def test_reset_app_state_empties_cart(login_as, inventory_page: InventoryPage, cart_page: CartPage, menu: Menu):
    # Positive: Reset App State empties the cart
    login_as()
    inventory_page.add_to_cart(BACKPACK)
    inventory_page.add_to_cart(ONESIE)
    expect(inventory_page.cart_badge).to_have_text("2")

    menu.reset_app_state()

    expect(inventory_page.cart_badge).to_be_hidden()
    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.items).to_have_count(0)

    # Back on the products page every button is "Add to cart" again
    cart_page.continue_shopping()
    inventory_page.expect_loaded()
    expect(inventory_page.add_buttons).to_have_count(6)

@pytest.mark.xfail(reason="saucedemo bug: Reset App State leaves stale Remove buttons on the page", strict=True)
def test_reset_app_state_updates_buttons(login_as, inventory_page: InventoryPage, menu: Menu):
    # Negative: right after Reset, the products page shouldn't show any Remove buttons
    login_as()
    inventory_page.add_to_cart(BACKPACK)
    inventory_page.add_to_cart(ONESIE)
    expect(inventory_page.cart_badge).to_have_text("2")

    menu.reset_app_state()

    # The hidden badge proves the Reset was handled; today both buttons still say Remove until the page re-renders
    expect(inventory_page.cart_badge).to_be_hidden()
    expect(inventory_page.remove_buttons).to_have_count(0)

def test_back_after_logout_is_blocked(page: Page, login_as, login_page: LoginPage, menu: Menu):
    # Negative: the browser's Back button can't reopen the products page after logging out
    login_as()
    menu.logout()
    login_page.expect_loaded()

    page.go_back()

    login_page.expect_access_denied("/inventory.html")

@pytest.mark.parametrize("network, text, href", SOCIAL_LINKS, ids=["x", "facebook", "linkedin"])
def test_footer_social_links(login_as, footer: Footer, network: str, text: str, href: str):
    # Positive: each footer link points to Sauce Labs' page and opens in a new tab
    login_as()

    link = footer.social_link(network)
    expect(link).to_have_text(text)
    expect(link).to_have_attribute("href", href)
    expect(link).to_have_attribute("target", "_blank")
    expect(link).to_have_attribute("rel", "noreferrer")

def test_social_link_opens_new_tab(page: Page, login_as, inventory_page: InventoryPage, footer: Footer):
    # Positive: clicking a footer link opens a new tab and leaves the products page where it is
    login_as()
    # Answer with a stub page so the test never loads x.com. The route goes on the context, because page routes skip popups
    page.context.route("https://x.com/**", lambda route: route.fulfill(body="<p>stub</p>", content_type="text/html"))

    with page.expect_popup() as popup_info:
        footer.social_link("x").click()

    expect(popup_info.value).to_have_url("https://x.com/saucelabs")
    expect(page).to_have_url(InventoryPage.URL)

def test_footer_copyright(login_as, footer: Footer):
    # Positive: the footer shows the copyright line
    login_as()

    expect(footer.copyright).to_have_text(COPYRIGHT)

def test_copyright_year_follows_browser_clock(page: Page, login_as, footer: Footer):
    # Edge case: the copyright year comes from the browser's clock, not from a fixed string
    # The clock must be set before the page loads, because the footer reads the year when it renders
    page.clock.set_fixed_time("2030-06-01")
    login_as()

    expect(footer.copyright).to_have_text(re.compile(r"^© 2030 Sauce Labs\."))
