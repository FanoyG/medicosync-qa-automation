from playwright.sync_api import Page

from tests.pages.base_page import BasePage


class DashboardPage(BasePage):
    URL = "/pages/dashboard.html"  # change to the path your browser shows after login

    def __init__(self, page: Page):
        super().__init__(page)
        self.welcome_heading = page.locator("#welcome-text")
        self.user_email = page.locator("#user-email")
        self.logout_button = page.get_by_role("button", name="Logout")

    def logout(self):
        self.logout_button.click()