# Test strategy

What this suite tests, how it tests it, and what it leaves out on purpose.

**System under test:** [SauceDemo](https://www.saucedemo.com), Sauce Labs' public demo shop. It is a React single-page app with no backend of its own. The login check, the cart and the order all run in the browser: the session is one cookie (`session-username`), and the cart lives in `localStorage`. A full login, add to cart and checkout sends no API requests, only image downloads.

## Scope

### In scope
The UI of the 7 features a shopper uses, tested end to end in a real browser:

| Feature | File | Focus |
| --- | --- | --- |
| Login | `test_login.py` | every persona, invalid input, the error banner, logout |
| Sorting | `test_sorting.py` | the 4 sort options and the default, persona faults, what sorting must leave alone |
| Product detail | `test_product_detail.py` | the detail page against its card, unknown ids, broken buttons |
| Cart | `test_cart.py` | add and remove from both pages, the badge, persistence |
| Checkout | `test_checkout.py` | the whole flow, totals and tax, required fields, cancel |
| Menu + footer | `test_menu.py` | menu items and navigation, Reset App State, social links, copyright |
| Dynamic Catalog | `test_dynamic_catalog.py` | lazy loading, the spinner, slider timing |

Two concerns cut across the features:
- **Access control.** Every page that needs a login is also opened logged out, to check that it redirects to the login page with an error.
- **Concurrency.** `test_concurrency_async.py` drives several browser sessions at once: concurrent logins, concurrent checkouts, and one user logged in on two browsers.

The full list of cases is in [test-cases.md](test-cases.md).

### Out of scope
- **Third-party sites.** The About and social links are checked by their `href`. The one test that clicks a link answers it with a stub page, so the suite never depends on x.com.
- **Anything without a UI.** There is no SauceDemo API to test (see above).
- The areas in [Not covered yet](#not-covered-yet), each with its reason.

## Approach

### Risk first
The suite goes deepest where a bug would cost a real shop the most:
1. **Money and orders:** cart contents, checkout totals and tax, whether an order can be placed.
2. **Access:** who can log in, and what a logged-out visitor can open.
3. **Browsing:** sorting, product details, the menu and the Dynamic Catalog pages.
4. **Cosmetics:** the footer and the copyright line.

Every test is classed as **Positive** (the feature works), **Negative** (bad input, a blocked action, or a known fault) or **Edge case** (limits, timing, state that has to survive a reload or a logout). The [test case catalogue](test-cases.md) gives the class of each one.

### Users as personas
SauceDemo has 6 accounts, and each one is broken in its own way on purpose. The suite treats them as personas with known faults. Each fault gets a Negative test that pins down today's behaviour, so a change in any persona is noticed.

| User | Intended fault |
| --- | --- |
| `standard_user` | none; the default user of every test |
| `locked_out_user` | can't log in |
| `problem_user` | broken images, cart buttons, product links, sorting, checkout form and About link |
| `performance_glitch_user` | login takes about 5 seconds |
| `error_user` | broken cart buttons, sorting and checkout |
| `visual_user` | misplaced cart icon |

[bug-reports.md](bug-reports.md#intended-persona-faults) lists each fault and the tests that pin it down.

### Test design techniques
- **Equivalence classes** for form input: an empty username, an empty password, a wrong password, an unknown user, and the username in the wrong case each give their own error.
- **Boundary values:** product id `6` (one past the last product), the spinner at 499 ms and at 3 s, and the slider at 1999 ms and at 2000 ms.
- **State transitions:** the cart through logout and login, a reload, Reset App State, and checkout cancel on either step.
- **Expected values come from the page.** Sorted orders are computed with Python's `sorted()`, and checkout totals from the item prices on the page. Detail pages are compared with their own product card. When the site's data changes, the tests follow it, and only real behaviour changes make them fail.

## Browsers
- **Chromium** is the default (pytest-playwright's default), at a 1280×720 viewport.
- **Firefox** runs the login suite in the end-to-end check before a merge to `main`, to show the page objects aren't tied to one engine.
- Any browser Playwright supports can run the suite with `--browser firefox` or `--browser webkit`. WebKit isn't checked regularly.

## Test data
- **Users and products** live in [`data/`](../data). The 6 products are named constants (`BACKPACK`, `BIKE_LIGHT`, …), each with its id, name, cart-button slug and price.
- **The site URL** is in [`config.py`](../config.py). Set `BASE_URL` to run the suite against another copy of the site.
- **Every test starts clean.** It gets a new browser context, with its own cookies and `localStorage`, so no test depends on another. This is also what makes `pytest -n` parallel runs safe.
- **Tests that aren't about logging in skip the form.** They set the session cookie with the `login_as` fixture. The login tests, the concurrency tests and the log-back-in step of `test_cart_persists_after_logout` still use the form.

## Known bugs
A bug the suite finds is not left as a red test, and it isn't skipped. Its test is marked `@pytest.mark.xfail(strict=True)`, with the bug in the `reason`:
- **While the bug exists**, the test reports `XFAIL` and the run stays green.
- **Once the site fixes it**, the test passes, and strict mode turns that `XPASS` into a failure. That failure is the signal to remove the marker and keep the test as a normal check.
- **Each xfail test fails at the bug, not by accident.** Before the failing assertion, it proves the action was handled: it opens the cart, or waits for the badge to hide. Running with `--runxfail` shows each one failing on its bug assertion.

The 4 bugs found so far are written up in [bug-reports.md](bug-reports.md).

## Flakiness policy
A test that sometimes fails is fixed, not retried. The suite has no rerun plugin.
- **No sleeps.** There is no `time.sleep` or `wait_for_timeout` anywhere. Assertions use Playwright's `expect`, which retries until the page matches or the timeout ends.
- **Waits live in page methods, each with a comment on why it's needed.** For example, `InventoryPage.get_names()` waits for all 6 products before reading them, because `all_inner_texts()` doesn't wait.
- **Timers run on a frozen clock.** The spinner, the slider and the copyright year depend on time. Their tests stop the browser clock with `page.clock` and move it forward by hand, so a 2-second slider step takes no real time and never races.
- **External sites are stubbed.** The test that opens the X link answers it with `page.context.route`.
- **New and changed tests run at least twice before they are committed,** and the whole suite runs twice in a row before a merge to `main`.

## Not covered yet
| Area | Why not yet |
| --- | --- |
| **Visual regression** | Screenshot comparison needs a stored baseline per browser and per OS. Today, `visual_user`'s fault is checked by the `visual_failure` class on the cart icon, not by pixels. |
| **Accessibility** | No automated scan (such as axe-core) yet. Only the spinner is found by its ARIA role. |
| **API** | SauceDemo has no API: login, the cart and orders all run in the browser. |
| **Performance and load** | SauceDemo is a shared public demo, so load-testing it isn't appropriate. The only timing check is that `performance_glitch_user` gets in within 15 seconds. |
| **Mobile viewports** | Every test runs at 1280×720. The Lazy Load counts depend on that size. |
| **CI** | The suite runs locally. A CI pipeline with an HTML report is the next step. |
