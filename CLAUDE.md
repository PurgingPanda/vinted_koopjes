# Vinted Price Watch Django Application

## Project Overview
A Django-based web application that monitors Vinted listings for underpriced items based on statistical analysis and user-defined price thresholds. Users create "price watches" with search parameters, and the system continuously monitors for deals.

## Tech Stack
- **Backend**: Django with SQLite database
- **Frontend**: Tailwind CSS
- **API Integration**: Vinted API with Playwright for token management
- **Background Tasks**: Django background tasks for continuous monitoring
- **Notifications**: Email notifications for immediate alerts
- **Testing**: Playwright MCP for frontend layout verification

## Core Features

### 1. Price Watch Management
- Users create named price watches with search parameters
- Each watch stores Vinted API search parameters (search_text, catalog_ids, price_to, brand_ids, etc.)
- Support for all Vinted API parameters from the search endpoint

### 2. Item Condition Tracking
- Track items by condition using Vinted status_ids:
  - 6: As new with price tag
  - 1: As new without price tag
  - 2: Very good
  - 3: Good
  - 4: Heavily used
- Separate price statistics per condition
- Condition-aware underpricing detection

### 3. Statistical Price Analysis
- Generate histograms of item prices per condition
- Calculate mean and standard deviation for each condition
- Configurable underpricing detection:
  - Statistical method: Items below X standard deviations (user configurable)
  - Absolute price: Items below user-defined price threshold
  - Both methods can be used simultaneously

### 4. Continuous Monitoring
- Background tasks continuously poll Vinted API
- Index all items found in searches
- Store complete API response data for all items
- Detect newly listed underpriced items
- Immediate email notifications when deals are found

### 5. Authentication & API Management
- Use Playwright to obtain `access_token_web` cookie from Vinted homepage
- Manage cookie refresh automatically
- Handle rate limiting and API errors gracefully

## Data Models

### PriceWatch
```python
class PriceWatch(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_parameters = models.JSONField()  # All Vinted API parameters
    std_dev_threshold = models.FloatField(default=1.5)
    absolute_price_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"
```

### VintedItem
```python
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
    
    # Complete API response for additional data
    api_response = models.JSONField()
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
    class Meta:
        indexes = [
            models.Index(fields=['condition', 'price']),
            models.Index(fields=['vinted_id']),
        ]
```

### PriceStatistics
```python
class PriceStatistics(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    condition = models.IntegerField()
    mean_price = models.DecimalField(max_digits=10, decimal_places=2)
    std_deviation = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField()
    last_calculated = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['price_watch', 'condition']
```

### UnderpriceAlert
```python
class UnderpriceAlert(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    item = models.ForeignKey(VintedItem, on_delete=models.CASCADE)
    detected_at = models.DateTimeField(auto_now_add=True)
    price_difference = models.DecimalField(max_digits=10, decimal_places=2)
    std_deviations_below = models.FloatField()
    email_sent = models.BooleanField(default=False)
    email_sent_at = models.DateTimeField(null=True, blank=True)
    
    class Meta:
        unique_together = ['price_watch', 'item']
```

## API Integration

### Vinted API Endpoint
```
GET https://www.vinted.be/api/v2/catalog/items
```

### Required Parameters
- access_token_web: Cookie obtained via Playwright
- per_page: Number of items per page
- page: Page number for pagination

### Optional Search Parameters
- search_text: Search query
- catalog_ids: Category IDs
- price_to: Maximum price
- currency: Currency code
- order: Sort order
- size_ids: Size filters
- brand_ids: Brand filters
- status_ids: Condition filters
- color_ids: Color filters
- patterns_ids: Pattern filters
- material_ids: Material filters

## Implementation Plan

### Phase 1: Core Setup
1. Django project setup with user authentication
2. Create data models
3. Set up Tailwind CSS
4. Basic CRUD for price watches

### Phase 2: API Integration
1. Implement Playwright token management
2. Create Vinted API client
3. Item indexing and storage
4. API response field mapping

### Phase 3: Statistics Engine
1. Price statistics calculation
2. Histogram generation
3. Underpricing detection algorithms
4. Statistics dashboard

### Phase 4: Monitoring System
1. Background task system
2. Continuous polling implementation
3. New item detection
4. Email notification system

### Phase 5: Frontend Enhancement
1. Dashboard with statistics visualizations
2. Price watch management interface
3. Alert history and management
4. Mobile-responsive design
5. Use Playwright MCP to verify frontend layout and functionality

## Development Commands

### Setup
```bash
# Install dependencies
pip install django playwright django-tailwind django-background-tasks

# Initialize Tailwind (using django-tailwind package)
python manage.py tailwind install
python manage.py tailwind init

# Database setup
python manage.py makemigrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Install Playwright browsers
playwright install
```

### Development
```bash
# Run development server
python manage.py runserver

# Run Tailwind CSS in watch mode (separate terminal)
python manage.py tailwind start

# Run background tasks (separate terminal)
python manage.py process_tasks

# Run tests
python manage.py test

# Build Tailwind for production
python manage.py tailwind build

# Static files collection
python manage.py collectstatic

# Frontend layout verification using Playwright MCP
# Verify responsive design and component functionality
```

## Security Considerations
- Store Vinted cookies securely
- Rate limit API calls to avoid blocking
- Implement proper user authentication
- Secure email configuration
- Handle API errors and failures gracefully

## Django Forms & Views

### PriceWatchForm
```python
from django import forms
from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, ListView
from .models import PriceWatch

class PriceWatchForm(forms.ModelForm):
    class Meta:
        model = PriceWatch
        fields = ['name', 'search_parameters', 'std_dev_threshold', 'absolute_price_threshold']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'search_parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

class PriceWatchCreateView(CreateView):
    model = PriceWatch
    form_class = PriceWatchForm
    template_name = 'watches/create.html'
    
    def form_valid(self, form):
        form.instance.user = self.request.user
        return super().form_valid(form)
```

### Authentication Views
```python
from django.contrib.auth.views import LoginView
from django.contrib.auth.forms import UserCreationForm
from django.urls import reverse_lazy

class CustomLoginView(LoginView):
    template_name = 'auth/login.html'
    redirect_authenticated_user = True

class SignUpView(CreateView):
    form_class = UserCreationForm
    template_name = 'auth/signup.html'
    success_url = reverse_lazy('login')
```

## Background Task System

### Task Management
```python
from background_task import background
from django.core.mail import send_mail
import requests
from playwright.sync_api import sync_playwright

@background(schedule=300)  # Run every 5 minutes
def monitor_price_watches():
    """Continuously monitor all active price watches"""
    for watch in PriceWatch.objects.filter(is_active=True):
        check_price_watch.now(watch.id)

@background
def check_price_watch(watch_id):
    """Check a specific price watch for new underpriced items"""
    try:
        watch = PriceWatch.objects.get(id=watch_id)
        token = get_vinted_token()
        items = fetch_vinted_items(watch.search_parameters, token)
        
        for item_data in items:
            process_item(item_data, watch)
            
    except Exception as e:
        logger.error(f"Error checking price watch {watch_id}: {e}")

def get_vinted_token():
    """Use Playwright to obtain access_token_web cookie"""
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto('https://www.vinted.be')
        cookies = page.context.cookies()
        token = next((c['value'] for c in cookies if c['name'] == 'access_token_web'), None)
        browser.close()
        return token
```

## Scalability Notes
- Current design uses SQLite for development
- For production, consider PostgreSQL
- Add Redis for caching frequent calculations
- Implement proper logging and monitoring
- Consider API call optimization strategies
- Use django-background-tasks for job processing