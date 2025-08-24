import logging
import sys
import os
from typing import Dict, Any, List, Optional

# Add the vinted_scraper to Python path so we can import it
vinted_scraper_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'vinted_scraper', 'src')
if vinted_scraper_path not in sys.path:
    sys.path.insert(0, vinted_scraper_path)

try:
    from vinted_scraper import VintedScraper
except ImportError as e:
    logging.error(f"Failed to import VintedScraper: {e}")
    VintedScraper = None


class VintedAPIError(Exception):
    """Custom exception for Vinted API errors"""
    pass


logger = logging.getLogger(__name__)


class VintedAPI:
    """
    Vinted API client using the working scraper implementation
    """
    BASE_URL = "https://www.vinted.be"
    
    def __init__(self):
        """Initialize the API client with the working scraper"""
        if VintedScraper is None:
            raise VintedAPIError("VintedScraper could not be imported")
        
        self._scraper = None
        logger.info("VintedAPI initialized with working scraper")
    
    def _get_scraper(self):
        """Get or create scraper instance - let vinted_scraper handle everything"""
        if self._scraper is None:
            try:
                # Let the vinted_scraper handle cookie fetching completely
                logger.info("🔄 Creating VintedScraper (auto-handles cookies)")
                
                # Use default configuration - let vinted_scraper handle everything
                self._scraper = VintedScraper(self.BASE_URL)
                logger.info("✅ VintedScraper instance created")
            except Exception as e:
                error_msg = str(e).lower()
                if "403" in error_msg or "blocking" in error_msg:
                    logger.warning(f"🔒 Vinted is temporarily blocking requests: {e}")
                    raise VintedAPIError(f"Temporary blocking detected (403): {e}")
                else:
                    logger.error(f"Failed to create VintedScraper: {e}")
                    raise VintedAPIError(f"Failed to initialize scraper: {e}")
        return self._scraper
    
    def _get_existing_session_cookie(self):
        """Try to get existing session cookie from our database or cache"""
        try:
            from django.core.cache import cache
            
            # Try cache first
            cached_token = cache.get('vinted_access_token')
            if cached_token:
                logger.info("Found cached access token")
                return cached_token
                
        except Exception as e:
            logger.debug(f"No existing session cookie found: {e}")
        
        return None
    
    def set_session_cookie(self, session_cookie: str):
        """Manually set a session cookie and reset the scraper"""
        try:
            from django.core.cache import cache
            
            # Store in cache
            cache.set('vinted_access_token', session_cookie, timeout=3600*24)  # 24 hours
            logger.info("✅ Session cookie stored in cache")
            
            # Reset scraper to use new cookie
            self._scraper = None
            
        except Exception as e:
            logger.error(f"Error setting session cookie: {e}")
            raise VintedAPIError(f"Failed to set session cookie: {e}")
    
    def test_connection(self) -> bool:
        """Test if we can connect to Vinted API"""
        try:
            # Simple test search with minimal results
            result = self.search_items({'search_text': 'test', 'per_page': 1})
            return len(result) >= 0  # Even 0 results means connection works
        except Exception as e:
            logger.error(f"API connection test failed: {e}")
            return False
    
    def search_items(self, search_params: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Search for items using the working scraper
        """
        try:
            logger.info(f"Searching items with params: {search_params}")
            scraper = self._get_scraper()
            
            # Use the working scraper's search method
            with scraper:
                results = scraper.search(search_params)
                
            # Convert VintedItem objects to dictionaries
            items = []
            for item in results:
                try:
                    # VintedItem objects need to be converted to dict format for Django
                    item_dict = {}
                    
                    # Helper function to convert any object to dict recursively
                    def obj_to_dict(obj, depth=0):
                        # Prevent infinite recursion
                        if depth > 3:
                            return str(obj)
                        
                        # Handle basic types
                        if isinstance(obj, (str, int, float, bool, type(None))):
                            return obj
                        
                        # Handle lists
                        if isinstance(obj, (list, tuple)):
                            return [obj_to_dict(item, depth + 1) for item in obj]
                        
                        # Handle dicts
                        if isinstance(obj, dict):
                            return {k: obj_to_dict(v, depth + 1) for k, v in obj.items()}
                        
                        # Handle objects with __dict__
                        if hasattr(obj, '__dict__'):
                            result = {}
                            for attr_name in dir(obj):
                                if not attr_name.startswith('_'):
                                    try:
                                        attr_value = getattr(obj, attr_name)
                                        if not callable(attr_value):
                                            result[attr_name] = obj_to_dict(attr_value, depth + 1)
                                    except:
                                        continue
                            return result
                        
                        # Fallback to string representation
                        return str(obj)
                    
                    # Get all attributes from the VintedItem object
                    for attr_name in dir(item):
                        if not attr_name.startswith('_'):  # Skip private attributes
                            try:
                                attr_value = getattr(item, attr_name)
                                # Skip methods
                                if not callable(attr_value):
                                    item_dict[attr_name] = obj_to_dict(attr_value)
                            except:
                                continue
                    
                    # The recursive obj_to_dict function above handles all nested objects automatically
                    
                    # Ensure required fields have defaults
                    item_dict.setdefault('id', None)
                    item_dict.setdefault('title', '')
                    item_dict.setdefault('price', '0')
                    item_dict.setdefault('currency', 'EUR')
                    item_dict.setdefault('is_visible', 1)
                    
                    items.append(item_dict)
                except Exception as e:
                    logger.warning(f"Error converting item to dict: {e}")
                    continue
            
            logger.info(f"✅ Found {len(items)} items using working scraper")
            return items
            
        except Exception as e:
            error_msg = str(e).lower()
            if "403" in error_msg or "blocking" in error_msg:
                logger.warning(f"🔒 Temporary blocking detected during search: {e}")
                # Reset scraper to force re-initialization on next call
                self._scraper = None
                raise VintedAPIError(f"Temporary blocking (403) - scraper will retry: {e}")
            else:
                logger.error(f"Error in search_items: {e}")
                raise VintedAPIError(f"Search failed: {e}")
    
    def __del__(self):
        """Cleanup scraper when instance is destroyed"""
        if self._scraper:
            try:
                self._scraper.__exit__(None, None, None)
            except:
                pass