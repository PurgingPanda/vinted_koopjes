import logging
from background_task import background
from django.utils import timezone
from django.db.models import Q
from datetime import timedelta

from .models import PriceWatch, VintedItem
from .utils import fetch_and_process_items
from .services import VintedAPI
from .activity_logger import ActivityLogger

logger = logging.getLogger(__name__)


@background(schedule=300)  # Run every 5 minutes
def monitor_price_watches():
    """
    Main background task that monitors all active price watches
    """
    with ActivityLogger('monitor') as activity_log:
        print("🔄 BACKGROUND TASK: Starting price watch monitoring cycle")
        logger.info("Starting price watch monitoring cycle")
        
        # Get all active price watches
        active_watches = PriceWatch.objects.filter(is_active=True)
        
        print(f"📊 Found {active_watches.count()} active price watches")
        logger.info(f"Found {active_watches.count()} active price watches")
        
        total_processed = 0
        for watch in active_watches:
            print(f"   • Scheduling check for: {watch.name}")
            # Schedule individual watch processing
            check_price_watch.now(watch.id)
            total_processed += 1
        
        # Clean up old inactive items
        cleanup_old_items.now()
        print("✅ Price watch monitoring cycle completed")
        
        # Update activity stats
        activity_log.update_stats(items_processed=total_processed)


@background
def check_price_watch(watch_id: int):
    """
    Process a specific price watch
    """
    watch = None
    try:
        watch = PriceWatch.objects.get(id=watch_id, is_active=True)
        
        with ActivityLogger('check_watch', watch) as activity_log:
            print(f"🔍 Processing price watch: {watch.name}")
            logger.info(f"Processing price watch: {watch.name}")
            
            # Fetch and process items
            processed_count = fetch_and_process_items(watch)
            
            print(f"📈 Completed processing watch {watch.name}: {processed_count} items processed")
            logger.info(f"Completed processing watch {watch.name}: {processed_count} items processed")
            
            # Update activity stats
            activity_log.update_stats(items_processed=processed_count)
            
    except PriceWatch.DoesNotExist:
        print(f"⚠️ Price watch {watch_id} not found or inactive")
        logger.warning(f"Price watch {watch_id} not found or inactive")
    except Exception as e:
        print(f"❌ Error processing price watch {watch_id}: {e}")
        logger.error(f"Error processing price watch {watch_id}: {e}")
        raise


@background(schedule=3600)  # Run every hour
def cleanup_old_items():
    """
    Mark items as inactive if they haven't been seen recently
    """
    try:
        # Mark items as inactive if not seen in the last 24 hours
        cutoff_time = timezone.now() - timedelta(hours=24)
        
        updated_count = VintedItem.objects.filter(
            last_seen__lt=cutoff_time,
            is_active=True
        ).update(is_active=False)
        
        logger.info(f"Marked {updated_count} items as inactive")
        
    except Exception as e:
        logger.error(f"Error in cleanup_old_items: {e}")


@background(schedule=7200)  # Run every 2 hours
def refresh_vinted_token():
    """
    Proactively refresh Vinted access token
    """
    try:
        logger.info("Proactively refreshing Vinted access token")
        vinted_api.get_access_token(force_refresh=True)
        logger.info("Successfully refreshed Vinted access token")
        
    except Exception as e:
        logger.error(f"Error refreshing Vinted token: {e}")


@background
def test_vinted_connection():
    """
    Test Vinted API connection
    """
    try:
        logger.info("Testing Vinted API connection")
        success = vinted_api.test_connection()
        
        if success:
            logger.info("Vinted API connection test passed")
        else:
            logger.error("Vinted API connection test failed")
            
        return success
        
    except Exception as e:
        logger.error(f"Error testing Vinted connection: {e}")
        return False


def start_monitoring():
    """
    Initialize the monitoring system
    """
    logger.info("Starting Vinted price monitoring system")
    
    # Test connection first
    test_vinted_connection.now()
    
    # Start the main monitoring loop with proper repeat scheduling
    monitor_price_watches(repeat=300)  # Every 5 minutes
    
    # Start token refresh cycle
    refresh_vinted_token(repeat=7200)  # Every 2 hours
    
    # Start cleanup cycle  
    cleanup_old_items(repeat=3600)  # Every hour
    
    logger.info("Price monitoring system started successfully")
    return True