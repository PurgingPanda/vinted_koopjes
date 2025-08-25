# pylint: disable=missing-module-docstring
import os
import logging

logger = logging.getLogger(__name__)

# Configuration for scraper mode
SCRAPER_MODE = os.getenv('VINTED_SCRAPER_MODE', 'playwright').lower()

# Try to import Playwright components
try:
    from ._playwright_vinted_scraper import PlaywrightVintedScraper
    from ._playwright_vinted_wrapper import PlaywrightVintedWrapper
    PLAYWRIGHT_AVAILABLE = True
    logger.info("✅ Playwright scraper components available")
except ImportError as e:
    PLAYWRIGHT_AVAILABLE = False
    logger.warning(f"⚠️ Playwright not available: {e}")
    PlaywrightVintedScraper = None
    PlaywrightVintedWrapper = None

# Try to import Network Interception components
try:
    from ._network_interception_scraper import NetworkInterceptionScraper
    from ._network_interception_wrapper import NetworkInterceptionWrapper
    NETWORK_INTERCEPTION_AVAILABLE = True
    logger.info("✅ Network interception scraper components available")
except ImportError as e:
    NETWORK_INTERCEPTION_AVAILABLE = False
    logger.warning(f"⚠️ Network interception not available: {e}")
    NetworkInterceptionScraper = None
    NetworkInterceptionWrapper = None

# Import original HTTP-based components as fallback
try:
    from ._async_vinted_scraper import AsyncVintedScraper as OriginalAsyncVintedScraper
    from ._async_vinted_wrapper import AsyncVintedWrapper as OriginalAsyncVintedWrapper
    from ._vinted_scraper import VintedScraper as OriginalVintedScraper
    from ._vinted_wrapper import VintedWrapper as OriginalVintedWrapper
    HTTP_AVAILABLE = True
    logger.info("✅ HTTP scraper components available")
except ImportError as e:
    HTTP_AVAILABLE = False
    logger.error(f"❌ HTTP scraper components not available: {e}")
    OriginalAsyncVintedScraper = None
    OriginalAsyncVintedWrapper = None
    OriginalVintedScraper = None
    OriginalVintedWrapper = None

# Smart selection of scraper implementation
def _get_scraper_class():
    """Select the best available scraper implementation"""
    if SCRAPER_MODE == 'network' and NETWORK_INTERCEPTION_AVAILABLE:
        logger.info("🌐 Using Network Interception scraper for maximum stealth")
        return NetworkInterceptionScraper
    elif SCRAPER_MODE == 'playwright' and PLAYWRIGHT_AVAILABLE:
        logger.info("🎭 Using Playwright-based scraper for maximum stealth")
        return PlaywrightVintedScraper
    elif SCRAPER_MODE == 'http' and HTTP_AVAILABLE:
        logger.info("🌐 Using HTTP-based scraper (legacy mode)")
        return OriginalVintedScraper
    elif NETWORK_INTERCEPTION_AVAILABLE:
        logger.info("🌐 Fallback to Network Interception scraper")
        return NetworkInterceptionScraper
    elif PLAYWRIGHT_AVAILABLE:
        logger.info("🎭 Fallback to Playwright-based scraper")
        return PlaywrightVintedScraper
    elif HTTP_AVAILABLE:
        logger.info("🌐 Fallback to HTTP-based scraper")
        return OriginalVintedScraper
    else:
        raise ImportError(
            "No scraper implementation available. "
            "Install playwright: pip install playwright && playwright install chromium"
        )

def _get_wrapper_class():
    """Select the best available wrapper implementation"""
    if SCRAPER_MODE == 'network' and NETWORK_INTERCEPTION_AVAILABLE:
        logger.info("🌐 Using Network Interception wrapper for maximum stealth")
        return NetworkInterceptionWrapper
    elif SCRAPER_MODE == 'playwright' and PLAYWRIGHT_AVAILABLE:
        logger.info("🎭 Using Playwright-based wrapper for maximum stealth")
        return PlaywrightVintedWrapper
    elif SCRAPER_MODE == 'http' and HTTP_AVAILABLE:
        logger.info("🌐 Using HTTP-based wrapper (legacy mode)")
        return OriginalVintedWrapper
    elif NETWORK_INTERCEPTION_AVAILABLE:
        logger.info("🌐 Fallback to Network Interception wrapper")
        return NetworkInterceptionWrapper
    elif PLAYWRIGHT_AVAILABLE:
        logger.info("🎭 Fallback to Playwright-based wrapper")
        return PlaywrightVintedWrapper
    elif HTTP_AVAILABLE:
        logger.info("🌐 Fallback to HTTP-based wrapper")
        return OriginalVintedWrapper
    else:
        raise ImportError(
            "No wrapper implementation available. "
            "Install playwright: pip install playwright && playwright install chromium"
        )

# Export the selected implementations
VintedScraper = _get_scraper_class()
VintedWrapper = _get_wrapper_class()

# For async versions, prefer HTTP for now (Playwright async version can be added later)
if HTTP_AVAILABLE:
    AsyncVintedScraper = OriginalAsyncVintedScraper
    AsyncVintedWrapper = OriginalAsyncVintedWrapper
else:
    AsyncVintedScraper = None
    AsyncVintedWrapper = None

__all__ = ["VintedScraper", "VintedWrapper"]

# Add async versions if available
if AsyncVintedScraper and AsyncVintedWrapper:
    __all__.extend(["AsyncVintedScraper", "AsyncVintedWrapper"])

# Log the final configuration
logger.info(f"🚀 VintedScraper initialized: mode={SCRAPER_MODE}, implementation={VintedScraper.__name__ if VintedScraper else 'None'}")
