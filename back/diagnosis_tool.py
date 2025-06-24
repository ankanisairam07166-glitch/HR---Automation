import asyncio
import os
import logging
from playwright.async_api import async_playwright
import json

# Configuration
BAMBOOHR_DOMAIN = "https://greenoceanpm.bamboohr.com"
LOGIN_URL = BAMBOOHR_DOMAIN + "/login.php"

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

async def diagnose_bamboo_page():
    """Diagnose BambooHR login page structure"""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=False)
        context = await browser.new_context(viewport={'width': 1920, 'height': 1080})
        page = await context.new_page()
        
        try:
            logger.info("Loading BambooHR login page...")
            await page.goto(LOGIN_URL)
            await page.wait_for_load_state("networkidle")
            await page.screenshot(path="diagnosis_initial.png")
            
            # Analyze page structure
            logger.info("Analyzing page structure...")
            
            # Get all buttons
            buttons = await page.query_selector_all("button")
            logger.info(f"Found {len(buttons)} buttons:")
            for i, button in enumerate(buttons):
                try:
                    text = await button.inner_text()
                    classes = await button.get_attribute("class")
                    logger.info(f"  Button {i+1}: '{text}' (classes: {classes})")
                except:
                    pass
            
            # Look for email login button and click it
            email_button = None
            selectors_to_try = [
                "button.js-normalLoginLink",
                "button:has-text('Log in with Email and Password')",
                ".js-normalLoginLink"
            ]
            
            for selector in selectors_to_try:
                try:
                    email_button = await page.wait_for_selector(selector, timeout=3000)
                    if email_button:
                        logger.info(f"Found email button with: {selector}")
                        break
                except:
                    continue
            
            if email_button:
                await email_button.click()
                logger.info("Clicked email login button")
                await asyncio.sleep(3)
                await page.screenshot(path="diagnosis_after_email_click.png")
            
            # Analyze inputs after clicking
            inputs = await page.query_selector_all("input")
            logger.info(f"Found {len(inputs)} input fields:")
            for i, input_field in enumerate(inputs):
                try:
                    input_type = await input_field.get_attribute("type")
                    name = await input_field.get_attribute("name")
                    id_attr = await input_field.get_attribute("id")
                    placeholder = await input_field.get_attribute("placeholder")
                    classes = await input_field.get_attribute("class")
                    is_visible = await input_field.is_visible()
                    
                    logger.info(f"  Input {i+1}: type='{input_type}', name='{name}', id='{id_attr}', placeholder='{placeholder}', visible={is_visible}")
                    logger.info(f"    Classes: {classes}")
                except Exception as e:
                    logger.debug(f"Error analyzing input {i+1}: {e}")
            
            # Check frames
            frames = page.frames
            logger.info(f"Found {len(frames)} frames:")
            for i, frame in enumerate(frames):
                logger.info(f"  Frame {i+1}: {frame.url}")
                if frame.url != "about:blank":
                    try:
                        frame_inputs = await frame.query_selector_all("input")
                        logger.info(f"    Frame {i+1} has {len(frame_inputs)} inputs")
                        for j, input_field in enumerate(frame_inputs):
                            try:
                                input_type = await input_field.get_attribute("type")
                                name = await input_field.get_attribute("name")
                                placeholder = await input_field.get_attribute("placeholder")
                                is_visible = await input_field.is_visible()
                                logger.info(f"      Frame input {j+1}: type='{input_type}', name='{name}', placeholder='{placeholder}', visible={is_visible}")
                            except:
                                pass
                    except Exception as e:
                        logger.debug(f"Error analyzing frame {i+1}: {e}")
            
            # Save page HTML
            html_content = await page.content()
            with open("diagnosis_page_content.html", "w", encoding="utf-8") as f:
                f.write(html_content)
            logger.info("Page HTML saved to diagnosis_page_content.html")
            
            # Save page info as JSON
            page_info = {
                "url": page.url,
                "title": await page.title(),
                "buttons_count": len(buttons),
                "inputs_count": len(inputs),
                "frames_count": len(frames)
            }
            
            with open("diagnosis_page_info.json", "w") as f:
                json.dump(page_info, f, indent=2)
            
            logger.info("✅ Diagnosis complete!")
            logger.info("Generated files:")
            logger.info("  - diagnosis_initial.png")
            logger.info("  - diagnosis_after_email_click.png")
            logger.info("  - diagnosis_page_content.html")
            logger.info("  - diagnosis_page_info.json")
            
            # Keep browser open for manual inspection
            input("\nPress Enter to close browser and continue...")
            
        except Exception as e:
            logger.error(f"Error during diagnosis: {e}")
            await page.screenshot(path="diagnosis_error.png")
        
        finally:
            await browser.close()

if __name__ == "__main__":
    print("🔍 BambooHR Page Diagnosis Tool")
    print("=" * 50)
    print("This tool will analyze the BambooHR login page structure")
    print("to help debug login issues.")
    print("=" * 50)
    
    asyncio.run(diagnose_bamboo_page())