import re, time
from behave import given, when, then
from playwright.sync_api import expect

LOGIN_URL = "https://v2.zenclass.in/login"

# ---------- Locator helpers ----------
def email_input(page):
    for ph in ["Enter your mail", "Enter your email", "Email", "Email address"]:
        loc = page.get_by_placeholder(ph)
        if loc.count() > 0:
            return loc.first
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
    for c in [page.get_by_role("button", name=re.compile(r"(sign\s*in|login|log\s*in)", re.I)),
              page.locator('button[type="submit"]'),
              page.locator('input[type="submit"]')]:
        if c.count() > 0:
            return c.first
    return page.locator('button[type="submit"]')

def logout_control(page):
    # You mentioned <div class="user-avatar-menu">Log out</div>
    for c in [page.locator("div.user-avatar-menu", has_text=re.compile(r"log\s*out", re.I)),
              page.get_by_role("menuitem", name=re.compile(r"log\s*out|sign\s*out", re.I)),
              page.get_by_role("button",   name=re.compile(r"log\s*out|sign\s*out", re.I)),
              page.get_by_role("link",     name=re.compile(r"log\s*out|sign\s*out", re.I)),
              page.locator("[data-testid='logout'], [href*='logout']"),
              page.get_by_text(re.compile(r"\blog\s*out\b|\bsign\s*out\b", re.I))]:
        if c.count() > 0:
            return c.first
    return None

def wait_for_post_login(page, timeout_ms=20000):
    """Wait until: welcome banner OR logout appears OR URL leaves /login OR login inputs disappear."""
    deadline = time.time() + timeout_ms/1000.0
    while time.time() < deadline:
        try:
            if page.locator("p.student-name").count() > 0 and page.locator("p.student-name").first.is_visible():
                return True
            if logout_control(page) and logout_control(page).is_visible():
                return True
            if "/login" not in page.url:
                return True
            if email_input(page).is_hidden() and pass_input(page).is_hidden():
                return True
        except Exception:
            pass
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
    ok = wait_for_post_login(context.page, timeout_ms=20000)
    assert ok, f"Login did not complete. Current URL: {context.page.url}"

@then('the user sees welcome banner for "{full_name}"')
def step_user_sees_welcome_for(context, full_name):
    banner = context.page.locator('p.student-name').first
    expect(banner).to_be_visible(timeout=20000)
    # Accept with/without space after comma
    expect(banner).to_have_text(re.compile(rf'^\s*Welcome,\s*{re.escape(full_name)}\s*$', re.I))

@then('the user logs out')
def step_user_logs_out(context):
    page = context.page
    lg = logout_control(page)
    if not lg:
        for t in [page.get_by_role("button", name=re.compile(r"(account|profile|user|menu)", re.I)),
                  page.locator("[data-testid='avatar'], [aria-label*='account'], [aria-label*='profile']"),
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
