"""
Network interception wrapper providing identical interface to original VintedWrapper
Drop-in replacement with network request interception capabilities
"""
import logging
from typing import Dict, Any, Optional, Union, List

from ._network_interception_scraper import NetworkInterceptionScraper

logger = logging.getLogger(__name__)


class NetworkInterceptionWrapper:
    """
    Wrapper for NetworkInterceptionScraper providing identical interface to VintedWrapper
    Uses network request interception for maximum stealth and direct API data access
    """
    
    def __init__(self, base_url: str = "https://www.vinted.be"):
        self.base_url = base_url.rstrip('/')
        self._scraper = None
        
        logger.info(f"🌐 NetworkInterceptionWrapper initialized for {base_url}")
    
    def _get_scraper(self, session_cookie: Optional[str] = None) -> NetworkInterceptionScraper:
        """Get or create scraper instance (session_cookie ignored for natural behavior)"""
        if self._scraper is None:
            config = {
                'headless': True,
                'slowmo': 150,  # Maximum stealth timing
            }
            # Don't pass session_cookie - let browser obtain cookies naturally
            self._scraper = NetworkInterceptionScraper(
                baseurl=self.base_url,
                config=config
            )
        return self._scraper
    
    def search(
        self,
        search_text: Optional[str] = None,
        catalog_ids: Optional[Union[int, List[int]]] = None,
        brand_ids: Optional[Union[int, List[int]]] = None,
        size_ids: Optional[Union[int, List[int]]] = None,
        color_ids: Optional[Union[int, List[int]]] = None,
        material_ids: Optional[Union[int, List[int]]] = None,
        status_ids: Optional[Union[int, List[int]]] = None,
        price_from: Optional[float] = None,
        price_to: Optional[float] = None,
        currency: str = "EUR",
        order: str = "newest_first",
        per_page: int = 24,
        page: int = 1,
        session_cookie: Optional[str] = None,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Search items using network interception - identical interface to VintedWrapper
        
        :param search_text: Search query text
        :param catalog_ids: Category IDs (single int or list of ints)
        :param brand_ids: Brand IDs (single int or list of ints)
        :param size_ids: Size IDs (single int or list of ints)
        :param color_ids: Color IDs (single int or list of ints)
        :param material_ids: Material IDs (single int or list of ints)
        :param status_ids: Status/condition IDs (single int or list of ints)
        :param price_from: Minimum price
        :param price_to: Maximum price
        :param currency: Currency code
        :param order: Sort order
        :param per_page: Items per page
        :param page: Page number
        :param session_cookie: Session cookie
        :param kwargs: Additional parameters
        :return: Dict containing search results
        """
        try:
            # Note: session_cookie parameter is ignored for network interception
            # The browser will obtain cookies naturally for maximum stealth
            
            # Convert parameters to API format
            params = self._build_search_params(
                search_text=search_text,
                catalog_ids=catalog_ids,
                brand_ids=brand_ids,
                size_ids=size_ids,
                color_ids=color_ids,
                material_ids=material_ids,
                status_ids=status_ids,
                price_from=price_from,
                price_to=price_to,
                currency=currency,
                order=order,
                per_page=per_page,
                page=page,
                **kwargs
            )
            
            scraper = self._get_scraper(session_cookie)
            result = scraper.search(params)
            
            # Ensure consistent response format
            if 'items' not in result:
                result = {'items': []}
            
            return result
            
        except Exception as e:
            logger.error(f"❌ Network interception search failed: {e}")
            return {'items': []}
    
    def item(
        self, 
        item_id: Union[int, str], 
        session_cookie: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get item details using network interception - identical interface to VintedWrapper
        
        :param item_id: Item ID
        :param session_cookie: Session cookie
        :return: Dict containing item data
        """
        try:
            # Note: session_cookie parameter is ignored for network interception
            # The browser will obtain cookies naturally for maximum stealth
            scraper = self._get_scraper(session_cookie)
            result = scraper.item(str(item_id))
            
            # Ensure consistent response format
            if 'item' not in result:
                result = {'item': {}}
                
            return result
            
        except Exception as e:
            logger.error(f"❌ Network interception item fetch failed: {e}")
            return {'item': {}}
    
    def _build_search_params(self, **kwargs) -> Dict[str, Any]:
        """Build search parameters dict from individual arguments"""
        params = {}
        
        # Helper function to normalize list parameters
        def normalize_list_param(value):
            if value is None:
                return None
            if isinstance(value, (list, tuple)):
                return [str(v) for v in value]
            else:
                return [str(value)]
        
        # Map parameters
        param_mapping = {
            'search_text': 'search_text',
            'catalog_ids': 'catalog_ids',
            'brand_ids': 'brand_ids',
            'size_ids': 'size_ids',
            'color_ids': 'color_ids',
            'material_ids': 'material_ids',
            'status_ids': 'status_ids',
            'price_from': 'price_from',
            'price_to': 'price_to',
            'currency': 'currency',
            'order': 'order',
            'per_page': 'per_page',
            'page': 'page'
        }
        
        for param_name, api_name in param_mapping.items():
            value = kwargs.get(param_name)
            if value is not None:
                # Handle list parameters
                if param_name.endswith('_ids'):
                    params[api_name] = normalize_list_param(value)
                else:
                    params[api_name] = value
        
        # Add any additional parameters
        for key, value in kwargs.items():
            if key not in param_mapping and value is not None:
                params[key] = value
        
        return params
    
    def close(self):
        """Close the scraper and cleanup resources"""
        if self._scraper:
            try:
                import asyncio
                asyncio.run(self._scraper.close())
            except Exception as e:
                logger.warning(f"Error closing network interception scraper: {e}")
            finally:
                self._scraper = None
    
    def __del__(self):
        """Cleanup on deletion"""
        self.close()
    
    def __enter__(self):
        """Context manager entry"""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.close()