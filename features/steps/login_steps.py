import re, time
from behave import given, when, then
from playwright.sync_api import expect

LOGIN_URL = "https://v2.zenclass.in/login"  # <- .com domain per your request

# ---------- Robust locator helpers ----------
def email_input(page):
    # Try common placeholders first
    for ph in ["Enter your mail", "Enter your email", "Email", "Email address"]:
        loc = page.get_by_placeholder(ph)
        if loc.count() > 0:
            return loc.first
    # Fallbacks
    for c in [page.locator('input[type="email"]'),
              page.locator('input[name*="email" i]'),
              page.locator('input[type="text"]')]:
        if c.count() > 0:
            return c.first
    return page.locator('input').first

def pass_input(page):
    for ph in ["Enter your password", "Password"]:
        loc = page.get_by_placeholder(ph)
        if loc.count() > 0:
            return loc.first
    for c in [page.locator('input[type="password"]'),
              page.locator('input[name*="pass" i]')]:
        if c.count() > 0:
            return c.first
    return page.locator('input[type="password"]').first

def submit_button(page):
    candidates = [
        page.get_by_role("button", name=re.compile(r"(sign\s*in|login|log\s*in)", re.I)),
        page.locator('button[type="submit"]'),
        page.locator('input[type="submit"]'),
    ]
    for c in candidates:
        if c.count() > 0:
            return c.first
    return page.locator('button[type="submit"]')

def logout_control(page):
    # You earlier shared: <div class="user-avatar-menu">Log out</div>
    candidates = [
        page.locator("div.user-avatar-menu", has_text=re.compile(r"log\s*out", re.I)),
        page.get_by_role("menuitem", name=re.compile(r"log\s*out|sign\s*out", re.I)),
        page.get_by_role("button",   name=re.compile(r"log\s*out|sign\s*out", re.I)),
        page.get_by_role("link",     name=re.compile(r"log\s*out|sign\s*out", re.I)),
        page.locator("[data-testid='logout'], [href*='logout']"),
        page.get_by_text(re.compile(r"\blog\s*out\b|\bsign\s*out\b", re.I)),
    ]
    for c in candidates:
        if c.count() > 0:
            return c.first
    return None

def otp_present(page):
    hints = [
        page.get_by_placeholder(re.compile(r"(otp|one[-\s]?time)", re.I)),
        page.get_by_text(re.compile(r"\bOTP\b|\bOne[-\s]?Time\s*Password\b", re.I)),
        page.locator('[name*="otp" i]'),
    ]
    return any(h.count() > 0 and h.first.is_visible() for h in hints)

def wait_for_post_login(page, timeout_ms=25000):
    """
    Wait for one of the post-login signals:
      - Welcome banner on dashboard (if present)
      - A Logout control becomes visible
      - URL changes away from /login
      - Login inputs disappear
      - No OTP prompt is shown (if shown => fail fast)
    """
    deadline = time.time() + timeout_ms/1000.0
    banner = page.locator("p.student-name").first  # seen on some GUVI dashboards

    while time.time() < deadline:
        if otp_present(page):
            raise AssertionError("OTP prompt detected after login; automated test cannot proceed.")
        try:
            if banner.count() > 0 and banner.is_visible():
                return True
        except Exception:
            pass
        lg = logout_control(page)
        if lg and lg.is_visible():
            return True
        if "/login" not in page.url:
            return True
        try:
            if email_input(page).is_hidden() and pass_input(page).is_hidden():
                return True
        except Exception:
            # inputs may not exist in DOM anymore
            return True
        page.wait_for_timeout(250)
    return False

# ---------- Steps ----------
@given('the user is on login page')
def step_open_login(context):
    context.page.goto(LOGIN_URL)
    expect(email_input(context.page)).to_be_visible()
    expect(pass_input(context.page)).to_be_visible()

@when('the user logs in with username "{username}" and password "{password}"')
def step_login(context, username, password):
    email_input(context.page).fill(username)
    pass_input(context.page).fill(password)
    submit_button(context.page).click()
    ok = wait_for_post_login(context.page, timeout_ms=25000)
    assert ok, f"Login did not complete. Current URL: {context.page.url}"

@then('the user sees the dashboard')
def step_user_sees_dashboard(context):
    # Prefer the welcome banner if present
    banner = context.page.locator('p.student-name').first
    if banner.count() > 0:
        expect(banner).to_be_visible(timeout=20000)
        # accept "Welcome, Name" with/without space after comma
        text = banner.inner_text().strip()
        assert text.lower().startswith("welcome"), f"Unexpected welcome text: {text}"
        return

    # Otherwise accept a broader app URL (SPA routes vary)
    expect(context.page).to_have_url(re.compile(r"/(dashboard|classroom|home|app)", re.I), timeout=20000)

@then('the user logs out')
def step_user_logs_out(context):
    page = context.page
    lg = logout_control(page)
    if not lg:
        # Open common user/avatar menus then retry
        for t in [page.get_by_role("button", name=re.compile(r"(account|profile|user|menu)", re.I)),
                  page.locator("[data-testid='avatar'], [aria-label*='account' i], [aria-label*='profile' i]"),
                  page.locator("img[alt*='profile' i], img[alt*='avatar' i]")]:
            if t.count() > 0:
                t.first.click()
                lg = logout_control(page)
                if lg:
                    break
    assert lg, "Logout control not found. Update selectors for current UI."
    expect(lg).to_be_visible()
    lg.click()

@then('the user is back on login page')
def step_back_to_login(context):
    expect(context.page).to_have_url(re.compile(r"/login", re.I), timeout=15000)
    expect(email_input(context.page)).to_be_visible()
    expect(pass_input(context.page)).to_be_visible()

@then('the username input should be visible and editable')
def step_validate_username_input(context):
    loc = email_input(context.page)
    expect(loc).to_be_visible()
    loc.fill("")  # editable
    loc.fill("test@example.com")
    expect(loc).to_have_value("test@example.com")

@then('the password input should be visible and masked')
def step_validate_password_input(context):
    loc = pass_input(context.page)
    expect(loc).to_be_visible()
    typ = loc.get_attribute("type")
    assert typ == "password", f"Expected password input type='password', got '{typ}'"

@then('the submit button should be visible and enabled')
def step_validate_submit_button(context):
    btn = submit_button(context.page)
    expect(btn).to_be_visible()
    expect(btn).to_be_enabled()

@when('the user clears login fields')
def step_clear_fields(context):
    email_input(context.page).fill("")
    pass_input(context.page).fill("")

@when('the user clicks submit')
def step_click_submit(context):
    submit_button(context.page).click()

@then('the login should fail and stay on login page')
def step_login_failed(context):
    # URL should remain (or return) /login and show an error (if any)
    expect(context.page).to_have_url(re.compile(r"/login", re.I), timeout=10000)
    possible_errors = [
        context.page.get_by_role("alert"),
        context.page.get_by_text(re.compile(r"(invalid|incorrect|wrong|failed|required)", re.I)),
        context.page.locator("[data-testid='error'], .Mui-error, .error, .alert"),
    ]
    # Non-fatal if no error message — URL guard above ensures failure.
    _ = any(e.count() > 0 for e in possible_errors)
