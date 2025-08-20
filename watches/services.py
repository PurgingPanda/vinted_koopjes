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
    CACHE_KEY_BACKUP_TOKEN = "vinted_backup_token"
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
                # Advanced Chrome spoofing arguments
                browser_args = [
                    '--no-sandbox',
                    '--disable-setuid-sandbox', 
                    '--disable-dev-shm-usage',
                    '--disable-blink-features=AutomationControlled',
                    '--disable-features=VizDisplayCompositor',
                    '--exclude-switches=enable-automation',
                    '--disable-extensions-except=/path/to/extension',
                    '--disable-plugins-discovery',
                    '--disable-default-apps',
                    '--no-first-run',
                    '--no-service-autorun',
                    '--password-store=basic',
                    '--use-mock-keychain',
                    '--disable-component-extensions-with-background-pages',
                    '--disable-background-timer-throttling',
                    '--disable-renderer-backgrounding',
                    '--disable-backgrounding-occluded-windows',
                    '--disable-ipc-flooding-protection'
                ]
                
                print("🎭 Launching advanced Chrome spoofing...")
                
                # Use only headless for better stealth
                browser = p.chromium.launch(
                    headless=True,
                    args=browser_args,
                    ignore_default_args=['--enable-automation']
                )
                
                # Create realistic browser context with full Chrome spoofing
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36',
                    viewport={'width': 1920, 'height': 1080},
                    locale='en-US',
                    timezone_id='Europe/Brussels',
                    permissions=['geolocation'],
                    geolocation={'latitude': 50.8503, 'longitude': 4.3517},  # Brussels
                    color_scheme='light',
                    reduced_motion='no-preference',
                    forced_colors='none',
                    extra_http_headers={
                        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                        'Accept-Encoding': 'gzip, deflate, br',
                        'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8,fr;q=0.7',
                        'Cache-Control': 'max-age=0',
                        'sec-ch-ua': '"Not A(Brand";v="99", "Google Chrome";v="121", "Chromium";v="121"',
                        'sec-ch-ua-mobile': '?0',
                        'sec-ch-ua-platform': '"Windows"',
                        'Sec-Fetch-Dest': 'document',
                        'Sec-Fetch-Mode': 'navigate',
                        'Sec-Fetch-Site': 'none',
                        'Sec-Fetch-User': '?1',
                        'Upgrade-Insecure-Requests': '1'
                    }
                )
                
                # Comprehensive stealth script to mimic real Chrome
                stealth_script = """
                // Remove webdriver property
                Object.defineProperty(navigator, 'webdriver', {
                    get: () => undefined,
                });

                // Add chrome object
                window.chrome = {
                    app: {
                        isInstalled: false,
                    },
                    webstore: {
                        onInstallStageChanged: {},
                        onDownloadProgress: {},
                    },
                    runtime: {
                        onConnect: {},
                        onMessage: {},
                    },
                };

                // Mock plugins
                Object.defineProperty(navigator, 'plugins', {
                    get: () => [
                        {
                            0: {type: "application/x-google-chrome-pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                            description: "Portable Document Format",
                            filename: "internal-pdf-viewer",
                            length: 1,
                            name: "Chrome PDF Plugin"
                        },
                        {
                            0: {type: "application/pdf", suffixes: "pdf", description: "Portable Document Format", enabledPlugin: Plugin},
                            description: "Portable Document Format", 
                            filename: "mhjfbmdgcfjbbpaeojofohoefgiehjai",
                            length: 1,
                            name: "Chrome PDF Viewer"
                        },
                        {
                            0: {type: "application/x-nacl", suffixes: "", description: "Native Client Executable", enabledPlugin: Plugin},
                            1: {type: "application/x-pnacl", suffixes: "", description: "Portable Native Client Executable", enabledPlugin: Plugin},
                            description: "Native Client",
                            filename: "internal-nacl-plugin",
                            length: 2,
                            name: "Native Client"
                        }
                    ],
                });

                // Mock languages
                Object.defineProperty(navigator, 'languages', {
                    get: () => ['en-US', 'en', 'nl', 'fr'],
                });

                // Mock permissions
                const originalQuery = window.navigator.permissions.query;
                window.navigator.permissions.query = (parameters) => (
                    parameters.name === 'notifications' ?
                        Promise.resolve({ state: Notification.permission }) :
                        originalQuery(parameters)
                );

                // Mock battery API
                Object.defineProperty(navigator, 'getBattery', {
                    get: () => () => Promise.resolve({
                        charging: true,
                        chargingTime: 0,
                        dischargingTime: Infinity,
                        level: 1.0
                    }),
                });

                // Randomize screen properties
                Object.defineProperty(screen, 'availHeight', {get: () => 1040});
                Object.defineProperty(screen, 'availWidth', {get: () => 1920});
                Object.defineProperty(screen, 'colorDepth', {get: () => 24});
                Object.defineProperty(screen, 'height', {get: () => 1080});
                Object.defineProperty(screen, 'pixelDepth', {get: () => 24});
                Object.defineProperty(screen, 'width', {get: () => 1920});
                
                // Mock WebGL
                const getParameter = WebGLRenderingContext.getParameter;
                WebGLRenderingContext.prototype.getParameter = function(parameter) {
                    if (parameter === 37445) {
                        return 'Intel Inc.';
                    }
                    if (parameter === 37446) {
                        return 'Intel(R) HD Graphics 620';
                    }
                    return getParameter(parameter);
                };
                """
                
                context.add_init_script(stealth_script)
                
                page = context.new_page()
                
                # Set realistic timeout
                page.set_default_timeout(45000)  # 45 seconds
                
                # Add realistic human-like delay
                human_delay = 1.5 + (time.time() % 2.5)  # 1.5-4 seconds
                print(f"🕐 Human-like delay: {human_delay:.1f}s")
                time.sleep(human_delay)
                
                try:
                    print("🌐 Loading Vinted homepage with realistic browsing behavior...")
                    
                    # Navigate with realistic expectations
                    response = page.goto(
                        self.HOMEPAGE_URL, 
                        wait_until='domcontentloaded',
                        timeout=30000
                    )
                    
                    print(f"📊 Response status: {response.status}")
                    
                    # Simulate human reading behavior
                    time.sleep(2 + (time.time() % 2))  # 2-4 seconds
                    
                    # Scroll slightly like a human would
                    page.evaluate("""() => {
                        window.scrollTo(0, 100 + Math.random() * 200);
                    }""")
                    
                    time.sleep(1 + (time.time() % 1))  # 1-2 seconds
                    
                    # Move mouse randomly
                    page.mouse.move(
                        100 + (time.time() % 800), 
                        100 + (time.time() % 400)
                    )
                    
                    # Wait for JavaScript and any lazy loading
                    try:
                        page.wait_for_load_state('networkidle', timeout=8000)
                        print("✅ Network idle achieved")
                    except:
                        print("⚠️ Network still active, continuing anyway...")
                        # Wait a bit more
                        time.sleep(3)
                        
                except Exception as e:
                    print(f"❌ Page load failed: {e}")
                    browser.close()
                    raise VintedAPIError(f"Failed to load Vinted homepage: {e}")
                
                # Final wait for dynamic content
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
                    print("❌ No access_token_web cookie found")
                    # Try to use backup token if available
                    backup_token = cache.get(self.CACHE_KEY_BACKUP_TOKEN)
                    if backup_token and not force_refresh:
                        print("🔄 Using backup token")
                        return backup_token
                    
                    error_message = (
                        "Could not obtain access_token_web cookie from Vinted. "
                        "This likely means Vinted is blocking automated access. "
                        "Please manually inject a token via the web interface."
                    )
                    raise VintedAPIError(error_message)
                
                print("✅ Successfully obtained Vinted access token")
                
                # Cache both primary and backup tokens
                cache.set(self.CACHE_KEY_TOKEN, access_token, self.TOKEN_CACHE_DURATION)
                cache.set(self.CACHE_KEY_BACKUP_TOKEN, access_token, self.TOKEN_CACHE_DURATION * 2)  # Backup lasts longer
                logger.info("Successfully obtained and cached new Vinted access token")
                
                return access_token
                
        except Exception as e:
            logger.error(f"Error obtaining Vinted access token: {e}")
            raise VintedAPIError(f"Failed to obtain access token: {e}")
    
    def make_request(self, endpoint: str, params: Dict[str, Any] = None, retry_count: int = 0) -> Dict[str, Any]:
        """
        Make authenticated request to Vinted API with improved error handling
        """
        if retry_count > 3:
            raise VintedAPIError("Max retry attempts reached")
        
        try:
            # Get access token (with retry logic built-in)
            access_token = self.get_access_token(force_refresh=retry_count > 0)
        except VintedAPIError as e:
            if retry_count < 3:
                print(f"⚠️ Token error, retrying in {retry_count + 2} seconds...")
                time.sleep(retry_count + 2)  # Progressive backoff
                return self.make_request(endpoint, params, retry_count + 1)
            else:
                raise e
        
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