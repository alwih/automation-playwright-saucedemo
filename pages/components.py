import re

from playwright.sync_api import Locator, Page, expect

class Menu:
    """The burger menu, on every logged-in page"""

    def __init__(self, page: Page):
        self.page = page
        # Click the buttons, not get_by_test_id("open-menu") / ("close-menu"): those are icon images under the buttons
        self.open_button = page.locator("#react-burger-menu-btn")
        self.close_button = page.locator("#react-burger-cross-btn")
        # The closed menu is moved off-screen, not hidden, so open/closed is checked with to_be_in_viewport()
        self.panel = page.locator(".bm-menu-wrap")
        # Only the 5 top-level items: submenu links end in "-link", not "-sidebar-link"
        self.items = page.get_by_test_id(re.compile(r"-sidebar-link$"))
        self.all_items_link = page.get_by_test_id("inventory-sidebar-link")
        self.dynamic_catalog_link = page.get_by_test_id("dynamic-catalog-sidebar-link")
        # Only in the page while it is open
        self.dynamic_catalog_submenu = page.get_by_test_id("dynamic-catalog-submenu")
        self.dynamic_catalog_submenu_links = self.dynamic_catalog_submenu.get_by_test_id(re.compile(r"^dynamic-catalog-.+-link$"))
        self.about_link = page.get_by_test_id("about-sidebar-link")
        self.logout_link = page.get_by_test_id("logout-sidebar-link")
        self.reset_link = page.get_by_test_id("reset-sidebar-link")

    def open(self):
        """Open the menu and wait until it has slid into view"""
        self.open_button.click()
        expect(self.panel).to_be_in_viewport()

    def close(self):
        self.close_button.click()

    def all_items(self):
        self.open()
        self.all_items_link.click()

    def toggle_dynamic_catalog(self):
        """Open or close the Dynamic Catalog submenu (the menu must be open)"""
        self.dynamic_catalog_link.click()

    def open_dynamic_catalog_page(self, slug: str):
        """Go to a Dynamic Catalog page through the submenu (slug is 'lazy-load', 'spinner' or 'slider')"""
        self.open()
        self.toggle_dynamic_catalog()
        self.page.get_by_test_id(f"dynamic-catalog-{slug}-link").click()

    def logout(self):
        self.open()
        self.logout_link.click()

    def reset_app_state(self):
        self.open()
        self.reset_link.click()

class Footer:
    """The footer, on every logged-in page"""

    def __init__(self, page: Page):
        self.page = page
        self.copyright = page.get_by_test_id("footer-copy")

    def social_link(self, network: str) -> Locator:
        """Link to Sauce Labs' page on network: 'x', 'facebook' or 'linkedin'"""
        return self.page.get_by_test_id(f"social-{network}")
