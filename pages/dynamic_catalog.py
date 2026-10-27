import re
from datetime import datetime, timedelta

from playwright.sync_api import Locator, Page, expect
from config import BASE_URL
from data.products import PRODUCTS
from pages.base_page import BasePage

class DynamicCatalogPage(BasePage):
    """A Dynamic Catalog page: /dynamic-catalog-<SLUG>.html (each subclass sets SLUG and URL)"""

    SLUG = ""

    def __init__(self, page: Page):
        super().__init__(page)
        self.container = page.get_by_test_id(f"dynamic-catalog-{self.SLUG}-container")

    def open(self, freeze_clock: bool = False):
        """Open the page by URL; freeze_clock stops the browser clock, so timers only fire on page.clock.run_for()"""
        if freeze_clock:
            # install() alone keeps fake time running; pause_at() stops it, so timers only fire on page.clock.run_for()
            # This runs before the goto, so the page creates its timers on the paused clock
            self.page.clock.install()
            self.page.clock.pause_at(datetime.now() + timedelta(seconds=1))
        self.page.goto(self.URL)
        expect(self.container).to_be_visible()

    def expect_loaded(self):
        expect(self.page).to_have_url(self.URL)
        expect(self.container).to_be_visible()

class LazyCard:
    """Card n of the Lazy Load list; until it scrolls on screen it only holds a "Loading…" placeholder"""

    def __init__(self, page: Page, n: int):
        self.root = page.get_by_test_id(f"lazy-load-item-{n}")
        self.name = page.get_by_test_id(f"lazy-load-item-{n}-name")
        self.price = page.get_by_test_id(f"lazy-load-item-{n}-price")
        self.image = page.get_by_test_id(f"lazy-load-item-{n}-img")

class LazyLoadPage(DynamicCatalogPage):
    SLUG = "lazy-load"
    URL = f"{BASE_URL}/dynamic-catalog-{SLUG}.html"
    # Cards added each time the sentinel at the bottom comes into view
    BATCH = 6

    def __init__(self, page: Page):
        super().__init__(page)
        # The "\d+$" keeps the -img / -name / -price inside each card out of the match
        self.cards = page.get_by_test_id(re.compile(r"^lazy-load-item-\d+$"))
        self.names = page.get_by_test_id(re.compile(r"^lazy-load-item-\d+-name$"))
        self.placeholders = page.get_by_test_id(re.compile(r"-placeholder$"))
        self.sentinel = page.get_by_test_id("dynamic-catalog-lazy-load-sentinel")

    def card(self, n: int) -> LazyCard:
        return LazyCard(self.page, n)

    def load_next_batch(self, count: int):
        """Scroll the sentinel into view and wait until the list grows from count - 6 to count cards"""
        # Wait for the previous batch first, or the scroll could be counted against it
        expect(self.cards).to_have_count(count - self.BATCH)
        self.sentinel.scroll_into_view_if_needed()
        expect(self.cards).to_have_count(count)

class SpinnerPage(DynamicCatalogPage):
    SLUG = "spinner"
    URL = f"{BASE_URL}/dynamic-catalog-{SLUG}.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.spinner = page.get_by_test_id("dynamic-catalog-spinner")
        # The same spinner, found the way a screen reader announces it
        self.loading_status = page.get_by_role("status", name="Loading")
        self.grid = page.get_by_test_id("dynamic-catalog-spinner-grid")
        self.grid_names = self.grid.get_by_test_id(re.compile(r"-name$"))
        self.grid_prices = self.grid.get_by_test_id(re.compile(r"-price$"))

class SliderPage(DynamicCatalogPage):
    SLUG = "slider"
    URL = f"{BASE_URL}/dynamic-catalog-{SLUG}.html"

    def __init__(self, page: Page):
        super().__init__(page)
        self.name = page.get_by_test_id("dynamic-catalog-slider-item-name")
        self.price = page.get_by_test_id("dynamic-catalog-slider-item-price")
        self.image = page.get_by_test_id("dynamic-catalog-slider-item-img")
        self.dots = page.get_by_test_id(re.compile(r"^dynamic-catalog-slider-dot-"))
        self.current_dot = self.dots.and_(page.locator("[aria-current='true']"))

    def dot(self, index: int) -> Locator:
        return self.page.get_by_test_id(f"dynamic-catalog-slider-dot-{index}")

    def expect_slide(self, index: int):
        """Assert the slider shows PRODUCTS[index] and only its dot is marked current"""
        product = PRODUCTS[index]
        expect(self.name).to_have_text(product.name)
        expect(self.price).to_have_text(product.price)
        expect(self.image).to_have_attribute("alt", product.name)
        expect(self.dot(index)).to_have_attribute("aria-current", "true")
        expect(self.current_dot).to_have_count(1)
