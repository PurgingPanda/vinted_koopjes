# Playwright-Based Vinted Scraper Plan

## Overview
Create a drop-in replacement for the current `vinted_scraper` package that uses Playwright instead of direct HTTP requests to avoid blocking. The interface will remain identical to ensure compatibility with existing code.

## Current Architecture Analysis

### Existing VintedScraper Interface
```python
# Current interface from vinted_scraper/__init__.py
from ._async_vinted_scraper import AsyncVintedScraper
from ._async_vinted_wrapper import AsyncVintedWrapper
from ._vinted_scraper import VintedScraper
from ._vinted_wrapper import VintedWrapper
```

### Key Methods to Replace
1. **VintedWrapper/AsyncVintedWrapper**:
   - `search_items(search_params)` - Main search functionality
   - `get_item(item_id)` - Get individual item details
   - `get_access_token()` - Token management
   - Error handling and retry logic

2. **Data Models** (keep unchanged):
   - VintedItem, VintedUser, VintedBrand, etc.
   - All model structures remain the same for compatibility

## Playwright Implementation Strategy

### 1. Browser Management
- **Persistent Browser Context**: Maintain long-running browser instances
- **Session Management**: Handle cookies and authentication automatically
- **Stealth Mode**: Configure browser to appear more human-like
- **User-Agent Rotation**: Rotate user agents to avoid detection

### 2. Anti-Detection Features
- **Human-like Timing**: Random delays between requests (2-8 seconds)
- **Mouse Movement Simulation**: Simulate realistic mouse movements
- **Viewport Randomization**: Vary browser window sizes
- **Request Interception**: Block unnecessary resources (images, CSS) for speed
- **Fingerprint Randomization**: Randomize canvas fingerprint, WebGL, etc.

### 3. Performance Optimizations
- **Headless Mode**: Run without GUI for production
- **Resource Blocking**: Block images, stylesheets, fonts to speed up loading
- **Connection Reuse**: Maintain persistent browser instances
- **Concurrent Processing**: Process multiple searches in parallel

### 4. Error Handling & Recovery
- **Automatic Retry**: Retry failed requests with exponential backoff
- **Captcha Detection**: Detect and handle captcha challenges
- **Rate Limit Detection**: Detect when being rate limited and back off
- **Browser Recovery**: Restart browser if it becomes unresponsive

## Implementation Plan

### Phase 1: Core Playwright Infrastructure (Day 1)
1. Create `PlaywrightVintedScraper` class with same interface
2. Implement browser lifecycle management
3. Add basic search functionality
4. Configure stealth settings and anti-detection

### Phase 2: Feature Parity (Day 2)  
1. Implement all methods from original wrapper
2. Add comprehensive error handling
3. Implement token management via browser automation
4. Add data extraction and parsing logic

### Phase 3: Optimization & Testing (Day 3)
1. Add performance optimizations
2. Implement human-like behavior patterns
3. Add comprehensive logging and monitoring
4. Create test suite to verify functionality

### Phase 4: Integration & Deployment (Day 4)
1. Create drop-in replacement mechanism
2. Add configuration options for Playwright vs HTTP modes
3. Performance testing and optimization
4. Documentation and deployment

## File Structure

```
vinted_scraper/
├── src/vinted_scraper/
│   ├── __init__.py                    # Export both HTTP and Playwright versions
│   ├── _playwright_vinted_scraper.py  # Main Playwright implementation
│   ├── _playwright_vinted_wrapper.py  # Wrapper with same interface
│   ├── _browser_manager.py            # Browser lifecycle management
│   ├── _stealth_config.py             # Anti-detection configuration
│   ├── _human_behavior.py             # Human-like interaction patterns
│   └── models/                        # Keep existing models unchanged
└── config/
    └── playwright_config.py           # Configuration settings
```

## Key Technical Details

### Browser Configuration
```python
browser_args = [
    '--no-sandbox',
    '--disable-blink-features=AutomationControlled',
    '--disable-extensions-file-access-check',
    '--disable-extensions-http-throttling',
    '--disable-extensions-http2-throttling',
    '--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
]
```

### Stealth Techniques
- Remove `navigator.webdriver` property
- Override `navigator.plugins` and `navigator.languages`
- Randomize screen resolution and color depth
- Inject realistic timing patterns
- Emulate real browser font rendering

### Search Implementation
```python
async def search_items(self, search_params):
    """
    Navigate to Vinted search page and extract results using browser automation
    """
    # Navigate to search URL with parameters
    # Wait for page load and content rendering  
    # Extract item data from DOM
    # Handle pagination if needed
    # Return structured data matching existing format
```

## Benefits of Playwright Approach

1. **Better Blocking Resistance**: Acts like real browser, harder to detect
2. **JavaScript Rendering**: Can handle dynamic content and SPAs
3. **Cookie Management**: Automatic session and authentication handling
4. **Debugging**: Can screenshot and inspect page state for debugging
5. **Flexibility**: Can adapt to UI changes more easily than API parsing

## Configuration Options

### Environment Variables
- `VINTED_SCRAPER_MODE`: "http" or "playwright" (default: "playwright")
- `PLAYWRIGHT_HEADLESS`: true/false (default: true)
- `PLAYWRIGHT_SLOWMO`: delay in ms between actions (default: 100)
- `PLAYWRIGHT_TIMEOUT`: page timeout in seconds (default: 30)

### Performance Tuning
- Concurrent browser contexts for parallel processing
- Resource blocking configuration
- Retry policies and backoff strategies
- Memory management and browser recycling

## Risk Mitigation

1. **Fallback Strategy**: Auto-fallback to HTTP scraper if Playwright fails
2. **Resource Management**: Proper cleanup of browser resources
3. **Monitoring**: Comprehensive logging of success/failure rates
4. **Graceful Degradation**: Handle partial failures gracefully

## Questions for Clarification

1. **Browser Choice**: Should we use Chromium (default), Firefox, or WebKit?
2. **Deployment Environment**: Will this run in Docker? Any specific system requirements?
3. **Proxy Support**: Do you need proxy rotation capabilities?
4. **Performance vs Stealth**: Priority on speed or avoiding detection?
5. **Storage**: Should we persist browser profiles/cookies between restarts?

## Expected Outcomes

- **50-80% reduction** in blocking frequency
- **Maintained compatibility** with existing codebase  
- **Improved reliability** for continuous monitoring
- **Better debugging capabilities** when issues occur
- **Future-proof architecture** that can adapt to site changes

This approach will provide a robust, stealthy alternative to HTTP-based scraping while maintaining full compatibility with your existing Django application.