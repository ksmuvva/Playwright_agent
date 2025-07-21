#!/usr/bin/env python3
"""
Proactive Cookie Learning - Intelligent cookie consent handling
Learns from successful cookie interactions and applies patterns automatically.
"""
import asyncio
import json
import logging
import sqlite3
import time
from typing import Any, Dict, List, Optional, Tuple
from urllib.parse import urlparse

from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError

# Configure logging
logger = logging.getLogger("cookie_learning")

class ProactiveCookieLearning:
    """Proactive cookie consent learning and handling system."""
    
    def __init__(self, db_conn: sqlite3.Connection):
        self.db_conn = db_conn
        self.cookie_patterns = {}
        self.domain_patterns = {}
        self._initialize_database()
        self._load_patterns()
    
    def _initialize_database(self):
        """Initialize cookie learning database tables."""
        try:
            # Cookie patterns table
            self.db_conn.execute('''
                CREATE TABLE IF NOT EXISTS cookie_patterns (
                    id INTEGER PRIMARY KEY,
                    domain TEXT,
                    selector_used TEXT,
                    action_type TEXT,
                    success_count INTEGER DEFAULT 0,
                    failure_count INTEGER DEFAULT 0,
                    last_used DATETIME,
                    effectiveness_score REAL DEFAULT 0.5,
                    pattern_data TEXT
                )
            ''')
            
            # Domain-specific cookie behaviors
            self.db_conn.execute('''
                CREATE TABLE IF NOT EXISTS domain_cookie_behaviors (
                    id INTEGER PRIMARY KEY,
                    domain TEXT,
                    behavior_type TEXT,
                    pattern_description TEXT,
                    success_rate REAL DEFAULT 0.5,
                    last_seen DATETIME,
                    usage_count INTEGER DEFAULT 0
                )
            ''')
            
            self.db_conn.commit()
            logger.info("Cookie learning database initialized")
            
        except Exception as e:
            logger.error(f"Failed to initialize cookie learning database: {e}")
    
    def _load_patterns(self):
        """Load existing cookie patterns from database."""
        try:
            cursor = self.db_conn.cursor()
            
            # Load cookie patterns
            cursor.execute("""
                SELECT domain, selector_used, action_type, effectiveness_score, pattern_data
                FROM cookie_patterns 
                WHERE effectiveness_score > 0.3
                ORDER BY effectiveness_score DESC
            """)
            
            for domain, selector, action_type, score, pattern_data in cursor.fetchall():
                if domain not in self.cookie_patterns:
                    self.cookie_patterns[domain] = []
                
                pattern = {
                    "selector": selector,
                    "action_type": action_type,
                    "effectiveness_score": score,
                    "pattern_data": json.loads(pattern_data) if pattern_data else {}
                }
                self.cookie_patterns[domain].append(pattern)
            
            # Load domain behaviors
            cursor.execute("""
                SELECT domain, behavior_type, pattern_description, success_rate
                FROM domain_cookie_behaviors
                WHERE success_rate > 0.3
                ORDER BY success_rate DESC
            """)
            
            for domain, behavior_type, description, success_rate in cursor.fetchall():
                if domain not in self.domain_patterns:
                    self.domain_patterns[domain] = []
                
                self.domain_patterns[domain].append({
                    "behavior_type": behavior_type,
                    "description": description,
                    "success_rate": success_rate
                })
            
            logger.info(f"Loaded {len(self.cookie_patterns)} cookie patterns for {len(self.domain_patterns)} domains")
            
        except Exception as e:
            logger.error(f"Failed to load cookie patterns: {e}")
    
    def get_domain_from_url(self, url: str) -> str:
        """Extract domain from URL."""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove www. prefix for pattern matching
            if domain.startswith('www.'):
                domain = domain[4:]
            return domain
        except Exception:
            return ""
    
    async def detect_cookie_consent(self, page: Page, url: str) -> Dict[str, Any]:
        """Detect if there's a cookie consent banner on the page."""
        domain = self.get_domain_from_url(url)
        
        try:
            # Common cookie consent selectors
            cookie_selectors = [
                # Generic selectors
                "[id*='cookie']",
                "[class*='cookie']",
                "[id*='consent']",
                "[class*='consent']",
                "[aria-label*='cookie' i]",
                "[aria-label*='consent' i]",
                
                # Common cookie banner frameworks
                "#cookieConsent",
                ".cookie-consent",
                ".cookie-banner",
                ".cookie-notice",
                ".gdpr-banner",
                ".privacy-banner",
                "#onetrust-banner-sdk",
                "#cookiescript_injected",
                ".cc-banner",
                ".cookielaw-banner",
                
                # Button-specific selectors
                "button:has-text('Accept')",
                "button:has-text('Accept All')",
                "button:has-text('Allow')",
                "button:has-text('I Accept')",
                "button:has-text('Agree')",
                "button:has-text('OK')",
                "a:has-text('Accept')",
                "a:has-text('Accept All')",
                
                # Domain-specific patterns if available
            ]
            
            # Add domain-specific patterns
            if domain in self.cookie_patterns:
                for pattern in self.cookie_patterns[domain]:
                    cookie_selectors.insert(0, pattern["selector"])  # Prioritize learned patterns
            
            detected_elements = []
            
            for selector in cookie_selectors:
                try:
                    elements = await page.locator(selector).all()
                    for element in elements:
                        is_visible = await element.is_visible()
                        if is_visible:
                            text_content = await element.text_content() or ""
                            bounding_box = await element.bounding_box()
                            
                            detected_elements.append({
                                "selector": selector,
                                "text": text_content[:100],
                                "is_visible": is_visible,
                                "bounding_box": bounding_box,
                                "element_type": await element.evaluate("el => el.tagName.toLowerCase()")
                            })
                            
                            # If we found a visible element, we likely have a cookie banner
                            if len(detected_elements) >= 3:  # Found enough evidence
                                break
                    
                    if len(detected_elements) >= 3:
                        break
                        
                except Exception as e:
                    logger.debug(f"Error checking selector {selector}: {e}")
                    continue
            
            has_cookie_banner = len(detected_elements) > 0
            
            return {
                "has_cookie_banner": has_cookie_banner,
                "detected_elements": detected_elements,
                "domain": domain,
                "confidence": min(len(detected_elements) / 3.0, 1.0)
            }
            
        except Exception as e:
            logger.error(f"Error detecting cookie consent: {e}")
            return {
                "has_cookie_banner": False,
                "detected_elements": [],
                "domain": domain,
                "confidence": 0.0,
                "error": str(e)
            }
    
    async def handle_cookie_consent(self, page: Page, url: str, action: str = "accept") -> Tuple[bool, str]:
        """Handle cookie consent using learned patterns and fallbacks."""
        domain = self.get_domain_from_url(url)
        
        try:
            # First, detect if there's a cookie banner
            detection_result = await self.detect_cookie_consent(page, url)
            
            if not detection_result["has_cookie_banner"]:
                return True, "no_banner_detected"
            
            print(f"🍪 Cookie banner detected on {domain}, attempting to handle...")
            
            # Try learned patterns first
            if domain in self.cookie_patterns:
                for pattern in sorted(self.cookie_patterns[domain], 
                                    key=lambda x: x["effectiveness_score"], reverse=True):
                    try:
                        selector = pattern["selector"]
                        action_type = pattern["action_type"]
                        
                        print(f"🍪 Trying learned pattern: {selector} ({action_type})")
                        
                        element = await page.locator(selector).first
                        if await element.is_visible(timeout=2000):
                            if action_type == "click":
                                await element.click()
                            elif action_type == "hover_click":
                                await element.hover()
                                await asyncio.sleep(0.5)
                                await element.click()
                            
                            # Record success
                            await self._record_pattern_usage(domain, selector, action_type, True)
                            
                            print(f"✅ Successfully handled cookies using learned pattern")
                            return True, f"learned_pattern_{action_type}"
                            
                    except Exception as e:
                        logger.debug(f"Learned pattern failed: {e}")
                        # Record failure
                        await self._record_pattern_usage(domain, selector, action_type, False)
                        continue
            
            # Fallback to common patterns
            fallback_selectors = [
                # High-priority accept buttons
                "button:has-text('Accept All')",
                "button:has-text('Accept all')",
                "button:has-text('Accept')",
                "a:has-text('Accept All')",
                "a:has-text('Accept')",
                
                # ID and class-based selectors
                "#accept-cookies",
                "#acceptCookies",
                ".accept-cookies",
                ".accept-all",
                ".cookie-accept",
                
                # ARIA-based selectors
                "[aria-label*='Accept' i]",
                "[aria-label*='Allow' i]",
                
                # Common framework selectors
                "#onetrust-accept-btn-handler",
                ".ot-sdk-show-settings",
                "#cookiescript_accept",
                ".cc-allow",
                ".cookielaw-accept",
                
                # Generic button patterns
                "button[class*='accept']",
                "button[id*='accept']",
                "input[value*='Accept']",
                
                # Text-based fallbacks
                "button:has-text('Allow')",
                "button:has-text('I Accept')",
                "button:has-text('Agree')",
                "button:has-text('OK')",
                "button:has-text('Got it')",
                "a:has-text('I Accept')",
                "a:has-text('Agree')"
            ]
            
            for selector in fallback_selectors:
                try:
                    print(f"🍪 Trying fallback selector: {selector}")
                    
                    element = await page.locator(selector).first
                    if await element.is_visible(timeout=1000):
                        await element.click()
                        
                        # Learn this successful pattern
                        await self._learn_new_pattern(domain, selector, "click", True)
                        
                        print(f"✅ Successfully handled cookies using fallback: {selector}")
                        return True, f"fallback_click"
                        
                except Exception as e:
                    logger.debug(f"Fallback selector failed: {e}")
                    continue
            
            # If all else fails, try to find any clickable element with cookie-related text
            try:
                print("🍪 Trying text-based detection as last resort...")
                
                cookie_keywords = ["accept", "allow", "agree", "ok", "got it", "continue"]
                
                for keyword in cookie_keywords:
                    try:
                        # Look for any clickable element containing the keyword
                        elements = await page.locator(f"button, a, [role='button']").all()
                        
                        for element in elements:
                            try:
                                text = await element.text_content()
                                if text and keyword.lower() in text.lower():
                                    if await element.is_visible():
                                        await element.click()
                                        
                                        # Learn this pattern
                                        element_selector = await element.evaluate("""
                                            el => {
                                                if (el.id) return '#' + el.id;
                                                if (el.className) return '.' + el.className.split(' ')[0];
                                                return el.tagName.toLowerCase();
                                            }
                                        """)
                                        
                                        await self._learn_new_pattern(domain, element_selector, "click", True)
                                        
                                        print(f"✅ Successfully handled cookies using text detection: {keyword}")
                                        return True, f"text_detection_{keyword}"
                                        
                            except Exception:
                                continue
                                
                    except Exception:
                        continue
                        
            except Exception as e:
                logger.debug(f"Text-based detection failed: {e}")
            
            print("⚠️ Could not handle cookie consent automatically")
            return False, "no_suitable_element_found"
            
        except Exception as e:
            logger.error(f"Error handling cookie consent: {e}")
            return False, f"error_{str(e)}"
    
    async def _record_pattern_usage(self, domain: str, selector: str, action_type: str, success: bool):
        """Record the usage of a cookie pattern."""
        try:
            cursor = self.db_conn.cursor()
            
            # Check if pattern exists
            cursor.execute("""
                SELECT id, success_count, failure_count FROM cookie_patterns
                WHERE domain = ? AND selector_used = ? AND action_type = ?
            """, (domain, selector, action_type))
            
            result = cursor.fetchone()
            
            if result:
                pattern_id, success_count, failure_count = result
                
                if success:
                    success_count += 1
                else:
                    failure_count += 1
                
                total_uses = success_count + failure_count
                effectiveness_score = success_count / total_uses if total_uses > 0 else 0.5
                
                cursor.execute("""
                    UPDATE cookie_patterns 
                    SET success_count = ?, failure_count = ?, effectiveness_score = ?, last_used = CURRENT_TIMESTAMP
                    WHERE id = ?
                """, (success_count, failure_count, effectiveness_score, pattern_id))
                
            self.db_conn.commit()
            
        except Exception as e:
            logger.error(f"Error recording pattern usage: {e}")
    
    async def _learn_new_pattern(self, domain: str, selector: str, action_type: str, success: bool):
        """Learn a new cookie handling pattern."""
        try:
            cursor = self.db_conn.cursor()
            
            # Check if this pattern already exists
            cursor.execute("""
                SELECT id FROM cookie_patterns
                WHERE domain = ? AND selector_used = ? AND action_type = ?
            """, (domain, selector, action_type))
            
            if cursor.fetchone():
                # Pattern exists, just record usage
                await self._record_pattern_usage(domain, selector, action_type, success)
                return
            
            # Create new pattern
            initial_score = 0.8 if success else 0.2
            success_count = 1 if success else 0
            failure_count = 0 if success else 1
            
            pattern_data = {
                "discovered_at": time.time(),
                "discovery_method": "automatic_learning",
                "selector_type": self._classify_selector(selector)
            }
            
            cursor.execute("""
                INSERT INTO cookie_patterns 
                (domain, selector_used, action_type, success_count, failure_count, 
                 effectiveness_score, last_used, pattern_data)
                VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, ?)
            """, (domain, selector, action_type, success_count, failure_count, 
                  initial_score, json.dumps(pattern_data)))
            
            self.db_conn.commit()
            
            # Update in-memory patterns
            if domain not in self.cookie_patterns:
                self.cookie_patterns[domain] = []
            
            self.cookie_patterns[domain].append({
                "selector": selector,
                "action_type": action_type,
                "effectiveness_score": initial_score,
                "pattern_data": pattern_data
            })
            
            logger.info(f"Learned new cookie pattern for {domain}: {selector} ({action_type})")
            
        except Exception as e:
            logger.error(f"Error learning new pattern: {e}")
    
    def _classify_selector(self, selector: str) -> str:
        """Classify the type of selector for pattern analysis."""
        if selector.startswith('#'):
            return "id"
        elif selector.startswith('.'):
            return "class"
        elif ':has-text(' in selector:
            return "text_based"
        elif '[aria-label' in selector:
            return "aria_label"
        elif selector.startswith('button'):
            return "button_tag"
        elif selector.startswith('a'):
            return "link_tag"
        else:
            return "complex"
    
    def get_domain_statistics(self, domain: str) -> Dict[str, Any]:
        """Get statistics for cookie handling on a specific domain."""
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(*) as pattern_count,
                    AVG(effectiveness_score) as avg_effectiveness,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures
                FROM cookie_patterns
                WHERE domain = ?
            """, (domain,))
            
            result = cursor.fetchone()
            
            if result:
                pattern_count, avg_effectiveness, total_successes, total_failures = result
                total_attempts = (total_successes or 0) + (total_failures or 0)
                
                return {
                    "domain": domain,
                    "pattern_count": pattern_count or 0,
                    "average_effectiveness": avg_effectiveness or 0.0,
                    "total_successes": total_successes or 0,
                    "total_failures": total_failures or 0,
                    "total_attempts": total_attempts,
                    "success_rate": (total_successes / total_attempts) if total_attempts > 0 else 0.0
                }
            else:
                return {
                    "domain": domain,
                    "pattern_count": 0,
                    "average_effectiveness": 0.0,
                    "total_successes": 0,
                    "total_failures": 0,
                    "total_attempts": 0,
                    "success_rate": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting domain statistics: {e}")
            return {"error": str(e)}
    
    def get_global_statistics(self) -> Dict[str, Any]:
        """Get global cookie handling statistics."""
        try:
            cursor = self.db_conn.cursor()
            
            cursor.execute("""
                SELECT 
                    COUNT(DISTINCT domain) as domains_learned,
                    COUNT(*) as total_patterns,
                    AVG(effectiveness_score) as avg_effectiveness,
                    SUM(success_count) as total_successes,
                    SUM(failure_count) as total_failures
                FROM cookie_patterns
            """)
            
            result = cursor.fetchone()
            
            if result:
                domains, patterns, avg_eff, successes, failures = result
                total_attempts = (successes or 0) + (failures or 0)
                
                return {
                    "domains_learned": domains or 0,
                    "total_patterns": patterns or 0,
                    "average_effectiveness": avg_eff or 0.0,
                    "total_successes": successes or 0,
                    "total_failures": failures or 0,
                    "total_attempts": total_attempts,
                    "global_success_rate": (successes / total_attempts) if total_attempts > 0 else 0.0
                }
            else:
                return {
                    "domains_learned": 0,
                    "total_patterns": 0,
                    "average_effectiveness": 0.0,
                    "total_successes": 0,
                    "total_failures": 0,
                    "total_attempts": 0,
                    "global_success_rate": 0.0
                }
                
        except Exception as e:
            logger.error(f"Error getting global statistics: {e}")
            return {"error": str(e)}


# Helper function for integration with main tools
async def auto_handle_cookies(page: Page, url: str, cookie_learning: ProactiveCookieLearning = None) -> Tuple[bool, str]:
    """Auto-handle cookies using the proactive learning system."""
    if cookie_learning is None:
        # Fallback to basic cookie handling if no learning system available
        return await _basic_cookie_handling(page, url)
    
    return await cookie_learning.handle_cookie_consent(page, url)


async def _basic_cookie_handling(page: Page, url: str) -> Tuple[bool, str]:
    """Basic cookie handling without learning."""
    try:
        # Simple fallback selectors
        basic_selectors = [
            "button:has-text('Accept')",
            "button:has-text('Accept All')",
            "#accept-cookies",
            ".cookie-accept",
            "[aria-label*='Accept']"
        ]
        
        for selector in basic_selectors:
            try:
                element = await page.locator(selector).first
                if await element.is_visible(timeout=2000):
                    await element.click()
                    return True, "basic_fallback"
            except Exception:
                continue
        
        return False, "no_basic_pattern_found"
        
    except Exception as e:
        return False, f"basic_error_{str(e)}"


def add_proactive_cookie_step(task_info: Dict[str, Any], cookie_learning: ProactiveCookieLearning) -> Dict[str, Any]:
    """Add a proactive cookie handling step to task execution steps."""
    try:
        # Check if we already have a cookie step
        has_cookie_step = any(
            "cookie" in step.get("step_description", "").lower() 
            for step in task_info.get("execution_steps", [])
        )
        
        if has_cookie_step:
            return task_info  # Already has cookie handling
        
        # Check if we have a navigation step
        navigation_steps = [
            step for step in task_info.get("execution_steps", [])
            if step.get("tool") == "playwright_navigate"
        ]
        
        if navigation_steps:
            # Add cookie handling step after navigation
            cookie_step = {
                "step_description": "Proactively handle cookie consent if present",
                "tool": "playwright_smart_click",
                "parameters": {"text": "Accept", "element_type": "button"},
                "is_proactive_cookie_step": True
            }
            
            # Insert after the first navigation step
            insert_index = task_info["execution_steps"].index(navigation_steps[0]) + 1
            task_info["execution_steps"].insert(insert_index, cookie_step)
            
            task_info["parsing_debug"].append("🍪 Added proactive cookie handling step")
        
        return task_info
        
    except Exception as e:
        logger.error(f"Error adding proactive cookie step: {e}")
        return task_info
