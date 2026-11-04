# test/e2e/test_login_pom.py
import pytest
import re
from playwright.sync_api import expect
from pages.login_page import LoginPage

@pytest.fixture
def login_page(page):
    lp = LoginPage(page)
    lp.open()
    return lp

def test_login(login_page, page):
    login_page.login("standard_user", "secret_sauce")
    expect(page).to_have_url(re.compile("inventory"))   # the check stays in the test

def test_login_wrong_password(login_page, page):
    login_page.login("standard_user", "Wrong-password")
    expect(page.get_by_text("do not match any user")).to_be_visible()


@pytest.mark.parametrize(
    "user, pwd, expected",
    [
        ("standard_user", "secret_sauce", "inventory"),
        ("locked_out_user", "secret_sauce", "locked out"),
        ("standard_user", "wrong", "do not match"),
    ],
    ids=["valid_login", "locked_user", "wrong_password"],
)
def test_login_cases(login_page, user, pwd, expected):
    login_page.login(user, pwd)

    if expected == "inventory":
        expect(login_page.page).to_have_url(re.compile("inventory"))
    else:
        expect(login_page.page.get_by_text(expected)).to_be_visible()
           