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


def get_monitor_schedule():
    """Get the current monitoring schedule based on blocking state"""
    from .models import BlockingState
    blocking_state = BlockingState.get_current_state()
    return blocking_state.get_blocked_check_interval()

@background(schedule=300)  # Initial schedule, will be dynamically updated
def monitor_price_watches():
    """
    Main background task that monitors all active price watches
    Schedule adjusts automatically: 5 minutes when active, 30 minutes when blocked
    """
    from .models import BlockingState
    
    with ActivityLogger('monitor') as activity_log:
        print("🔄 BACKGROUND TASK: Starting price watch monitoring cycle")
        logger.info("Starting price watch monitoring cycle")
        
        # Check blocking state
        blocking_state = BlockingState.get_current_state()
        current_schedule = blocking_state.get_blocked_check_interval()
        
        if blocking_state.is_blocked:
            print(f"🔒 API is BLOCKED - monitoring every {current_schedule//60} minutes")
            logger.info(f"API blocked since {blocking_state.blocked_since}, consecutive failures: {blocking_state.consecutive_failures}")
        else:
            print(f"✅ API is ACTIVE - monitoring every {current_schedule//60} minutes")
            
        # Process all active watches (blocking detection happens in individual watch processing)
        active_watches = PriceWatch.objects.filter(is_active=True)
        
        print(f"📊 Found {active_watches.count()} active price watches")
        logger.info(f"Found {active_watches.count()} active price watches")
        
        total_processed = 0
        for watch in active_watches:
            print(f"   • Scheduling check for: {watch.name}")
            # Schedule individual watch processing
            check_price_watch.now(watch.id)
            total_processed += 1
        
        # Clean up old inactive items only when not blocked
        if not blocking_state.is_blocked:
            cleanup_old_items.now()
        
        print("✅ Price watch monitoring cycle completed")
        
        # Update activity stats
        activity_log.update_stats(items_processed=total_processed)
        
        # Reschedule next run based on current blocking state
        monitor_price_watches(schedule=current_schedule)


@background
def check_price_watch(watch_id: int):
    """
    Process a specific price watch with automatic blocking detection
    """
    from .models import BlockingState
    
    watch = None
    try:
        watch = PriceWatch.objects.get(id=watch_id, is_active=True)
        
        with ActivityLogger('check_watch', watch) as activity_log:
            print(f"🔍 Processing price watch: {watch.name}")
            logger.info(f"Processing price watch: {watch.name}")
            
            # Fetch and process items
            processed_count = fetch_and_process_items(watch)
            
            # If we get here successfully, mark API as unblocked
            blocking_state = BlockingState.get_current_state()
            if blocking_state.is_blocked:
                print(f"✅ API RECOVERED: Watch {watch.name} processed successfully - marking API as unblocked")
                logger.info(f"API recovery detected during normal processing of watch {watch.name}")
                blocking_state.mark_unblocked()
            
            print(f"📈 Completed processing watch {watch.name}: {processed_count} items processed")
            logger.info(f"Completed processing watch {watch.name}: {processed_count} items processed")
            
            # Update activity stats
            activity_log.update_stats(items_processed=processed_count)
            
    except PriceWatch.DoesNotExist:
        print(f"⚠️ Price watch {watch_id} not found or inactive")
        logger.warning(f"Price watch {watch_id} not found or inactive")
    except Exception as e:
        error_msg = str(e).lower()
        
        # Check if this is a 403/blocking error
        if "403" in error_msg or "blocked" in error_msg or "forbidden" in error_msg:
            blocking_state = BlockingState.get_current_state()
            blocking_state.mark_blocked()
            print(f"🔒 API BLOCKED: Detected 403/blocking error - switching to 30-minute monitoring")
            logger.warning(f"API blocking detected for watch {watch_id}: {e}")
        else:
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
    Initialize the monitoring system with adaptive scheduling
    """
    logger.info("Starting Vinted price monitoring system with adaptive scheduling")
    
    # Test connection first
    test_vinted_connection.now()
    
    # Start the main monitoring loop (schedule adapts automatically based on blocking state)
    monitor_price_watches(repeat=get_monitor_schedule())  # Adaptive: 5 min active, 30 min blocked
    
    # Start token refresh cycle
    refresh_vinted_token(repeat=7200)  # Every 2 hours
    
    # Start cleanup cycle  
    cleanup_old_items(repeat=3600)  # Every hour
    
    logger.info("Adaptive price monitoring system started successfully")
    return True