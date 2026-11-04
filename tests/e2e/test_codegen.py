from playwright.sync_api import Page

def test_recorded(page: Page):
    page.goto("https://playwright.dev/")
    page.get_by_role("link", name="Docs").click()
    page.get_by_role("link", name="Writing tests", exact=True).click()
    page.get_by_role("link", name="Trace viewer").first.click()
    page.get_by_role("link", name="How to record a trace").click()