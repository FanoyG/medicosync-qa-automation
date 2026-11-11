from playwright.sync_api import Page


class BasePage:
    URL = ""   # every page sets its own path

    def __init__(self, page: Page):
        self.page = page

    def open(self):
        if not self.URL:
            raise NotImplementedError(f"{type(self).__name__} must set URL")
        self.page.goto(self.URL)