#!/usr/bin/env python3
"""
Minimal Lexware login script — reduced.
"""
import os
import sys
from pathlib import Path
from types import SimpleNamespace
from dotenv import load_dotenv
from playwright.async_api import async_playwright

BASE_URL = "https://app.lexware.de/sign-in/authenticate?redirect=%2Fvouchers"


def get_env_credentials():
    p = Path(__file__).resolve().parents[1] / '.env'
    if p.exists():
        load_dotenv(p)
    else:
        load_dotenv()
    u = os.getenv('LEXWARE_USERNAME')
    pw = os.getenv('LEXWARE_PASSWORD')
    if not u or not pw:
        raise SystemExit('Set LEXWARE_USERNAME and LEXWARE_PASSWORD in .env')
    return u, pw

async def get_browser_context(playwright, headless=True):
    browser = await playwright.chromium.launch(headless=headless, args=["--disable-blink-features=AutomationControlled"]) 
    # Reduce bot-detection surface: set a common user-agent and remove webdriver flag
    ua = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    context = await browser.new_context(user_agent=ua)
    return context

async def accept_privacy_consent(page):
    try:
        button = await page.wait_for_selector('button[data-testid="uc-accept-all-button"]', timeout=3000)
        await button.click()
        print("Accepted privacy consent.")
    except Exception as e:
        print(f"No privacy consent dialog found: {e}")
        raise e

async def fill_username_and_password(page, username, password):
    try:
        input_user_field = await page.wait_for_selector('input[name="username"]', timeout=3000)
        await input_user_field.fill(username)
        input_password_field = await page.wait_for_selector('input[name="password"]', timeout=3000)
        await input_password_field.fill(password)
        await input_password_field.press("Enter")
        print("Submitted username and password.")
    except Exception as e:
        print(f"Error filling username: {e}")
        raise e
    
async def check_login_success(page):
    try:
        # Wait for an element that is only present after successful login
        await page.wait_for_selector('div[translate="VOUCHER_DND_UPLOAD_FILE_RESTRICTIONS"]', timeout=10000)
        print("Login successful.")
    except Exception as e:
        print("Login failed or took too long.")
        raise e
    
async def check_upload_success(page):
        """
        Check whether the upload succeeded by waiting for a success notification.

        The Lexware UI shows a success notification with the following structure:
        <div class="alert alert-success ...">
            <div class="lx-notification-content">
                ... <span>2 Belege  hochgeladen</span>
            </div>
        </div>
        """
        try:
            sel = 'div.alert.alert-success .lx-notification-content span'
            await page.wait_for_selector(sel, timeout=100000)
            print("Upload successful.")
        except Exception as e:
            print(f"No success notification found within 10s: {e}")
            raise e

async def upload_files(page, files: list):
    print(f"Preparing to upload files: {files}")
    # Normalize and validate file paths
    file_paths = [os.path.abspath(f) for f in files]
    missing = [p for p in file_paths if not os.path.exists(p)]
    if missing:
        print(f"File(s) not found: {missing}. Skipping upload.")
        raise FileNotFoundError(f"File(s) not found: {missing}")
    try:
        # Pass the whole list of files at once (works even if the input is not visible)
        await page.set_input_files('#grldPersonalVoucherUploadBtn', file_paths)
        print("Files uploaded, waiting for success notification...")
    except Exception as e:
        # Maintain previous behavior: log the failure but allow the success-check to run.
        print(f"File input failed: {e}")
    await check_upload_success(page)

async def handle_lexware(username, password, files: list, headless=True):
    async with async_playwright() as p:
        context = await get_browser_context(p, headless)
        page = await context.new_page()
        print(f"Öffne {BASE_URL}")
        await page.goto(BASE_URL)

        await accept_privacy_consent(page)
        await fill_username_and_password(page, username, password)
        await check_login_success(page)
        await upload_files(page, files)

async def upload_voucher(username, password, filepath):
    """
    Upload a voucher to Lexware using Playwright Async API.

    This function is asynchronous and must be awaited by callers. It returns
    a SimpleNamespace with a status_code attribute (202 for success, 500 for
    error), keeping compatibility with caller expectations.
    """
    # Simple response-like object that callers expect to have a status_code attribute
    response = SimpleNamespace(status_code=None)

    try:
        await handle_lexware(username, password, headless=True, files=[filepath])
        # Success: Lexware accepted the upload
        response.status_code = 202

    except Exception as e:
        # For unexpected errors print brief message and return a non-202 status
        print(f"ERROR: {e}", file=sys.stderr)
        # Any non-zero return code indicates failure
        response.status_code = 500

    return response

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--headless', action='store_true')
    # Make files a mandatory positional argument so callers must provide files
    # to upload. Accept one or more files.
    parser.add_argument('files', nargs='+', help='File(s) to upload to Lexware')
    args = parser.parse_args()

    try:
        user, pw = get_env_credentials()
        import asyncio as _asyncio
        exit_code = _asyncio.run(handle_lexware(username=user, password=pw, headless=args.headless, files=args.files))
    except Exception as e:
        # For unexpected errors print brief message and exit non-zero
        print(f"ERROR: {e}", file=sys.stderr)
        sys.exit(1)

    sys.exit(exit_code)
