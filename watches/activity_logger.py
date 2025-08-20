from django.utils import timezone
from .models import ScrapeActivity, PriceWatch
import logging

logger = logging.getLogger(__name__)


class ActivityLogger:
    """Context manager for logging scraping activities"""
    
    def __init__(self, task_type, price_watch=None):
        self.task_type = task_type
        self.price_watch = price_watch
        self.activity = None
        
    def __enter__(self):
        """Start logging the activity"""
        self.activity = ScrapeActivity.objects.create(
            task_type=self.task_type,
            price_watch=self.price_watch,
            status='started'
        )
        print(f"📝 Started logging {self.task_type} activity (ID: {self.activity.id})")
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Complete the activity log"""
        if exc_type is None:
            # Success
            self.activity.status = 'completed'
            self.activity.completed_at = timezone.now()
            print(f"✅ Completed {self.task_type} activity - {self.activity.items_processed} items processed")
        else:
            # Error occurred
            self.activity.status = 'failed'
            self.activity.completed_at = timezone.now()
            self.activity.error_message = f"{exc_type.__name__}: {exc_val}"
            print(f"❌ Failed {self.task_type} activity: {exc_val}")
        
        self.activity.save()
        
    def update_stats(self, items_processed=0, pages_fetched=0, new_items_found=0, alerts_generated=0):
        """Update activity statistics"""
        if self.activity:
            self.activity.items_processed += items_processed
            self.activity.pages_fetched += pages_fetched
            self.activity.new_items_found += new_items_found
            self.activity.alerts_generated += alerts_generated
            self.activity.save()


def log_activity(task_type, price_watch=None):
    """Decorator for logging function activities"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with ActivityLogger(task_type, price_watch) as logger:
                result = func(*args, **kwargs)
                # Try to extract stats from result if it's a dict
                if isinstance(result, dict):
                    logger.update_stats(**result)
                return result
        return wrapper
    return decorator


def get_recent_activities(hours=24, task_type=None):
    """Get recent scraping activities"""
    cutoff = timezone.now() - timezone.timedelta(hours=hours)
    activities = ScrapeActivity.objects.filter(started_at__gte=cutoff)
    
    if task_type:
        activities = activities.filter(task_type=task_type)
        
    return activities.order_by('-started_at')


def get_activity_summary():
    """Get summary of recent activities for dashboard"""
    from datetime import timedelta
    
    now = timezone.now()
    last_24h = now - timedelta(hours=24)
    last_hour = now - timedelta(hours=1)
    
    summary = {
        'last_24h': {
            'total': ScrapeActivity.objects.filter(started_at__gte=last_24h).count(),
            'completed': ScrapeActivity.objects.filter(started_at__gte=last_24h, status='completed').count(),
            'failed': ScrapeActivity.objects.filter(started_at__gte=last_24h, status='failed').count(),
        },
        'last_hour': {
            'total': ScrapeActivity.objects.filter(started_at__gte=last_hour).count(),
            'completed': ScrapeActivity.objects.filter(started_at__gte=last_hour, status='completed').count(),
            'failed': ScrapeActivity.objects.filter(started_at__gte=last_hour, status='failed').count(),
        },
        'last_activity': ScrapeActivity.objects.order_by('-started_at').first(),
    }
    
    return summary