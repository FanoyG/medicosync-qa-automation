import uuid

from playwright.sync_api import Page, expect

from tests.pages.dashboard_page import DashboardPage
from tests.pages.login_page import LoginPage


def test_login_page_opens(page: Page):
    login = LoginPage(page)
    login.open()

    expect(login.email_input).to_be_visible()
    expect(login.password_input).to_be_visible()
    expect(login.submit_button).to_be_visible()


def test_login_success_shows_dashboard(page: Page, registered_user):
    login = LoginPage(page)
    login.open()
    login.login(registered_user["email"], registered_user["password"])

    dashboard = DashboardPage(page)
    expect(dashboard.welcome_heading).to_be_visible()
    expect(dashboard.user_email).to_have_text(registered_user["email"])


def test_login_wrong_password_shows_error(page: Page, registered_user):
    login = LoginPage(page)
    login.open()
    login.login(registered_user["email"], "WrongPass999!")

    expect(login.message).to_contain_text("Invalid credentials")
    expect(login.email_input).to_be_visible()  # still on the login page


def test_login_unknown_email_shows_error(page: Page):
    login = LoginPage(page)
    login.open()
    login.login(f"nobody_{uuid.uuid4().hex[:8]}@example.com", "StrongPass123!")

    expect(login.message).to_contain_text("Invalid credentials")


def test_login_empty_form_does_not_submit(page: Page):
    login = LoginPage(page)
    login.open()
    login.submit_button.click()  # the browser blocks it: both fields are required

    expect(login.message).to_have_text("")
    expect(login.email_input).to_be_visible()