from playwright.sync_api import Page, expect

def test_valid_login(page: Page):
    # 1. Navigate to the login page
    page.goto("https://www.saucedemo.com")

    # 2. Fill in credentials (Positive Case)
    page.fill("input#user-name", "standard_user")
    page.fill("input#password", "secret_sauce")

    # 3. Click login
    page.click("input#login-button")

    # 4. Verify successful login by checking URL and inventory
    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    expect(page.locator(".inventory_list")).to_be_visible()
    expect(page.locator("[data-test='title']")).to_have_text("Products")

def test_locked_out_user(page: Page):
    # 1. Navigate to the login page
    page.goto("https://www.saucedemo.com")

    # 2. Fill in credentials (Negative Case - Locked out user)
    page.fill("input#user-name", "locked_out_user")
    page.fill("input#password", "secret_sauce")

    # 3. Click login
    page.click("input#login-button")

    # 4. Verify the error message is visible and contains expected text
    error_message = page.locator("[data-test='error']")
    expect(error_message).to_be_visible()
    expect(error_message).to_contain_text("Epic sadface: Sorry, this user has been locked out.")
