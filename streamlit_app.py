import streamlit as st
import pandas as pd
import time
from playwright.sync_api import sync_playwright, expect
from io import BytesIO
import os
import sys
import asyncio
import warnings
import subprocess

# Ensure Playwright browsers are installed
try:
    from playwright.sync_api import sync_playwright
    # Test if browsers are available
    try:
        with sync_playwright() as p:
            p.chromium.launch().close()
    except:
        st.warning("Installing Playwright browsers... (this happens only once)")
        subprocess.run([sys.executable, "-m", "playwright", "install", "chromium"], check=True)
except Exception as e:
    st.error(f"Playwright setup error: {e}")

# Fix for Playwright on Windows with Python 3.14
if sys.platform == "win32":
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", DeprecationWarning)
        asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

st.set_page_config(page_title="Validity Check App", layout="wide")

st.title("📋 Landline Validity Checker")
st.markdown("Upload an Excel file to check landline numbers validity")

# File uploader
uploaded_file = st.file_uploader("Upload Excel file with Landline numbers", type=['xlsx', 'xls'])

if uploaded_file:
    try:
        # Read the uploaded file
        df = pd.read_excel(uploaded_file, dtype={"Landline": str})
        
        # Convert datetime and object columns to strings to avoid PyArrow errors
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                df[col] = df[col].astype(str)
            elif df[col].dtype == 'object':
                df[col] = df[col].astype(str)
        
        st.subheader("📊 Preview of Uploaded File")
        st.dataframe(df.head(10))
        
        # Add Status and Bill columns if not present
        if "Status" not in df.columns:
            df["Status"] = ""
        if "Bill" not in df.columns:
            df["Bill"] = ""
        
        # Start button
        if st.button("🚀 Start Validity Check"):
            st.info("⏳ Processing may take a few minutes. Do not close this window.")
            
            progress_bar = st.progress(0)
            status_placeholder = st.empty()
            results_placeholder = st.empty()
            
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
                    
                    # Add leading 0 if not present
                    if not number.startswith("0"):
                        number = "0" + number
                    
                    try:
                        status_placeholder.info(f"({i+1}/{len(df)}) Checking: {number}")
                        
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
                        
                        # Wait for either valid or invalid response
                        valid_selector = page.locator("#amountPaid")
                        invalid_selector = page.locator("text=Invalid account number")
                        
                        expect(valid_selector.or_(invalid_selector)).to_be_visible(timeout=30000)
                        
                        # Check status
                        if valid_selector.is_visible():
                            df.at[i, "Status"] = "Valid"
                            bill_input = page.locator("#amountPaid")
                            df.at[i, "Bill"] = bill_input.input_value()
                        elif invalid_selector.is_visible():
                            df.at[i, "Status"] = "Invalid"
                            df.at[i, "Bill"] = ""
                        else:
                            df.at[i, "Status"] = "Unknown"
                            df.at[i, "Bill"] = ""
                    
                    except Exception as e:
                        print(f"Error for {number}: {e}")
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
                                headless=True,
                                args=["--disable-blink-features=AutomationControlled"]
                            )
                            page = browser.new_page()
                            page.add_init_script("""
                                Object.defineProperty(navigator, 'webdriver', {
                                    get: () => false,
                                });
                            """)
                        
                        df.at[i, "Status"] = "Error"
                        df.at[i, "Bill"] = str(e)
                    
                    time.sleep(2)
                    progress = (i + 1) / len(df)
                    progress_bar.progress(progress)
                
                browser.close()
            
            # Show results
            st.success("✅ Validity check completed!")
            
            # Display results table
            st.subheader("📋 Validity Check Results")
            # Convert datetime columns to strings for display
            display_df = df.copy()
            for col in display_df.columns:
                if pd.api.types.is_datetime64_any_dtype(display_df[col]):
                    display_df[col] = display_df[col].astype(str)
            st.dataframe(display_df, width='stretch')
            
            # Download results
            output = BytesIO()
            df.to_excel(output, index=False, sheet_name='Results')
            output.seek(0)
            
            st.download_button(
                label="📥 Download Results (Excel)",
                data=output.getvalue(),
                file_name="validity_check_results.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
            
            # Summary statistics
            st.subheader("📊 Summary Statistics")
            col1, col2, col3, col4 = st.columns(4)
            
            valid_count = (df["Status"] == "Valid").sum()
            invalid_count = (df["Status"] == "Invalid").sum()
            error_count = (df["Status"] == "Error").sum()
            total = len(df)
            
            col1.metric("Total Checked", total)
            col2.metric("Valid", valid_count)
            col3.metric("Invalid", invalid_count)
            col4.metric("Errors", error_count)
    
    except Exception as e:
        st.error(f"❌ Error reading file: {str(e)}")
        st.info("Please ensure the file has a 'Landline' column")
