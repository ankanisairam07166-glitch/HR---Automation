import asyncio
import os
import logging
from playwright.async_api import async_playwright
import requests
import time

# Configuration
BAMBOOHR_DOMAIN = "https://greenoceanpm.bamboohr.com"
LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"
BAMBOOHR_EMAIL = "support@smoothoperations.ai"
BAMBOOHR_PASSWORD = "Password1%"

# 2FA Configuration
TWOFA_WEBHOOK_URL = "https://n8n.greenoceanpropertymanagement.com/webhook/2f1b815e-31d5-4f0f-b2f6-b07e7637ecf5"
TWOFA_API_KEY = "67593101297393632845404167993723"

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def get_2fa_code():
    """Get 2FA code from webhook"""
    try:
        headers = {"x-api-key": TWOFA_API_KEY}
        response = requests.get(TWOFA_WEBHOOK_URL, headers=headers, timeout=15)
        
        if response.status_code == 200:
            data = response.json()
            if isinstance(data, list) and len(data) > 0:
                token = data[0].get('output', {}).get('token') or data[0].get('token')
            elif isinstance(data, dict):
                token = data.get('token')
            else:
                token = None
                
            if token:
                logger.info(f"Got 2FA code: {token}")
                return str(token)
                
    except Exception as e:
        logger.error(f"Error getting 2FA code: {e}")
    return None

async def test_bamboo_login():
    """Test BambooHR login step by step"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            # Step 1: Navigate to login page
            logger.info("Step 1: Navigating to login page")
            await page.goto(LOGIN_URL)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="step1_initial_page.png")
            logger.info("Screenshot saved: step1_initial_page.png")
            
            # Step 2: Look for and click email login button
            logger.info("Step 2: Looking for email login button")
            
            # Try different selectors for the email login button
            email_button_selectors = [
                "button.js-normalLoginLink",
                "button:has-text('Log in with Email and Password')",
                ".js-normalLoginLink"
            ]
            
            email_button = None
            for selector in email_button_selectors:
                try:
                    email_button = await page.wait_for_selector(selector, timeout=5000)
                    if email_button and await email_button.is_visible():
                        logger.info(f"Found email button with selector: {selector}")
                        break
                except:
                    continue
            
            if email_button:
                await email_button.click()
                logger.info("Clicked email login button")
                await asyncio.sleep(3)
                await page.screenshot(path="step2_after_email_button.png")
            else:
                logger.warning("Email login button not found")
                await page.screenshot(path="step2_no_email_button.png")
            
            # Step 3: Find email input
            logger.info("Step 3: Looking for email input")
            
            email_selectors = [
                "input[name='email']",
                "input[type='email']", 
                "input[id='femail']",
                "input[placeholder*='Email']",
                "input[placeholder*='email']"
            ]
            
            email_input = None
            for selector in email_selectors:
                try:
                    email_input = await page.wait_for_selector(selector, timeout=5000)
                    if email_input and await email_input.is_visible():
                        logger.info(f"Found email input with selector: {selector}")
                        break
                except:
                    continue
            
            if not email_input:
                logger.error("Email input not found")
                await page.screenshot(path="step3_no_email_input.png")
                
                # Try to find it in frames
                logger.info("Checking frames for email input...")
                for i, frame in enumerate(page.frames):
                    try:
                        logger.info(f"Checking frame {i}: {frame.url}")
                        for selector in email_selectors:
                            try:
                                frame_email = await frame.wait_for_selector(selector, timeout=3000)
                                if frame_email and await frame_email.is_visible():
                                    logger.info(f"Found email input in frame {i}")
                                    email_input = frame_email
                                    page = frame  # Switch to frame
                                    break
                            except:
                                continue
                        if email_input:
                            break
                    except Exception as e:
                        logger.debug(f"Error checking frame {i}: {e}")
            
            if not email_input:
                logger.error("Could not find email input anywhere!")
                
                # Dump page content for debugging
                content = await page.content()
                with open("debug_page_content.html", "w", encoding="utf-8") as f:
                    f.write(content)
                logger.info("Page content saved to debug_page_content.html")
                return False
            
            # Step 4: Fill email
            logger.info("Step 4: Filling email")
            await email_input.click()
            await email_input.fill(BAMBOOHR_EMAIL)
            logger.info(f"Entered email: {BAMBOOHR_EMAIL}")
            await page.screenshot(path="step4_email_filled.png")
            
            # Step 5: Find and fill password
            logger.info("Step 5: Looking for password input")
            
            password_selectors = [
                "input[name='password']",
                "input[type='password']",
                "input[id='password']"
            ]
            
            password_input = None
            for selector in password_selectors:
                try:
                    password_input = await page.wait_for_selector(selector, timeout=5000)
                    if password_input and await password_input.is_visible():
                        logger.info(f"Found password input with selector: {selector}")
                        break
                except:
                    continue
            
            if not password_input:
                logger.error("Password input not found")
                await page.screenshot(path="step5_no_password.png")
                return False
            
            await password_input.click()
            await password_input.fill(BAMBOOHR_PASSWORD)
            logger.info("Password entered")
            await page.screenshot(path="step5_password_filled.png")
            
            # Step 6: Submit form
            logger.info("Step 6: Submitting form")
            
            login_button_selectors = [
                "button[type='submit']",
                "input[type='submit']",
                "button:has-text('Log In')",
                "button:has-text('Log in')"
            ]
            
            login_button = None
            for selector in login_button_selectors:
                try:
                    login_button = await page.wait_for_selector(selector, timeout=5000)
                    if login_button and await login_button.is_visible():
                        logger.info(f"Found login button with selector: {selector}")
                        break
                except:
                    continue
            
            if login_button:
                await login_button.click()
                logger.info("Clicked login button")
            else:
                logger.info("Login button not found, using Enter key")
                await password_input.press("Enter")
            
            # Step 7: Wait for response
            logger.info("Step 7: Waiting for login response")
            await page.wait_for_load_state("networkidle", timeout=20000)
            await asyncio.sleep(3)
            await page.screenshot(path="step7_after_login.png")
            
            current_url = page.url
            logger.info(f"Current URL: {current_url}")
            
            # Step 8: Check for 2FA
            logger.info("Step 8: Checking for 2FA")
            
            needs_2fa = False
            twofa_indicators = ["two-factor", "2fa", "verify", "authentication"]
            
            if any(indicator in current_url.lower() for indicator in twofa_indicators):
                needs_2fa = True
                logger.info("2FA detected from URL")
            
            if not needs_2fa:
                try:
                    page_text = await page.inner_text("body")
                    if any(phrase in page_text.lower() for phrase in ["verification code", "authenticator", "2fa", "enter code"]):
                        needs_2fa = True
                        logger.info("2FA detected from page content")
                except:
                    pass
            
            if needs_2fa:
                logger.info("Processing 2FA...")
                await page.screenshot(path="step8_2fa_page.png")
                
                # Get 2FA code
                twofa_code = get_2fa_code()
                if not twofa_code:
                    logger.error("Failed to get 2FA code")
                    return False
                
                # Find 2FA input
                twofa_selectors = [
                    "input[type='text']",
                    "input[type='number']",
                    "input[name*='code']",
                    "input[placeholder*='code']"
                ]
                
                twofa_input = None
                for selector in twofa_selectors:
                    try:
                        twofa_input = await page.wait_for_selector(selector, timeout=5000)
                        if twofa_input and await twofa_input.is_visible():
                            logger.info(f"Found 2FA input with selector: {selector}")
                            break
                    except:
                        continue
                
                if twofa_input:
                    await twofa_input.fill(twofa_code)
                    logger.info(f"Entered 2FA code: {twofa_code}")
                    
                    # Submit 2FA
                    try:
                        submit_btn = await page.wait_for_selector("button[type='submit']", timeout=5000)
                        await submit_btn.click()
                    except:
                        await twofa_input.press("Enter")
                    
                    await page.wait_for_load_state("networkidle", timeout=20000)
                    await asyncio.sleep(3)
                    await page.screenshot(path="step8_after_2fa.png")
                else:
                    logger.error("2FA input not found")
                    return False
            
            # Step 9: Verify login success
            logger.info("Step 9: Verifying login success")
            
            final_url = page.url
            logger.info(f"Final URL: {final_url}")
            
            success_indicators = ["home", "dashboard", "hiring", "employees"]
            login_successful = any(indicator in final_url.lower() for indicator in success_indicators)
            
            if not login_successful:
                # Check for navigation elements
                nav_selectors = [
                    "a[href*='/hiring']",
                    "a[href*='/employees']",
                    "nav",
                    ".navigation"
                ]
                
                for selector in nav_selectors:
                    try:
                        nav_element = await page.wait_for_selector(selector, timeout=3000)
                        if nav_element:
                            login_successful = True
                            logger.info(f"Found navigation: {selector}")
                            break
                    except:
                        continue
            
            await page.screenshot(path="step9_final_state.png")
            
            if login_successful:
                logger.info("✅ LOGIN SUCCESSFUL!")
                return True
            else:
                logger.error("❌ LOGIN FAILED")
                
                # Log page text for debugging
                try:
                    page_text = await page.inner_text("body")
                    logger.info(f"Final page text: {page_text[:300]}...")
                except:
                    pass
                
                return False
                
        except Exception as e:
            logger.error(f"Error during test: {e}")
            await page.screenshot(path="error_screenshot.png")
            return False
        
        finally:
            await browser.close()

async def main():
    """Main test function"""
    print("🧪 BambooHR Login Test")
    print("=" * 40)
    print(f"Testing login to: {LOGIN_URL}")
    print(f"Email: {BAMBOOHR_EMAIL}")
    print("=" * 40)
    
    success = await test_bamboo_login()
    
    if success:
        print("\n🎉 Test completed successfully!")
        print("The login process is working correctly.")
    else:
        print("\n❌ Test failed!")
        print("Check the screenshots and logs for debugging information.")
        print("\nGenerated files:")
        print("- step*.png (screenshots of each step)")
        print("- debug_page_content.html (page HTML if email input not found)")

if __name__ == "__main__":
    asyncio.run(main())