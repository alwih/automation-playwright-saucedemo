# Bug reports

The 4 bugs this suite found on SauceDemo, written up as bug reports. Each one has a test marked `xfail(strict=True)` that fails on the bug today and turns red once the site fixes it (see [Known bugs](test-strategy.md#known-bugs)).

These are separate from the faults Sauce Labs built into the demo accounts on purpose, which are listed under [Intended persona faults](#intended-persona-faults).

| ID | Title | Severity | Priority | Test |
| --- | --- | --- | --- | --- |
| [BUG-01](#bug-01-checkout-is-allowed-with-an-empty-cart) | Checkout is allowed with an empty cart | Major | P2 | `test_checkout_disabled_for_empty_cart` |
| [BUG-02](#bug-02-item-not-found-page-adds-a-ghost-item-to-the-cart) | ITEM NOT FOUND page adds a ghost item to the cart | Major | P2 | `test_not_found_item_cannot_be_added_to_cart` |
| [BUG-03](#bug-03-reset-app-state-leaves-stale-remove-buttons) | Reset App State leaves stale Remove buttons | Minor | P3 | `test_reset_app_state_updates_buttons` |
| [BUG-04](#bug-04-lazy-load-lists-the-red-t-shirt-l-twice) | Lazy Load lists the Red T-Shirt (L) twice | Minor | P4 | `test_lazy_load_no_duplicate_products` |

**Severity** is how much harm the bug does:
- **Critical:** blocks the main flow with no workaround, or loses data.
- **Major:** a wrong result in a business flow, or a crash the user can get around.
- **Minor:** the UI is out of step with the data, but the user can recover.
- **Trivial:** cosmetic.

**Priority** is how soon it should be fixed, from P1 (now) to P4 (when convenient).

**Environment** (the same for every report)

| Setting | Value |
| --- | --- |
| Site | https://www.saucedemo.com |
| Browsers | Chromium 145.0.7632.6 and Firefox 146.0.1, through Playwright 1.58.0 |
| Window | 1280×720 |
| OS | macOS |
| Account | `standard_user` / `secret_sauce` |
| Last reproduced | 2026-10-28, on both browsers |

## BUG-01: Checkout is allowed with an empty cart
- **Severity / priority:** Major / P2
- **Feature:** Cart, Checkout
- **Preconditions:** Logged in. The cart is empty.

**Steps to reproduce**
1. Click the cart icon. The cart page lists no items.
2. Click **Checkout**.
3. Fill in First Name, Last Name and Postal Code, then click **Continue**.
4. Click **Finish**.

**Expected result:** Checkout is disabled, or shows an error, while the cart is empty. No order can be placed.

**Actual result:** Checkout is enabled and opens "Checkout: Your Information". The Overview lists no items and shows "Item total: $0", "Tax: $0.00" and "Total: $0.00". Finish confirms the empty order with "Thank you for your order!".

**Impact:** An order with nothing in it reaches the confirmation page. In a real shop it would go on to payment and fulfilment.

**Note:** "Item total: $0" has no cents, unlike Tax and Total. This is cosmetic and was seen while reproducing the bug, so it isn't filed on its own.

**Automated test:** `test_checkout_disabled_for_empty_cart` in [`tests/test_cart.py`](../tests/test_cart.py) covers steps 1–2. It fails at `expect(cart_page.checkout_button).to_be_disabled()`, because the button is enabled.

## BUG-02: ITEM NOT FOUND page adds a ghost item to the cart
- **Severity / priority:** Major / P2
- **Feature:** Product detail, Cart, Checkout
- **Preconditions:** Logged in. The cart is empty.

**Steps to reproduce**
1. Open `https://www.saucedemo.com/inventory-item.html?id=99`. No product has that id. The page shows "ITEM NOT FOUND", a price of `$√-1` and an **Add to cart** button.
2. Click **Add to cart**.
3. Click the cart icon.
4. Click **Checkout**, fill in the form and click **Continue**.

**Expected result:** A product that doesn't exist can't be added. The page offers no Add to cart button, or the button does nothing, and the cart badge stays hidden.

**Actual result:**
- After step 2, the badge shows `1`, and `localStorage` `cart-contents` is `[99]`.
- The cart page lists no items, but the badge still says `1`, so the item can't be removed there.
- After step 4, the Overview page is blank. The app crashes with `TypeError: Cannot read properties of undefined (reading 'price')`.

**Impact:** A stale or mistyped product link leaves a phantom item in the cart that turns checkout into a white page. `problem_user` reaches the ITEM NOT FOUND page from the product list, because its Fleece Jacket link opens `?id=6`.

**Automated test:** `test_not_found_item_cannot_be_added_to_cart` in [`tests/test_product_detail.py`](../tests/test_product_detail.py) covers steps 1–3. It fails at `expect(cart_page.cart_badge).to_be_hidden()`: the cart lists 0 items, but the badge is visible. The Overview crash in step 4 was found while writing this report, and no test covers it yet.

## BUG-03: Reset App State leaves stale Remove buttons
- **Severity / priority:** Minor / P3
- **Feature:** Burger menu, Products page
- **Preconditions:** Logged in, on the Products page.

**Steps to reproduce**
1. Click **Add to cart** on Sauce Labs Backpack and on Sauce Labs Onesie. The badge shows `2`.
2. Open the menu (☰) and click **Reset App State**.

**Expected result:** The cart is emptied, and every product shows **Add to cart** again.

**Actual result:**
- The cart is emptied: `cart-contents` is removed from `localStorage` and the badge disappears.
- Both products still show **Remove**. Clicking one of them only switches that button back.
- The buttons are correct again after a reload or after leaving the page.

**Impact:** The page contradicts the cart, saying both items are still in it. A user may think the reset failed.

**Automated test:** `test_reset_app_state_updates_buttons` in [`tests/test_menu.py`](../tests/test_menu.py). It fails at `expect(inventory_page.remove_buttons).to_have_count(0)`, because 2 Remove buttons are still shown.

## BUG-04: Lazy Load lists the Red T-Shirt (L) twice
- **Severity / priority:** Minor / P4
- **Feature:** Dynamic Catalog, Lazy Load page
- **Preconditions:** Logged in. The browser window is 1280×720.

**Steps to reproduce**
1. Open the menu, click **Dynamic Catalog**, then **Lazy Load** (`/dynamic-catalog-lazy-load.html`).
2. Scroll to the bottom of the list twice, so 24 cards are loaded. The list starts over after 22 cards.
3. Read the names of the first 22 cards.

**Expected result:** Each product variant appears once in one pass through the list.

**Actual result:** "Test.allTheThings() T-Shirt (Red) (L)" is listed twice, as cards `lazy-load-item-13` and `lazy-load-item-14`, so the 22 cards hold only 21 distinct names. The Red T-Shirt comes in 7 sizes (XS, S, M, L, L, XL, XXL), while the Bolt T-Shirt and the Fleece Jacket each come in 6.

**Impact:** Shoppers see the same variant twice. It points to duplicated catalogue data.

**Automated test:** `test_lazy_load_no_duplicate_products` in [`tests/test_dynamic_catalog.py`](../tests/test_dynamic_catalog.py). It fails at `assert len(set(names)) == len(names)` (21 == 22).

## Intended persona faults
Sauce Labs built these faults into the demo accounts on purpose, so they aren't reported as bugs. The suite checks each one as today's expected behaviour with a normal passing test. If a persona changes, its test fails, and the change is noticed.

| User | Intended fault | Checked by |
| --- | --- | --- |
| `locked_out_user` | Login is refused with "Sorry, this user has been locked out." | `test_locked_out_user` |
| `problem_user` | Every product image is the same `sl-404` picture | `test_problem_user` |
| `problem_user` | Add to cart does nothing for the Bolt T-Shirt, Fleece Jacket and Red T-Shirt, and Remove does nothing at all | `test_broken_add_to_cart_buttons`, `test_broken_remove_button`, `test_broken_cart_buttons_on_detail_page` |
| `problem_user` | Each product links to the next product's page | `test_problem_user_opens_wrong_product` |
| `problem_user` | Sorting does nothing | `test_problem_user_sort_does_nothing` |
| `problem_user` | At checkout, typing a last name overwrites the first name | `test_problem_user_last_name_overwrites_first_name` |
| `problem_user` | About links to a 404 page | `test_problem_user_about_link_is_404` |
| `error_user` | The same broken Add to cart and Remove buttons as `problem_user` | `test_broken_add_to_cart_buttons`, `test_broken_remove_button`, `test_broken_cart_buttons_on_detail_page` |
| `error_user` | Sorting shows a "Sorting is broken!" alert | `test_error_user_sort_shows_alert` |
| `error_user` | Last Name ignores typing, and Finish throws a JavaScript error, so the order never goes through | `test_error_user_cannot_finish` |
| `performance_glitch_user` | Login takes about 5 seconds | `test_performance_glitch_user` |
| `visual_user` | The cart icon is misplaced (a `visual_failure` class) | `test_visual_user` |
| `visual_user` | The Products page shows random prices on every load, while the detail page shows the real price | Not covered yet: it needs visual checks (see [Not covered yet](test-strategy.md#not-covered-yet)) |
