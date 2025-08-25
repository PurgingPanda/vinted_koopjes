"""
Network interception-based Vinted scraper with maximum stealth
Intercepts actual API calls made by Vinted's frontend for perfect data extraction
"""
import asyncio
import json
import logging
import random
import time
from typing import Dict, Any, Optional, List
from urllib.parse import urlencode, parse_qs, urlparse

try:
    from playwright.async_api import Page, TimeoutError as PlaywrightTimeoutError, Response
except ImportError:
    Page = None
    PlaywrightTimeoutError = Exception
    Response = None

from ._browser_manager import BrowserManager
from ._error_handling import (
    with_retry, handle_scraping_error, is_scraping_blocked,
    BlockedError, CaptchaError, RateLimitError, RetryableError
)

logger = logging.getLogger(__name__)


class NetworkInterceptionScraper:
    """
    Network interception-based Vinted scraper with maximum stealth
    Navigates to actual pages and intercepts the API calls that Vinted makes naturally
    """
    
    def __init__(
        self, 
        baseurl: str,
        session_cookie: Optional[str] = None,  # Ignored - cookies obtained naturally
        user_agent: Optional[str] = None,      # Ignored - browser handles this
        config: Optional[Dict] = None
    ):
        self.baseurl = baseurl.rstrip('/')
        # Deliberately ignore session_cookie and user_agent for maximum stealth
        # The browser will handle these naturally like a real user
        self.config = config or {}
        
        # Browser manager for maximum stealth
        self.browser_manager = BrowserManager(
            headless=self.config.get('headless', True),
            slowmo=self.config.get('slowmo', 150)  # Slightly slower for maximum stealth
        )
        
        # Network interception state
        self._intercepted_data = None
        self._interception_complete = False
        self._api_call_detected = False
        
        logger.info(f"🌐 NetworkInterceptionScraper initialized for {baseurl} (cookies obtained naturally)")
    
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
        Search for items using network interception - sync interface
        
        :param params: Dictionary with query parameters (search_text, etc.)
        :return: Dict containing intercepted JSON response
        """
        # Check if we're in blocked state
        if is_scraping_blocked():
            raise BlockedError("Scraping is currently blocked due to previous errors")
        
        return asyncio.run(self._search_async(params))
    
    def item(self, item_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retrieve item details using network interception - sync interface
        
        :param item_id: The unique identifier of the item
        :param params: Optional query parameters
        :return: Dict containing intercepted JSON response
        """
        # Check if we're in blocked state
        if is_scraping_blocked():
            raise BlockedError("Scraping is currently blocked due to previous errors")
        
        return asyncio.run(self._item_async(item_id, params))
    
    @with_retry(max_retries=3, base_delay=3.0, max_delay=45.0)
    async def _search_async(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Async implementation of search with network interception"""
        try:
            await self.browser_manager.start()
            
            async with self.browser_manager.new_page() as page:
                # Set up network interception
                await self._setup_network_interception(page, 'search')
                
                # Navigate to search page with maximum stealth
                search_url = await self._build_frontend_search_url(params)
                logger.info(f"🎯 NETWORK SCRAPER: Starting navigation to search page")
                logger.info(f"🌐 TARGET URL: {search_url}")
                
                # Perform stealth navigation and interaction
                await self._navigate_with_maximum_stealth(page, search_url)
                
                # Log current page URL after navigation
                current_url = page.url
                logger.info(f"📍 Current page URL after navigation: {current_url}")
                
                # Wait for and capture API calls
                intercepted_data = await self._wait_for_api_interception(page)
                
                if intercepted_data:
                    logger.info(f"✅ Successfully intercepted search data: {len(intercepted_data.get('items', []))} items")
                    return intercepted_data
                else:
                    logger.warning("⚠️ No API calls intercepted - returning empty results")
                    return {'items': []}
                
        except Exception as e:
            logger.error(f"❌ Network interception search failed: {e}")
            classified_error = handle_scraping_error(e, "network_search")
            raise classified_error from e
    
    @with_retry(max_retries=3, base_delay=3.0, max_delay=45.0)
    async def _item_async(self, item_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Async implementation of item details with network interception"""
        try:
            await self.browser_manager.start()
            
            async with self.browser_manager.new_page() as page:
                # Set up network interception for item calls
                await self._setup_network_interception(page, 'item')
                
                # Navigate to item page
                item_url = f"{self.baseurl}/items/{item_id}"
                logger.info(f"🎯 NETWORK SCRAPER: Starting navigation to item page")
                logger.info(f"🌐 TARGET URL: {item_url}")
                
                # Perform stealth navigation
                await self._navigate_with_maximum_stealth(page, item_url)
                
                # Log current page URL after navigation
                current_url = page.url
                logger.info(f"📍 Current page URL after item navigation: {current_url}")
                
                # Wait for and capture API calls
                intercepted_data = await self._wait_for_api_interception(page)
                
                if intercepted_data:
                    logger.info(f"✅ Successfully intercepted item data for {item_id}")
                    return intercepted_data
                else:
                    logger.warning(f"⚠️ No API calls intercepted for item {item_id} - returning empty results")
                    return {'item': {}}
                
        except Exception as e:
            logger.error(f"❌ Network interception item fetch failed: {e}")
            classified_error = handle_scraping_error(e, "network_item")
            raise classified_error from e
    
    async def _setup_network_interception(self, page: Page, operation_type: str):
        """Set up network request/response interception for Vinted API calls"""
        self._intercepted_data = None
        self._interception_complete = False
        self._api_call_detected = False
        
        async def handle_response(response: Response):
            """Handle network responses and intercept Vinted API calls"""
            try:
                url = response.url
                logger.debug(f"🌐 Network response: {response.status} {url}")
                
                # Focus on catalog/items API endpoint
                if '/api/v2/catalog/items' in url and response.status == 200:
                    logger.info(f"🎯 SUCCESS: Intercepted Vinted API call: {url}")
                    self._api_call_detected = True
                    
                    try:
                        # Extract JSON data from the response
                        json_data = await response.json()
                        self._intercepted_data = json_data
                        self._interception_complete = True
                        logger.info(f"📦 Captured API data: {len(json_data.get('items', []))} items")
                        
                    except Exception as json_error:
                        logger.warning(f"⚠️ Could not parse JSON from API response: {json_error}")
                
                # For item pages, also check for item detail API calls
                elif operation_type == 'item' and '/api/v2/items/' in url and response.status == 200:
                    logger.info(f"🎯 Intercepted Vinted item API call: {url}")
                    self._api_call_detected = True
                    
                    try:
                        json_data = await response.json()
                        self._intercepted_data = json_data
                        self._interception_complete = True
                        logger.info(f"📦 Captured item API data")
                        
                    except Exception as json_error:
                        logger.warning(f"⚠️ Could not parse JSON from item API response: {json_error}")
                
            except Exception as e:
                logger.debug(f"Response handler error (non-critical): {e}")
        
        # Set up the response handler
        page.on("response", handle_response)
        
        logger.info(f"🎧 Network interception set up for {operation_type} operation")
    
    async def _build_frontend_search_url(self, params: Optional[Dict] = None) -> str:
        """Build the frontend search URL that users would visit"""
        # Base catalog URL that users see
        search_url = f"{self.baseurl}/catalog"
        
        if params:
            # Convert API parameters to frontend URL parameters
            frontend_params = {}
            
            # Map common API parameters to frontend equivalents
            param_mapping = {
                'search_text': 'search_text',
                'catalog_ids': 'catalog[]',
                'brand_ids': 'brand_ids[]',
                'size_ids': 'size_ids[]',
                'color_ids': 'color_ids[]',
                'material_ids': 'material_ids[]',
                'status_ids': 'status_ids[]',
                'price_from': 'price_from',
                'price_to': 'price_to',
                'currency': 'currency',
                'order': 'order'
            }
            
            for api_param, frontend_param in param_mapping.items():
                if api_param in params and params[api_param]:
                    frontend_params[frontend_param] = params[api_param]
            
            if frontend_params:
                search_url += f"?{urlencode(frontend_params, doseq=True)}"
        
        return search_url
    
    async def _navigate_with_maximum_stealth(self, page: Page, url: str):
        """Navigate to URL with maximum stealth and realistic behavior"""
        try:
            # Random delay before navigation
            await self.browser_manager.random_delay(2, 5)
            
            logger.info(f"🧭 STARTING BROWSER NAVIGATION TO: {url}")
            
            # Navigate to page
            response = await page.goto(
                url,
                wait_until='networkidle',
                timeout=45000  # Longer timeout for maximum stealth
            )
            
            if response:
                logger.info(f"📥 NAVIGATION COMPLETED: HTTP {response.status} - {response.status_text}")
                if response.status >= 400:
                    raise RuntimeError(f"HTTP {response.status}: {response.status_text}")
            else:
                logger.warning("⚠️ No response received from navigation")
            
            # Simulate realistic human behavior after page load
            await self._simulate_human_behavior(page)
            
            logger.debug("✅ Maximum stealth navigation completed")
            
        except PlaywrightTimeoutError:
            raise RuntimeError("Navigation timeout - possible blocking or slow response")
        except Exception as e:
            raise RuntimeError(f"Navigation failed: {e}") from e
    
    async def _simulate_human_behavior(self, page: Page):
        """Simulate realistic human behavior on the page"""
        try:
            # Wait for page to fully load
            await self.browser_manager.random_delay(3, 6)
            
            # Random mouse movements
            for _ in range(random.randint(2, 4)):
                await self.browser_manager.random_mouse_movement(page)
                await self.browser_manager.random_delay(0.5, 1.5)
            
            # Simulate reading the page (scroll a bit)
            scroll_amount = random.randint(100, 400)
            await self.browser_manager.human_like_scroll(page, scroll_amount)
            await self.browser_manager.random_delay(2, 4)
            
            # Maybe scroll back up a bit (realistic behavior)
            if random.random() < 0.3:  # 30% chance
                await self.browser_manager.human_like_scroll(page, -scroll_amount // 2)
                await self.browser_manager.random_delay(1, 2)
            
            logger.debug("🤖 Human behavior simulation completed")
            
        except Exception as e:
            logger.debug(f"Human behavior simulation error (non-critical): {e}")
    
    async def _wait_for_api_interception(self, page: Page, timeout: float = 30.0) -> Optional[Dict[str, Any]]:
        """Wait for API calls to be intercepted"""
        start_time = time.time()
        check_interval = 0.5
        
        logger.info(f"⏳ Waiting for API interception (timeout: {timeout}s)")
        
        while time.time() - start_time < timeout:
            # Check if we've successfully intercepted data
            if self._interception_complete and self._intercepted_data:
                logger.info("✅ API interception completed successfully")
                return self._intercepted_data
            
            # If we detected an API call but haven't completed interception, keep waiting
            if self._api_call_detected:
                logger.debug("🎯 API call detected, waiting for data extraction...")
            
            await asyncio.sleep(check_interval)
            
            # Occasionally simulate some user activity to keep the page alive
            if int(time.time() - start_time) % 10 == 0:  # Every 10 seconds
                try:
                    await self.browser_manager.random_mouse_movement(page)
                except:
                    pass  # Ignore errors in this simulation
        
        # Timeout reached
        if self._api_call_detected:
            logger.warning("⚠️ API call was detected but data extraction timed out")
        else:
            logger.warning("⚠️ No API calls detected within timeout period")
        
        return None