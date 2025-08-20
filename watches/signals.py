from django.db.models.signals import post_delete
from django.dispatch import receiver
from .models import PriceWatch, VintedItem, UnderpriceAlert
import logging

logger = logging.getLogger(__name__)


@receiver(post_delete, sender=PriceWatch)
def cleanup_orphaned_items(sender, instance, **kwargs):
    """
    Clean up VintedItems that are no longer associated with any PriceWatch
    when a PriceWatch is deleted.
    """
    print(f"🧹 Cleaning up after deleting PriceWatch: {instance.name}")
    logger.info(f"Cleaning up after deleting PriceWatch: {instance.name}")
    
    try:
        # Find VintedItems that are no longer associated with any watches
        orphaned_items = VintedItem.objects.filter(watches__isnull=True)
        orphaned_count = orphaned_items.count()
        
        if orphaned_count > 0:
            print(f"   🗑️ Deleting {orphaned_count} orphaned items")
            logger.info(f"Deleting {orphaned_count} orphaned VintedItems")
            
            # Delete orphaned items (this will cascade to alerts)
            orphaned_items.delete()
            
            print(f"   ✅ Cleaned up {orphaned_count} orphaned items")
        else:
            print("   ✅ No orphaned items to clean up")
            
    except Exception as e:
        print(f"   ❌ Error cleaning up orphaned items: {e}")
        logger.error(f"Error cleaning up orphaned items: {e}")


@receiver(post_delete, sender=PriceWatch)
def cleanup_orphaned_alerts(sender, instance, **kwargs):
    """
    Clean up UnderpriceAlerts associated with the deleted PriceWatch
    """
    try:
        # Delete alerts for this watch
        alerts_count = UnderpriceAlert.objects.filter(price_watch=instance).count()
        if alerts_count > 0:
            print(f"   🔔 Deleting {alerts_count} alerts for this watch")
            logger.info(f"Deleting {alerts_count} alerts for PriceWatch {instance.name}")
            UnderpriceAlert.objects.filter(price_watch=instance).delete()
            
    except Exception as e:
        print(f"   ❌ Error cleaning up alerts: {e}")
        logger.error(f"Error cleaning up alerts: {e}")