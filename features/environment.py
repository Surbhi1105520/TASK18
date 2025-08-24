import os, re
from datetime import datetime
from playwright.sync_api import sync_playwright

# Optional: attach screenshots to Allure on failure (if allure is installed)
try:
    from allure_commons._allure import attach
    from allure_commons.types import AttachmentType
except Exception:
    attach = None
    AttachmentType = None

def before_all(context):
    context.playwright = sync_playwright().start()
    # Flip to headless=True for CI
    context.browser = context.playwright.chromium.launch(headless=False)
    os.makedirs("reports/artifacts", exist_ok=True)

def after_all(context):
    context.browser.close()
    context.playwright.stop()

def before_scenario(context, scenario):
    context.page = context.browser.new_page()
    context.page.set_default_timeout(10000)

def after_scenario(context, scenario):
    context.page.close()

def after_step(context, step):
    if step.status == "failed":
        safe = re.sub(r"[^a-zA-Z0-9_.-]+", "_", step.name)[:60]
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        path = f"reports/artifacts/FAILED_{safe}_{stamp}.png"
        try:
            context.page.screenshot(path=path, full_page=True)
            if attach and AttachmentType:
                attach.file(path, name=step.name, attachment_type=AttachmentType.PNG)
        except Exception:
            pass
