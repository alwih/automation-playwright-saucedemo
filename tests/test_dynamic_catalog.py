import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from data.products import PRODUCTS
from pages.dynamic_catalog import DynamicCatalogPage, LazyLoadPage, SliderPage, SpinnerPage
from pages.inventory_page import InventoryPage
from pages.login_page import LoginPage

# At pytest-playwright's default 1280x720 viewport (4 cards per row, 2 rows on screen) the page
# settles at 12 cards, and only the 8 on screen are loaded
FIRST_SCREEN_CARDS = 12
FIRST_SCREEN_LOADED = 8
# Cards added each time the sentinel comes into view, and the list's length before it repeats
LAZY_BATCH = LazyLoadPage.BATCH
LAZY_CYCLE = 22

# The site shows the spinner for 500 + Math.random() * 2500 ms
SPINNER_MIN_MS = 500
SPINNER_MAX_MS = 3000

# The slider moves to the next product on a 2-second setInterval
SLIDE_MS = 2000

@pytest.fixture
def go_to_dynamic_page(login_page: LoginPage, inventory_page: InventoryPage):
    """Log in, then open a Dynamic Catalog page by URL"""
    def go(dynamic_page: DynamicCatalogPage, freeze_clock: bool = False):
        login_page.login()
        # Wait for the login to finish first, so the goto can't race it
        inventory_page.expect_loaded()
        dynamic_page.open(freeze_clock=freeze_clock)
    return go

def test_lazy_load_first_screen(go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Positive: the cards on screen are loaded, the ones below the fold still say "Loading…"
    go_to_dynamic_page(lazy_load_page)

    expect(lazy_load_page.cards).to_have_count(FIRST_SCREEN_CARDS)
    expect(lazy_load_page.names).to_have_count(FIRST_SCREEN_LOADED)
    expect(lazy_load_page.card(0).name).to_have_text("Sauce Labs Bike Light")
    expect(lazy_load_page.card(0).price).to_have_text("$9.99")
    expect(lazy_load_page.placeholders).to_have_text(["Loading…"] * (FIRST_SCREEN_CARDS - FIRST_SCREEN_LOADED))
    expect(lazy_load_page.sentinel).not_to_be_in_viewport()

def test_placeholder_loads_when_scrolled_into_view(go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Positive: a placeholder card loads its product once it is scrolled on screen
    go_to_dynamic_page(lazy_load_page)
    card = lazy_load_page.card(11)
    expect(card.root).to_have_text("Loading…")

    card.root.scroll_into_view_if_needed()

    expect(card.name).to_have_text("Test.allTheThings() T-Shirt (Red) (S)")
    expect(card.price).to_have_text("$15.99")

def test_sentinel_loads_more_cards(go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Positive: each time the sentinel at the bottom comes into view, 6 more cards are added
    go_to_dynamic_page(lazy_load_page)

    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + LAZY_BATCH)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)

    # Each scroll moves less than one screen, so every new card passed through the viewport and loaded
    expect(lazy_load_page.placeholders).to_have_count(0)

def test_lazy_load_list_repeats(go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Edge case: the list loops over 22 entries, so card 22 is card 0 again and the page never runs out
    go_to_dynamic_page(lazy_load_page)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + LAZY_BATCH)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)
    expect(lazy_load_page.placeholders).to_have_count(0)

    first_card = lazy_load_page.card(0)
    name = first_card.name.inner_text()
    price = first_card.price.inner_text()
    image = first_card.image.get_attribute("src")

    repeated_card = lazy_load_page.card(LAZY_CYCLE)
    expect(repeated_card.name).to_have_text(name)
    expect(repeated_card.price).to_have_text(price)
    expect(repeated_card.image).to_have_attribute("src", image)

@pytest.mark.xfail(reason="saucedemo bug: Lazy Load lists the Red T-Shirt (L) twice", strict=True)
def test_lazy_load_no_duplicate_products(go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Negative: one pass through the list shouldn't show the same product twice
    go_to_dynamic_page(lazy_load_page)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + LAZY_BATCH)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)
    # all_inner_texts() doesn't wait, so read the names only once every card has loaded
    expect(lazy_load_page.placeholders).to_have_count(0)

    names = lazy_load_page.names.all_inner_texts()[:LAZY_CYCLE]

    # Today "Test.allTheThings() T-Shirt (Red) (L)" is both card 13 and card 14
    assert len(set(names)) == len(names)

def test_lazy_load_resets_after_reload(page: Page, go_to_dynamic_page, lazy_load_page: LazyLoadPage):
    # Edge case: the loaded cards aren't remembered, so a reload shows the first screen again
    go_to_dynamic_page(lazy_load_page)
    lazy_load_page.load_next_batch(FIRST_SCREEN_CARDS + LAZY_BATCH)

    page.reload()

    expect(lazy_load_page.cards).to_have_count(FIRST_SCREEN_CARDS)
    expect(lazy_load_page.placeholders).to_have_count(FIRST_SCREEN_CARDS - FIRST_SCREEN_LOADED)

def test_spinner_then_products(page: Page, go_to_dynamic_page, spinner_page: SpinnerPage):
    # Positive: a loading spinner shows first, then the grid of the 6 products replaces it
    go_to_dynamic_page(spinner_page, freeze_clock=True)
    expect(spinner_page.loading_status).to_be_visible()
    expect(spinner_page.grid).to_have_count(0)

    page.clock.run_for(SPINNER_MAX_MS)

    expect(spinner_page.loading_status).to_have_count(0)
    expect(spinner_page.grid_names).to_have_text([product.name for product in PRODUCTS])
    expect(spinner_page.grid_prices).to_have_text([product.price for product in PRODUCTS])

def test_spinner_wait_bounds(page: Page, go_to_dynamic_page, spinner_page: SpinnerPage):
    # Edge case: the site waits a random 0.5-3 s, so the spinner is still there at 499 ms and gone by 3000 ms
    go_to_dynamic_page(spinner_page, freeze_clock=True)

    page.clock.run_for(SPINNER_MIN_MS - 1)
    expect(spinner_page.spinner).to_be_visible()

    page.clock.run_for(SPINNER_MAX_MS - (SPINNER_MIN_MS - 1))
    expect(spinner_page.spinner).to_have_count(0)
    expect(spinner_page.grid).to_be_visible()

def test_slider_starts_on_first_product(go_to_dynamic_page, slider_page: SliderPage):
    # Positive: there is one dot per product, and the slider starts on the first one
    go_to_dynamic_page(slider_page, freeze_clock=True)

    expect(slider_page.dots).to_have_count(len(PRODUCTS))
    for index, product in enumerate(PRODUCTS):
        expect(slider_page.dot(index)).to_have_attribute("aria-label", f"Show {product.name}")
    slider_page.expect_slide(0)

def test_slider_cycles_through_products(page: Page, go_to_dynamic_page, slider_page: SliderPage):
    # Positive: every 2 seconds the slider moves to the next product, and after the last one it starts over
    go_to_dynamic_page(slider_page, freeze_clock=True)
    slider_page.expect_slide(0)

    for step in range(1, len(PRODUCTS) + 1):
        page.clock.run_for(SLIDE_MS)
        slider_page.expect_slide(step % len(PRODUCTS))

def test_slider_waits_two_seconds(page: Page, go_to_dynamic_page, slider_page: SliderPage):
    # Edge case: the slide changes at exactly 2 seconds, not before
    go_to_dynamic_page(slider_page, freeze_clock=True)

    page.clock.run_for(SLIDE_MS - 1)
    slider_page.expect_slide(0)

    page.clock.run_for(1)
    slider_page.expect_slide(1)

@pytest.mark.parametrize("index", [1, 2, 3, 4, 5], ids=["dot_1", "dot_2", "dot_3", "dot_4", "dot_5"])
def test_slider_dot_shows_product(go_to_dynamic_page, slider_page: SliderPage, index: int):
    # Positive: clicking a dot shows its product (the clock is frozen, so the slider can't move by itself)
    go_to_dynamic_page(slider_page, freeze_clock=True)

    slider_page.dot(index).click()

    slider_page.expect_slide(index)

def test_slider_dot_click_keeps_timer(page: Page, go_to_dynamic_page, slider_page: SliderPage):
    # Edge case: clicking a dot doesn't restart the 2-second timer, so the next slide comes 1 second later
    go_to_dynamic_page(slider_page, freeze_clock=True)
    page.clock.run_for(SLIDE_MS // 2)
    slider_page.dot(4).click()
    slider_page.expect_slide(4)

    page.clock.run_for(SLIDE_MS // 2)

    slider_page.expect_slide(5)

@pytest.mark.parametrize("slug", ["lazy-load", "spinner", "slider"], ids=["lazy_load", "spinner", "slider"])
def test_dynamic_catalog_requires_login(page: Page, login_page: LoginPage, slug: str):
    # Negative: the Dynamic Catalog pages can't be opened without logging in
    page.goto(f"{BASE_URL}/dynamic-catalog-{slug}.html")

    login_page.expect_access_denied(f"/dynamic-catalog-{slug}.html")
