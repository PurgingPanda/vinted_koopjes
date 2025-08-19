import requests
import logging
from typing import Dict, List, Optional, Any
from django.conf import settings
from django.core.cache import cache
from playwright.sync_api import sync_playwright
import time
import json

logger = logging.getLogger(__name__)


class VintedAPIError(Exception):
    """Custom exception for Vinted API errors"""
    pass


class VintedAPI:
    """Service class for interacting with the Vinted API"""
    
    BASE_URL = "https://www.vinted.be/api/v2"
    HOMEPAGE_URL = "https://www.vinted.be"
    CACHE_KEY_TOKEN = "vinted_access_token"
    TOKEN_CACHE_DURATION = 3600  # 1 hour
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/json',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'DNT': '1',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def get_access_token(self, force_refresh: bool = False) -> str:
        """
        Get access token from cache or fetch new one using Playwright
        """
        if not force_refresh:
            cached_token = cache.get(self.CACHE_KEY_TOKEN)
            if cached_token:
                logger.info("Using cached Vinted access token")
                return cached_token
        
        logger.info("Fetching new Vinted access token using Playwright")
        
        try:
            with sync_playwright() as p:
                # Launch browser in headless mode
                browser = p.chromium.launch(headless=True)
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080}
                )
                
                page = context.new_page()
                
                # Navigate to Vinted homepage
                page.goto(self.HOMEPAGE_URL, wait_until='networkidle')
                
                # Wait a bit for JavaScript to load
                time.sleep(2)
                
                # Get all cookies
                cookies = context.cookies()
                
                # Find the access_token_web cookie
                access_token = None
                for cookie in cookies:
                    if cookie['name'] == 'access_token_web':
                        access_token = cookie['value']
                        break
                
                browser.close()
                
                if not access_token:
                    raise VintedAPIError("Could not obtain access_token_web cookie from Vinted")
                
                # Cache the token
                cache.set(self.CACHE_KEY_TOKEN, access_token, self.TOKEN_CACHE_DURATION)
                logger.info("Successfully obtained and cached new Vinted access token")
                
                return access_token
                
        except Exception as e:
            logger.error(f"Error obtaining Vinted access token: {e}")
            raise VintedAPIError(f"Failed to obtain access token: {e}")
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None, retry_count: int = 0) -> Dict[str, Any]:
        """
        Make authenticated request to Vinted API
        """
        if retry_count > 2:
            raise VintedAPIError("Max retry attempts reached")
        
        # Get access token
        access_token = self.get_access_token(force_refresh=retry_count > 0)
        
        # Prepare request
        url = f"{self.BASE_URL}{endpoint}"
        
        # Add access token to cookies
        self.session.cookies.set('access_token_web', access_token, domain='.vinted.be')
        
        # Default parameters
        if params is None:
            params = {}
        
        params.setdefault('per_page', 96)
        params.setdefault('currency', 'EUR')
        
        try:
            logger.info(f"Making request to Vinted API: {endpoint}")
            response = self.session.get(url, params=params, timeout=30)
            
            if response.status_code == 401:
                # Token might be expired, retry with fresh token
                logger.warning("Received 401, refreshing token and retrying")
                cache.delete(self.CACHE_KEY_TOKEN)
                return self.make_request(endpoint, params, retry_count + 1)
            
            if response.status_code == 429:
                # Rate limited, wait and retry
                logger.warning("Rate limited, waiting before retry")
                time.sleep(5)
                return self.make_request(endpoint, params, retry_count + 1)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise VintedAPIError(f"API request failed: {e}")
    
    def search_items(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for items using the catalog endpoint
        """
        endpoint = "/catalog/items"
        
        try:
            response_data = self.make_request(endpoint, search_params)
            
            # Extract items from response
            items = response_data.get('items', [])
            
            logger.info(f"Found {len(items)} items for search parameters: {search_params}")
            return items
            
        except Exception as e:
            logger.error(f"Error searching items: {e}")
            raise VintedAPIError(f"Failed to search items: {e}")
    
    def get_item_details(self, item_id: int) -> Dict[str, Any]:
        """
        Get detailed information for a specific item
        """
        endpoint = f"/items/{item_id}"
        
        try:
            response_data = self.make_request(endpoint)
            return response_data.get('item', {})
            
        except Exception as e:
            logger.error(f"Error getting item details for {item_id}: {e}")
            raise VintedAPIError(f"Failed to get item details: {e}")
    
    def test_connection(self) -> bool:
        """
        Test if API connection is working
        """
        try:
            # Simple search to test connection
            test_params = {
                'search_text': 'test',
                'per_page': 1
            }
            
            response = self.search_items(test_params)
            logger.info("Vinted API connection test successful")
            return True
            
        except Exception as e:
            logger.error(f"Vinted API connection test failed: {e}")
            return False


# Global API instance
vinted_api = VintedAPI()