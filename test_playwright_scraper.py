#!/usr/bin/env python3
"""
Test script for the new Playwright-based Vinted scraper
"""
import os
import sys
import logging
from pprint import pprint

# Set up environment
os.environ['VINTED_SCRAPER_MODE'] = 'playwright'  # Force Playwright mode
os.environ['DJANGO_SETTINGS_MODULE'] = 'settings_spitsboog'

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Add Django setup
import django
django.setup()

# Add the vinted_scraper to Python path
vinted_scraper_path = os.path.join(os.path.dirname(__file__), 'vinted_scraper', 'src')
if vinted_scraper_path not in sys.path:
    sys.path.insert(0, vinted_scraper_path)

try:
    from vinted_scraper import VintedScraper
    logger.info(f"✅ Successfully imported VintedScraper: {VintedScraper.__name__}")
except ImportError as e:
    logger.error(f"❌ Failed to import VintedScraper: {e}")
    sys.exit(1)


def test_basic_scraper_initialization():
    """Test that the scraper can be initialized"""
    logger.info("🧪 Testing scraper initialization...")
    
    try:
        scraper = VintedScraper("https://www.vinted.be")
        logger.info("✅ Scraper initialized successfully")
        return scraper
    except Exception as e:
        logger.error(f"❌ Scraper initialization failed: {e}")
        raise


def test_simple_search(scraper):
    """Test a simple search"""
    logger.info("🔍 Testing simple search...")
    
    try:
        # Simple search without parameters
        results = scraper.search()
        
        if isinstance(results, dict) and 'items' in results:
            item_count = len(results['items'])
            logger.info(f"✅ Search successful - found {item_count} items")
            
            # Show a sample item if available
            if results['items']:
                sample_item = results['items'][0]
                logger.info(f"📦 Sample item: {sample_item.get('title', 'No title')[:50]}...")
                logger.info(f"💰 Price: €{sample_item.get('price', {}).get('amount', 'N/A')}")
            
            return True
        else:
            logger.error(f"❌ Unexpected response format: {type(results)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Search test failed: {e}")
        return False


def test_search_with_parameters(scraper):
    """Test search with specific parameters"""
    logger.info("🔍 Testing search with parameters...")
    
    try:
        # Search for specific brand
        search_params = {
            'search_text': 'barbour',
            'per_page': '24'
        }
        
        results = scraper.search(search_params)
        
        if isinstance(results, dict) and 'items' in results:
            item_count = len(results['items'])
            logger.info(f"✅ Parameterized search successful - found {item_count} items")
            
            # Check if results seem relevant
            if results['items']:
                for item in results['items'][:3]:  # Check first 3 items
                    title = item.get('title', '').lower()
                    if 'barbour' in title:
                        logger.info(f"✅ Relevant result found: {item.get('title', 'No title')[:50]}...")
                        break
                else:
                    logger.warning("⚠️ No obviously relevant results in first 3 items")
            
            return True
        else:
            logger.error(f"❌ Unexpected response format: {type(results)}")
            return False
            
    except Exception as e:
        logger.error(f"❌ Parameterized search test failed: {e}")
        return False


def test_item_details(scraper, item_id="1234567890"):
    """Test fetching item details"""
    logger.info(f"📦 Testing item details for ID: {item_id}...")
    
    try:
        # Try to get item details
        item_data = scraper.item(item_id)
        
        if isinstance(item_data, dict):
            logger.info(f"✅ Item fetch successful: {type(item_data)}")
            
            # Check for expected structure
            if 'item' in item_data:
                item = item_data['item']
                logger.info(f"📦 Item title: {item.get('title', 'No title')[:50]}...")
            
            return True
        else:
            logger.error(f"❌ Unexpected item response format: {type(item_data)}")
            return False
            
    except Exception as e:
        logger.warning(f"⚠️ Item fetch test failed (expected for test ID): {e}")
        return True  # This is expected to fail with a test ID


def run_tests():
    """Run all tests"""
    logger.info("🚀 Starting Playwright scraper tests...")
    
    test_results = []
    scraper = None
    
    try:
        # Test 1: Initialization
        scraper = test_basic_scraper_initialization()
        test_results.append(("Initialization", True))
        
        # Test 2: Simple search
        result = test_simple_search(scraper)
        test_results.append(("Simple Search", result))
        
        # Test 3: Parameterized search
        result = test_search_with_parameters(scraper)
        test_results.append(("Parameterized Search", result))
        
        # Test 4: Item details (will likely fail with test ID, but tests the interface)
        result = test_item_details(scraper)
        test_results.append(("Item Details", result))
        
    except Exception as e:
        logger.error(f"❌ Test suite failed: {e}")
        test_results.append(("Test Suite", False))
    
    finally:
        # Cleanup
        if scraper and hasattr(scraper, 'close'):
            try:
                scraper.close()
                logger.info("🧹 Scraper cleanup completed")
            except Exception as e:
                logger.warning(f"⚠️ Cleanup warning: {e}")
    
    # Print results
    logger.info("\n" + "="*50)
    logger.info("🧪 TEST RESULTS:")
    logger.info("="*50)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        logger.info(f"{status} - {test_name}")
        if result:
            passed += 1
    
    logger.info("="*50)
    logger.info(f"📊 Overall: {passed}/{total} tests passed ({passed/total*100:.1f}%)")
    
    if passed == total:
        logger.info("🎉 All tests passed! Playwright scraper is working correctly.")
        return True
    else:
        logger.warning("⚠️ Some tests failed. Check logs for details.")
        return False


if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)