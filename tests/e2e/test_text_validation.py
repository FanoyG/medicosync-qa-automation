from playwright.sync_api import expect

PAGE = """
<title>Order Page</title>
<input aria-label="Email">
<button disabled>Place order</button>
<p id="status">Order status: pending</p>
<script>
  const btn = document.querySelector('button');
  document.querySelector('input').oninput = e => btn.disabled = !e.target.value;
  btn.onclick = () => document.getElementById('status').textContent = 'Order status: confirmed';
</script>
"""

def test_checks(page):
    page.set_content(PAGE)
    button = page.get_by_role("button", name="Place order")

    expect(page).to_have_title("Order Page")
    expect(button).to_be_disabled()

    page.get_by_label("Email").fill("a@b.com")
    expect(button).to_be_enabled()

    button.click()
    status = page.get_by_text("Order status")
    expect(status).to_be_visible()
    expect(status).to_have_text("Order status: confirmed")
    expect(status).to_contain_text("confirmed")


def test_title_and_url(page):
    page.goto("https://www.saucedemo.com/")
    expect(page).to_have_title("Swag Labs")
    expect(page).to_have_url("https://www.saucedemo.com/")