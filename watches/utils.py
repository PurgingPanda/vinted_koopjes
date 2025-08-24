import logging
from typing import Dict, List, Any
from decimal import Decimal
from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.conf import settings
import statistics
import math

from .models import PriceWatch, VintedItem, PriceStatistics, UnderpriceAlert
from .services import VintedAPI, VintedAPIError

logger = logging.getLogger(__name__)


def is_item_blacklisted(item_data: Dict[str, Any], price_watch: PriceWatch) -> bool:
    """
    Check if an item should be blacklisted based on price watch blacklist words
    """
    if not price_watch.blacklist_words.strip():
        return False
    
    # Get blacklist words (comma-separated, case-insensitive)
    blacklist_words = [word.strip().lower() for word in price_watch.blacklist_words.split(',') if word.strip()]
    
    if not blacklist_words:
        return False
    
    # Check title and description for blacklist words
    title = item_data.get('title', '').lower()
    description = item_data.get('description', '').lower()
    brand_title = item_data.get('brand_title', '').lower()
    
    search_text = f"{title} {description} {brand_title}"
    
    for blacklist_word in blacklist_words:
        if blacklist_word in search_text:
            logger.info(f"Item {item_data.get('id')} blacklisted due to word: '{blacklist_word}'")
            return True
    
    return False


def is_item_highlighted(item_data: Dict[str, Any], price_watch: PriceWatch) -> bool:
    """
    Check if an item should be highlighted based on price watch highlight words
    """
    if not price_watch.highlight_words.strip():
        return False
    
    # Get highlight words (comma-separated, case-insensitive)
    highlight_words = [word.strip().lower() for word in price_watch.highlight_words.split(',') if word.strip()]
    
    if not highlight_words:
        return False
    
    # Check title and description for highlight words
    title = item_data.get('title', '').lower()
    description = item_data.get('description', '').lower()
    brand_title = item_data.get('brand_title', '').lower()
    
    search_text = f"{title} {description} {brand_title}"
    
    for highlight_word in highlight_words:
        if highlight_word in search_text:
            logger.info(f"Item {item_data.get('id')} highlighted due to word: '{highlight_word}'")
            return True
    
    return False


def process_item(item_data: Dict[str, Any], price_watch: PriceWatch) -> VintedItem:
    """
    Process a single item from Vinted API response
    """
    try:
        vinted_id = item_data.get('id')
        if not vinted_id:
            logger.warning("Item missing ID, skipping")
            return None
        
        # Check if item is blacklisted
        if is_item_blacklisted(item_data, price_watch):
            logger.info(f"Skipping blacklisted item {vinted_id}")
            return None
        
        # Extract price
        price_data = item_data.get('price', {})
        if isinstance(price_data, dict):
            price_amount = price_data.get('amount')
        else:
            price_amount = price_data
        
        if not price_amount:
            logger.warning(f"Item {vinted_id} missing price, skipping")
            return None
        
        price = Decimal(str(price_amount))
        
        # Extract condition (status_id)
        condition = item_data.get('status_id')
        
        # If condition is text, map it to numeric value
        if isinstance(condition, str) or condition is None:
            status_text = item_data.get('status', '').lower()
            condition_mapping = {
                'new with tags': 6,
                'new without tags': 1, 
                'very good': 2,
                'good': 3,
                'satisfactory': 4,  # This was causing the error
                'heavily used': 4,  # Map both to same ID
            }
            condition = condition_mapping.get(status_text, 2)  # Default to "Very good"
        
        # Extract additional fields
        title = item_data.get('title', '')
        brand = item_data.get('brand_title', '')
        size = item_data.get('size_title', '') or item_data.get('size', '')
        color = item_data.get('color', '') or item_data.get('colour', '')
        description = item_data.get('description', '')
        
        # Extract seller information
        user_data = item_data.get('user', {})
        seller_id = user_data.get('id') if user_data else None
        seller_login = user_data.get('login', '') if user_data else ''
        seller_business = user_data.get('is_business_account', False) if user_data else False
        
        # Extract upload date from timestamp
        upload_date = None
        timestamp = None
        
        # Try different timestamp sources in order of preference
        if 'timestamp' in item_data:
            timestamp = item_data['timestamp']
        elif item_data.get('photo', {}).get('high_resolution', {}).get('timestamp'):
            timestamp = item_data['photo']['high_resolution']['timestamp']
        
        if timestamp:
            try:
                from datetime import datetime
                import pytz
                
                # Handle Unix timestamp (integer)
                if isinstance(timestamp, (int, float)):
                    upload_date = datetime.fromtimestamp(timestamp, tz=pytz.UTC)
                # Handle ISO string format
                elif isinstance(timestamp, str):
                    if timestamp.isdigit():
                        upload_date = datetime.fromtimestamp(int(timestamp), tz=pytz.UTC)
                    else:
                        upload_date = datetime.fromisoformat(timestamp.replace('Z', '+00:00'))
                        
            except (ValueError, AttributeError, OSError) as e:
                logger.warning(f"Could not parse timestamp for item {vinted_id}: {timestamp} - {e}")
        
        # Extract additional API fields
        favourite_count = item_data.get('favourite_count')
        view_count = item_data.get('view_count') 
        
        # Extract service fee
        service_fee_data = item_data.get('service_fee', {})
        service_fee = None
        if isinstance(service_fee_data, dict) and 'amount' in service_fee_data:
            service_fee = Decimal(str(service_fee_data['amount']))
        
        # Extract total item price
        total_item_price_data = item_data.get('total_item_price', {})
        total_item_price = None
        if isinstance(total_item_price_data, dict) and 'amount' in total_item_price_data:
            total_item_price = Decimal(str(total_item_price_data['amount']))
        
        # Get or create item
        item, created = VintedItem.objects.get_or_create(
            vinted_id=vinted_id,
            defaults={
                'price': price,
                'condition': condition,
                'title': title,
                'brand': brand,
                'size': size,
                'color': color,
                'description': description,
                'upload_date': upload_date,
                'seller_id': seller_id,
                'seller_login': seller_login,
                'seller_business': seller_business,
                'favourite_count': favourite_count,
                'view_count': view_count,
                'service_fee': service_fee,
                'total_item_price': total_item_price,
                'api_response': item_data,
                'is_active': True
            }
        )
        
        if not created:
            # Update existing item
            item.price = price
            item.condition = condition
            item.title = title
            item.brand = brand
            item.size = size
            item.color = color
            item.description = description
            item.upload_date = upload_date
            item.seller_id = seller_id
            item.seller_login = seller_login
            item.seller_business = seller_business
            item.favourite_count = favourite_count
            item.view_count = view_count
            item.service_fee = service_fee
            item.total_item_price = total_item_price
            item.api_response = item_data
            item.last_seen = timezone.now()
            item.is_active = True
            item.save()
        
        # Associate item with this price watch
        price_watch.items.add(item)
        
        # Check if item is underpriced
        check_underpriced_item(item, price_watch)
        
        return item
        
    except Exception as e:
        import traceback
        logger.error(f"Error processing item {item_data.get('id', 'unknown')}: {e}")
        logger.error(f"Full traceback: {traceback.format_exc()}")
        print(f"🚨 ERROR processing item {item_data.get('id', 'unknown')}: {e}")
        return None


def calculate_price_statistics(price_watch: PriceWatch, condition: int = None):
    """
    Calculate price statistics for items in a price watch (excluding blacklisted items)
    """
    try:
        # Get all items for this price watch through the many-to-many relationship
        query = price_watch.items.all()
        
        if condition is not None:
            query = query.filter(condition=condition)
        
        # Group by condition if no specific condition provided
        if condition is None:
            conditions = query.values_list('condition', flat=True).distinct()
            for cond in conditions:
                calculate_price_statistics(price_watch, cond)
            return
        
        all_items = list(query.filter(condition=condition))
        
        # Filter out blacklisted items from statistics calculation
        items = []
        for item in all_items:
            # Reconstruct item data to check blacklist
            item_data = {
                'id': item.vinted_id,
                'title': item.title or '',
                'description': item.description or '',
                'brand_title': item.brand or ''
            }
            
            if not is_item_blacklisted(item_data, price_watch):
                items.append(item)
            else:
                logger.debug(f"Excluding blacklisted item {item.vinted_id} from statistics")
        
        
        if len(items) < 2:
            logger.info(f"Not enough items ({len(items)}) for statistics calculation")
            return
        
        prices = [float(item.price) for item in items]
        
        mean_price = statistics.mean(prices)
        std_deviation = statistics.stdev(prices) if len(prices) > 1 else 0
        
        # Update or create statistics
        stats, created = PriceStatistics.objects.update_or_create(
            price_watch=price_watch,
            condition=condition,
            defaults={
                'mean_price': Decimal(str(round(mean_price, 2))),
                'std_deviation': Decimal(str(round(std_deviation, 2))),
                'item_count': len(items)
            }
        )
        
        logger.info(f"Updated statistics for watch {price_watch.name}, condition {condition}: "
                   f"mean={mean_price:.2f}, std={std_deviation:.2f}, count={len(items)}")
        
    except Exception as e:
        logger.error(f"Error calculating price statistics: {e}")


def check_underpriced_item(item: VintedItem, price_watch: PriceWatch) -> bool:
    """
    Check if an item is underpriced based on watch criteria
    """
    try:
        # Get statistics for this item's condition
        try:
            stats = PriceStatistics.objects.get(
                price_watch=price_watch,
                condition=item.condition
            )
        except PriceStatistics.DoesNotExist:
            # No statistics available yet
            logger.info(f"No statistics available for condition {item.condition}")
            return False
        
        item_price = float(item.price)
        mean_price = float(stats.mean_price)
        std_deviation = float(stats.std_deviation)
        
        is_underpriced = False
        price_difference = mean_price - item_price
        std_deviations_below = 0
        
        # Check statistical threshold
        if std_deviation > 0:
            std_deviations_below = (mean_price - item_price) / std_deviation
            if std_deviations_below >= price_watch.std_dev_threshold:
                is_underpriced = True
        
        # Check absolute price threshold
        if (price_watch.absolute_price_threshold and 
            item_price <= float(price_watch.absolute_price_threshold)):
            is_underpriced = True
        
        if is_underpriced:
            # Create alert if it doesn't exist
            alert, created = UnderpriceAlert.objects.get_or_create(
                price_watch=price_watch,
                item=item,
                defaults={
                    'price_difference': Decimal(str(round(price_difference, 2))),
                    'std_deviations_below': std_deviations_below
                }
            )
            
            if created:
                logger.info(f"Created underprice alert for item {item.vinted_id} "
                           f"in watch {price_watch.name}")
                
                # Send email notification
                send_alert_email(alert)
        
        return is_underpriced
        
    except Exception as e:
        logger.error(f"Error checking underpriced item {item.vinted_id}: {e}")
        return False


def send_alert_email(alert: UnderpriceAlert):
    """
    Send email notification for an underprice alert
    """
    try:
        if alert.email_sent:
            return
        
        user = alert.price_watch.user
        item = alert.item
        
        # Extract item details from API response
        api_data = item.api_response
        title = api_data.get('title', f'Item {item.vinted_id}')
        brand = api_data.get('brand', {}).get('title', 'Unknown Brand')
        url = api_data.get('url', f'https://www.vinted.be/items/{item.vinted_id}')
        
        # Format the email
        subject = f'Price Alert: {title} - €{item.price}'
        
        message = f"""
Hello {user.username},

Great news! We found an underpriced item matching your watch "{alert.price_watch.name}":

📦 Item: {title}
🏷️  Brand: {brand}
💰 Price: €{item.price}
📉 Below average by: €{alert.price_difference} ({alert.std_deviations_below:.1f} standard deviations)
🔗 Link: {url}

Condition: {item.get_condition_display()}

Don't miss out on this deal!

Best regards,
Vinted Price Watch Team
        """
        
        # Send email
        send_mail(
            subject=subject,
            message=message.strip(),
            from_email=settings.DEFAULT_FROM_EMAIL if hasattr(settings, 'DEFAULT_FROM_EMAIL') else 'noreply@vintedwatch.com',
            recipient_list=[user.email],
            fail_silently=True
        )
        
        # Mark as sent
        alert.email_sent = True
        alert.email_sent_at = timezone.now()
        alert.save()
        
        logger.info(f"Sent email alert to {user.email} for item {item.vinted_id}")
        
    except Exception as e:
        logger.error(f"Error sending email alert: {e}")


def fetch_and_process_items(price_watch: PriceWatch, max_pages: int = 5) -> int:
    """
    Fetch items for a price watch and process them
    
    Args:
        price_watch: The price watch to process
        max_pages: Maximum number of pages to fetch (default: 1)
    """
    try:
        print(f"🔍 Processing price watch: {price_watch.name} (fetching up to {max_pages} pages)")
        logger.info(f"Processing price watch: {price_watch.name} (max {max_pages} pages)")
        
        processed_count = 0
        
        # Process multiple pages
        for page in range(1, max_pages + 1):
            try:
                # Update search parameters with current page
                search_params = price_watch.search_parameters.copy()
                search_params['page'] = page
                
                # Set default order to newest_first if not specified
                if 'order' not in search_params:
                    search_params['order'] = 'newest_first'
                
                print(f"   📄 Fetching page {page}...")
                logger.info(f"Fetching page {page} for watch {price_watch.name}")
                
                # Fetch items from Vinted API
                vinted_api = VintedAPI()
                items_data = vinted_api.search_items(search_params)
                
                if not items_data:
                    print(f"   ⚠️ No items found on page {page}, stopping pagination")
                    logger.info(f"No items found on page {page}, stopping")
                    break
                
                for item_data in items_data:
                    try:
                        with transaction.atomic():
                            print(f"🔄 Processing item {item_data.get('id', 'unknown')}...")
                            item = process_item(item_data, price_watch)
                            if item:
                                processed_count += 1
                                print(f"✅ Successfully processed item {item.vinted_id}")
                            else:
                                print(f"❌ process_item returned None for item {item_data.get('id', 'unknown')}")
                    except Exception as e:
                        import traceback
                        logger.error(f"Failed to process item in transaction: {e}")
                        logger.error(f"Transaction traceback: {traceback.format_exc()}")
                        print(f"🚨 TRANSACTION ERROR for item {item_data.get('id', 'unknown')}: {e}")
                        continue
                
                print(f"   ✅ Page {page}: {len(items_data)} items fetched")
                logger.info(f"Processed page {page}: {len(items_data)} items")
                
                # Add human-like delay between pages (except for the last page)
                if page < max_pages and len(items_data) > 0:
                    import random
                    import time
                    
                    # Normal distribution with mean=30, std_dev=8 (most delays between 14-46 seconds)
                    delay = max(5, random.normalvariate(30, 8))  # Minimum 5 seconds
                    delay = min(delay, 60)  # Maximum 60 seconds
                    
                    print(f"   ⏳ Waiting {delay:.1f} seconds before next page...")
                    logger.info(f"Waiting {delay:.1f} seconds before fetching page {page + 1}")
                    time.sleep(delay)
                
            except VintedAPIError as e:
                error_msg = str(e).lower()
                if "403" in error_msg or "blocking" in error_msg:
                    print(f"   🔒 Temporary blocking detected on page {page}, skipping remaining pages")
                    logger.warning(f"Temporary blocking on page {page} for watch {price_watch.name}: {e}")
                    # Don't break completely, just stop this watch and continue with others
                    break
                else:
                    logger.error(f"Vinted API error on page {page} for watch {price_watch.name}: {e}")
                    break
            except Exception as e:
                logger.error(f"Error processing page {page} for watch {price_watch.name}: {e}")
                break
        
        # Recalculate statistics after processing new items
        calculate_price_statistics(price_watch)
        
        print(f"📊 Total processed: {processed_count} items for watch {price_watch.name}")
        logger.info(f"Processed total {processed_count} items for watch {price_watch.name}")
        return processed_count
        
    except Exception as e:
        logger.error(f"Error processing watch {price_watch.name}: {e}")
        return 0


def index_all_items(price_watch: PriceWatch) -> int:
    """
    Index all available items across all pages for a price watch
    """
    try:
        # Start with a high number and let it break when no more items
        # Vinted typically shows max 5000 results across ~52 pages (96 per page)
        max_pages = 50
        return fetch_and_process_items(price_watch, max_pages)
        
    except Exception as e:
        logger.error(f"Error indexing all items for watch {price_watch.name}: {e}")
        return 0


def clear_and_reindex_items(price_watch: PriceWatch) -> dict:
    """
    Clear all existing item associations and re-index with current criteria
    
    Returns:
        dict: Statistics about the operation
    """
    try:
        logger.info(f"Clearing and re-indexing items for watch: {price_watch.name}")
        
        # Get counts before clearing
        items_before = price_watch.items.count()
        
        # Clear all existing item associations
        price_watch.items.clear()
        logger.info(f"Cleared {items_before} existing item associations")
        
        # Clear existing statistics to force recalculation
        PriceStatistics.objects.filter(price_watch=price_watch).delete()
        logger.info("Cleared existing price statistics")
        
        # Clear existing alerts since they may no longer be relevant
        UnderpriceAlert.objects.filter(price_watch=price_watch).delete()
        logger.info("Cleared existing underprice alerts")
        
        # Re-index all items with current criteria
        new_items_count = index_all_items(price_watch)
        
        # Get final count
        items_after = price_watch.items.count()
        
        result = {
            'items_before': items_before,
            'items_after': items_after,
            'new_items_processed': new_items_count,
            'cleared_statistics': True,
            'cleared_alerts': True
        }
        
        logger.info(f"Clear and re-index completed: {items_before} → {items_after} items")
        return result
        
    except Exception as e:
        logger.error(f"Error clearing and re-indexing items for watch {price_watch.name}: {e}")
        return {
            'error': str(e),
            'items_before': 0,
            'items_after': 0,
            'new_items_processed': 0
        }