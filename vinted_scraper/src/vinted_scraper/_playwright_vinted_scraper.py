"""
Playwright-based Vinted scraper with maximum stealth and human-like behavior
Drop-in replacement for the HTTP-based scraper
"""
import asyncio
import json
import logging
import re
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, urlparse, parse_qs

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError
except ImportError:
    Page = None
    PlaywrightTimeoutError = Exception

from ._browser_manager import BrowserManager
from ._error_handling import (
    with_retry, handle_scraping_error, is_scraping_blocked,
    BlockedError, CaptchaError, RateLimitError, RetryableError
)

logger = logging.getLogger(__name__)


class PlaywrightVintedScraper:
    """
    Playwright-based Vinted scraper with identical interface to VintedScraper
    Provides maximum stealth and human-like behavior to avoid detection
    """
    
    def __init__(
        self, 
        baseurl: str,
        session_cookie: Optional[str] = None,
        user_agent: Optional[str] = None,
        config: Optional[Dict] = None
    ):
        self.baseurl = baseurl.rstrip('/')
        self.session_cookie = session_cookie
        self.user_agent = user_agent
        self.config = config or {}
        
        # Browser manager for stealth browsing
        self.browser_manager = BrowserManager(
            headless=self.config.get('headless', True),
            slowmo=self.config.get('slowmo', 100)
        )
        
        # Cache for session management
        self._session_established = False
        
        logger.info(f"🎭 PlaywrightVintedScraper initialized for {baseurl}")
    
    def __enter__(self):
        """Sync context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Sync context manager exit"""
        asyncio.run(self.close())
    
    async def close(self):
        """Close browser and cleanup resources"""
        await self.browser_manager.close()
    
    def search(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search for items on Vinted - sync interface matching original scraper
        
        :param params: Dictionary with query parameters (search_text, etc.)
        :return: Dict containing JSON response with search results
        """
        # Check if we're in blocked state
        if is_scraping_blocked():
            raise BlockedError("Scraping is currently blocked due to previous errors")
        
        return asyncio.run(self._search_async(params))
    
    def item(self, item_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retrieve details of a specific item - sync interface matching original
        
        :param item_id: The unique identifier of the item
        :param params: Optional query parameters
        :return: Dict containing JSON response with item details
        """
        # Check if we're in blocked state
        if is_scraping_blocked():
            raise BlockedError("Scraping is currently blocked due to previous errors")
        
        return asyncio.run(self._item_async(item_id, params))
    
    @with_retry(max_retries=3, base_delay=2.0, max_delay=30.0)
    async def _search_async(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Async implementation of search with stealth behavior"""
        try:
            await self.browser_manager.start()
            
            async with self.browser_manager.new_page() as page:
                # Establish session if needed
                await self._ensure_session(page)
                
                # Build search URL
                search_url = await self._build_search_url(params)
                
                logger.info(f"🔍 Searching Vinted: {search_url}")
                
                # Navigate with human-like behavior
                await self._navigate_with_stealth(page, search_url)
                
                # Extract search results
                results = await self._extract_search_results(page)
                
                logger.info(f"✅ Found {len(results.get('items', []))} items")
                return results
                
        except Exception as e:
            logger.error(f"❌ Search failed: {e}")
            classified_error = handle_scraping_error(e, "search")
            raise classified_error from e
    
    @with_retry(max_retries=3, base_delay=2.0, max_delay=30.0)
    async def _item_async(self, item_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Async implementation of item details retrieval"""
        try:
            await self.browser_manager.start()
            
            async with self.browser_manager.new_page() as page:
                # Establish session if needed
                await self._ensure_session(page)
                
                # Build item URL
                item_url = f"{self.baseurl}/items/{item_id}"
                if params:
                    item_url += f"?{urlencode(params)}"
                
                logger.info(f"🔍 Fetching item: {item_url}")
                
                # Navigate with human-like behavior
                await self._navigate_with_stealth(page, item_url)
                
                # Extract item data
                item_data = await self._extract_item_data(page)
                
                logger.info(f"✅ Retrieved item {item_id}")
                return item_data
                
        except Exception as e:
            logger.error(f"❌ Item fetch failed: {e}")
            classified_error = handle_scraping_error(e, "item_fetch")
            raise classified_error from e
    
    async def _ensure_session(self, page: Page):
        """Ensure we have a valid session with Vinted"""
        if self._session_established:
            return
        
        logger.info("🔐 Establishing session with Vinted...")
        
        # Visit home page to establish session
        await self._navigate_with_stealth(page, self.baseurl)
        
        # Add some realistic browsing behavior
        await self.browser_manager.random_delay(1, 3)
        await self.browser_manager.random_mouse_movement(page)
        
        # Check if we're blocked or have captcha
        await self._check_for_blocks(page)
        
        self._session_established = True
        logger.info("✅ Session established successfully")
    
    async def _build_search_url(self, params: Optional[Dict] = None) -> str:
        """Build search URL with parameters"""
        search_url = f"{self.baseurl}/catalog/items"
        
        if params:
            # Clean and validate parameters
            clean_params = {}
            for key, value in params.items():
                if value is not None and value != '':
                    clean_params[key] = str(value)
            
            if clean_params:
                search_url += f"?{urlencode(clean_params)}"
        
        return search_url
    
    async def _navigate_with_stealth(self, page: Page, url: str):
        """Navigate to URL with maximum stealth and human-like behavior"""
        try:
            # Random delay before navigation
            await self.browser_manager.random_delay(1, 3)
            
            # Navigate to page
            logger.debug(f"🧭 Navigating to: {url}")
            response = await page.goto(
                url,
                wait_until='networkidle',
                timeout=30000
            )
            
            if response and response.status >= 400:
                raise RuntimeError(f"HTTP {response.status}: {response.status_text}")
            
            # Add human-like behavior after page load
            await self.browser_manager.random_delay(2, 4)
            
            # Random mouse movement
            await self.browser_manager.random_mouse_movement(page)
            
            # Occasionally scroll to simulate reading
            if asyncio.get_event_loop().time() % 3 == 0:  # 33% chance
                await self.browser_manager.human_like_scroll(page, 200)
            
            logger.debug("✅ Navigation completed with stealth behavior")
            
        except PlaywrightTimeoutError:
            raise RuntimeError("Navigation timeout - possible blocking or slow response")
        except Exception as e:
            raise RuntimeError(f"Navigation failed: {e}") from e
    
    async def _check_for_blocks(self, page: Page):
        """Check if we're being blocked or facing captcha"""
        try:
            # Check for common blocking indicators
            title = await page.title()
            url = page.url
            
            blocking_indicators = [
                'blocked', 'captcha', 'bot', 'automated', 'suspicious', 
                'access denied', 'forbidden', '403', '429'
            ]
            
            page_content = (title + url).lower()
            for indicator in blocking_indicators:
                if indicator in page_content:
                    logger.warning(f"🚫 Blocking detected: {indicator} in page content")
                    raise RuntimeError(f"Access blocked: {indicator} detected")
            
            # Check for CAPTCHA elements
            captcha_selectors = [
                '[class*="captcha"]',
                '[class*="recaptcha"]', 
                '[id*="captcha"]',
                'iframe[src*="captcha"]',
                'iframe[src*="recaptcha"]'
            ]
            
            for selector in captcha_selectors:
                if await page.query_selector(selector):
                    logger.warning("🚫 CAPTCHA detected on page")
                    raise RuntimeError("CAPTCHA challenge detected")
            
        except Exception as e:
            if "blocked" in str(e) or "captcha" in str(e).lower():
                raise
            logger.debug(f"Block check completed: {e}")
    
    async def _extract_search_results(self, page: Page) -> Dict[str, Any]:
        """Extract search results from the page"""
        try:
            # Wait for results to load
            await page.wait_for_selector('[data-testid="catalog-item"]', timeout=10000)
            
            # Look for JSON data in script tags (common pattern)
            json_data = await self._extract_json_from_scripts(page)
            if json_data and 'items' in json_data:
                return json_data
            
            # Fallback: extract from DOM elements
            return await self._extract_search_results_from_dom(page)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract search results: {e}")
            return {'items': [], 'search_tracking_id': None}
    
    async def _extract_item_data(self, page: Page) -> Dict[str, Any]:
        """Extract item data from item detail page"""
        try:
            # Wait for item content to load
            await page.wait_for_selector('[data-testid="item-details"]', timeout=10000)
            
            # Look for JSON data in script tags
            json_data = await self._extract_json_from_scripts(page)
            if json_data and 'item' in json_data:
                return json_data
            
            # Fallback: extract from DOM
            return await self._extract_item_data_from_dom(page)
            
        except Exception as e:
            logger.warning(f"⚠️ Could not extract item data: {e}")
            return {'item': {}}
    
    async def _extract_json_from_scripts(self, page: Page) -> Optional[Dict[str, Any]]:
        """Extract JSON data from script tags"""
        try:
            # Look for JSON data in script tags
            scripts = await page.query_selector_all('script')
            
            for script in scripts:
                content = await script.inner_text()
                
                # Look for patterns that might contain item data
                json_patterns = [
                    r'window\.__INITIAL_STATE__\s*=\s*({.*?});',
                    r'window\.__CATALOG_ITEMS__\s*=\s*({.*?});',
                    r'window\.__ITEM_DATA__\s*=\s*({.*?});',
                    r'"items"\s*:\s*\[.*?\]',
                    r'"pagination"\s*:\s*{.*?}'
                ]
                
                for pattern in json_patterns:
                    matches = re.findall(pattern, content, re.DOTALL)
                    if matches:
                        try:
                            # Try to parse as JSON
                            data = json.loads(matches[0])
                            if isinstance(data, dict) and ('items' in data or 'item' in data):
                                logger.debug("✅ Found JSON data in script tag")
                                return data
                        except json.JSONDecodeError:
                            continue
            
            return None
            
        except Exception as e:
            logger.debug(f"Could not extract JSON from scripts: {e}")
            return None
    
    async def _extract_search_results_from_dom(self, page: Page) -> Dict[str, Any]:
        """Fallback: Extract search results from DOM elements"""
        try:
            items = []
            
            # Find item containers
            item_elements = await page.query_selector_all('[data-testid="catalog-item"]')
            
            for item_el in item_elements:
                try:
                    item_data = {}
                    
                    # Extract basic item info from DOM
                    title_el = await item_el.query_selector('[data-testid="item-title"]')
                    if title_el:
                        item_data['title'] = await title_el.inner_text()
                    
                    price_el = await item_el.query_selector('[data-testid="item-price"]')
                    if price_el:
                        price_text = await price_el.inner_text()
                        price_match = re.search(r'€([\d,\.]+)', price_text)
                        if price_match:
                            item_data['price'] = {'amount': price_match.group(1).replace(',', '.')}
                    
                    # Extract item ID from URL
                    link_el = await item_el.query_selector('a[href*="/items/"]')
                    if link_el:
                        href = await link_el.get_attribute('href')
                        id_match = re.search(r'/items/(\d+)', href)
                        if id_match:
                            item_data['id'] = int(id_match.group(1))
                            item_data['url'] = f"{self.baseurl}{href}"
                    
                    if item_data.get('id'):
                        items.append(item_data)
                        
                except Exception as e:
                    logger.debug(f"Could not extract item data: {e}")
                    continue
            
            return {
                'items': items,
                'search_tracking_id': f"dom_extraction_{int(time.time())}"
            }
            
        except Exception as e:
            logger.warning(f"DOM extraction failed: {e}")
            return {'items': []}
    
    async def _extract_item_data_from_dom(self, page: Page) -> Dict[str, Any]:
        """Fallback: Extract item data from DOM elements"""
        try:
            item_data = {}
            
            # Extract title
            title_el = await page.query_selector('h1[data-testid="item-title"]')
            if title_el:
                item_data['title'] = await title_el.inner_text()
            
            # Extract price
            price_el = await page.query_selector('[data-testid="item-price"]')
            if price_el:
                price_text = await price_el.inner_text()
                price_match = re.search(r'€([\d,\.]+)', price_text)
                if price_match:
                    item_data['price'] = {'amount': price_match.group(1).replace(',', '.')}
            
            # Extract description
            desc_el = await page.query_selector('[data-testid="item-description"]')
            if desc_el:
                item_data['description'] = await desc_el.inner_text()
            
            return {'item': item_data}
            
        except Exception as e:
            logger.warning(f"DOM item extraction failed: {e}")
            return {'item': {}}