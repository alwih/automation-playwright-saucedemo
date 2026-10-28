# SauceDemo UI Test Suite

![Python 3.11](https://img.shields.io/badge/python-3.11-3776AB?logo=python&logoColor=white)
![Playwright 1.58](https://img.shields.io/badge/playwright-1.58-2EAD33?logo=playwright&logoColor=white)
![pytest 9](https://img.shields.io/badge/pytest-9-0A9EDC?logo=pytest&logoColor=white)

End-to-end UI tests for [SauceDemo](https://www.saucedemo.com), Sauce Labs' demo shop, written in Python with Playwright and pytest. The suite is built like a production framework, with page objects, pinned dependencies and parallel runs. It found 4 real bugs in the site.

**Docs:** [Test strategy](docs/test-strategy.md) · [Test case catalogue](docs/test-cases.md) · [Bug reports](docs/bug-reports.md)

## Highlights
- **124 tests across 7 features and 6 user personas:** login, sorting, product detail, cart, checkout, menu + footer, and the Dynamic Catalog pages.
- **[4 site bugs found](docs/bug-reports.md).** Each is written up as a bug report and kept as a strict `xfail` test, which turns red the day the bug is fixed.
- **No sleeps.** The spinner, the slider and the copyright year run on a frozen browser clock (`page.clock`), which the tests move forward by hand.
- **No dependence on other sites.** External links are checked by their `href`. The one test that clicks a link answers it with a stub page through `context.route`.
- **Popups and dialogs handled:** a footer link that opens a new tab, and `error_user`'s JavaScript alert.
- **Concurrent multi-session tests** with Playwright's async API: 5 users log in at once, 3 check out at once, and one user is logged in on two browsers.
- **Expected values read off the page instead of hard-coded:**
  - sort orders computed with `sorted()` from the page
  - checkout totals and tax computed from the item prices on the page
  - each product detail page compared with its own card

A full run takes about a minute with `pytest -n 2`: 120 passed and 4 xfailed (the 4 bugs).

## Tech stack
| Tool | Used for |
| --- | --- |
| Python 3.11 | The language |
| Playwright 1.58 | Browser automation: the sync API everywhere, the async API for the concurrency tests |
| pytest 9 + pytest-playwright | Test runner, browser fixtures, and the `--browser`, `--headed` and `--slowmo` options |
| pytest-asyncio | Runs the async concurrency tests |
| pytest-xdist | Runs tests in parallel with `-n` |
| conda or pip | Environment setup, with versions pinned in `requirements.txt` |

## Architecture
```text
tests/      WHAT to check: one file per feature; the assertions live here
   │        asks for page objects as pytest fixtures (tests/conftest.py)
   ▼
pages/      HOW to reach it: one class per page, owning its locators, actions and waits
   │
   ▼
Playwright  drives Chromium, Firefox or WebKit

data/       users and products, shared by tests and pages
config.py   BASE_URL, which the BASE_URL environment variable overrides
```

A test asks for the pages it needs and reads like the user's steps:

```python
def test_add_to_cart(login_as, inventory_page: InventoryPage, cart_page: CartPage):
    # Positive: an item added on the products page shows on the badge and in the cart
    login_as()

    inventory_page.add_to_cart(BACKPACK)
    expect(inventory_page.cart_badge).to_have_text("1")

    inventory_page.open_cart()
    cart_page.expect_loaded()
    expect(cart_page.item_names).to_have_text(BACKPACK.name)
```

<details>
<summary>Project layout</summary>

```text
.
├── pages/
│   ├── base_page.py            # BasePage: URL, open(), expect_loaded(), the header and the error banner
│   ├── login_page.py           # LoginPage: login(), expect_access_denied(path)
│   ├── inventory_page.py       # InventoryPage (cards, add / remove, sorting) and ProductCard
│   ├── product_page.py         # ProductPage: the product detail page
│   ├── cart_page.py            # CartPage: rows, remove, Continue Shopping, Checkout
│   ├── checkout_pages.py       # CheckoutInfoPage, CheckoutOverviewPage, CheckoutCompletePage
│   ├── components.py           # Menu (burger menu) and Footer, on every logged-in page
│   └── dynamic_catalog.py      # LazyLoadPage, SpinnerPage, SliderPage
├── tests/
│   ├── conftest.py             # Page object fixtures, cookie login (login_as), the async browser fixture
│   ├── test_login.py
│   ├── test_sorting.py
│   ├── test_product_detail.py
│   ├── test_cart.py
│   ├── test_checkout.py
│   ├── test_menu.py            # Burger menu + footer
│   ├── test_dynamic_catalog.py # Lazy Load, Spinner and Slider pages
│   └── test_concurrency_async.py # Several browser sessions at once (async API)
├── data/
│   ├── users.py                # Password, accepted users, users with broken cart buttons
│   └── products.py             # The 6 products: id, name, cart-button slug, price
├── docs/                       # Test strategy, test case catalogue, bug reports
├── config.py                   # BASE_URL
├── pyproject.toml              # pytest settings
├── requirements.txt            # Pinned Python packages
└── environment.yml             # Conda environment (Python 3.11 + requirements.txt)
```
</details>

## Quick start
Set up with **conda**:
```bash
conda env create -f environment.yml   # Python 3.11 + the pinned packages
conda activate playwright-py
playwright install chromium
```

Or with **pip**, in any Python 3.11 environment:
```bash
pip install -r requirements.txt
playwright install chromium
```

Run the tests:
```bash
pytest                          # the whole suite
pytest -n 2                     # in parallel, with 2 workers
pytest tests/test_checkout.py   # one feature
pytest -k sort                  # tests whose name matches "sort"
pytest --headed --slowmo 500    # watch the browser, 500 ms between actions
pytest --browser firefox        # another browser (run `playwright install firefox` first)
pytest --runxfail -k empty_cart # watch a known bug fail
```

## Design decisions

### Page objects, with the checks in the tests
- **Selectors live in the page classes.** Each page in `pages/` owns its locators, built with `get_by_test_id`, because SauceDemo marks its elements with `data-test`. CSS is kept only where an element has no usable `data-test`.
- **The tests keep the checks.** Page objects hold only `expect_loaded()` and a few checks that several tests share, such as `LoginPage.expect_access_denied(path)`.
- **Waits live in the page methods, each with a comment on why.** For example, `InventoryPage.get_names()` waits for all 6 products before reading them.
- **No chaining.** Methods don't return the next page. Tests ask for each page as a fixture, so every step stays visible in the test.

### Sync by default, async only for concurrency
Every test file uses Playwright's sync API except `test_concurrency_async.py`:
- **Async doesn't make pytest faster.** pytest runs `async def` tests one at a time, just like sync ones. Parallel speed comes from `-n` (pytest-xdist).
- **Copying a suite into async doubles the upkeep and checks nothing new.** An earlier version had async copies of the login and cart tests. They were replaced by 3 tests that actually need async.
- **Async earns its place inside one test that drives several browsers at once.** `asyncio.gather` logs in 5 users at the same time, so the test takes as long as the slowest login, not the sum of all 5.

Sync Playwright keeps its event loop marked as running until the session ends, so a hook in `conftest.py` runs the async tests first. The `async_browser` fixture reuses pytest-playwright's options, so `--browser`, `--headed` and `--slowmo` work for the async tests too.

### Cookie login for tests that aren't about logging in
SauceDemo keeps the whole session in one cookie, `session-username`. The `login_as` fixture sets it and opens the Products page, so the cart, checkout, sorting and other tests skip the login form. Only the login tests, the concurrency tests and the log-back-in step of `test_cart_persists_after_logout` use the form. The per-user faults still show, because they come from the cookie.

Measured on Chromium, headless:

| | Login form | Cookie |
| --- | --- | --- |
| One login, until the Products page has loaded (median of 20) | 348 ms | 227 ms (−35%) |
| Whole suite, `pytest -n 2` (median of 3) | 61.4 s | 57.3 s (−7%) |

The suite gains less than a single login does, because SauceDemo's login runs in the browser with no server round trip. On a site with a real server-side login, skipping the form saves more.

### Known bugs are strict xfails
A bug is neither left as a red test nor skipped. Its test is marked `@pytest.mark.xfail(strict=True, reason="saucedemo bug: …")`:
- **While the bug exists,** the run stays green and the report shows `XFAIL`.
- **When the site fixes it,** strict mode turns the unexpected pass into a failure. That failure is the reminder to remove the marker.
- **Each test fails at the bug, not by accident.** Before its failing assertion, it proves the action was handled, for example by opening the cart.

### Frozen clock instead of sleeps
The spinner waits a random 0.5–3 s, and the slider moves every 2 s. Their tests freeze the browser clock before the page loads, then call `page.clock.run_for(ms)`. That makes the boundary tests possible: the spinner is still there at 499 ms, and the slider hasn't moved at 1999 ms but has at 2000 ms. These tests take no real waiting time. The copyright test sets the clock to 2030 to show the footer year isn't hard-coded.

## Docs
| Doc | What's in it |
| --- | --- |
| [Test strategy](docs/test-strategy.md) | Scope, the risk-based approach, personas, browsers, test data, flakiness policy, and what isn't covered yet and why |
| [Test case catalogue](docs/test-cases.md) | Every test, its type (Positive / Negative / Edge case) and what it checks |
| [Bug reports](docs/bug-reports.md) | The 4 bugs found, with steps, expected and actual results, and the intended persona faults |
