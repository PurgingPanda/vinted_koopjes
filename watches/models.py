from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse


class PriceWatch(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_parameters = models.JSONField()  # All Vinted API parameters
    std_dev_threshold = models.FloatField(default=1.5)
    absolute_price_threshold = models.DecimalField(
        max_digits=10, decimal_places=2, null=True, blank=True
    )
    # Blacklist words in description/title (comma-separated)
    blacklist_words = models.TextField(
        blank=True, 
        help_text="Comma-separated words to exclude items from calculations. Items containing these words in title/description will be ignored."
    )
    # Highlight words in description/title (comma-separated)
    highlight_words = models.TextField(
        blank=True,
        help_text="Comma-separated words to highlight items with thick double border. Items containing these words in title/description will be visually highlighted."
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    # Track which items were found for this watch
    items = models.ManyToManyField('VintedItem', blank=True, related_name='watches')
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
    
    def get_absolute_url(self):
        return reverse('watch_detail', kwargs={'pk': self.pk})
    
    class Meta:
        verbose_name = "Price Watch"
        verbose_name_plural = "Price Watches"
        ordering = ['-created_at']


class VintedItem(models.Model):
    vinted_id = models.IntegerField(unique=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    condition = models.IntegerField()  # status_id from API
    
    # Extracted fields for efficient queries
    title = models.CharField(max_length=500, null=True, blank=True)
    brand = models.CharField(max_length=200, null=True, blank=True)
    size = models.CharField(max_length=100, null=True, blank=True)
    color = models.CharField(max_length=100, null=True, blank=True)
    description = models.TextField(null=True, blank=True)
    upload_date = models.DateTimeField(null=True, blank=True, help_text="When the item was uploaded to Vinted (from API timestamp)")
    
    # Seller information
    seller_id = models.IntegerField(null=True, blank=True, help_text="Vinted user ID of the seller")
    seller_login = models.CharField(max_length=200, null=True, blank=True, help_text="Seller's username/login")
    seller_business = models.BooleanField(default=False, help_text="Whether seller is a business account")
    
    # Additional API fields
    favourite_count = models.IntegerField(null=True, blank=True, help_text="Number of users who favorited this item")
    view_count = models.IntegerField(null=True, blank=True, help_text="Number of times this item was viewed")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Vinted's service fee for this item")
    total_item_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total price including fees")
    
    # Complete API response for additional data
    api_response = models.JSONField()
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        title_part = f"{self.title[:30]}..." if self.title and len(self.title) > 30 else (self.title or f"Item {self.vinted_id}")
        return f"{title_part} - €{self.price}"
    
    def get_condition_display(self):
        condition_map = {
            6: "As new with price tag",
            1: "As new without price tag", 
            2: "Very good",
            3: "Good",
            4: "Satisfactory/Heavily used"  # Combined since both map to 4
        }
        return condition_map.get(self.condition, "Unknown")
    
    class Meta:
        indexes = [
            models.Index(fields=['condition', 'price']),
            models.Index(fields=['vinted_id']),
            models.Index(fields=['upload_date']),
            models.Index(fields=['first_seen']),
            models.Index(fields=['seller_id']),
            models.Index(fields=['seller_login']),
            models.Index(fields=['last_seen']),
            models.Index(fields=['is_active']),
            models.Index(fields=['condition', 'upload_date']),
            models.Index(fields=['price', 'upload_date']),
        ]
        ordering = ['-first_seen']


class PriceStatistics(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    condition = models.IntegerField()
    mean_price = models.DecimalField(max_digits=10, decimal_places=2)
    std_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField()
    last_calculated = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.price_watch.name} - Condition {self.condition}"
    
    class Meta:
        unique_together = ['price_watch', 'condition']
        verbose_name = "Price Statistics"
        verbose_name_plural = "Price Statistics"


class UnderpriceAlert(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    item = models.ForeignKey(VintedItem, on_delete=models.CASCADE)
    detected_at = models.DateTimeField(auto_now_add=True)
    price_difference = models.DecimalField(max_digits=10, decimal_places=2)
    std_deviations_below = models.FloatField()
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    hidden = models.BooleanField(default=False, help_text="Hide this alert from display")
    
    def __str__(self):
        return f"Alert for {self.item} in {self.price_watch.name}"
    
    class Meta:
        unique_together = ['price_watch', 'item']
        indexes = [
            models.Index(fields=['price_watch', 'hidden']),
            models.Index(fields=['detected_at']),
            models.Index(fields=['hidden']),
            models.Index(fields=['email_sent']),
        ]
        verbose_name = "Underprice Alert"
        verbose_name_plural = "Underprice Alerts"
        ordering = ['-detected_at']


class PriceTrend(models.Model):
    """Track price trends over time for analysis"""
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    condition = models.IntegerField()
    date = models.DateField()
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField()
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"{self.price_watch.name} - {self.date} - Condition {self.condition}"
    
    class Meta:
        unique_together = ['price_watch', 'condition', 'date']
        indexes = [
            models.Index(fields=['price_watch', 'date']),
            models.Index(fields=['date']),
            models.Index(fields=['condition', 'date']),
        ]
        ordering = ['-date']


class ScrapeActivity(models.Model):
    """Track background task execution and scraping activity"""
    TASK_TYPES = [
        ('monitor', 'Monitor Price Watches'),
        ('check_watch', 'Check Individual Watch'),
        ('cleanup', 'Cleanup Old Items'),
        ('token_refresh', 'Token Refresh'),
        ('manual_index', 'Manual Index All'),
    ]
    
    STATUS_CHOICES = [
        ('started', 'Started'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
    ]
    
    task_type = models.CharField(max_length=20, choices=TASK_TYPES)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='started')
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE, null=True, blank=True, help_text="Related watch (if applicable)")
    items_processed = models.IntegerField(default=0, help_text="Number of items processed")
    pages_fetched = models.IntegerField(default=0, help_text="Number of pages fetched from API")
    new_items_found = models.IntegerField(default=0, help_text="Number of new items discovered")
    alerts_generated = models.IntegerField(default=0, help_text="Number of new alerts generated")
    error_message = models.TextField(blank=True, help_text="Error details if task failed")
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True, help_text="Task duration in seconds")
    
    class Meta:
        ordering = ['-started_at']
        indexes = [
            models.Index(fields=['task_type', '-started_at']),
            models.Index(fields=['status', '-started_at']),
            models.Index(fields=['price_watch', '-started_at']),
        ]
    
    def __str__(self):
        watch_info = f" ({self.price_watch.name})" if self.price_watch else ""
        return f"{self.get_task_type_display()}{watch_info} - {self.get_status_display()} at {self.started_at}"
    
    def save(self, *args, **kwargs):
        # Calculate duration if completed
        if self.completed_at and self.started_at:
            self.duration_seconds = (self.completed_at - self.started_at).total_seconds()
        super().save(*args, **kwargs)


