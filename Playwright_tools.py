#!/usr/bin/env python3
"""
Playwright Tools - Main collection of browser automation tools
This is the primary module that the AI Browser Agent will discover and use.
"""
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger("playwright_tools")

class PlaywrightTools:
    """Main collection of Playwright browser automation tools for the AI Browser Agent."""
    
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self.console_logs = []
        self.browser_initialized = False
        
        # Create a screenshots directory if it doesn't exist
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
        logger.info(f"Screenshots will be saved to: {self.screenshot_dir}")
    
    # === Helper Methods ===
    
    async def initialize(self):
        """Initialize Playwright without launching a browser."""
        try:
            self.playwright = await async_playwright().start()
            logger.info("Playwright initialized")
            
            # Pre-initialize browser for better reliability
            try:
                print("Pre-initializing browser for better reliability...")
                await self._ensure_browser_initialized()
                print("Browser pre-initialized successfully")
            except Exception as browser_err:
                logger.warning(f"Browser pre-initialization failed (will retry when needed): {browser_err}")
                
            return True
        except Exception as e:
            logger.error(f"Failed to initialize Playwright: {e}")
            return False
    
    async def _ensure_browser_initialized(self):
        """Ensure browser is initialized before using it."""
        if not self.browser_initialized:
            try:
                self.browser = await self.playwright.chromium.launch(headless=False)
                
                viewport_size = {"width": 1425, "height": 776}
                self.context = await self.browser.new_context(
                    viewport=viewport_size,
                    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
                )
                self.browser_initialized = True
                logger.info(f"Browser initialized with viewport size {viewport_size}")
                
                if len(self.pages) == 0:
                    page = await self.context.new_page()
                    await page.set_viewport_size(viewport_size)
                    self.pages.append(page)
                    logger.info(f"Created new page with viewport size {viewport_size}")
                
                # Try to maximize window
                try:
                    cdp_session = await self.pages[0].context.new_cdp_session(self.pages[0])
                    await cdp_session.send('Browser.setWindowBounds', {
                        'windowId': 1,
                        'bounds': {'windowState': 'maximized'}
                    })
                    logger.info("Browser window maximized via CDP")
                except Exception as e:
                    logger.warning(f"Could not maximize window via CDP: {e}")
                    
            except Exception as e:
                logger.error(f"Error initializing browser: {e}")
                self.browser_initialized = False
                raise

    async def _get_page(self, page_index: int) -> Optional[Page]:
        """Get a page by index, creating one if necessary."""
        if page_index < 0:
            return None
        
        await self._ensure_browser_initialized()
        
        while len(self.pages) <= page_index:
            new_page = await self.context.new_page()
            new_page.on("console", lambda msg: self.console_logs.append({
                "type": msg.type,
                "text": msg.text,
                "location": msg.location,
                "time": asyncio.get_event_loop().time()
            }))
            self.pages.append(new_page)
        
        return self.pages[page_index]
    
    def _get_screenshot_path(self, filename: str) -> str:
        """Get the full path for a screenshot file."""
        if not os.path.dirname(filename):
            return os.path.join(self.screenshot_dir, filename)
        return filename
    
    # === Core Browser Automation Tools ===

    async def playwright_navigate(self, url: str, wait_for_load: bool = True, 
                                 capture_screenshot: bool = False, page_index: int = 0) -> Dict[str, Any]:
        """Navigate to a URL."""
        try:
            if not self.browser_initialized:
                await self._ensure_browser_initialized()
            
            print(f"Navigating to {url}...")
            
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            if page.is_closed():
                page = await self.context.new_page()
                self.pages[page_index] = page
            
            if wait_for_load:
                await page.goto(url, wait_until="load")
            else:
                await page.goto(url, wait_until="domcontentloaded")
            
            if capture_screenshot:
                screenshot_path = self._get_screenshot_path("screenshot.png")
                await page.screenshot(path=screenshot_path)
                return {
                    "status": "success",
                    "message": f"Navigated to {url}",
                    "screenshot": screenshot_path
                }
                    
            return {
                "status": "success",
                "message": f"Navigated to {url}",
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_screenshot(self, filename: str, selector: str = "", page_index: int = 0, 
                                  full_page: bool = False) -> Dict[str, Any]:
        """Take a screenshot."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            if not filename.endswith(".png"):
                filename += ".png"
            
            full_path = self._get_screenshot_path(filename)
            
            if selector:
                element = await page.wait_for_selector(selector, state="visible", timeout=5000)
                if not element:
                    return {"status": "error", "message": f"Element not found: {selector}"}
                await element.screenshot(path=full_path)
            else:
                await page.screenshot(path=full_path, full_page=full_page)
            
            return {
                "status": "success",
                "message": f"Screenshot saved to {full_path}",
                "filename": full_path
            }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_click(self, selector: str, page_index: int = 0) -> Dict[str, Any]:
        """Click on an element."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.wait_for_selector(selector, state="visible")
            await page.click(selector)
            
            return {
                "status": "success",
                "message": f"Clicked on {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_fill(self, selector: str, text: str, page_index: int = 0) -> Dict[str, Any]:
        """Fill a form field."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.wait_for_selector(selector, state="visible")
            await page.fill(selector, text)
            
            return {
                "status": "success",
                "message": f"Filled {selector} with text"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_smart_click(self, text=None, selector=None, element_type: str = 'any', 
                                   page_index: int = 0) -> Dict[str, Any]:
        """Smart click that tries multiple selector strategies."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            # Handle cases where selector is provided instead of text
            if selector is not None and text is None:
                text = selector
            
            if text is None:
                return {"status": "error", "message": "Either text or selector must be provided"}
            
            # Create variations of the text for fuzzy matching
            text_variations = [text, text.lower(), text.upper(), text.title()]
            
            # Generate selectors based on element type
            selectors = []
            
            if element_type == "button" or element_type == "any":
                for variation in text_variations:
                    selectors.extend([
                        f"button:has-text('{variation}')",
                        f"input[type='submit'][value='{variation}']",
                        f"[role='button']:has-text('{variation}')",
                    ])
            
            if element_type == "link" or element_type == "any":
                for variation in text_variations:
                    selectors.extend([
                        f"a:has-text('{variation}')",
                        f"[role='link']:has-text('{variation}')"
                    ])
            
            if element_type == "any":
                for variation in text_variations:
                    selectors.extend([
                        f":has-text('{variation}'):visible",
                        f"[aria-label='{variation}']",
                        f"[title='{variation}']",
                    ])
            
            # Try each selector
            for sel in selectors:
                try:
                    element_count = await page.locator(sel).count()
                    if element_count > 0:
                        await page.locator(sel).first.wait_for(state='visible', timeout=5000)
                        await page.click(sel)
                        
                        return {
                            "status": "success",
                            "message": f"Smart click succeeded with selector: {sel}",
                            "matched_text": text,
                            "selector_used": sel
                        }
                except Exception:
                    continue
            
            return {
                "status": "error", 
                "message": f"Smart click failed: Could not find clickable element matching '{text}'"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_hover(self, selector: str, page_index: int = 0) -> Dict[str, Any]:
        """Hover over an element."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.wait_for_selector(selector, state="visible")
            await page.hover(selector)
            
            return {
                "status": "success",
                "message": f"Hovered over {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_select(self, selector: str, value: str, page_index: int = 0) -> Dict[str, Any]:
        """Select an option from a dropdown."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.wait_for_selector(selector, state="visible")
            await page.select_option(selector, value)
            
            return {
                "status": "success",
                "message": f"Selected value '{value}' in {selector}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_evaluate(self, script: str, page_index: int = 0) -> Dict[str, Any]:
        """Evaluate JavaScript in the page context."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            result = await page.evaluate(script)
            
            return {
                "status": "success",
                "result": result
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_text(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible text from the page."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            text = await page.text_content(selector)
            
            return {
                "status": "success",
                "text": text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_get_visible_html(self, selector: str = "body", page_index: int = 0) -> Dict[str, Any]:
        """Get visible HTML from the page."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            html = await page.inner_html(selector)
            
            return {
                "status": "success",
                "html": html
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_wait_for_element(self, selector: str, state: str = "visible", 
                                        timeout_ms: int = 30000, page_index: int = 0) -> Dict[str, Any]:
        """Wait for an element to reach a specific state."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.wait_for_selector(selector, state=state, timeout=timeout_ms)
            
            return {
                "status": "success",
                "message": f"Element {selector} reached state: {state}",
                "selector": selector,
                "state": state
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_wait_for_navigation(self, timeout_ms: int = 30000, 
                                           page_index: int = 0) -> Dict[str, Any]:
        """Wait for navigation to complete."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            async with page.expect_navigation(timeout=timeout_ms):
                pass
            
            return {
                "status": "success",
                "message": "Navigation completed",
                "url": page.url,
                "title": await page.title()
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_back(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate back in the browser history."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.go_back()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated back",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_go_forward(self, page_index: int = 0) -> Dict[str, Any]:
        """Navigate forward in the browser history."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.go_forward()
            await page.wait_for_load_state("networkidle")
            
            return {
                "status": "success",
                "message": "Navigated forward",
                "title": await page.title(),
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_press_key(self, key: str, page_index: int = 0) -> Dict[str, Any]:
        """Press a key."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            await page.keyboard.press(key)
            
            return {
                "status": "success",
                "message": f"Pressed key: {key}"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_console_logs(self, page_index: int = 0, count: int = 10) -> Dict[str, Any]:
        """Get console logs from the page."""
        try:
            page_logs = [log for log in self.console_logs if log.get("page_index", 0) == page_index]
            recent_logs = page_logs[-count:] if count < len(page_logs) else page_logs
            
            return {
                "status": "success",
                "logs": recent_logs
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_close(self, page_index: int = 0) -> Dict[str, Any]:
        """Close a page."""
        try:
            if page_index < 0 or page_index >= len(self.pages):
                return {"status": "error", "message": "Invalid page index"}
            
            await self.pages[page_index].close()
            self.pages.pop(page_index)
            
            return {
                "status": "success",
                "message": f"Closed page at index {page_index}",
                "remaining_pages": len(self.pages)
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Advanced Locator Methods ===

    async def playwright_css_locator(self, selector: str, action: str = "find", 
                                   text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """Use CSS selectors to locate elements with Playwright's enhanced CSS support."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            locator = page.locator(f"css={selector}")
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching CSS selector: {selector}"
                }
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching CSS selector: {selector}",
                "action_performed": action_result,
                "locator_type": "css"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_xpath_locator(self, xpath: str, action: str = "find", 
                                     text_input: str = "", page_index: int = 0) -> Dict[str, Any]:
        """Use XPath selector to locate elements."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            locator = page.locator(f"xpath={xpath}")
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found matching XPath: {xpath}"
                }
            
            # Perform the requested action on the first element
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements matching XPath: {xpath}",
                "action_performed": action_result,
                "locator_type": "xpath"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Accessibility Methods ===

    async def playwright_find_by_role(self, role: str, name: str = "", exact: bool = False,
                                    action: str = "find", text_input: str = "",
                                    page_index: int = 0) -> Dict[str, Any]:
        """Find elements by their ARIA role."""
        try:
            page = await self._get_page(page_index)
            if not page:
                return {"status": "error", "message": "Invalid page index"}
            
            options = {}
            if name:
                options["name"] = name
                options["exact"] = exact
            
            locator = page.get_by_role(role, **options)
            count = await locator.count()
            
            if count == 0:
                name_part = f" with name '{name}'" if name else ""
                return {
                    "status": "error",
                    "message": f"No elements found with role '{role}'{name_part}"
                }
            
            # Perform requested action
            action_result = None
            if action == "click":
                await locator.first.click()
                action_result = "Clicked element"
            elif action == "fill" and text_input:
                await locator.first.fill(text_input)
                action_result = f"Filled element with '{text_input}'"
            
            return {
                "status": "success",
                "message": f"Found {count} elements with role '{role}'{name_part}",
                "action_performed": action_result,
                "total_matches": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Cleanup ===

    async def cleanup(self):
        """Cleanup resources but maintain browser persistence."""
        try:
            for page in self.pages:
                if page and not page.is_closed():
                    try:
                        await page.close()
                    except Exception as e:
                        logger.warning(f"Error closing page: {e}")
            
            self.pages = []
                
            if self.browser_initialized:
                logger.info("Keeping browser session alive")
            
            if self.playwright:
                logger.info("Playwright session remains active")
            
            logger.info("Tools cleaned up (browser session remains open for persistence)")
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
