#!/usr/bin/env python3
"""
Advanced Playwright Tools - 23 Additional Tools
Collection of advanced browser automation tools to complete the 51-tool comprehensive toolkit
"""
import asyncio
import json
import logging
import os
import time
from typing import Any, Dict, List, Optional, Union

from playwright.async_api import async_playwright, Browser, BrowserContext, Page, CDPSession, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger("mcp_tools")

class PlaywrightAdvancedTools:
    """Collection of 23 advanced Playwright browser automation tools."""
    def __init__(self, playwright_tools_instance=None):
        """Initialize with reference to main PlaywrightTools instance."""
        self.main_tools = playwright_tools_instance
        self.playwright = None
        self.browser = None
        self.context = None
        self.pages = []
        self.browser_initialized = False
        
        # Create a screenshots directory if it doesn't exist
        self.screenshot_dir = os.path.join(os.getcwd(), "screenshots")
        os.makedirs(self.screenshot_dir, exist_ok=True)
    
    async def _get_page(self, page_index: int = 0) -> Optional[Page]:
        """Get a page by index from main tools or create one."""
        if self.main_tools and hasattr(self.main_tools, '_get_page'):
            return await self.main_tools._get_page(page_index)
        
        # Fallback implementation
        if page_index < 0:
            return None
        
        if not self.browser_initialized:
            await self._ensure_browser_initialized()
        
        while len(self.pages) <= page_index:
            new_page = await self.context.new_page()
            self.pages.append(new_page)
        
        return self.pages[page_index]
    
    async def _ensure_browser_initialized(self):
        """Ensure browser is initialized."""
        if self.main_tools and hasattr(self.main_tools, '_ensure_browser_initialized'):
            await self.main_tools._ensure_browser_initialized()
            self.browser = self.main_tools.browser
            self.context = self.main_tools.context
            self.pages = self.main_tools.pages
            self.browser_initialized = True
            return
        
        # Fallback implementation
        if not self.browser_initialized:
            if not self.playwright:
                self.playwright = await async_playwright().start()
            
            self.browser = await self.playwright.chromium.launch(headless=False)
            viewport_size = {"width": 1425, "height": 776}
            self.context = await self.browser.new_context(
                viewport=viewport_size,
                user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            )
            self.browser_initialized = True

    # === Advanced Locator Methods (6 tools) ===

    async def playwright_css_locator(self, css_selector: str, page_index: int = 0) -> Dict[str, Any]:
        """Enhanced CSS selector with Playwright features."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.locator(css_selector)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with CSS selector: {css_selector}"
                }
            
            elements = []
            for i in range(min(count, 10)):
                element = locator.nth(i)
                try:
                    text = await element.text_content()
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "text": text[:100] if text else "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "text": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with CSS selector: {css_selector}",
                "count": count,
                "elements": elements,
                "selector": css_selector
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_nth_element(self, selector: str, index: int, page_index: int = 0) -> Dict[str, Any]:
        """Target specific element by index."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.locator(selector)
            count = await locator.count()
            
            if index >= count or index < 0:
                return {
                    "status": "error",
                    "message": f"Index {index} out of range. Found {count} elements."
                }
            
            nth_element = locator.nth(index)
            text = await nth_element.text_content()
            is_visible = await nth_element.is_visible()
            
            return {
                "status": "success",
                "message": f"Found element at index {index}",
                "index": index,
                "text": text[:200] if text else "",
                "is_visible": is_visible,
                "total_count": count
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_parent_element(self, selector: str, page_index: int = 0) -> Dict[str, Any]:
        """Target parent of matched element."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            element = page.locator(selector).first
            parent = element.locator("..")
            
            parent_tag = await parent.evaluate("el => el.tagName.toLowerCase()")
            parent_text = await parent.text_content()
            parent_classes = await parent.get_attribute("class")
            parent_id = await parent.get_attribute("id")
            
            return {
                "status": "success",
                "message": f"Found parent element of {selector}",
                "parent_tag": parent_tag,
                "parent_text": parent_text[:200] if parent_text else "",
                "parent_classes": parent_classes or "",
                "parent_id": parent_id or ""
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_xpath_locator(self, xpath: str, page_index: int = 0) -> Dict[str, Any]:
        """XPath selector support."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.locator(f"xpath={xpath}")
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with XPath: {xpath}"
                }
            
            elements = []
            for i in range(min(count, 5)):
                element = locator.nth(i)
                try:
                    text = await element.text_content()
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "text": text[:100] if text else "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "text": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with XPath: {xpath}",
                "count": count,
                "elements": elements,
                "xpath": xpath
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_label_to_control(self, label_text: str, page_index: int = 0) -> Dict[str, Any]:
        """Find form controls by label text."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            label_locator = page.locator(f"label:has-text('{label_text}')")
            label_count = await label_locator.count()
            
            if label_count == 0:
                return {
                    "status": "error",
                    "message": f"No label found with text: {label_text}"
                }
            
            label = label_locator.first
            for_attr = await label.get_attribute("for")
            
            if for_attr:
                control = page.locator(f"#{for_attr}")
            else:
                control = label.locator("input, select, textarea").first
            
            control_count = await control.count()
            if control_count == 0:
                return {
                    "status": "error",
                    "message": f"No control found for label: {label_text}"
                }
            
            control_tag = await control.evaluate("el => el.tagName.toLowerCase()")
            control_type = await control.get_attribute("type")
            control_name = await control.get_attribute("name")
            control_id = await control.get_attribute("id")
            
            return {
                "status": "success",
                "message": f"Found control for label: {label_text}",
                "label_text": label_text,
                "control_tag": control_tag,
                "control_type": control_type or "",
                "control_name": control_name or "",
                "control_id": control_id or ""
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_custom_user_agent(self, user_agent: str, page_index: int = 0) -> Dict[str, Any]:
        """Set custom user agent."""
        try:
            if self.context:
                new_context = await self.browser.new_context(
                    user_agent=user_agent,
                    viewport={"width": 1425, "height": 776}
                )
                
                await self.context.close()
                self.context = new_context
                
                new_page = await self.context.new_page()
                
                if page_index < len(self.pages):
                    if not self.pages[page_index].is_closed():
                        await self.pages[page_index].close()
                    self.pages[page_index] = new_page
                else:
                    self.pages.append(new_page)
                
                return {
                    "status": "success",
                    "message": f"User agent set to: {user_agent}",
                    "user_agent": user_agent,
                    "page_index": page_index
                }
            else:
                return {
                    "status": "error",
                    "message": "Browser context not initialized"
                }
                
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Accessibility Methods (7 tools) ===

    async def playwright_accessibility_snapshot(self, page_index: int = 0) -> Dict[str, Any]:
        """ARIA accessibility tree snapshot."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            accessibility_tree = await page.accessibility.snapshot()
            
            def process_node(node, depth=0):
                if not node:
                    return None
                
                processed = {
                    "role": node.get("role", ""),
                    "name": node.get("name", ""),
                    "description": node.get("description", ""),
                    "value": node.get("value", ""),
                    "depth": depth
                }
                
                if "children" in node and depth < 3:
                    processed["children"] = []
                    for child in node["children"][:10]:
                        child_processed = process_node(child, depth + 1)
                        if child_processed:
                            processed["children"].append(child_processed)
                
                return processed
            
            processed_tree = process_node(accessibility_tree) if accessibility_tree else None
            
            return {
                "status": "success",
                "message": "Accessibility tree snapshot captured",
                "accessibility_tree": processed_tree
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_find_by_role(self, role: str, name: str = None, page_index: int = 0) -> Dict[str, Any]:
        """Find elements by ARIA role."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            if name:
                locator = page.get_by_role(role, name=name)
            else:
                locator = page.get_by_role(role)
            
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with role: {role}" + (f" and name: {name}" if name else "")
                }
            
            elements = []
            for i in range(min(count, 10)):
                element = locator.nth(i)
                try:
                    text = await element.text_content()
                    is_visible = await element.is_visible()
                    aria_label = await element.get_attribute("aria-label")
                    elements.append({
                        "index": i,
                        "text": text[:100] if text else "",
                        "is_visible": is_visible,
                        "aria_label": aria_label or ""
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "text": "",
                        "is_visible": False,
                        "aria_label": ""
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with role: {role}" + (f" and name: {name}" if name else ""),
                "count": count,
                "elements": elements,
                "role": role,
                "name": name
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_find_by_role_in_accessibility_tree(self, role: str, page_index: int = 0) -> Dict[str, Any]:
        """Role-based search in accessibility tree."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            accessibility_tree = await page.accessibility.snapshot()
            
            def find_by_role_recursive(node, target_role, results=None, depth=0):
                if results is None:
                    results = []
                
                if not node or depth > 5:
                    return results
                
                if node.get("role") == target_role:
                    results.append({
                        "role": node.get("role", ""),
                        "name": node.get("name", ""),
                        "description": node.get("description", ""),
                        "value": node.get("value", ""),
                        "depth": depth
                    })
                
                if "children" in node:
                    for child in node["children"]:
                        find_by_role_recursive(child, target_role, results, depth + 1)
                
                return results
            
            matching_nodes = find_by_role_recursive(accessibility_tree, role) if accessibility_tree else []
            
            return {
                "status": "success",
                "message": f"Found {len(matching_nodes)} nodes with role: {role} in accessibility tree",
                "count": len(matching_nodes),
                "nodes": matching_nodes[:20],
                "role": role
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_locator_by_label(self, label: str, page_index: int = 0) -> Dict[str, Any]:
        """Find by associated label."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.get_by_label(label)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with label: {label}"
                }
            
            elements = []
            for i in range(min(count, 5)):
                element = locator.nth(i)
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    element_type = await element.get_attribute("type")
                    value = await element.input_value() if tag_name in ["input", "textarea"] else await element.text_content()
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "type": element_type or "",
                        "value": value[:100] if value else "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "type": "",
                        "value": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with label: {label}",
                "count": count,
                "elements": elements,
                "label": label
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_locator_by_placeholder(self, placeholder: str, page_index: int = 0) -> Dict[str, Any]:
        """Find by placeholder text."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.get_by_placeholder(placeholder)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with placeholder: {placeholder}"
                }
            
            elements = []
            for i in range(min(count, 5)):
                element = locator.nth(i)
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    element_type = await element.get_attribute("type")
                    value = await element.input_value()
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "type": element_type or "",
                        "value": value or "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "type": "",
                        "value": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with placeholder: {placeholder}",
                "count": count,
                "elements": elements,
                "placeholder": placeholder
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_locator_by_alt_text(self, alt_text: str, page_index: int = 0) -> Dict[str, Any]:
        """Find by alt text (images)."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.get_by_alt_text(alt_text)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with alt text: {alt_text}"
                }
            
            elements = []
            for i in range(min(count, 10)):
                element = locator.nth(i)
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    src = await element.get_attribute("src")
                    title = await element.get_attribute("title")
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "src": src or "",
                        "title": title or "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "src": "",
                        "title": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with alt text: {alt_text}",
                "count": count,
                "elements": elements,
                "alt_text": alt_text
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_locator_by_title(self, title: str, page_index: int = 0) -> Dict[str, Any]:
        """Find by title attribute."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            locator = page.get_by_title(title)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with title: {title}"
                }
            
            elements = []
            for i in range(min(count, 10)):
                element = locator.nth(i)
                try:
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    text = await element.text_content()
                    is_visible = await element.is_visible()
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "text": text[:100] if text else "",
                        "is_visible": is_visible
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "text": "",
                        "is_visible": False
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with title: {title}",
                "count": count,
                "elements": elements,
                "title": title
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === CSS & Text Selectors (2 tools) ===

    async def playwright_css_text_selector(self, css_selector: str, text_content: str, page_index: int = 0) -> Dict[str, Any]:
        """CSS with text matching capabilities."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            combined_selector = f"{css_selector}:has-text('{text_content}')"
            locator = page.locator(combined_selector)
            count = await locator.count()
            
            if count == 0:
                return {
                    "status": "error",
                    "message": f"No elements found with CSS selector '{css_selector}' containing text '{text_content}'"
                }
            
            elements = []
            for i in range(min(count, 10)):
                element = locator.nth(i)
                try:
                    full_text = await element.text_content()
                    is_visible = await element.is_visible()
                    tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                    elements.append({
                        "index": i,
                        "tag_name": tag_name,
                        "text": full_text[:200] if full_text else "",
                        "is_visible": is_visible,
                        "matched_text": text_content
                    })
                except Exception:
                    elements.append({
                        "index": i,
                        "tag_name": "unknown",
                        "text": "",
                        "is_visible": False,
                        "matched_text": text_content
                    })
            
            return {
                "status": "success",
                "message": f"Found {count} elements with CSS selector '{css_selector}' containing text '{text_content}'",
                "count": count,
                "elements": elements,
                "css_selector": css_selector,
                "text_content": text_content
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_css_visibility_selector(self, css_selector: str, visibility_state: str = "visible", page_index: int = 0) -> Dict[str, Any]:
        """CSS with visibility filtering."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            all_locator = page.locator(css_selector)
            all_count = await all_locator.count()
            
            filtered_elements = []
            for i in range(all_count):
                element = all_locator.nth(i)
                is_visible = await element.is_visible()
                
                if (visibility_state == "visible" and is_visible) or \
                   (visibility_state == "hidden" and not is_visible) or \
                   (visibility_state == "all"):
                    
                    try:
                        text = await element.text_content()
                        tag_name = await element.evaluate("el => el.tagName.toLowerCase()")
                        filtered_elements.append({
                            "index": len(filtered_elements),
                            "original_index": i,
                            "tag_name": tag_name,
                            "text": text[:100] if text else "",
                            "is_visible": is_visible
                        })
                    except Exception:
                        filtered_elements.append({
                            "index": len(filtered_elements),
                            "original_index": i,
                            "tag_name": "unknown",
                            "text": "",
                            "is_visible": is_visible
                        })
                
                if len(filtered_elements) >= 20:
                    break
            
            return {
                "status": "success",
                "message": f"Found {len(filtered_elements)} {visibility_state} elements with CSS selector: {css_selector}",
                "total_elements": all_count,
                "filtered_count": len(filtered_elements),
                "elements": filtered_elements,
                "css_selector": css_selector,
                "visibility_filter": visibility_state
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Enhanced Navigation (5 tools) ===

    async def playwright_navigate_and_wait_for_url(self, url: str, url_pattern: str, timeout_ms: int = 30000, page_index: int = 0) -> Dict[str, Any]:
        """Navigate with URL pattern waiting."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            async with page.expect_url(url_pattern, timeout=timeout_ms):
                await page.goto(url)
            
            final_url = page.url
            title = await page.title()
            
            return {
                "status": "success",
                "message": f"Navigated to {url} and URL matched pattern: {url_pattern}",
                "initial_url": url,
                "final_url": final_url,
                "url_pattern": url_pattern,
                "title": title
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_wait_for_navigation(self, timeout_ms: int = 30000, page_index: int = 0) -> Dict[str, Any]:
        """Wait for navigation after actions."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            async with page.expect_navigation(timeout=timeout_ms):
                pass
            
            final_url = page.url
            title = await page.title()
            
            return {
                "status": "success",
                "message": "Navigation completed",
                "final_url": final_url,
                "title": title
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_wait_for_load_state_multiple(self, load_states: List[str], timeout_ms: int = 30000, page_index: int = 0) -> Dict[str, Any]:
        """Wait for multiple load states."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            completed_states = []
            
            for state in load_states:
                try:
                    await page.wait_for_load_state(state, timeout=timeout_ms)
                    completed_states.append(state)
                except Exception as e:
                    print(f"Failed to wait for load state '{state}': {e}")
            
            return {
                "status": "success",
                "message": f"Completed {len(completed_states)} of {len(load_states)} load states",
                "requested_states": load_states,
                "completed_states": completed_states,
                "url": page.url
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_intercept_requests(self, url_pattern: str, page_index: int = 0) -> Dict[str, Any]:
        """Network request interception."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            intercepted_requests = []
            
            def handle_request(request):
                if url_pattern in request.url:
                    intercepted_requests.append({
                        "url": request.url,
                        "method": request.method,
                        "headers": dict(request.headers),
                        "timestamp": time.time()
                    })
            
            page.on("request", handle_request)
            
            return {
                "status": "success",
                "message": f"Started intercepting requests matching pattern: {url_pattern}",
                "url_pattern": url_pattern,
                "intercepted_count": 0
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_stop_intercepting_requests(self, page_index: int = 0) -> Dict[str, Any]:
        """Stop request interception."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            page.remove_all_listeners("request")
            
            return {
                "status": "success",
                "message": "Stopped intercepting requests"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # === Dialog Handling (3 tools) ===

    async def playwright_set_dialog_handler(self, dialog_type: str, action: str = "accept", prompt_text: str = "", page_index: int = 0) -> Dict[str, Any]:
        """Set persistent dialog handlers."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            handled_dialogs = []
            
            def handle_dialog(dialog):
                dialog_info = {
                    "type": dialog.type,
                    "message": dialog.message,
                    "default_value": dialog.default_value,
                    "timestamp": time.time()
                }
                
                if dialog_type == "all" or dialog.type == dialog_type:
                    if action == "accept":
                        if dialog.type == "prompt":
                            dialog.accept(prompt_text)
                        else:
                            dialog.accept()
                        dialog_info["action_taken"] = "accepted"
                        dialog_info["prompt_text"] = prompt_text if dialog.type == "prompt" else None
                    elif action == "dismiss":
                        dialog.dismiss()
                        dialog_info["action_taken"] = "dismissed"
                    
                    handled_dialogs.append(dialog_info)
            
            page.on("dialog", handle_dialog)
            
            return {
                "status": "success",
                "message": f"Set dialog handler for {dialog_type} dialogs with action: {action}",
                "dialog_type": dialog_type,
                "action": action,
                "prompt_text": prompt_text if dialog_type == "prompt" else None
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_remove_dialog_handler(self, page_index: int = 0) -> Dict[str, Any]:
        """Remove dialog handlers."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            page.remove_all_listeners("dialog")
            
            return {
                "status": "success",
                "message": "Removed all dialog handlers"
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def playwright_auto_handle_next_dialog(self, action: str = "accept", prompt_text: str = "", page_index: int = 0) -> Dict[str, Any]:
        """Handle next dialog automatically."""
        page = await self._get_page(page_index)
        if not page:
            return {"status": "error", "message": "Invalid page index"}
        
        try:
            dialog_handled = False
            dialog_info = {}
            
            def handle_next_dialog(dialog):
                nonlocal dialog_handled, dialog_info
                if not dialog_handled:
                    dialog_info = {
                        "type": dialog.type,
                        "message": dialog.message,
                        "default_value": dialog.default_value,
                        "timestamp": time.time()
                    }
                    
                    if action == "accept":
                        if dialog.type == "prompt":
                            dialog.accept(prompt_text)
                        else:
                            dialog.accept()
                        dialog_info["action_taken"] = "accepted"
                        dialog_info["prompt_text"] = prompt_text if dialog.type == "prompt" else None
                    elif action == "dismiss":
                        dialog.dismiss()
                        dialog_info["action_taken"] = "dismissed"
                    
                    dialog_handled = True
                    page.remove_listener("dialog", handle_next_dialog)
            
            page.on("dialog", handle_next_dialog)
            
            return {
                "status": "success",
                "message": f"Set up auto-handler for next dialog with action: {action}",
                "action": action,
                "prompt_text": prompt_text if action == "accept" else None
            }
            
        except Exception as e:
            return {"status": "error", "message": str(e)}
