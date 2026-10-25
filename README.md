# Playwright Python Starter Guide (SauceDemo)

This project is a beginner-friendly introduction to UI automation using [Playwright](https://playwright.dev/python/) and [Miniconda](https://docs.anaconda.com/miniconda/). It tests login, cart, checkout, product sorting, the product detail page, and the burger menu + footer on `https://www.saucedemo.com`. The login and cart suites are written twice, once with Playwright's **sync** API and once with its **async** API, so you can compare them side by side. The checkout, sorting, product detail and menu suites use the sync API only.

## 🛠️ 1. Setup Environment (Miniconda)

We use `conda` to manage a clean Python environment (Python 3.10+). Follow these steps to get started:

1. **Create the environment:**
   ```bash
   conda create -n playwright-py python=3.10 -y
   ```
   Or create it, with all dependencies included, from the config file (then skip step 3):
   ```bash
   conda env create -f environment.yml
   ```

2. **Activate the environment:**
   ```bash
   conda activate playwright-py
   ```

3. **Install dependencies:**
   ```bash
   pip install pytest-playwright playwright pytest-asyncio pytest-xdist
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
├── conftest.py            # Shared constants, helpers (sync + async) and async fixtures
├── test_login.py          # Login tests, sync API (step-by-step)
├── test_login_async.py    # The same login tests, async API (+ a concurrent login test)
├── test_cart.py           # Cart tests, sync API (positive, negative and edge cases)
├── test_cart_async.py     # The same cart tests, async API
├── test_checkout.py       # Checkout tests, sync API only
├── test_sorting.py        # Product sorting tests, sync API only
├── test_product_detail.py # Product detail page tests, sync API only
├── test_menu.py           # Burger menu + footer tests, sync API only
├── environment.yml        # Conda environment config (name, Python version, pip packages)
└── .gitignore
```

### `conftest.py`, the shared toolbox
pytest loads `conftest.py` automatically. It holds everything the test files share:

| Name | Sync version | Async version |
| --- | --- | --- |
| Constants | `BASE_URL`, `INVENTORY_URL`, `PASSWORD`, `ACCEPTED_USERS` | (shared) |
| Log in | `login_to_saucedemo(page, ...)` | `await login_to_saucedemo_async(page, ...)` |
| Log out (burger menu) | `logout_from_saucedemo(page)` | `await logout_from_saucedemo_async(page)` |
| Error banner locator | `get_error_message(page)` | `get_error_message(page)` (same function, see below) |
| Assert on Products page | `expect_inventory_page(page, timeout)` | `await expect_inventory_page_async(page, timeout)` |
| Browser / page fixtures | `page` (from pytest-playwright) | `async_browser`, `async_page` (defined in `conftest.py`) |

## 🧪 3. Understanding the Code

Playwright offers two ways to write code: **Sync** and **Async**.

### Sync (Synchronous)
Used in `test_login.py`, `test_cart.py`, `test_checkout.py`, `test_sorting.py`, `test_product_detail.py` and `test_menu.py`. The code waits for each line to finish before moving to the next.
- Easy to read and debug for beginners.
- No `await` keywords needed.

### Async (Asynchronous)
Used in `test_login_async.py` and `test_cart_async.py`. While waiting for the browser, the code pauses and lets other async work run.
- Needed if you want to drive several browsers/pages at the same time in one test, or integrate with async apps.
- Uses `async def` and `await`.

### Sync vs Async side by side

| | Sync (`test_login.py`) | Async (`test_login_async.py`) |
| --- | --- | --- |
| Import | `from playwright.sync_api import Page, expect` | `from playwright.async_api import Page, expect` |
| Fixture | `page` | `async_page` |
| Test function | `def test_valid_login(page):` | `async def test_valid_login(async_page):` |
| Navigate / click / fill | `page.goto(url)` | `await async_page.goto(url)` |
| Assertion | `expect(locator).to_be_visible()` | `await expect(locator).to_be_visible()` |
| Get all matches | `for image in images.all():` | `for image in await images.all():` |
| Build a locator | `page.locator("css")` | `async_page.locator("css")` (**no** `await`) |

Rule of thumb: anything that talks to the browser (actions, assertions, `.all()`) is awaited. Building a locator does not talk to the browser, so it is never awaited. That's why `get_error_message()` works for both sync and async pages.

### How the async tests are wired up
pytest-playwright's built-in `page` fixture only supports the sync API, so `conftest.py` defines two async fixtures with **pytest-asyncio**:

- **`async_browser`** (session scope): starts Playwright and launches **one** browser for the whole run. It reuses pytest-playwright's options, so `--browser`, `--headed` and `--slowmo` work for async tests too.
- **`async_page`** (function scope): opens a fresh browser context + page for **each** test, so cookies and storage never leak between tests (same isolation as the sync `page`).

Both fixtures, and every test in `test_login_async.py` and `test_cart_async.py`, share one session-wide event loop (each async file sets this at the top):

```python
pytestmark = pytest.mark.asyncio(loop_scope="session")
```

Without this, each test would get its own event loop and couldn't use the shared browser.

### Concurrency: what async actually buys you
pytest still runs async tests **one at a time**. Marking a test `async` does not make the suite faster by itself (use `-n` for that). The speed-up shows up **inside** a test, where you can run several things at once with `asyncio.gather`. `test_concurrent_logins` logs in all 5 working users at the same time, each in its own isolated context:

```python
await asyncio.gather(*(login_as(user) for user in LOGIN_USERS))
```

It takes about as long as the slowest login (`performance_glitch_user`, ~5s) instead of the sum of all five.

### Running sync and async tests in the same run
Once sync Playwright starts, it keeps its event loop marked as "running" until the pytest session ends, and any async test that runs after it fails. To avoid this, a hook in `conftest.py` (`pytest_collection_modifyitems`) moves **async tests to the front** of the run. That's why `test_login_async.py` and `test_cart_async.py` run before the sync files when you call plain `pytest`. This also works with `pytest -n`.

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

### What the login tests cover
`test_login.py` and `test_login_async.py` contain the same cases (password for every user is `secret_sauce`):

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
| `test_concurrent_logins` *(async only)* | All 5 working users log in at the same time |

### What the cart tests cover
`test_cart.py` and `test_cart_async.py` contain the same cases. Tests log in as `standard_user` unless the table says otherwise:

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

## 🚀 4. Running the Tests

To run the tests and see the results:

```bash
# Run all tests (sync + async)
pytest

# Run a specific file
pytest test_login.py          # sync login tests
pytest test_login_async.py    # async login tests
pytest test_cart.py           # sync cart tests
pytest test_cart_async.py     # async cart tests
pytest test_checkout.py       # checkout tests (sync only)
pytest test_sorting.py        # sorting tests (sync only)
pytest test_product_detail.py # product detail tests (sync only)
pytest test_menu.py           # burger menu + footer tests (sync only)

# Run one test by name (in every file that has it)
pytest -k test_valid_login
pytest -k test_add_to_cart    # also matches test_add_to_cart_from_product_page

# Show each test name and its result
pytest -v

# Run tests in parallel (2 workers)
pytest -n 2 test_login.py test_login_async.py

# Run with browser visible (headed mode)
pytest --headed

# Run with custom slow motion (e.g., 500ms between actions)
pytest --headed --slowmo 500

# Run on another browser (install it first: playwright install firefox)
pytest --browser firefox
```
