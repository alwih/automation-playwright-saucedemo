# Test case catalogue

Every test in the suite: what it checks and what kind of case it is. The [test strategy](test-strategy.md) explains how the cases were chosen.

| Feature | File | Tests | Cases run | Known bugs (`xfail`) |
| --- | --- | --- | --- | --- |
| [Login](#login) | `tests/test_login.py` | 11 | 20 | |
| [Sorting](#sorting) | `tests/test_sorting.py` | 9 | 11 | |
| [Product detail](#product-detail) | `tests/test_product_detail.py` | 10 | 20 | 1 |
| [Cart](#cart) | `tests/test_cart.py` | 12 | 14 | 1 |
| [Checkout](#checkout) | `tests/test_checkout.py` | 9 | 14 | |
| [Menu + footer](#menu--footer) | `tests/test_menu.py` | 14 | 22 | 1 |
| [Dynamic Catalog](#dynamic-catalog) | `tests/test_dynamic_catalog.py` | 14 | 20 | 1 |
| [Concurrency](#concurrency) | `tests/test_concurrency_async.py` | 3 | 3 | |
| **Total** | | **82** | **124** | **4** |

**How to read the tables**
- **Type:** Positive (the feature works), Negative (bad input, a blocked action, or a known fault) or Edge case (limits, timing, state that has to survive a reload or a logout). Of the 82 tests, 39 are Positive, 27 Negative and 16 Edge cases.
- **`[...]`** after a name means the test is parametrized and runs once per value. That is why 82 tests run as 124 cases.
- **`xfail`** marks a test that fails today because of a site bug. Each one links to its bug report. See [Known bugs](test-strategy.md#known-bugs) for how they work.
- Unless a table says otherwise, tests log in as `standard_user` with the session cookie (the `login_as` fixture), not through the login form.

## Login
`tests/test_login.py`. These tests use the login form. The password for every user is `secret_sauce`.

| Test | Type | What it checks |
| --- | --- | --- |
| `test_accepted_users_listed_on_login_page` | Positive | The login page still lists exactly the users this suite knows about |
| `test_valid_login` | Positive | `standard_user` lands on the Products page |
| `test_locked_out_user` | Negative | `locked_out_user` gets the "locked out" error and stays on the login page |
| `test_problem_user` | Negative | Logs in, but every product shows the same broken `sl-404` image |
| `test_performance_glitch_user` | Edge case | Logs in after a ~5s delay (uses a 15s timeout) |
| `test_error_user` | Positive | Logs in normally (its bugs appear later in cart, checkout and sorting) |
| `test_visual_user` | Negative | Logs in, but the cart icon has the `visual_failure` class |
| `test_login_then_logout[...]` | Positive | Every user that can log in can also log out through the burger menu |
| `test_invalid_login[...]` | Negative | Empty fields, wrong password, unknown user, username in the wrong case → the right error text |
| `test_close_error_message` | Negative | The ✕ button hides the error banner |
| `test_inventory_requires_login` | Negative | Opening `/inventory.html` without logging in redirects back with an error |

## Sorting
`tests/test_sorting.py`. The expected order is computed with Python's `sorted()` from the names and prices on the page, not hard-coded.

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

## Product detail
`tests/test_product_detail.py`. A detail page's URL is `/inventory-item.html?id=<id>`.

| Test | Type | What it checks |
| --- | --- | --- |
| `test_detail_matches_inventory_card[...]` | Positive | For each of the 6 products, clicking its name opens its detail page, which shows the same description, price and image as its card (read off the products page, not hard-coded) |
| `test_open_product_from_image` | Positive | The product image opens the same detail page as the name |
| `test_back_to_products` | Positive | Back to Products returns to the products page |
| `test_remove_from_detail_page` | Positive | An item already in the cart shows Remove on its detail page; Remove there hides the badge, and the products page shows "Add to cart" for it again |
| `test_unknown_product_id[...]` | Negative | `?id=6`, `?id=99`, `?id=abc` and no id all show "ITEM NOT FOUND" |
| `test_not_found_item_cannot_be_added_to_cart` | Negative (`xfail`) | Add to cart on "ITEM NOT FOUND" shouldn't change the cart, but the badge shows `1` while the cart lists nothing. [BUG-02](bug-reports.md#bug-02-item-not-found-page-adds-a-ghost-item-to-the-cart) |
| `test_product_detail_requires_login` | Negative | Opening a detail page without logging in redirects back with an error |
| `test_problem_user_opens_wrong_product[...]` | Negative | For `problem_user`, every product links to the next id: the Backpack opens the Fleece Jacket, and the Fleece Jacket opens "ITEM NOT FOUND" |
| `test_broken_cart_buttons_on_detail_page[...]` | Negative | `problem_user` and `error_user` have the same broken buttons on the detail page as on the products page: Bolt T-Shirt can't be added and nothing can be removed |
| `test_detail_page_survives_reload` | Edge case | Reloading a detail page keeps the product and the cart |

## Cart
`tests/test_cart.py`

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
| `test_checkout_disabled_for_empty_cart` | Negative (`xfail`) | Checkout should be blocked for an empty cart, but the site allows it. [BUG-01](bug-reports.md#bug-01-checkout-is-allowed-with-an-empty-cart) |
| `test_add_all_items_to_cart` | Edge case | All 6 products can be added; the badge shows `6` and the cart lists them in inventory order |
| `test_remove_last_item_empties_cart` | Edge case | Removing the only item leaves the cart empty and hides the badge (it never shows `0`) |
| `test_cart_persists_after_logout` | Edge case | The cart is kept in `localStorage`, so it survives logging out and back in through the form |

## Checkout
`tests/test_checkout.py`

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

## Menu + footer
`tests/test_menu.py`. Logging out is already covered by the login tests, so it isn't repeated here.

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
| `test_reset_app_state_updates_buttons` | Negative (`xfail`) | Right after Reset App State the products page should show no Remove buttons, but they stay until the page re-renders. [BUG-03](bug-reports.md#bug-03-reset-app-state-leaves-stale-remove-buttons) |
| `test_back_after_logout_is_blocked` | Negative | After logging out, the browser's Back button redirects to the login page with an error |
| `test_footer_social_links[...]` | Positive | The X, Facebook and LinkedIn links point to Sauce Labs' pages and open in a new tab (`target="_blank"`) |
| `test_social_link_opens_new_tab` | Positive | Clicking X opens a new tab and the products page stays put. x.com itself is replaced by a stub page with `page.context.route`, so the test doesn't depend on another site |
| `test_footer_copyright` | Positive | The footer shows "© <year> Sauce Labs. All Rights Reserved. Terms of Service \| Privacy Policy" |
| `test_copyright_year_follows_browser_clock` | Edge case | With the browser clock set to 2030 (`page.clock`), the footer says "© 2030", so the year isn't hard-coded |

## Dynamic Catalog
`tests/test_dynamic_catalog.py`. Tests open each page by URL. Every user sees the same pages, so there are no user-specific tests. The spinner and slider run on timers, so their tests freeze the browser clock with `page.clock` and move it forward by hand with `page.clock.run_for(ms)` instead of waiting in real time. The Lazy Load counts assume the default 1280×720 browser window.

| Test | Type | What it checks |
| --- | --- | --- |
| `test_lazy_load_first_screen` | Positive | The page opens with 12 cards: the 8 on screen are loaded and the 4 below them still say "Loading…" |
| `test_placeholder_loads_when_scrolled_into_view` | Positive | A "Loading…" card shows its product once it is scrolled on screen |
| `test_sentinel_loads_more_cards` | Positive | Each scroll to the bottom of the list adds 6 more cards (12 → 18 → 24) |
| `test_lazy_load_list_repeats` | Edge case | The list repeats after 22 cards (card 22 is the same as card 0), so it never runs out |
| `test_lazy_load_no_duplicate_products` | Negative (`xfail`) | One pass through the list shouldn't show the same product twice, but "Test.allTheThings() T-Shirt (Red) (L)" is listed twice. [BUG-04](bug-reports.md#bug-04-lazy-load-lists-the-red-t-shirt-l-twice) |
| `test_lazy_load_resets_after_reload` | Edge case | Reloading brings back the first screen of 12 cards |
| `test_spinner_then_products` | Positive | A loading spinner shows first, then a grid of the 6 products replaces it |
| `test_spinner_wait_bounds` | Edge case | The spinner is still there at 499 ms and gone by 3 s (the site picks a random wait in between) |
| `test_slider_starts_on_first_product` | Positive | The slider has one dot per product and starts on the Bike Light |
| `test_slider_cycles_through_products` | Positive | Every 2 seconds the slider moves to the next product, and after the last one it starts over |
| `test_slider_waits_two_seconds` | Edge case | The slide changes at exactly 2 seconds, not before |
| `test_slider_dot_shows_product[...]` | Positive | Clicking a dot shows its product |
| `test_slider_dot_click_keeps_timer` | Edge case | Clicking a dot doesn't restart the 2-second timer, so the next slide can come sooner than 2 seconds after the click |
| `test_dynamic_catalog_requires_login[...]` | Negative | Opening a Dynamic Catalog page without logging in redirects back with an error |

## Concurrency
`tests/test_concurrency_async.py` is the only file that uses Playwright's async API. Each test opens several browser sessions and drives them at the same time with `asyncio.gather`, logging in through the form.

| Test | Type | What it checks |
| --- | --- | --- |
| `test_concurrent_logins` | Positive | All 5 users who can log in do so at the same time, each in their own session |
| `test_same_user_has_separate_carts_per_browser` | Edge case | `standard_user` is logged in on two browsers at once: one adds the Backpack, the other the Bike Light, and each cart lists only its own item. The cart belongs to the browser (`localStorage`), not the account |
| `test_concurrent_checkouts` | Positive | `standard_user`, `performance_glitch_user` and `visual_user` check out at the same time and each reaches "Thank you for your order!" (`problem_user` and `error_user` can't finish checkout; see [Checkout](#checkout)) |
