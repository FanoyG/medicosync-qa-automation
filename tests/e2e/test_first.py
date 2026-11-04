from playwright.sync_api import expect

def test_playwright_site(page, base_url):
    page.goto(base_url)
    page.pause()
    expect(page).to_have_title("Fast and reliable end-to-end testing for modern web apps | Playwright")