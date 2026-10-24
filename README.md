# Playwright Python Starter Guide (SauceDemo)

This project is a beginner-friendly introduction to UI automation using [Playwright](https://playwright.dev/python/) and [Miniconda](https://docs.anaconda.com/miniconda/). It tests login and add-to-cart scenarios on `https://www.saucedemo.com`. The login suite is written twice, once with Playwright's **sync** API and once with its **async** API, so you can compare them side by side.

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
├── test_cart.py           # Cart tests, sync API
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
Used in `test_login.py` and `test_cart.py`. The code waits for each line to finish before moving to the next.
- Easy to read and debug for beginners.
- No `await` keywords needed.

### Async (Asynchronous)
Used in `test_login_async.py`. While waiting for the browser, the code pauses and lets other async work run.
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

Both fixtures, and every test in `test_login_async.py`, share one session-wide event loop:

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
Once sync Playwright starts, it keeps its event loop marked as "running" until the pytest session ends, and any async test that runs after it fails. To avoid this, a hook in `conftest.py` (`pytest_collection_modifyitems`) moves **async tests to the front** of the run. That's why `test_login_async.py` runs before the sync files when you call plain `pytest`. This also works with `pytest -n`.

### Key Selectors for SauceDemo:
- **Username:** `input#user-name`
- **Password:** `input#password`
- **Login Button:** `input#login-button`
- **Error Message:** `[data-test="error"]`
- **Error Close Button:** `[data-test="error-button"]`
- **Accepted Usernames List:** `[data-test="login-credentials"]`
- **Burger Menu / Logout:** `#react-burger-menu-btn` → `#logout_sidebar_link`
- **Products Page:** `.inventory_list`, title `[data-test="title"]`
- **Cart Badge / Link:** `.shopping_cart_badge`, `.shopping_cart_link`

### What the login tests cover
`test_login.py` and `test_login_async.py` contain the same cases (password for every user is `secret_sauce`):

| Test | What it checks |
| --- | --- |
| `test_accepted_users_listed_on_login_page` | The login page still lists exactly the users this suite knows about |
| `test_valid_login` | `standard_user` lands on the Products page |
| `test_locked_out_user` | `locked_out_user` gets the "locked out" error and stays on the login page |
| `test_problem_user` | Logs in, but every product shows the same broken `sl-404` image |
| `test_performance_glitch_user` | Logs in after a ~5s delay (uses a 15s timeout) |
| `test_error_user` | Logs in normally (its bugs appear later in cart/checkout) |
| `test_visual_user` | Logs in, but the cart icon has the `visual_failure` class |
| `test_login_then_logout[...]` | Every user that can log in can also log out via the burger menu |
| `test_invalid_login[...]` | Empty fields, wrong password, unknown user, case-sensitive username → correct error text |
| `test_close_error_message` | The ✕ button hides the error banner |
| `test_inventory_requires_login` | Opening `/inventory.html` without logging in redirects back with an error |
| `test_concurrent_logins` *(async only)* | All 5 working users log in at the same time |

### What the cart tests cover
`test_cart.py` (sync API only). Tests log in as `standard_user` unless the table says otherwise:

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

## 🚀 4. Running the Tests

To run the tests and see the results:

```bash
# Run all tests (sync + async)
pytest

# Run a specific file
pytest test_login.py          # sync login tests
pytest test_login_async.py    # async login tests

# Run one test by name (in every file that has it)
pytest -k test_valid_login

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
