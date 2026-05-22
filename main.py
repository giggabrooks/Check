from playwright.sync_api import sync_playwright, expect
import pandas as pd
import time
import re
import sys
import asyncio

# Fix for Playwright on Windows with Python 3.14
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

df = pd.read_excel("SHEET1.xlsx", dtype={"Landline": str})
df["Status"] = ""
df["Bill"] = ""

with sync_playwright() as p:
    browser = p.chromium.launch(
        headless=False,
        args=["--disable-blink-features=AutomationControlled"]
    )
    page = browser.new_page()
    
    # Stealth mode - hide automation signals
    page.add_init_script("""
        Object.defineProperty(navigator, 'webdriver', {
            get: () => false,
        });
    """)

    for i, row in df.iterrows():
        number = str(row["Landline"]).strip()

        if not number.startswith("0"):
            number = "0" + number

        try:
            print(f"({i+1}/{len(df)}) Checking: {number}")

            page.goto("https://eand.ae/ecare/c/quick-pay", timeout=60000)

            # Wait for page to fully load
            page.wait_for_load_state("networkidle")

            # Try to find the input field
            try:
                page.wait_for_selector('input[type="tel"]', timeout=10000)
            except:
                # If not found, try alternative selectors
                print(f"Debug: Input tel not found, trying alternatives...")
                if page.locator('input[placeholder*="mobile" i]').count() > 0:
                    page.wait_for_selector('input[placeholder*="mobile" i]', timeout=5000)
                elif page.locator('input[name*="phone" i]').count() > 0:
                    page.wait_for_selector('input[name*="phone" i]', timeout=5000)
                else:
                    # Debug: take screenshot
                    page.screenshot(path=f"debug_{i}.png")
                    raise Exception("Input field not found on page")

            # Fill number
            page.fill('input[type="tel"]', number)

            # Click Next
            page.click('button:has-text("Next")')

            # WAIT FOR EITHER VALID PAGE OR ERROR TOAST
            valid_selector = page.locator("#amountPaid")
            invalid_selector = page.locator("text=Invalid account number")

            # Wait for either selector to be visible
            expect(valid_selector.or_(invalid_selector)).to_be_visible(timeout=20000)

            status = "Unknown"
            bill = ""

            # VALID CASE
            if valid_selector.is_visible():
                status = "Valid"

                # Extract bill from the input field
                bill_input = page.locator("#amountPaid")
                bill = bill_input.input_value()

            # INVALID CASE (TOAST)
            elif invalid_selector.is_visible():
                status = "Invalid"
                bill = ""

        except Exception as e:
            print("Error:", e)
            # Try to restart browser if it crashed
            try:
                page.close()
            except:
                pass
            try:
                page = browser.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                """)
            except:
                browser.close()
                browser = p.chromium.launch(
                    headless=False,
                    args=["--disable-blink-features=AutomationControlled"]
                )
                page = browser.new_page()
                page.add_init_script("""
                    Object.defineProperty(navigator, 'webdriver', {
                        get: () => false,
                    });
                """)
            
            status = "Error"
            bill = ""

        df.at[i, "Status"] = status
        df.at[i, "Bill"] = bill

        time.sleep(2)

    browser.close()

df.to_excel("output.xlsx", index=False)

print("Done!")
