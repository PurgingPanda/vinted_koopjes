from django.contrib import admin
from .models import PriceWatch, VintedItem, PriceStatistics, UnderpriceAlert


@admin.register(PriceWatch)
class PriceWatchAdmin(admin.ModelAdmin):
    list_display = ['name', 'user', 'is_active', 'created_at', 'std_dev_threshold']
    list_filter = ['is_active', 'created_at', 'user']
    search_fields = ['name', 'user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (None, {
            'fields': ('name', 'user', 'is_active')
        }),
        ('Search Parameters', {
            'fields': ('search_parameters',),
            'classes': ('collapse',)
        }),
        ('Detection Settings', {
            'fields': ('std_dev_threshold', 'absolute_price_threshold', 'blacklist_words')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(VintedItem)
class VintedItemAdmin(admin.ModelAdmin):
    list_display = ['vinted_id', 'title_short', 'brand', 'size', 'color', 'price', 'get_condition_display', 'upload_date', 'is_active', 'first_seen']
    list_filter = ['condition', 'is_active', 'first_seen', 'upload_date', 'brand']
    search_fields = ['vinted_id', 'title', 'brand', 'description']
    readonly_fields = ['first_seen', 'last_seen']
    list_per_page = 25
    
    def title_short(self, obj):
        """Display truncated title for better readability in list view"""
        if obj.title:
            return obj.title[:50] + '...' if len(obj.title) > 50 else obj.title
        return f'Item {obj.vinted_id}'
    title_short.short_description = 'Title'
    
    fieldsets = (
        (None, {
            'fields': ('vinted_id', 'price', 'condition', 'is_active')
        }),
        ('Item Details', {
            'fields': ('title', 'brand', 'size', 'color', 'description', 'upload_date')
        }),
        ('API Data', {
            'fields': ('api_response',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('first_seen', 'last_seen'),
            'classes': ('collapse',)
        }),
    )


@admin.register(PriceStatistics)
class PriceStatisticsAdmin(admin.ModelAdmin):
    list_display = ['price_watch', 'condition', 'mean_price', 'std_deviation', 'item_count', 'last_calculated']
    list_filter = ['condition', 'last_calculated']
    search_fields = ['price_watch__name']
    readonly_fields = ['last_calculated']


@admin.register(UnderpriceAlert)
class UnderpriceAlertAdmin(admin.ModelAdmin):
    list_display = ['price_watch', 'item', 'price_difference', 'std_deviations_below', 'email_sent', 'detected_at']
    list_filter = ['email_sent', 'detected_at']
    search_fields = ['price_watch__name', 'item__vinted_id']
    readonly_fields = ['detected_at', 'email_sent_at']
