from playwright.sync_api import Page, expect
from conftest import login_to_saucedemo

def test_valid_login(page: Page):
    login_to_saucedemo(page, username="standard_user", password="secret_sauce")

    expect(page).to_have_url("https://www.saucedemo.com/inventory.html")
    expect(page.locator(".inventory_list")).to_be_visible()
    expect(page.locator("[data-test='title']")).to_have_text("Products")

def test_locked_out_user(page: Page):
    login_to_saucedemo(page, username="locked_out_user", password="secret_sauce")

    error_message = page.locator("[data-test='error']")
    expect(error_message).to_be_visible()
    expect(error_message).to_contain_text("Epic sadface: Sorry, this user has been locked out.")