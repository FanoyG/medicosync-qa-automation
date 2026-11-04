import re
from playwright.sync_api import expect

def test_login(page):
    page.goto("https://www.saucedemo.com/")
    page.get_by_label("Username").fill("standard_user")
    page.get_by_label("Password").fill("secret_sauce")
    page.get_by_role("button", name="Login").click()

    expect(page).to_have_url(re.compile("inventory"))

def test_login_wrong_password(page):
    page.goto("https://www.saucedemo.com/")
    page.get_by_label("Username").fill("standard_user")
    page.get_by_label("Password").fill("wrong")
    page.get_by_role("button", name="Login").click()

    expect(page.get_by_text("do not match any user")).to_be_visible()


import html
from playwright.sync_api import expect

# The inner room (this is what lives INSIDE the iframe)
INNER = """
<label for="name">Name</label>
<input id="name">
<button onclick="document.getElementById('msg').textContent = 'Hello ' + document.getElementById('name').value">Send</button>
<p id="msg"></p>
"""

# The main room, with the inner room embedded
PAGE = f'<h1>Main page</h1><iframe title="Contact form" srcdoc="{html.escape(INNER, quote=True)}"></iframe>'


def test_inside_iframe(page):
    page.set_content(PAGE)
    page.pause()
    frame = page.frame_locator("iframe[title='Contact form']")   # step into the inner room
    frame.get_by_label("Name").fill("Adil")
    frame.get_by_role("button", name="Send").click()

    expect(frame.get_by_text("Hello Adil")).to_be_visible()


def test_outside_cannot_see_inside(page):
    page.set_content(PAGE)
    page.pause()

    # The bellboy searching the MAIN room finds no "Name" guest
    expect(page.get_by_label("Name")).to_have_count(0)