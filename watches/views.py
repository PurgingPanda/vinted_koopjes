from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView, DetailView
from django.urls import reverse_lazy
from django.contrib import messages
from django.db.models import Count, Avg
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime, timedelta
from django.utils import timezone
import json
from .models import PriceWatch, VintedItem, UnderpriceAlert, PriceStatistics
from .forms import PriceWatchForm
from .utils import index_all_items, clear_and_reindex_items


class PriceWatchListView(LoginRequiredMixin, ListView):
    model = PriceWatch
    template_name = 'watches/list.html'
    context_object_name = 'watches'
    paginate_by = 10

    def get_queryset(self):
        return PriceWatch.objects.filter(user=self.request.user).annotate(
            alert_count=Count('underpricealert')
        )


class PriceWatchCreateView(LoginRequiredMixin, CreateView):
    model = PriceWatch
    form_class = PriceWatchForm
    template_name = 'watches/form.html'
    success_url = reverse_lazy('watch_list')

    def form_valid(self, form):
        form.instance.user = self.request.user
        messages.success(self.request, 'Price watch created successfully!')
        return super().form_valid(form)


class PriceWatchUpdateView(LoginRequiredMixin, UpdateView):
    model = PriceWatch
    form_class = PriceWatchForm
    template_name = 'watches/form.html'

    def get_queryset(self):
        return PriceWatch.objects.filter(user=self.request.user)

    def get_success_url(self):
        return reverse('watch_detail', kwargs={'pk': self.object.pk})

    def form_valid(self, form):
        messages.success(self.request, 'Price watch updated successfully!')
        return super().form_valid(form)


def get_upload_age_color(upload_date, oldest_date, newest_date):
    """
    Calculate color based on upload age relative to the range of dates
    Returns CSS classes for styling
    """
    if not upload_date or not oldest_date or not newest_date:
        return {'border_color': 'border-gray-200', 'bg_color': 'bg-gray-50', 'age_category': 'unknown'}
    
    # Calculate the age as a percentage of the total range
    total_range = (newest_date - oldest_date).total_seconds()
    
    if total_range <= 0:
        # All items uploaded at the same time
        return {'border_color': 'border-green-200', 'bg_color': 'bg-green-50', 'age_category': 'new'}
    
    item_age = (newest_date - upload_date).total_seconds()
    age_ratio = item_age / total_range  # 0 = newest, 1 = oldest
    
    # Create color gradient from green (newest) to red (oldest)
    if age_ratio <= 0.2:  # Newest 20% - Green
        return {'border_color': 'border-green-200', 'bg_color': 'bg-green-50', 'age_category': 'very_new'}
    elif age_ratio <= 0.4:  # 20-40% - Light Green
        return {'border_color': 'border-green-300', 'bg_color': 'bg-green-100', 'age_category': 'new'}
    elif age_ratio <= 0.6:  # 40-60% - Yellow
        return {'border_color': 'border-yellow-300', 'bg_color': 'bg-yellow-50', 'age_category': 'medium'}
    elif age_ratio <= 0.8:  # 60-80% - Orange
        return {'border_color': 'border-orange-300', 'bg_color': 'bg-orange-50', 'age_category': 'old'}
    else:  # Oldest 20% - Red
        return {'border_color': 'border-red-300', 'bg_color': 'bg-red-50', 'age_category': 'very_old'}


class PriceWatchDetailView(LoginRequiredMixin, DetailView):
    model = PriceWatch
    template_name = 'watches/detail.html'
    context_object_name = 'watch'

    def get_queryset(self):
        return PriceWatch.objects.filter(user=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        watch = self.object
        
        # Get recent alerts
        context['recent_alerts'] = UnderpriceAlert.objects.filter(
            price_watch=watch
        ).select_related('item')[:10]
        
        # Get price statistics
        context['statistics'] = PriceStatistics.objects.filter(
            price_watch=watch
        )
        
        # Get item count by condition using the new relationship
        context['item_stats'] = watch.items.values('condition').annotate(
            count=Count('id'),
            avg_price=Avg('price')
        )
        
        # Calculate price outliers
        outliers = self.get_price_outliers(watch)
        context['underpriced_items'] = outliers['underpriced']
        context['overpriced_items'] = outliers['overpriced']
        
        # Add item count
        context['total_items'] = watch.items.count()
        
        # Add histogram data for D3.js
        histogram_data = self.get_histogram_data(watch)
        context['histogram_data'] = histogram_data
        context['histogram_data_json'] = json.dumps(histogram_data, cls=DjangoJSONEncoder)
        
        return context
    
    def get_price_outliers(self, watch):
        """Get the biggest price outliers (underpriced and overpriced items), excluding blacklisted items"""
        from .utils import is_item_blacklisted, is_item_highlighted
        
        outliers = {'underpriced': [], 'overpriced': []}
        
        # Get statistics for each condition
        stats_by_condition = {
            stat.condition: stat for stat in 
            PriceStatistics.objects.filter(price_watch=watch)
        }
        
        for condition, stats in stats_by_condition.items():
            # Only calculate outliers if we have enough data
            if stats.item_count < 5 or stats.std_deviation == 0:
                continue
                
            mean_price = float(stats.mean_price)
            std_dev = float(stats.std_deviation)
            
            # Get items for this condition
            all_items = watch.items.filter(condition=condition).select_related()
            
            for item in all_items:
                # Check if item should be blacklisted
                item_data = {
                    'id': item.vinted_id,
                    'title': item.title or '',
                    'description': item.description or '',
                    'brand_title': item.brand or ''
                }
                
                if is_item_blacklisted(item_data, watch):
                    continue  # Skip blacklisted items
                
                # Check if item should be highlighted
                is_highlighted = is_item_highlighted(item_data, watch)
                
                # Check if this item has a hidden alert
                has_hidden_alert = UnderpriceAlert.objects.filter(
                    price_watch=watch,
                    item=item,
                    hidden=True
                ).exists()
                
                if has_hidden_alert:
                    continue  # Skip items with hidden alerts
                
                # Process non-blacklisted items
                item_price = float(item.price)
                z_score = (item_price - mean_price) / std_dev
                
                # Extract item details from database fields and API response
                api_data = item.api_response or {}
                item_info = {
                    'item': item,
                    'z_score': z_score,
                    'price_difference': item_price - mean_price,
                    'condition_name': item.get_condition_display(),
                    'title': item.title or f'Item {item.vinted_id}',
                    'brand': item.brand or 'Unknown',
                    'size': item.size or '',
                    'color': item.color or '',
                    'description': item.description or '',
                    'upload_date': item.upload_date,
                    'url': api_data.get('url', f'https://www.vinted.be/items/{item.vinted_id}'),
                    'photo_url': api_data.get('photo', {}).get('url') if api_data.get('photo') else None,
                    'is_highlighted': is_highlighted
                }
                
                # Collect all items with negative z-scores (below average)
                if z_score < 0:
                    outliers['underpriced'].append(item_info)
        
        # Sort by z-score (most underpriced items first)
        outliers['underpriced'].sort(key=lambda x: x['z_score'])
        
        # Calculate color grading based on upload dates
        if outliers['underpriced']:
            # Get upload date range
            upload_dates = [item['upload_date'] for item in outliers['underpriced'] if item['upload_date']]
            
            if upload_dates:
                oldest_date = min(upload_dates)
                newest_date = max(upload_dates)
                
                # Add color information to each item
                for item_info in outliers['underpriced']:
                    color_info = get_upload_age_color(item_info['upload_date'], oldest_date, newest_date)
                    item_info.update(color_info)
            else:
                # No upload dates available - use default gray styling for all items
                for item_info in outliers['underpriced']:
                    item_info.update({
                        'border_color': 'border-gray-200', 
                        'bg_color': 'bg-gray-50', 
                        'age_category': 'unknown'
                    })
        
        # Return all underpriced items (we'll paginate in the template/JS)
        return outliers
    
    def get_histogram_data(self, watch):
        """Get data for D3.js histograms, excluding blacklisted items"""
        from .utils import is_item_blacklisted, is_item_highlighted
        
        histogram_data = {}
        
        # Get statistics for each condition
        stats_by_condition = {
            stat.condition: stat for stat in 
            PriceStatistics.objects.filter(price_watch=watch)
        }
        
        for condition, stats in stats_by_condition.items():
            # Get all items for this condition
            all_items = watch.items.filter(condition=condition)
            
            # Filter out blacklisted items and extract prices
            prices = []
            for item in all_items:
                item_data = {
                    'id': item.vinted_id,
                    'title': item.title or '',
                    'description': item.description or '',
                    'brand_title': item.brand or ''
                }
                
                if not is_item_blacklisted(item_data, watch):
                    prices.append(float(item.price))
            
            if len(prices) < 2:
                continue
                
            # Prices are already float for D3.js
            prices_float = prices
            
            # Get condition name
            sample_item = watch.items.filter(condition=condition).first()
            condition_name = sample_item.get_condition_display() if sample_item else f'Condition {condition}'
            
            histogram_data[condition] = {
                'condition': condition,
                'condition_name': condition_name,
                'prices': prices_float,
                'mean': float(stats.mean_price),
                'std_dev': float(stats.std_deviation),
                'count': len(prices_float),
                'min_price': min(prices_float),
                'max_price': max(prices_float)
            }
        
        return histogram_data


class PriceWatchDeleteView(LoginRequiredMixin, DeleteView):
    model = PriceWatch
    template_name = 'watches/delete.html'
    success_url = reverse_lazy('watch_list')

    def get_queryset(self):
        return PriceWatch.objects.filter(user=self.request.user)

    def delete(self, request, *args, **kwargs):
        messages.success(request, 'Price watch deleted successfully!')
        return super().delete(request, *args, **kwargs)


def get_watch_outliers(watch, limit=None):
    """Helper function to get outliers for a specific watch - similar to get_price_outliers but reusable"""
    from .utils import is_item_blacklisted, is_item_highlighted
    
    outliers = {'underpriced': []}
    
    # Get statistics for each condition
    statistics = PriceStatistics.objects.filter(price_watch=watch)
    
    for stat in statistics:
        condition = stat.condition
        mean_price = float(stat.mean_price)
        std_dev = float(stat.std_deviation)
        
        if std_dev == 0:
            continue
            
        # Get items for this condition
        all_items = watch.items.filter(condition=condition).select_related()
        
        for item in all_items:
            # Check if item should be blacklisted
            item_data = {
                'id': item.vinted_id,
                'title': item.title or '',
                'description': item.description or '',
                'brand_title': item.brand or ''
            }
            
            if is_item_blacklisted(item_data, watch):
                continue  # Skip blacklisted items
                
            # Check if this item has a hidden alert
            has_hidden_alert = UnderpriceAlert.objects.filter(
                price_watch=watch,
                item=item,
                hidden=True
            ).exists()
            
            if has_hidden_alert:
                continue  # Skip items with hidden alerts
            
            # Check if item should be highlighted
            is_highlighted = is_item_highlighted(item_data, watch)
            
            # Process non-blacklisted items
            item_price = float(item.price)
            z_score = (item_price - mean_price) / std_dev
            
            # Only include underpriced items (negative z-score)
            if z_score < 0:
                # Extract item details from database fields and API response
                api_data = item.api_response or {}
                item_info = {
                    'item': item,
                    'watch': watch,
                    'z_score': z_score,
                    'price_difference': item_price - mean_price,
                    'condition_name': item.get_condition_display(),
                    'title': item.title or f'Item {item.vinted_id}',
                    'brand': item.brand or 'Unknown',
                    'size': item.size or '',
                    'color': item.color or '',
                    'description': item.description or '',
                    'upload_date': item.upload_date,
                    'url': api_data.get('url', f'https://www.vinted.be/items/{item.vinted_id}'),
                    'photo_url': api_data.get('photo', {}).get('url') if api_data.get('photo') else None,
                    'is_highlighted': is_highlighted
                }
                
                outliers['underpriced'].append(item_info)
    
    # Sort by z-score (most underpriced first) and limit if specified
    outliers['underpriced'].sort(key=lambda x: x['z_score'])
    if limit:
        outliers['underpriced'] = outliers['underpriced'][:limit]
    
    # Apply color grading based on upload dates
    if outliers['underpriced']:
        # Get upload date range for this watch's items
        upload_dates = [item['upload_date'] for item in outliers['underpriced'] if item['upload_date']]
        
        if upload_dates:
            oldest_date = min(upload_dates)
            newest_date = max(upload_dates)
            date_range = (newest_date - oldest_date).total_seconds()
            
            for item_info in outliers['underpriced']:
                upload_date = item_info['upload_date']
                if upload_date:
                    # Calculate relative age (0 = newest, 1 = oldest)
                    if date_range > 0:
                        age_ratio = (newest_date - upload_date).total_seconds() / date_range
                    else:
                        age_ratio = 0
                    
                    # Assign colors based on age
                    if age_ratio <= 0.2:  # Newest 20%
                        border_color = 'border-green-400'
                        bg_color = 'bg-green-50'
                        age_category = 'newest'
                    elif age_ratio <= 0.4:  # New 20-40%
                        border_color = 'border-green-300'
                        bg_color = 'bg-green-25'
                        age_category = 'new'
                    elif age_ratio <= 0.6:  # Medium 40-60%
                        border_color = 'border-yellow-400'
                        bg_color = 'bg-yellow-50'
                        age_category = 'medium'
                    elif age_ratio <= 0.8:  # Old 60-80%
                        border_color = 'border-orange-400'
                        bg_color = 'bg-orange-50'
                        age_category = 'old'
                    else:  # Oldest 80-100%
                        border_color = 'border-red-400'
                        bg_color = 'bg-red-50'
                        age_category = 'oldest'
                    
                    item_info['border_color'] = border_color
                    item_info['bg_color'] = bg_color
                    item_info['age_category'] = age_category
                else:
                    # Fallback for items without upload dates
                    item_info['border_color'] = 'border-gray-200'
                    item_info['bg_color'] = 'bg-gray-50'
                    item_info['age_category'] = 'unknown'
    
    return outliers


@login_required
def dashboard(request):
    """Dashboard showing user's watches and most underpriced items from all watches"""
    # Get number of items to display from request parameter
    items_limit = int(request.GET.get('items', 25))
    if items_limit not in [25, 50, 100, 500]:
        items_limit = 25
    
    watches = PriceWatch.objects.filter(user=request.user).annotate(
        alert_count=Count('underpricealert')
    )[:5]
    
    recent_alerts = UnderpriceAlert.objects.filter(
        price_watch__user=request.user,
        hidden=False  # Exclude hidden alerts
    ).select_related('item', 'price_watch')[:10]
    
    # Get most underpriced items from all user's watches
    most_underpriced = []
    user_watches = PriceWatch.objects.filter(user=request.user).prefetch_related('items')
    
    if user_watches:
        # Get more items per watch to ensure we have enough candidates
        # Request 2x the target per watch to have enough items for sorting
        items_per_watch = max(items_limit * 2 // len(user_watches), 50)
        
        for watch in user_watches:
            watch_outliers = get_watch_outliers(watch, limit=items_per_watch)
            most_underpriced.extend(watch_outliers.get('underpriced', []))
    
    # Sort all underpriced items by z-score (most underpriced first) and take requested amount
    most_underpriced.sort(key=lambda x: x['z_score'])
    most_underpriced = most_underpriced[:items_limit]
    
    # Get recent items for live feed
    recent_items = VintedItem.objects.filter(
        watches__user=request.user
    ).select_related().order_by('-first_seen')[:10]
    
    # Get price trend data for charts (last 30 days)
    from datetime import date, timedelta
    from .models import PriceTrend
    
    thirty_days_ago = date.today() - timedelta(days=30)
    price_trends = PriceTrend.objects.filter(
        price_watch__user=request.user,
        date__gte=thirty_days_ago
    ).order_by('date')
    
    # Organize trend data by watch and condition
    trend_data = {}
    for trend in price_trends:
        watch_name = trend.price_watch.name
        if watch_name not in trend_data:
            trend_data[watch_name] = {}
        if trend.condition not in trend_data[watch_name]:
            trend_data[watch_name][trend.condition] = []
        
        trend_data[watch_name][trend.condition].append({
            'date': trend.date.isoformat(),
            'avg_price': float(trend.avg_price),
            'min_price': float(trend.min_price),
            'max_price': float(trend.max_price),
            'item_count': trend.item_count
        })
    
    stats = {
        'total_watches': PriceWatch.objects.filter(user=request.user).count(),
        'active_watches': PriceWatch.objects.filter(user=request.user, is_active=True).count(),
        'total_alerts': UnderpriceAlert.objects.filter(price_watch__user=request.user).count(),
        'unsent_alerts': UnderpriceAlert.objects.filter(
            price_watch__user=request.user, 
            email_sent=False
        ).count(),
    }
    
    context = {
        'watches': watches,
        'recent_alerts': recent_alerts,
        'most_underpriced': most_underpriced,
        'recent_items': recent_items,
        'stats': stats,
        'items_limit': items_limit,
        'trend_data': trend_data,
        'trend_data_json': json.dumps(trend_data, cls=DjangoJSONEncoder),
    }
    
    return render(request, 'watches/dashboard.html', context)


@login_required
def test_watch_api(request, pk):
    """Test API for a specific price watch"""
    watch = get_object_or_404(PriceWatch, pk=pk, user=request.user)
    
    if request.method == 'POST':
        try:
            from .utils import fetch_and_process_items
            from .activity_logger import ActivityLogger
            
            # Log manual indexing activity
            with ActivityLogger('manual_index', watch) as activity_log:
                # Fetch more pages for manual indexing
                processed_count = fetch_and_process_items(watch, max_pages=10)
                activity_log.update_stats(items_processed=processed_count)
                
            messages.success(request, f'Successfully processed {processed_count} items!')
        except Exception as e:
            messages.error(request, f'Error processing items: {e}')
    
    return redirect('watch_detail', pk=pk)


@login_required
def parse_vinted_url(request):
    """AJAX endpoint to parse Vinted URL and return form data"""
    from django.http import JsonResponse
    from .url_parser import vinted_parser
    
    if request.method == 'POST':
        url = request.POST.get('url', '').strip()
        
        if not url:
            return JsonResponse({'error': 'No URL provided'}, status=400)
        
        try:
            parsed_data = vinted_parser.parse_vinted_url(url)
            
            if not parsed_data:
                return JsonResponse({
                    'error': 'Could not parse URL. Please make sure it\'s a valid Vinted catalog URL.'
                }, status=400)
            
            # Generate preview
            preview = vinted_parser.generate_search_preview(parsed_data)
            
            return JsonResponse({
                'success': True,
                'data': parsed_data,
                'preview': preview
            })
            
        except Exception as e:
            return JsonResponse({
                'error': f'Error parsing URL: {str(e)}'
            }, status=500)
    
    return JsonResponse({'error': 'Invalid request method'}, status=405)


@login_required
def index_all_watch_items(request, pk):
    """Index all items for a specific price watch"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'})
    
    try:
        watch = get_object_or_404(PriceWatch, pk=pk, user=request.user)
        
        # Get current item count
        current_count = watch.items.count()
        
        # Index all items
        processed_count = index_all_items(watch)
        
        # Get new item count
        new_count = watch.items.count()
        
        return JsonResponse({
            'success': True,
            'processed_count': processed_count,
            'items_before': current_count,
            'items_after': new_count,
            'new_items': new_count - current_count
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error indexing all items for watch {pk}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def load_more_underpriced(request, pk):
    """Load more underpriced items for a specific price watch"""
    if request.method != 'GET':
        return JsonResponse({'success': False, 'error': 'GET request required'})
    
    try:
        watch = get_object_or_404(PriceWatch, pk=pk, user=request.user)
        
        # Get pagination parameters
        offset = int(request.GET.get('offset', 0))
        limit = int(request.GET.get('limit', 50))
        
        # Get all underpriced items
        outliers = PriceWatchDetailView().get_price_outliers(watch)
        underpriced_items = outliers['underpriced']
        
        # Paginate results
        paginated_items = underpriced_items[offset:offset + limit]
        has_more = len(underpriced_items) > offset + limit
        
        # Format items for JSON response
        items_data = []
        for item_info in paginated_items:
            # Format upload age text
            upload_age_text = ''
            if item_info['upload_date']:
                from django.utils.timesince import timesince
                upload_age_text = f"{timesince(item_info['upload_date'])} ago"
            
            items_data.append({
                'title': item_info['title'],
                'brand': item_info['brand'],
                'size': item_info['size'],
                'color': item_info['color'],
                'description': item_info['description'],
                'condition_name': item_info['condition_name'],
                'price': float(item_info['item'].price),
                'price_difference': float(item_info['price_difference']),
                'z_score': item_info['z_score'],
                'url': item_info['url'],
                'photo_url': item_info['photo_url'],
                'border_color': item_info.get('border_color', 'border-gray-200'),
                'bg_color': item_info.get('bg_color', 'bg-gray-50'),
                'age_category': item_info.get('age_category', 'unknown'),
                'upload_age_text': upload_age_text,
                'is_highlighted': item_info.get('is_highlighted', False)
            })
        
        return JsonResponse({
            'success': True,
            'items': items_data,
            'has_more': has_more,
            'total_count': len(underpriced_items),
            'loaded_count': offset + len(paginated_items)
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error loading more underpriced items for watch {pk}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def clear_and_reindex_watch_items(request, pk):
    """Clear all existing items and re-index for a specific price watch"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'})
    
    try:
        watch = get_object_or_404(PriceWatch, pk=pk, user=request.user)
        
        # Perform clear and re-index
        result = clear_and_reindex_items(watch)
        
        if 'error' in result:
            return JsonResponse({
                'success': False, 
                'error': result['error']
            })
        
        return JsonResponse({
            'success': True,
            'items_before': result['items_before'],
            'items_after': result['items_after'],
            'new_items_processed': result['new_items_processed'],
            'cleared_statistics': result['cleared_statistics'],
            'cleared_alerts': result['cleared_alerts']
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error clearing and re-indexing items for watch {pk}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
def clear_alerts(request, pk):
    """Clear all alerts for a specific price watch"""
    if request.method != 'POST':
        return JsonResponse({'success': False, 'error': 'POST request required'})
    
    try:
        watch = get_object_or_404(PriceWatch, pk=pk, user=request.user)
        
        # Count alerts before clearing
        alerts_count = UnderpriceAlert.objects.filter(price_watch=watch).count()
        
        # Clear all alerts for this watch
        UnderpriceAlert.objects.filter(price_watch=watch).delete()
        
        return JsonResponse({
            'success': True,
            'cleared_count': alerts_count
        })
        
    except Exception as e:
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Error clearing alerts for watch {pk}: {e}")
        return JsonResponse({'success': False, 'error': str(e)})


@login_required
@require_POST
def hide_underpriced_item(request, watch_id, item_id):
    """Hide an underpriced item by marking the alert as hidden"""
    try:
        watch = get_object_or_404(PriceWatch, pk=watch_id, user=request.user)
        item = get_object_or_404(VintedItem, vinted_id=item_id)
        
        # Find or create the alert for this watch and item
        alert, created = UnderpriceAlert.objects.get_or_create(
            price_watch=watch,
            item=item,
            defaults={
                'price_difference': 0,  # Will be calculated properly later
                'std_deviations_below': 0,  # Will be calculated properly later
                'hidden': True
            }
        )
        
        # If alert already exists, just mark it as hidden
        if not created:
            alert.hidden = True
            alert.save()
        
        return JsonResponse({'success': True})
            
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=500)
