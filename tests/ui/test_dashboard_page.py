from playwright.sync_api import expect

from tests.pages.dashboard_page import DashboardPage
from tests.pages.login_page import LoginPage


def test_dashboard_opens_when_logged_in(logged_in_page, registered_user):
    dashboard = DashboardPage(logged_in_page)
    dashboard.open()

    expect(dashboard.welcome_heading).to_be_visible()
    expect(dashboard.user_email).to_have_text(registered_user["email"])


def test_logout_goes_back_to_login_page(logged_in_page):
    dashboard = DashboardPage(logged_in_page)
    dashboard.open()
    dashboard.logout()

    expect(LoginPage(logged_in_page).submit_button).to_be_visible()