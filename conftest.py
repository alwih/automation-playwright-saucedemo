from playwright.sync_api import Page, expect

BASE_URL = "https://www.saucedemo.com"
INVENTORY_URL = f"{BASE_URL}/inventory.html"
PASSWORD = "secret_sauce"

# All usernames listed on the SauceDemo login page
ACCEPTED_USERS = [
    "standard_user",
    "locked_out_user",
    "problem_user",
    "performance_glitch_user",
    "error_user",
    "visual_user",
]

def login_to_saucedemo(page: Page, username: str = "standard_user", password: str = PASSWORD):
    page.goto(BASE_URL)
    page.fill("input#user-name", username)
    page.fill("input#password", password)
    page.click("input#login-button")

def logout_from_saucedemo(page: Page):
    """Logout through the burger menu"""
    page.click("#react-burger-menu-btn")
    page.click("#logout_sidebar_link")

def get_error_message(page: Page):
    """Locator for the error banner on the login page"""
    return page.locator("[data-test='error']")

def expect_inventory_page(page: Page, timeout: float = 5000):
    """Assert the user landed on the Products (inventory) page"""
    expect(page).to_have_url(INVENTORY_URL, timeout=timeout)
    expect(page.locator(".inventory_list")).to_be_visible(timeout=timeout)
    expect(page.locator("[data-test='title']")).to_have_text("Products", timeout=timeout)
