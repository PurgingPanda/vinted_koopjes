"""
Playwright-based VintedWrapper with identical interface to original
Drop-in replacement for HTTP-based wrapper
"""
import logging
from typing import Dict, Any, Optional

from ._playwright_vinted_scraper import PlaywrightVintedScraper

logger = logging.getLogger(__name__)


class PlaywrightVintedWrapper:
    """
    Playwright-based VintedWrapper that matches the exact interface of the original
    Can be used as a drop-in replacement with identical method signatures
    """
    
    def __init__(
        self,
        baseurl: str,
        session_cookie: Optional[str] = None,
        user_agent: Optional[str] = None,
        config: Optional[Dict] = None,
    ):
        """
        Initialize the Playwright-based wrapper
        
        :param baseurl: Base URL for Vinted (e.g., 'https://www.vinted.be')
        :param session_cookie: Optional session cookie (handled automatically by browser)
        :param user_agent: Optional user agent (randomized automatically for stealth)
        :param config: Optional configuration dict
        """
        self.baseurl = baseurl
        self.session_cookie = session_cookie
        self.user_agent = user_agent
        self.config = config or {}
        
        # Internal scraper instance
        self._scraper = PlaywrightVintedScraper(
            baseurl=baseurl,
            session_cookie=session_cookie,
            user_agent=user_agent,
            config=config
        )
        
        logger.info(f"🎭 PlaywrightVintedWrapper initialized for {baseurl}")
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self._scraper.__exit__(exc_type, exc_val, exc_tb)
    
    def session_cookie(self, retries: int = 3) -> str:
        """
        Get session cookie - matches original interface
        For Playwright version, this is handled automatically by the browser
        
        :param retries: Number of retries (for interface compatibility)
        :return: Session cookie string (or placeholder for browser-based approach)
        """
        logger.info("🍪 Session cookie handled automatically by browser")
        return "browser_managed_session"
    
    def search(self, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Search for items on Vinted - exact same interface as original
        
        :param params: Dictionary with query parameters
        :return: Dict containing JSON response with search results
        """
        logger.info(f"🔍 Searching with params: {params}")
        return self._scraper.search(params)
    
    def item(self, item_id: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Retrieve details of a specific item - exact same interface as original
        
        :param item_id: The unique identifier of the item
        :param params: Optional query parameters
        :return: Dict containing JSON response with item details
        """
        logger.info(f"📦 Fetching item: {item_id}")
        return self._scraper.item(item_id, params)
    
    def _curl(self, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """
        Internal method for interface compatibility
        Routes to appropriate scraper method based on endpoint
        
        :param endpoint: API endpoint
        :param params: Optional parameters
        :return: JSON response
        """
        if endpoint.startswith('/catalog/items'):
            return self.search(params)
        elif endpoint.startswith('/items/'):
            # Extract item ID from endpoint
            item_id = endpoint.split('/')[-1]
            return self.item(item_id, params)
        else:
            raise NotImplementedError(f"Endpoint {endpoint} not implemented in Playwright version")
    
    def close(self):
        """Close browser and cleanup resources"""
        if hasattr(self._scraper, 'close'):
            import asyncio
            asyncio.run(self._scraper.close())


# For backward compatibility, also create a non-async version
class VintedWrapper(PlaywrightVintedWrapper):
    """Alias for PlaywrightVintedWrapper for backward compatibility"""
    pass