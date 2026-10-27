from playwright.sync_api import Page, expect

class Menu:
    """The burger menu, on every logged-in page"""

    def __init__(self, page: Page):
        self.page = page
        # Click the buttons, not get_by_test_id("open-menu") / ("close-menu"): those are icon images under the buttons
        self.open_button = page.locator("#react-burger-menu-btn")
        self.close_button = page.locator("#react-burger-cross-btn")
        # The closed menu is moved off-screen, not hidden, so open/closed is checked with to_be_in_viewport()
        self.panel = page.locator(".bm-menu-wrap")
        self.logout_link = page.get_by_test_id("logout-sidebar-link")

    def open(self):
        """Open the menu and wait until it has slid into view"""
        self.open_button.click()
        expect(self.panel).to_be_in_viewport()

    def close(self):
        self.close_button.click()

    def logout(self):
        self.open()
        self.logout_link.click()
