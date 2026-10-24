from playwright.sync_api import Page

def login_to_saucedemo(page: Page, username: str = "standard_user", password: str = "secret_sauce"):
    """Reusable login function for SauceDemo"""
    page.goto("https://www.saucedemo.com")
    page.fill("input#user-name", username)
    page.fill("input#password", password)
    page.click("input#login-button")
