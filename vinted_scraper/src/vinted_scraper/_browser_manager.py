"""
Browser manager for Playwright-based Vinted scraping with maximum stealth
"""
import asyncio
import logging
import random
import time
from typing import Optional, Dict, Any, List
from contextlib import asynccontextmanager

try:
    from playwright.async_api import async_playwright, Browser, BrowserContext, Page, Playwright
    from playwright_stealth.stealth import Stealth
    STEALTH_AVAILABLE = True
except ImportError:
    # Fallback for when Playwright or stealth is not installed
    async_playwright = None
    Browser = None
    BrowserContext = None
    Page = None
    Playwright = None
    Stealth = None
    STEALTH_AVAILABLE = False

logger = logging.getLogger(__name__)


class BrowserManager:
    """Manages Playwright browser instances with maximum stealth configuration"""
    
    def __init__(self, headless: bool = True, slowmo: int = 100):
        self.headless = headless
        self.slowmo = slowmo
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self._lock = asyncio.Lock()
        
        # Initialize stealth instance
        if STEALTH_AVAILABLE and Stealth:
            self.stealth = Stealth()
        else:
            self.stealth = None
        
        if async_playwright is None:
            raise ImportError(
                "Playwright is required for browser-based scraping. "
                "Install it with: pip install playwright && playwright install chromium"
            )
    
    async def __aenter__(self):
        """Async context manager entry"""
        await self.start()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        await self.close()
    
    async def start(self):
        """Start the browser with stealth configuration"""
        if self.browser is not None:
            return
        
        async with self._lock:
            if self.browser is not None:  # Double-check after acquiring lock
                return
            
            logger.info("🚀 Starting Playwright browser with maximum stealth configuration")
            
            self.playwright = await async_playwright().start()
            
            # Launch Chromium with stealth arguments
            self.browser = await self.playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slowmo,
                args=self._get_stealth_args()
            )
            
            # Create context with stealth settings
            context_config = self._get_context_config()
            logger.info(f"🎭 Using randomized user agent: {context_config.get('user_agent', 'unknown')[:60]}...")
            self.context = await self.browser.new_context(**context_config)
            
            # Add stealth scripts to all pages
            await self.context.add_init_script(self._get_stealth_script())
            
            stealth_status = "with playwright-stealth" if STEALTH_AVAILABLE else "basic stealth only"
            logger.info(f"✅ Browser started successfully ({stealth_status})")
    
    async def close(self):
        """Close browser and cleanup resources"""
        async with self._lock:
            if self.context:
                await self.context.close()
                self.context = None
            
            if self.browser:
                await self.browser.close()
                self.browser = None
            
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        
        logger.info("🛑 Browser closed")
    
    @asynccontextmanager
    async def new_page(self):
        """Create a new page with stealth configuration"""
        if self.context is None:
            await self.start()
        
        page = await self.context.new_page()
        
        try:
            # Configure page for maximum stealth
            await self._configure_page_stealth(page)
            yield page
        finally:
            await page.close()
    
    def _get_stealth_args(self) -> List[str]:
        """Get Chromium launch arguments for maximum stealth"""
        return [
            '--no-sandbox',
            '--disable-blink-features=AutomationControlled',
            '--disable-extensions-file-access-check',
            '--disable-extensions-http-throttling',
            '--disable-extensions-https-throttling',
            '--disable-background-timer-throttling',
            '--disable-backgrounding-occluded-windows',
            '--disable-renderer-backgrounding',
            '--disable-features=TranslateUI',
            '--disable-features=VizDisplayCompositor',
            '--disable-features=AudioServiceOutOfProcess',
            '--disable-features=VizServiceDisplayCompositor',
            '--disable-ipc-flooding-protection',
            '--disable-dev-shm-usage',
            '--disable-component-extensions-with-background-pages',
            '--disable-extensions',
            '--disable-plugins',
            '--disable-web-security',
            '--disable-features=site-per-process',
            '--flag-switches-begin',
            '--disable-features=VizDisplayCompositor',
            '--flag-switches-end'
        ]
    
    def _get_context_config(self) -> Dict[str, Any]:
        """Get browser context configuration for stealth"""
        # Randomize screen resolution
        screen_widths = [1366, 1920, 1440, 1280, 1024]
        screen_heights = [768, 1080, 900, 720, 768]
        width = random.choice(screen_widths)
        height = random.choice(screen_heights)
        
        return {
            'viewport': {'width': width, 'height': height},
            'screen': {'width': width, 'height': height},
            'user_agent': self._get_random_user_agent(),
            'locale': 'en-US',
            'timezone_id': 'Europe/Brussels',  # Belgium timezone for vinted.be
            'permissions': [],
            'geolocation': {'latitude': 50.8503, 'longitude': 4.3517},  # Brussels coordinates
            'extra_http_headers': {
                'Accept-Language': 'en-US,en;q=0.9,nl;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
                'Connection': 'keep-alive',
                'Upgrade-Insecure-Requests': '1',
                'Sec-Fetch-Site': 'none',
                'Sec-Fetch-Mode': 'navigate',
                'Sec-Fetch-User': '?1',
                'Cache-Control': 'max-age=0'
            }
        }
    
    def _get_random_user_agent(self) -> str:
        """Get a random realistic user agent - updated for 2024/2025"""
        user_agents = [
            # Chrome Windows (most popular)
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0.0.0 Safari/537.36',
            
            # Chrome macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/130.0.0.0 Safari/537.36',
            
            # Chrome Linux
            'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36',
            
            # Firefox Windows
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:132.0) Gecko/20100101 Firefox/132.0',
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:131.0) Gecko/20100101 Firefox/131.0',
            
            # Firefox macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:132.0) Gecko/20100101 Firefox/132.0',
            
            # Safari macOS
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.6 Safari/605.1.15',
            'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Safari/605.1.15',
            
            # Edge Windows 
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36 Edg/131.0.0.0',
        ]
        selected = random.choice(user_agents)
        logger.debug(f"🎭 Selected user agent: {selected[:50]}...")
        return selected
    
    def _get_stealth_script(self) -> str:
        """Get JavaScript code to inject for maximum stealth"""
        return """
        // Remove webdriver property
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined,
        });
        
        // Mock plugins
        Object.defineProperty(navigator, 'plugins', {
            get: () => [1, 2, 3, 4, 5],
        });
        
        // Mock languages
        Object.defineProperty(navigator, 'languages', {
            get: () => ['en-US', 'en', 'nl'],
        });
        
        // Mock permissions
        const originalQuery = window.navigator.permissions.query;
        window.navigator.permissions.query = (parameters) => (
            parameters.name === 'notifications' ?
                Promise.resolve({ state: Notification.permission }) :
                originalQuery(parameters)
        );
        
        // Mock chrome runtime
        Object.defineProperty(window, 'chrome', {
            get: () => ({
                runtime: {
                    onConnect: undefined,
                    onMessage: undefined,
                }
            })
        });
        
        // Override the `call` function to prevent detection
        const originalCall = Function.prototype.call;
        Function.prototype.call = function(...args) {
            if (this.toString().indexOf('_getInstallRelatedApps') !== -1) {
                return Promise.resolve([]);
            }
            return originalCall.apply(this, args);
        };
        
        // Mock getBattery API
        Object.defineProperty(navigator, 'getBattery', {
            get: () => () => Promise.resolve({
                charging: true,
                chargingTime: 0,
                dischargingTime: Infinity,
                level: 1.0
            })
        });
        """
    
    async def _configure_page_stealth(self, page: Page):
        """Configure individual page for maximum stealth"""
        # Apply playwright-stealth if available
        if self.stealth:
            logger.info("🥷 Applying playwright-stealth to page")
            await self.stealth.apply_stealth_async(page)
        else:
            logger.warning("⚠️ playwright-stealth not available, using basic stealth")
        
        # Block unnecessary resources for speed (but keep some for realism)
        await page.route("**/*.{png,jpg,jpeg,gif,svg,woff,woff2,ttf,eot}", 
                         lambda route: route.abort())
        
        # Don't block CSS as it might trigger detection
        # await page.route("**/*.css", lambda route: route.abort())
        
        # Set additional headers for maximum stealth
        await page.set_extra_http_headers({
            'sec-ch-ua': '"Google Chrome";v="120", "Chromium";v="120", "Not?A_Brand";v="24"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
        })
        
        logger.debug("📄 Page configured with stealth settings")
    
    async def random_delay(self, min_seconds: float = 2.0, max_seconds: float = 8.0):
        """Add random human-like delay"""
        delay = random.uniform(min_seconds, max_seconds)
        logger.debug(f"⏳ Random delay: {delay:.2f} seconds")
        await asyncio.sleep(delay)
    
    async def human_like_scroll(self, page: Page, pixels: int = 300):
        """Simulate human-like scrolling"""
        await page.evaluate(f"""
            window.scrollBy({{
                top: {pixels},
                left: 0,
                behavior: 'smooth'
            }});
        """)
        await self.random_delay(0.5, 1.5)
    
    async def random_mouse_movement(self, page: Page):
        """Simulate random mouse movement"""
        viewport = page.viewport_size
        if viewport:
            x = random.randint(0, viewport['width'] - 1)
            y = random.randint(0, viewport['height'] - 1)
            
            await page.mouse.move(x, y)
            await self.random_delay(0.1, 0.3)