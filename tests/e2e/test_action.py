from playwright.sync_api import expect

PAGE = """
<input id="name" aria-label="Name">
<label><input type="checkbox"> I agree</label>
<button id="go" disabled>Submit</button>
<p id="msg"></p>
<script>
  // The button becomes enabled after 2 seconds
  setTimeout(() => document.getElementById('go').disabled = false, 2000);

  // When clicked, wait 10 seconds before showing the message
  document.getElementById('go').onclick = () => {
    setTimeout(() => {
      document.getElementById('msg').textContent = 'Submitted!';
    }, 10000); // 10000ms = 10 seconds
  };
</script>

"""

def test_auto_wait(page):
    page.set_content(PAGE)
    page.get_by_label("Name").fill("Adil")
    page.get_by_role("checkbox", name="I agree").check()
    page.get_by_role("button", name="Submit").click()   # no sleep!

    # assert page.get_by_text("Submitted!").is_visible()
    expect(page.get_by_text("Submitted!")).to_be_visible(timeout=12000)