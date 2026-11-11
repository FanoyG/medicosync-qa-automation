from playwright.sync_api import Page

from tests.pages.base_page import BasePage


class LoginPage(BasePage):
    URL = "/login"  # change to the path your browser shows for the login page

    def __init__(self, page: Page):
        super().__init__(page)
        # The page has a login form AND a register form with the same field
        # names, so every locator starts from the login form only.
        form = page.locator(".form-box.login")
        self.email_input = form.get_by_placeholder("Email", exact=True)
        self.password_input = form.get_by_placeholder("Password", exact=True)
        self.submit_button = form.get_by_role("button", name="Login")
        self.message = form.locator(".auth-message")

    def login(self, email: str, password: str):
        self.email_input.fill(email)
        self.password_input.fill(password)
        self.submit_button.click()