# Playwright Python Starter Guide (SauceDemo)

This project is a beginner-friendly introduction to UI automation using [Playwright](https://playwright.dev/python/) and [Miniconda](https://docs.anaconda.com/miniconda/). It tests login, cart, checkout, product sorting, the product detail page, the burger menu + footer, and the Dynamic Catalog pages on `https://www.saucedemo.com`. Every suite uses Playwright's **sync** API, except `test_concurrency_async.py`, which uses the **async** API to drive several browser sessions at once (see [Sync by default, async only for concurrency](#sync-by-default-async-only-for-concurrency)).

## 🛠️ 1. Setup Environment (Miniconda)

We use `conda` to manage a clean Python environment (Python 3.11). Follow these steps to get started:

1. **Create the environment:**
   ```bash
   conda create -n playwright-py python=3.11 -y
   ```
   Or create it, with all dependencies included, from the config file (then skip step 3):
   ```bash
   conda env create -f environment.yml
   ```

2. **Activate the environment:**
   ```bash
   conda activate playwright-py
   ```

3. **Install dependencies** (pinned versions, from `requirements.txt`):
   ```bash
   pip install -r requirements.txt
   ```
   | Package | Why we need it |
   | --- | --- |
   | `playwright` | The browser automation library (sync + async APIs) |
   | `pytest-playwright` | pytest plugin: the sync `page` fixture and the `--headed`, `--slowmo`, `--browser` options |
   | `pytest-asyncio` | Lets pytest run `async def` tests and fixtures |
   | `pytest-xdist` | Runs tests in parallel with `-n` |

4. **Install Browsers:**
   Playwright needs to download the actual browser binaries:
   ```bash
   playwright install chromium
   ```

## 📂 2. Project Structure

```text
.
├── pages/                      # Page objects: one class per page, holding its locators and actions
│   ├── base_page.py            # BasePage: URL, open(), expect_loaded(), the header and the error banner
│   ├── login_page.py           # LoginPage: login(), expect_access_denied(path)
│   ├── inventory_page.py       # InventoryPage (cards, add / remove, sorting) and ProductCard
│   ├── product_page.py         # ProductPage: the product detail page
│   ├── cart_page.py            # CartPage: rows, remove, Continue Shopping, Checkout
│   ├── checkout_pages.py       # CheckoutInfoPage, CheckoutOverviewPage, CheckoutCompletePage
│   ├── components.py           # Menu (burger menu) and Footer, on every logged-in page
│   └── dynamic_catalog.py      # LazyLoadPage, SpinnerPage, SliderPage
├── tests/
│   ├── conftest.py             # Page object fixtures and the async browser fixture
│   ├── test_login.py           # Login tests (step-by-step)
│   ├── test_cart.py            # Cart tests (positive, negative and edge cases)
│   ├── test_checkout.py        # Checkout tests
│   ├── test_sorting.py         # Product sorting tests
│   ├── test_product_detail.py  # Product detail page tests
│   ├── test_menu.py            # Burger menu + footer tests
│   ├── test_dynamic_catalog.py # Dynamic Catalog pages (lazy load, spinner, slider)
│   └── test_concurrency_async.py # Async API: several browser sessions at once in one test
├── data/
│   ├── users.py                # Password, the accepted users and the users with broken cart buttons
│   └── products.py             # The 6 products (id, name, cart-button slug, price)
├── config.py                   # BASE_URL (override with the BASE_URL environment variable)
├── pyproject.toml              # pytest settings (test folder, import path, default options)
├── requirements.txt            # Pinned Python packages
├── environment.yml             # Conda environment config (name, Python version, installs requirements.txt)
└── .gitignore
```

### Page objects
Tests don't hold selectors. Each page of the site has a class in `pages/` that owns its locators and actions, and `tests/conftest.py` passes each one to the tests as a fixture: `login_page`, `inventory_page`, `product_page`, `cart_page`, `checkout_info_page`, `checkout_overview_page`, `checkout_complete_page`, `lazy_load_page`, `spinner_page`, `slider_page`, `menu` and `footer`. They all wrap the same `page`, so a test asks for as many as it needs:

```python
def test_add_to_cart(login_page: LoginPage, inventory_page: InventoryPage, cart_page: CartPage):
    login_page.login()

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.item_names).to_have_text(BACKPACK.name)
```

- **Locators use `get_by_test_id`.** SauceDemo marks its elements with `data-test`, so `conftest.py` makes that the test id attribute. CSS stays only where an element has no usable `data-test`. For example, the burger menu's `data-test` sits on the icon underneath the button, which can't be clicked.
- **Checks stay in the tests.** Page objects hold only `expect_loaded()` and a few checks that several tests share, such as `LoginPage.expect_access_denied(path)` and `SliderPage.expect_slide(index)`. Expected values (labels, error texts, URLs) stay in the tests or in `data/`.
- **Waits live in the page methods, each with a comment on why.** For example, `InventoryPage.get_names()` waits for all 6 products before reading them. `CheckoutOverviewPage.expect_loaded()` waits for the new title, because the URL changes before the page re-renders.
- **Shared setup steps within one file are factory fixtures in that file.** For example, `go_to_checkout(products=..., username=...)` in `test_checkout.py`.

Test data lives in `data/` and the site URL in `config.py`. The async helpers (`login`, `expect_inventory_page`, `new_session`) live in `test_concurrency_async.py`, the only file that uses them.

## 🧪 3. Understanding the Code

### Sync by default, async only for concurrency
Playwright has a **sync** API and an **async** API. Every test file uses the sync one, except `test_concurrency_async.py`:
- **Async doesn't make pytest faster.** pytest runs `async def` tests one at a time, just like sync ones. To speed up the suite, run tests in parallel with `-n` (pytest-xdist).
- **A second copy costs double the upkeep.** An async copy of a sync suite checks nothing new, but every change has to be made twice.
- **Async pays off inside one test that drives several browser sessions at the same time.** That is what `test_concurrency_async.py` does with `asyncio.gather`. For example, `test_concurrent_logins` logs in all 5 working users at once, each in its own session, so it takes about as long as the slowest login (`performance_glitch_user`, ~5s) instead of the sum of all five:

```python
await asyncio.gather(*(login_user(user) for user in LOGIN_USERS))
```

### How the async tests are wired up
pytest-playwright's built-in fixtures only support the sync API, so `conftest.py` defines **`async_browser`** with **pytest-asyncio**. It starts Playwright and launches **one** browser for the whole run, and it reuses pytest-playwright's options, so `--browser`, `--headed` and `--slowmo` work for async tests too. It also sets `data-test` as the test id attribute, so the async tests find elements with `page.get_by_test_id("...")`.

Each test opens its sessions from that browser with `new_session()`, a fresh context + page, so every session has its own cookies and localStorage, like a separate browser.

The fixture and every test in the file share one session-wide event loop (set at the top of the file):

```python
pytestmark = pytest.mark.asyncio(loop_scope="session")
```

Without this, each test would get its own event loop and couldn't use the shared browser.

### Running sync and async tests in the same run
Once sync Playwright starts, it keeps its event loop marked as "running" until the pytest session ends, and any async test that runs after it fails. To avoid this, a hook in `conftest.py` (`pytest_collection_modifyitems`) moves **async tests to the front** of the run. That's why `test_concurrency_async.py` runs before the sync files when you call plain `pytest`. This also works with `pytest -n`.

### Key Selectors for SauceDemo:
- **Username:** `input#user-name`
- **Password:** `input#password`
- **Login Button:** `input#login-button`
- **Error Message:** `[data-test="error"]`
- **Error Close Button:** `[data-test="error-button"]`
- **Accepted Usernames List:** `[data-test="login-credentials"]`
- **Burger Menu Buttons:** open `#react-burger-menu-btn`, close `#react-burger-cross-btn`. Don't click `[data-test="open-menu"]` / `[data-test="close-menu"]`: those are the icon images, and the invisible button on top of them catches the click, so the click times out
- **Burger Menu Panel:** `.bm-menu-wrap`. When closed it is moved off-screen, not hidden, so check it with `to_be_in_viewport()` instead of `to_be_visible()`
- **Burger Menu Items:** `[data-test="inventory-sidebar-link"]` (All Items), `[data-test="dynamic-catalog-sidebar-link"]`, `[data-test="about-sidebar-link"]`, `[data-test="logout-sidebar-link"]` (also `#logout_sidebar_link`), `[data-test="reset-sidebar-link"]` (Reset App State); `[data-test$="-sidebar-link"]` matches all 5
- **Dynamic Catalog Submenu:** `[data-test="dynamic-catalog-submenu"]` (only in the page while open), links `[data-test="dynamic-catalog-lazy-load-link"]`, `[data-test="dynamic-catalog-spinner-link"]`, `[data-test="dynamic-catalog-slider-link"]`
- **Footer:** `[data-test="footer"]`, links `[data-test="social-x"]`, `[data-test="social-facebook"]`, `[data-test="social-linkedin"]`, copyright `[data-test="footer-copy"]`
- **Products Page:** `.inventory_list`, title `[data-test="title"]`
- **Cart Badge / Link:** `.shopping_cart_badge`, `.shopping_cart_link`
- **Add / Remove (products page):** `[data-test="add-to-cart-<product>"]`, `[data-test="remove-<product>"]`, e.g. `add-to-cart-sauce-labs-backpack`
- **Cart Page:** rows `.cart_item`, buttons `[data-test="continue-shopping"]`, `[data-test="checkout"]`
- **Checkout Form (step one):** `[data-test="firstName"]`, `[data-test="lastName"]`, `[data-test="postalCode"]`, buttons `[data-test="continue"]`, `[data-test="cancel"]`
- **Checkout Overview (step two):** `[data-test="subtotal-label"]`, `[data-test="tax-label"]`, `[data-test="total-label"]`, `[data-test="payment-info-value"]`, `[data-test="shipping-info-value"]`, button `[data-test="finish"]`
- **Checkout Complete:** `[data-test="complete-header"]`, button `[data-test="back-to-products"]`
- **Sort Dropdown:** `[data-test="product-sort-container"]` (option values `az`, `za`, `lohi`, `hilo`), label shown on it `[data-test="active-option"]`
- **Product Name / Price:** `[data-test="inventory-item-name"]`, `[data-test="inventory-item-price"]`
- **Product Card Links:** `[data-test="item-<id>-title-link"]` (the name), `[data-test="item-<id>-img-link"]` (the image), e.g. `item-4-title-link` for the Backpack
- **Product Detail Page:** scope `.inventory_details_container` (it reuses the products page's `inventory-item-name` / `-desc` / `-price` data-tests), image `.inventory_details_img`, buttons `[data-test="add-to-cart"]` / `[data-test="remove"]` (no product suffix), `[data-test="back-to-products"]`
- **Dynamic Catalog Pages:** `/dynamic-catalog-<slug>.html` with slug `lazy-load`, `spinner` or `slider`, container `[data-test="dynamic-catalog-<slug>-container"]`. Every card has `[data-test="<prefix>-img"]` (its `alt` is the product name), `<prefix>-name` and `<prefix>-price`, where the prefix is `lazy-load-item-<n>`, `spinner-item-<id>` or `dynamic-catalog-slider-item`
- **Lazy Load:** a card not loaded yet holds only `[data-test="lazy-load-item-<n>-placeholder"]` ("Loading…"); scrolling `[data-test="dynamic-catalog-lazy-load-sentinel"]` into view adds 6 more cards
- **Spinner:** `[data-test="dynamic-catalog-spinner"]` (`role="status"`, `aria-label="Loading"`), then `[data-test="dynamic-catalog-spinner-grid"]`
- **Slider:** card `[data-test="dynamic-catalog-slider-item"]`, dots `[data-test="dynamic-catalog-slider-dot-<n>"]` (the current one has `aria-current="true"`)

### What the login tests cover
`test_login.py` (password for every user is `secret_sauce`):

| Test | What it checks |
| --- | --- |
| `test_accepted_users_listed_on_login_page` | The login page still lists exactly the users this suite knows about |
| `test_valid_login` | `standard_user` lands on the Products page |
| `test_locked_out_user` | `locked_out_user` gets the "locked out" error and stays on the login page |
| `test_problem_user` | Logs in, but every product shows the same broken `sl-404` image |
| `test_performance_glitch_user` | Logs in after a ~5s delay (uses a 15s timeout) |
| `test_error_user` | Logs in normally (its bugs appear later in cart, checkout and sorting) |
| `test_visual_user` | Logs in, but the cart icon has the `visual_failure` class |
| `test_login_then_logout[...]` | Every user that can log in can also log out via the burger menu |
| `test_invalid_login[...]` | Empty fields, wrong password, unknown user, case-sensitive username → correct error text |
| `test_close_error_message` | The ✕ button hides the error banner |
| `test_inventory_requires_login` | Opening `/inventory.html` without logging in redirects back with an error |

### What the cart tests cover
`test_cart.py`. Tests log in as `standard_user` unless the table says otherwise:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_add_to_cart` | Positive | Adding the Sauce Labs Backpack shows `1` on the cart badge and the item is in the cart |
| `test_add_to_cart_from_product_page` | Positive | An item can be added from its own product page; the button turns into Remove |
| `test_remove_item_from_products_page` | Positive | Remove on the products page takes the item out of the cart and lowers the badge |
| `test_cart_shows_item_details` | Positive | The cart row shows quantity `1`, the name and the same price as the products page |
| `test_cart_navigation` | Positive | Continue Shopping goes back to the products page (cart kept); Checkout opens checkout step one |
| `test_cart_requires_login` | Negative | Opening `/cart.html` without logging in redirects back with an error |
| `test_broken_add_to_cart_buttons[...]` | Negative | `problem_user` and `error_user` can't add Bolt T-Shirt, Fleece Jacket or Test.allTheThings() T-Shirt |
| `test_broken_remove_button[...]` | Negative | `problem_user` and `error_user` can't remove items from the products page |
| `test_checkout_disabled_for_empty_cart` | Negative (`xfail`) | Checkout should be blocked for an empty cart, but saucedemo allows it. Marked as an expected failure; it turns red if the site ever fixes the bug |
| `test_add_all_items_to_cart` | Edge case | All 6 products can be added; badge shows `6` and the cart lists them in inventory order |
| `test_remove_last_item_empties_cart` | Edge case | Removing the only item leaves the cart empty and hides the badge (it never shows `0`) |
| `test_cart_persists_after_logout` | Edge case | The cart is kept in localStorage, so it survives logging out and back in |

### What the checkout tests cover
`test_checkout.py` is sync only. Tests log in as `standard_user` unless the table says otherwise:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_complete_checkout` | Positive | Cart → Your Information → Overview → Finish shows "Thank you for your order!" and hides the badge; Back Home returns to the products page with an empty cart |
| `test_checkout_overview_totals` | Positive | With 2 items: Item total is the sum of the prices, Tax is 8% and Total adds them up (computed from the prices on the page); payment and shipping info are shown |
| `test_checkout_overview_lists_items` | Positive | The Overview lists the same names, quantities and prices as the cart |
| `test_checkout_required_fields[...]` | Negative | An empty first name, last name or postal code shows "Error: … is required" and the page stays on step one |
| `test_close_checkout_error` | Negative | The ✕ button hides the form's error banner |
| `test_checkout_requires_login[...]` | Negative | Opening any checkout page without logging in redirects back with an error |
| `test_problem_user_last_name_overwrites_first_name` | Negative | For `problem_user`, typing a last name replaces the first name, so Continue fails |
| `test_error_user_cannot_finish` | Negative | For `error_user`, the Last Name field ignores typing and Finish crashes, so the order never goes through |
| `test_checkout_cancel_buttons` | Edge case | Cancel on step one goes back to the cart and Cancel on the Overview goes back to the products page; the cart is kept |

### What the sorting tests cover
`test_sorting.py` is sync only. Tests log in as `standard_user` unless the table says otherwise. The expected order is computed with Python's `sorted()` from the names and prices on the page, not hard-coded:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_sort_options` | Positive | The dropdown lists exactly Name (A to Z), Name (Z to A), Price (low to high) and Price (high to low) |
| `test_default_sort_is_name_a_to_z` | Positive | Products start sorted by name, A to Z |
| `test_sort_by_name` | Positive | Name (Z to A) reverses the list and Name (A to Z) puts it back |
| `test_sort_by_price[...]` | Positive | Price (low to high) and Price (high to low) order the prices correctly |
| `test_problem_user_sort_does_nothing[...]` | Negative | For `problem_user`, picking a sort option changes nothing |
| `test_error_user_sort_shows_alert` | Negative | For `error_user`, sorting shows a "Sorting is broken!" alert and the list stays A to Z |
| `test_sort_keeps_cart` | Edge case | Re-sorting keeps the cart badge and the Remove buttons |
| `test_sort_moves_whole_cards` | Edge case | Every product keeps its own price after sorting |
| `test_sort_resets_after_leaving_page` | Edge case | The chosen sort isn't remembered: going to the cart and back, or reloading, brings back A to Z |

### What the product detail tests cover
`test_product_detail.py` is sync only. Tests log in as `standard_user` unless the table says otherwise. A detail page's URL is `/inventory-item.html?id=<id>`:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_detail_matches_inventory_card[...]` | Positive | For each of the 6 products, clicking its name opens its detail page, which shows the same description, price and image as its card (read off the products page, not hard-coded) |
| `test_open_product_from_image` | Positive | The product image opens the same detail page as the name |
| `test_back_to_products` | Positive | Back to Products returns to the products page |
| `test_remove_from_detail_page` | Positive | An item already in the cart shows Remove on its detail page; Remove there hides the badge, and the products page shows "Add to cart" for it again |
| `test_unknown_product_id[...]` | Negative | `?id=6`, `?id=99`, `?id=abc` and no id all show "ITEM NOT FOUND" |
| `test_not_found_item_cannot_be_added_to_cart` | Negative (`xfail`) | Add to cart on "ITEM NOT FOUND" shouldn't change the cart, but saucedemo shows `1` on the badge while the cart lists nothing. Marked as an expected failure; it turns red if the site ever fixes the bug |
| `test_product_detail_requires_login` | Negative | Opening a detail page without logging in redirects back with an error |
| `test_problem_user_opens_wrong_product[...]` | Negative | For `problem_user`, every product links to the next id: the Backpack opens the Fleece Jacket, and the Fleece Jacket opens "ITEM NOT FOUND" |
| `test_broken_cart_buttons_on_detail_page[...]` | Negative | `problem_user` and `error_user` have the same broken buttons on the detail page as on the products page: Bolt T-Shirt can't be added and nothing can be removed |
| `test_detail_page_survives_reload` | Edge case | Reloading a detail page keeps the product and the cart |

### What the menu and footer tests cover
`test_menu.py` is sync only. Tests log in as `standard_user` unless the table says otherwise. Logging out is already covered by the login tests, so it isn't repeated here:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_menu_items` | Positive | The menu starts closed and opens with All Items, Dynamic Catalog, About, Logout and Reset App State, in that order |
| `test_close_menu[...]` | Positive | The ✕ button and the Escape key both close the menu |
| `test_all_items_from_other_pages[...]` | Positive | All Items goes back to the products page from the cart, a product detail page, checkout step one and the checkout complete page, and keeps the cart |
| `test_dynamic_catalog_submenu` | Positive | Dynamic Catalog opens a submenu with Lazy Load, Spinner and Slider, and a second click closes it |
| `test_dynamic_catalog_links[...]` | Positive | Each submenu link opens its own Dynamic Catalog page |
| `test_about_link` | Positive | About links to `https://saucelabs.com/` |
| `test_problem_user_about_link_is_404` | Negative | For `problem_user`, About links to a 404 page |
| `test_reset_app_state_empties_cart` | Positive | Reset App State hides the badge and empties the cart |
| `test_reset_app_state_updates_buttons` | Negative (`xfail`) | Right after Reset App State the products page should show no Remove buttons, but saucedemo keeps showing them until the page re-renders. Marked as an expected failure; it turns red if the site ever fixes the bug |
| `test_back_after_logout_is_blocked` | Negative | After logging out, the browser's Back button redirects to the login page with an error |
| `test_footer_social_links[...]` | Positive | The X, Facebook and LinkedIn links point to Sauce Labs' pages and open in a new tab (`target="_blank"`) |
| `test_social_link_opens_new_tab` | Positive | Clicking X opens a new tab and the products page stays put. x.com itself is replaced by a stub page with `page.context.route`, so the test doesn't depend on another site |
| `test_footer_copyright` | Positive | The footer shows "© <year> Sauce Labs. All Rights Reserved. Terms of Service \| Privacy Policy" |
| `test_copyright_year_follows_browser_clock` | Edge case | With the browser clock set to 2030 (`page.clock`), the footer says "© 2030", so the year isn't hard-coded |

### What the Dynamic Catalog tests cover
`test_dynamic_catalog.py` is sync only. Tests log in as `standard_user` and open each page by URL; every user sees the same pages, so there are no user-specific tests. The spinner and slider run on timers, so their tests freeze the browser clock with `page.clock` and move it forward by hand with `page.clock.run_for(ms)` instead of waiting in real time. The Lazy Load counts assume the default 1280×720 browser window:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_lazy_load_first_screen` | Positive | The page opens with 12 cards: the 8 on screen are loaded and the 4 below them still say "Loading…" |
| `test_placeholder_loads_when_scrolled_into_view` | Positive | A "Loading…" card shows its product once it is scrolled on screen |
| `test_sentinel_loads_more_cards` | Positive | Each scroll to the bottom of the list adds 6 more cards (12 → 18 → 24) |
| `test_lazy_load_list_repeats` | Edge case | The list repeats after 22 cards (card 22 is the same as card 0), so it never runs out |
| `test_lazy_load_no_duplicate_products` | Negative (`xfail`) | One pass through the list shouldn't show the same product twice, but saucedemo lists "Test.allTheThings() T-Shirt (Red) (L)" twice. Marked as an expected failure; it turns red if the site ever fixes the bug |
| `test_lazy_load_resets_after_reload` | Edge case | Reloading brings back the first screen of 12 cards |
| `test_spinner_then_products` | Positive | A loading spinner shows first, then a grid of the 6 products replaces it |
| `test_spinner_wait_bounds` | Edge case | The spinner is still there at 499 ms and gone by 3 s (the site picks a random wait in between) |
| `test_slider_starts_on_first_product` | Positive | The slider has one dot per product and starts on the Bike Light |
| `test_slider_cycles_through_products` | Positive | Every 2 seconds the slider moves to the next product, and after the last one it starts over |
| `test_slider_waits_two_seconds` | Edge case | The slide changes at exactly 2 seconds, not before |
| `test_slider_dot_shows_product[...]` | Positive | Clicking a dot shows its product |
| `test_slider_dot_click_keeps_timer` | Edge case | Clicking a dot doesn't restart the 2-second timer, so the next slide can come sooner than 2 seconds after the click |
| `test_dynamic_catalog_requires_login[...]` | Negative | Opening a Dynamic Catalog page without logging in redirects back with an error |

### What the concurrency tests cover
`test_concurrency_async.py` is the only async file. Each test opens several browser sessions and drives them at the same time:

| Test | Type | What it checks |
| --- | --- | --- |
| `test_concurrent_logins` | Positive | All 5 users who can log in do so at the same time, each in their own session |
| `test_same_user_has_separate_carts_per_browser` | Edge case | `standard_user` is logged in on two browsers at once: one adds the Backpack, the other the Bike Light, and each cart lists only its own item. The cart belongs to the browser (localStorage), not the account |
| `test_concurrent_checkouts` | Positive | `standard_user`, `performance_glitch_user` and `visual_user` check out at the same time and each reaches "Thank you for your order!" (`problem_user` and `error_user` can't finish checkout; see the checkout tests) |

## 🚀 4. Running the Tests

To run the tests and see the results:

```bash
# Run all tests (sync + async); pyproject.toml points pytest at tests/
pytest

# Run a specific file
pytest tests/test_login.py             # login tests
pytest tests/test_cart.py              # cart tests
pytest tests/test_checkout.py          # checkout tests
pytest tests/test_sorting.py           # sorting tests
pytest tests/test_product_detail.py    # product detail tests
pytest tests/test_menu.py              # burger menu + footer tests
pytest tests/test_dynamic_catalog.py   # Dynamic Catalog tests
pytest tests/test_concurrency_async.py # concurrency tests (async)

# Run tests by name (-k matches part of the name)
pytest -k test_valid_login
pytest -k test_add_to_cart     # also matches test_add_to_cart_from_product_page

# Show each test name and its result
pytest -v

# Run tests in parallel (2 workers)
pytest -n 2

# Run with browser visible (headed mode)
pytest --headed

# Run with custom slow motion (e.g., 500ms between actions)
pytest --headed --slowmo 500

# Run on another browser (install it first: playwright install firefox)
pytest --browser firefox
```
