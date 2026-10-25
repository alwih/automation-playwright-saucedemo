from datetime import datetime, timedelta
import pytest
from playwright.sync_api import Page, expect
from config import BASE_URL
from conftest import (
    expect_inventory_page,
    get_error_message,
    login_to_saucedemo,
)
from data.products import PRODUCTS

# Lazy Load: the ">" keeps the -img / -name / -price inside each card out of the match
LAZY_CARDS = "[data-test='dynamic-catalog-lazy-load-container'] > [data-test^='lazy-load-item-']"
LAZY_NAMES = "[data-test^='lazy-load-item-'][data-test$='-name']"
LAZY_PLACEHOLDERS = "[data-test$='-placeholder']"
SENTINEL = "[data-test='dynamic-catalog-lazy-load-sentinel']"
# At pytest-playwright's default 1280x720 viewport (4 cards per row, 2 rows on screen) the page
# settles at 12 cards, and only the 8 on screen are loaded
FIRST_SCREEN_CARDS = 12
FIRST_SCREEN_LOADED = 8
# Cards added each time the sentinel comes into view, and the list's length before it repeats
LAZY_BATCH = 6
LAZY_CYCLE = 22

SPINNER = "[data-test='dynamic-catalog-spinner']"
SPINNER_GRID = "[data-test='dynamic-catalog-spinner-grid']"
# The site shows the spinner for 500 + Math.random() * 2500 ms
SPINNER_MIN_MS = 500
SPINNER_MAX_MS = 3000

# The slider moves to the next product on a 2-second setInterval
SLIDE_MS = 2000
SLIDER_DOTS = "[data-test^='dynamic-catalog-slider-dot-']"
CURRENT_DOT = f"{SLIDER_DOTS}[aria-current='true']"

def go_to_dynamic_page(page: Page, slug: str, freeze_clock: bool = False):
    """Log in, then open a Dynamic Catalog page by URL (slug is 'lazy-load', 'spinner' or 'slider')"""
    login_to_saucedemo(page)
    # Wait for the login to finish first, so the goto can't race it
    expect_inventory_page(page)
    if freeze_clock:
        # install() alone keeps fake time running; pause_at() stops it, so timers only fire on page.clock.run_for()
        # This runs before the goto, so the page creates its timers on the paused clock
        page.clock.install()
        page.clock.pause_at(datetime.now() + timedelta(seconds=1))
    page.goto(f"{BASE_URL}/dynamic-catalog-{slug}.html")
    expect(page.locator(f"[data-test='dynamic-catalog-{slug}-container']")).to_be_visible()

def load_next_batch(page: Page, count: int):
    """Scroll the sentinel into view and wait until the list grows from count - 6 to count cards"""
    cards = page.locator(LAZY_CARDS)
    # Wait for the previous batch first, or the scroll could be counted against it
    expect(cards).to_have_count(count - LAZY_BATCH)
    page.locator(SENTINEL).scroll_into_view_if_needed()
    expect(cards).to_have_count(count)

def expect_slide(page: Page, index: int):
    """Assert the slider shows PRODUCTS[index] and only its dot is marked current"""
    product = PRODUCTS[index]
    expect(page.locator("[data-test='dynamic-catalog-slider-item-name']")).to_have_text(product.name)
    expect(page.locator("[data-test='dynamic-catalog-slider-item-price']")).to_have_text(product.price)
    expect(page.locator("[data-test='dynamic-catalog-slider-item-img']")).to_have_attribute("alt", product.name)
    expect(page.locator(f"[data-test='dynamic-catalog-slider-dot-{index}']")).to_have_attribute("aria-current", "true")
    expect(page.locator(CURRENT_DOT)).to_have_count(1)

def test_lazy_load_first_screen(page: Page):
    # Positive: the cards on screen are loaded, the ones below the fold still say "Loading…"
    go_to_dynamic_page(page, "lazy-load")

    expect(page.locator(LAZY_CARDS)).to_have_count(FIRST_SCREEN_CARDS)
    expect(page.locator(LAZY_NAMES)).to_have_count(FIRST_SCREEN_LOADED)
    expect(page.locator("[data-test='lazy-load-item-0-name']")).to_have_text("Sauce Labs Bike Light")
    expect(page.locator("[data-test='lazy-load-item-0-price']")).to_have_text("$9.99")
    expect(page.locator(LAZY_PLACEHOLDERS)).to_have_text(["Loading…"] * (FIRST_SCREEN_CARDS - FIRST_SCREEN_LOADED))
    expect(page.locator(SENTINEL)).not_to_be_in_viewport()

def test_placeholder_loads_when_scrolled_into_view(page: Page):
    # Positive: a placeholder card loads its product once it is scrolled on screen
    go_to_dynamic_page(page, "lazy-load")
    card = page.locator("[data-test='lazy-load-item-11']")
    expect(card).to_have_text("Loading…")

    card.scroll_into_view_if_needed()

    expect(page.locator("[data-test='lazy-load-item-11-name']")).to_have_text("Test.allTheThings() T-Shirt (Red) (S)")
    expect(page.locator("[data-test='lazy-load-item-11-price']")).to_have_text("$15.99")

def test_sentinel_loads_more_cards(page: Page):
    # Positive: each time the sentinel at the bottom comes into view, 6 more cards are added
    go_to_dynamic_page(page, "lazy-load")

    load_next_batch(page, FIRST_SCREEN_CARDS + LAZY_BATCH)
    load_next_batch(page, FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)

    # Each scroll moves less than one screen, so every new card passed through the viewport and loaded
    expect(page.locator(LAZY_PLACEHOLDERS)).to_have_count(0)

def test_lazy_load_list_repeats(page: Page):
    # Edge case: the list loops over 22 entries, so card 22 is card 0 again and the page never runs out
    go_to_dynamic_page(page, "lazy-load")
    load_next_batch(page, FIRST_SCREEN_CARDS + LAZY_BATCH)
    load_next_batch(page, FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)
    expect(page.locator(LAZY_PLACEHOLDERS)).to_have_count(0)

    name = page.locator("[data-test='lazy-load-item-0-name']").inner_text()
    price = page.locator("[data-test='lazy-load-item-0-price']").inner_text()
    image = page.locator("[data-test='lazy-load-item-0-img']").get_attribute("src")

    expect(page.locator(f"[data-test='lazy-load-item-{LAZY_CYCLE}-name']")).to_have_text(name)
    expect(page.locator(f"[data-test='lazy-load-item-{LAZY_CYCLE}-price']")).to_have_text(price)
    expect(page.locator(f"[data-test='lazy-load-item-{LAZY_CYCLE}-img']")).to_have_attribute("src", image)

@pytest.mark.xfail(reason="saucedemo bug: Lazy Load lists the Red T-Shirt (L) twice", strict=True)
def test_lazy_load_no_duplicate_products(page: Page):
    # Negative: one pass through the list shouldn't show the same product twice
    go_to_dynamic_page(page, "lazy-load")
    load_next_batch(page, FIRST_SCREEN_CARDS + LAZY_BATCH)
    load_next_batch(page, FIRST_SCREEN_CARDS + 2 * LAZY_BATCH)
    # all_inner_texts() doesn't wait, so read the names only once every card has loaded
    expect(page.locator(LAZY_PLACEHOLDERS)).to_have_count(0)

    names = page.locator(LAZY_NAMES).all_inner_texts()[:LAZY_CYCLE]

    # Today "Test.allTheThings() T-Shirt (Red) (L)" is both card 13 and card 14
    assert len(set(names)) == len(names)

def test_lazy_load_resets_after_reload(page: Page):
    # Edge case: the loaded cards aren't remembered, so a reload shows the first screen again
    go_to_dynamic_page(page, "lazy-load")
    load_next_batch(page, FIRST_SCREEN_CARDS + LAZY_BATCH)

    page.reload()

    expect(page.locator(LAZY_CARDS)).to_have_count(FIRST_SCREEN_CARDS)
    expect(page.locator(LAZY_PLACEHOLDERS)).to_have_count(FIRST_SCREEN_CARDS - FIRST_SCREEN_LOADED)

def test_spinner_then_products(page: Page):
    # Positive: a loading spinner shows first, then the grid of the 6 products replaces it
    go_to_dynamic_page(page, "spinner", freeze_clock=True)
    spinner = page.get_by_role("status", name="Loading")
    expect(spinner).to_be_visible()
    expect(page.locator(SPINNER_GRID)).to_have_count(0)

    page.clock.run_for(SPINNER_MAX_MS)

    expect(spinner).to_have_count(0)
    grid = page.locator(SPINNER_GRID)
    expect(grid.locator("[data-test$='-name']")).to_have_text([product.name for product in PRODUCTS])
    expect(grid.locator("[data-test$='-price']")).to_have_text([product.price for product in PRODUCTS])

def test_spinner_wait_bounds(page: Page):
    # Edge case: the site waits a random 0.5-3 s, so the spinner is still there at 499 ms and gone by 3000 ms
    go_to_dynamic_page(page, "spinner", freeze_clock=True)
    spinner = page.locator(SPINNER)

    page.clock.run_for(SPINNER_MIN_MS - 1)
    expect(spinner).to_be_visible()

    page.clock.run_for(SPINNER_MAX_MS - (SPINNER_MIN_MS - 1))
    expect(spinner).to_have_count(0)
    expect(page.locator(SPINNER_GRID)).to_be_visible()

def test_slider_starts_on_first_product(page: Page):
    # Positive: there is one dot per product, and the slider starts on the first one
    go_to_dynamic_page(page, "slider", freeze_clock=True)

    expect(page.locator(SLIDER_DOTS)).to_have_count(len(PRODUCTS))
    for index, product in enumerate(PRODUCTS):
        expect(page.locator(f"[data-test='dynamic-catalog-slider-dot-{index}']")).to_have_attribute("aria-label", f"Show {product.name}")
    expect_slide(page, 0)

def test_slider_cycles_through_products(page: Page):
    # Positive: every 2 seconds the slider moves to the next product, and after the last one it starts over
    go_to_dynamic_page(page, "slider", freeze_clock=True)
    expect_slide(page, 0)

    for step in range(1, len(PRODUCTS) + 1):
        page.clock.run_for(SLIDE_MS)
        expect_slide(page, step % len(PRODUCTS))

def test_slider_waits_two_seconds(page: Page):
    # Edge case: the slide changes at exactly 2 seconds, not before
    go_to_dynamic_page(page, "slider", freeze_clock=True)

    page.clock.run_for(SLIDE_MS - 1)
    expect_slide(page, 0)

    page.clock.run_for(1)
    expect_slide(page, 1)

@pytest.mark.parametrize("index", [1, 2, 3, 4, 5], ids=["dot_1", "dot_2", "dot_3", "dot_4", "dot_5"])
def test_slider_dot_shows_product(page: Page, index: int):
    # Positive: clicking a dot shows its product (the clock is frozen, so the slider can't move by itself)
    go_to_dynamic_page(page, "slider", freeze_clock=True)

    page.click(f"[data-test='dynamic-catalog-slider-dot-{index}']")

    expect_slide(page, index)

def test_slider_dot_click_keeps_timer(page: Page):
    # Edge case: clicking a dot doesn't restart the 2-second timer, so the next slide comes 1 second later
    go_to_dynamic_page(page, "slider", freeze_clock=True)
    page.clock.run_for(SLIDE_MS // 2)
    page.click("[data-test='dynamic-catalog-slider-dot-4']")
    expect_slide(page, 4)

    page.clock.run_for(SLIDE_MS // 2)

    expect_slide(page, 5)

@pytest.mark.parametrize("slug", ["lazy-load", "spinner", "slider"], ids=["lazy_load", "spinner", "slider"])
def test_dynamic_catalog_requires_login(page: Page, slug: str):
    # Negative: the Dynamic Catalog pages can't be opened without logging in
    page.goto(f"{BASE_URL}/dynamic-catalog-{slug}.html")

    expect(page).to_have_url(f"{BASE_URL}/")
    expect(get_error_message(page)).to_have_text(
        f"Epic sadface: You can only access '/dynamic-catalog-{slug}.html' when you are logged in."
    )
