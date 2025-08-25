# Vinted Price Watch Django Application

## Project Overview
A Django-based web application that monitors Vinted listings for underpriced items based on statistical analysis and user-defined price thresholds. Users create "price watches" with search parameters, and the system continuously monitors for deals.

## 🚀 IMPORTANT: User Setup & Startup Process

### **For New Installations:**
Users ALWAYS use `./setup.sh` to set up the application:
- Installs all dependencies (including clustering: scikit-learn, sentence-transformers, torch, etc.)
- Creates database and runs ALL migrations (including clustering migration 0017)
- Sets up admin user with default credentials
- Creates necessary directories

### **For Starting the Application:**
Users ALWAYS use `./start_all.sh` to start services:
- Runs Django server on **port 8080** (not 8000!)
- Uses **PostgreSQL database** (settings_spitsboog)
- Starts background task processor automatically
- Provides correct URLs: http://spitsboog.org:8080

### **Never assume manual commands** - users rely on these scripts!

## Tech Stack
- **Backend**: Django with PostgreSQL database (migrated from SQLite)
- **Frontend**: Tailwind CSS with Chart.js for visualizations
- **API Integration**: Vinted API with Playwright for token management
- **Background Tasks**: Django background tasks for continuous monitoring
- **Machine Learning**: scikit-learn (DBSCAN), sentence-transformers, PyTorch, PIL
- **Text Embeddings**: SentenceTransformer (`all-MiniLM-L6-v2` model)
- **Image Embeddings**: CLIP (`clip-ViT-B-32` model)
- **HTTP Client**: httpx for async/sync API requests with retry logic
- **Notifications**: Email notifications for immediate alerts
- **Testing**: Playwright MCP for frontend layout verification, comprehensive test suite
- **Database**: Remote PostgreSQL on spitsboog.org for production scalability
- **Deployment**: Docker, docker-compose, Supervisor for process management
- **Monitoring**: Real-time activity logging with emoji-rich console output

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

### 4. Visual Enhancement Features
- **Color Grading**: Items color-coded by upload age (green=newest, yellow=medium, red=oldest)
- **Highlight Words**: Thick double borders with black outline for items containing specified keywords
- **Blacklist Filtering**: Exclude items with unwanted words from calculations and display
- **Upload Date Tracking**: Extract timestamps from Vinted photo metadata for accurate age-based coloring

### 5. Continuous Monitoring & Activity Tracking
- Background tasks continuously poll Vinted API with enhanced pagination (5 pages automatic, 10 pages manual)
- Index all items found in searches with comprehensive logging
- Store complete API response data for all items
- Detect newly listed underpriced items with statistical analysis
- Immediate email notifications when deals are found
- **ScrapeActivity Model**: Complete tracking of background task execution with timing, success rates, and error logging
- **Activity Logger**: Context manager for automatic task monitoring and statistics collection
- **Real-time Console Output**: Emoji-rich console logging for background task visibility

### 6. Authentication & API Management
- Use Playwright to obtain `access_token_web` cookie from Vinted homepage
- Manage cookie refresh automatically
- Handle rate limiting and API errors gracefully

### 7. Advanced Dashboard Features (Latest)
- **Dynamic Item Count Selection**: Dropdown to select 25, 50, 100, or 500 most underpriced items
- **Live Feed**: Real-time display of recently indexed items with photos and metadata
- **Price Trend Charts**: Interactive Chart.js visualizations showing price movements over time
- **Enhanced Pagination**: Intelligent item distribution across multiple watches for accurate counts
- **Hide Functionality**: One-click item hiding with smooth animations and persistent state
- **Color Grading & Highlighting**: Consistent visual enhancement across all views

### 8. Admin Features & Management (Latest)
- **Superuser Access**: Admin users can view and manage all price watches from all users
- **Cross-User Visibility**: Admin dashboard shows system-wide statistics, alerts, and items
- **Owner Identification**: All watches display owner username in admin views
- **Full Management Rights**: Admin can edit, delete, and control any user's price watches
- **Admin Badge**: Visual indicator in navigation showing admin status
- **Enhanced Dashboard**: Admin-specific welcome message and system-wide data overview
- **Complete Oversight**: Access to all background tasks, alerts, and monitoring activities

### 9. PostgreSQL Migration & Production Readiness (Latest)
- **Database Migration**: Comprehensive migration from SQLite to PostgreSQL completed
- **Remote Database**: Running on spitsboog.org PostgreSQL server for scalability
- **Data Preservation**: All 2,830+ items, price watches, and alerts migrated successfully
- **Connection Pooling**: Optimized PostgreSQL configuration with connection management
- **Concurrent Access**: Resolved database lock issues with enterprise-grade database
- **Backup Strategy**: Migration scripts created for future data management

### 10. Security & Configuration Enhancements
- **Environment Variables**: Secure `.env` file for EMAIL_HOST_PASSWORD and sensitive settings
- **Automatic Cleanup**: Django signals automatically remove orphaned items when watches are deleted
- **Database Optimization**: Comprehensive indexing for improved query performance
- **Error Handling**: Robust error handling with detailed logging and graceful degradation
- **User Authentication**: Secure admin account with custom password management

### 11. Machine Learning Clustering System 🤖
- **ItemEmbedding Model**: Stores multi-modal embeddings for each item combining text and visual features
- **Text Embeddings**: Uses SentenceTransformer `all-MiniLM-L6-v2` model for title/description analysis
- **Image Embeddings**: Uses CLIP `clip-ViT-B-32` model for product photo similarity
- **Combined Distance Calculation**: Weighted similarity scoring (33% title, 33% description, 33% image)
- **DBSCAN Clustering**: Unsupervised clustering algorithm to group similar items automatically
- **Representative Selection**: Identifies most typical items in each cluster for quick browsing
- **Cluster Analysis**: Full clustering pipeline with performance tracking and error handling
- **Interactive UI**: Dedicated cluster overview and detail pages with visual item groupings
- **Noise Detection**: Identifies unique items that don't fit into any meaningful cluster

### 12. Smart API Blocking Management 🛡️
- **BlockingState Model**: Singleton tracking system for Vinted API availability status
- **Adaptive Monitoring**: Switches from 5-minute checks to hourly when API is blocked
- **Failure Tracking**: Monitors consecutive API failures and blocking duration
- **Automatic Recovery**: Periodically tests API status during blocked periods
- **Test Watch Selection**: Uses designated watch for API health checks during blocking
- **Performance Optimization**: Prevents unnecessary API calls during known blocking periods
- **Graceful Degradation**: Maintains application functionality during API unavailability

### 13. Professional Vinted Scraper Package 📦
- **Standalone Module**: Complete `vinted_scraper/` package with independent pyproject.toml
- **Async/Sync Support**: Both AsyncVintedWrapper and VintedWrapper implementations
- **Type Safety**: Full TypeScript-style typing with py.typed marker file
- **Rich Data Models**: Comprehensive models for VintedItem, VintedUser, VintedBrand, etc.
- **HTTP Client**: Optimized httpx-based client with retry logic and rate limiting
- **Testing Framework**: Extensive test suite with mock data and utilities
- **Constants Management**: Centralized configuration for API endpoints and parameters
- **Logging Integration**: Built-in logging with configurable levels and formatting

## Data Models

### PriceWatch
```python
class PriceWatch(models.Model):
    name = models.CharField(max_length=200)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    search_parameters = models.JSONField()  # All Vinted API parameters
    std_dev_threshold = models.FloatField(default=1.5)
    absolute_price_threshold = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    blacklist_words = models.TextField(blank=True, help_text="Comma-separated words to exclude items")
    highlight_words = models.TextField(blank=True, help_text="Comma-separated words to highlight items with thick borders")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    items = models.ManyToManyField('VintedItem', blank=True, related_name='watches')
    
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
    upload_date = models.DateTimeField(null=True, blank=True, help_text="When the item was uploaded to Vinted")
    
    # Seller information (Enhanced)
    seller_id = models.IntegerField(null=True, blank=True, help_text="Vinted user ID of the seller")
    seller_login = models.CharField(max_length=200, null=True, blank=True, help_text="Seller's username/login")
    seller_business = models.BooleanField(default=False, help_text="Whether seller is a business account")
    
    # Engagement metrics (Enhanced)
    favourite_count = models.IntegerField(null=True, blank=True, help_text="Number of users who favorited this item")
    view_count = models.IntegerField(null=True, blank=True, help_text="Number of times this item was viewed")
    service_fee = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Vinted's service fee for this item")
    total_item_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, help_text="Total price including fees")
    
    # Complete API response for additional data
    api_response = models.JSONField()
    first_seen = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(auto_now=True)
    is_active = models.BooleanField(default=True)
    
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
    hidden = models.BooleanField(default=False, help_text="Hide this alert from display")
    
    class Meta:
        unique_together = ['price_watch', 'item']
```

### ScrapeActivity (Latest)
```python
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
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE, null=True, blank=True)
    items_processed = models.IntegerField(default=0)
    pages_fetched = models.IntegerField(default=0)
    new_items_found = models.IntegerField(default=0)
    alerts_generated = models.IntegerField(default=0)
    error_message = models.TextField(blank=True)
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    duration_seconds = models.FloatField(null=True, blank=True)
```

### PriceTrend
```python
class PriceTrend(models.Model):
    """Track price trends over time for analytics"""
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE, related_name='price_trends')
    condition = models.IntegerField(help_text="Item condition (status_id)")
    date = models.DateField(help_text="Date of the trend data")
    avg_price = models.DecimalField(max_digits=10, decimal_places=2)
    min_price = models.DecimalField(max_digits=10, decimal_places=2)
    max_price = models.DecimalField(max_digits=10, decimal_places=2)
    item_count = models.IntegerField(help_text="Number of items found for this condition")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['price_watch', 'condition', 'date']
```

### ItemEmbedding (Machine Learning)
```python
class ItemEmbedding(models.Model):
    """Store embeddings for items for clustering analysis"""
    item = models.OneToOneField(VintedItem, on_delete=models.CASCADE)
    title_embedding = models.JSONField(help_text="Title text embedding as list")
    description_embedding = models.JSONField(help_text="Description text embedding as list")
    image_embedding = models.JSONField(help_text="Image embedding as list")
    embedding_version = models.CharField(max_length=50, help_text="Track model versions")
    created_at = models.DateTimeField(auto_now_add=True)
```

### ClusterAnalysis (Machine Learning)
```python
class ClusterAnalysis(models.Model):
    """Track clustering analysis runs"""
    STATUS_CHOICES = [
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ]
    
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    total_items = models.IntegerField(help_text="Total items analyzed")
    total_clusters = models.IntegerField(help_text="Number of clusters found")
    noise_items = models.IntegerField(help_text="Items that didn't cluster")
    eps_parameter = models.FloatField(default=0.5, help_text="DBSCAN eps parameter")
    min_samples = models.IntegerField(default=5, help_text="DBSCAN min_samples parameter")
    execution_time = models.FloatField(help_text="Execution time in seconds")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='running')
    error_message = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
```

### ItemCluster (Machine Learning)
```python
class ItemCluster(models.Model):
    """Assign items to clusters"""
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    cluster_analysis = models.ForeignKey(ClusterAnalysis, on_delete=models.CASCADE)
    item = models.ForeignKey(VintedItem, on_delete=models.CASCADE)
    cluster_id = models.IntegerField(help_text="Cluster ID (-1 for noise/outliers)")
    distance_to_centroid = models.FloatField(help_text="Distance from cluster centroid")
    is_representative = models.BooleanField(default=False, help_text="Is this item representative of the cluster")
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['cluster_analysis', 'item']
```

### BlockingState (API Management)
```python
class BlockingState(models.Model):
    """Track Vinted API blocking status for smart monitoring"""
    is_blocked = models.BooleanField(default=False, help_text="Is the API currently blocked?")
    blocked_since = models.DateTimeField(null=True, blank=True, help_text="When blocking started")
    last_blocked_check = models.DateTimeField(auto_now=True, help_text="Last time we checked blocking status")
    last_successful_request = models.DateTimeField(null=True, blank=True, help_text="Last successful API call")
    consecutive_failures = models.IntegerField(default=0, help_text="Number of consecutive API failures")
    test_watch_id = models.IntegerField(null=True, blank=True, help_text="ID of watch to use for testing during blocked state")
    
    @classmethod
    def get_current_state(cls):
        """Get or create the singleton blocking state record"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def should_use_hourly_check(self):
        """Determine if we should check hourly (when blocked) vs every 5 minutes"""
        return self.is_blocked
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

### Advanced Management Commands

#### Data Migration & Maintenance
```bash
# Backfill missing item fields from API responses
python manage.py backfill_item_fields

# Backfill seller information for existing items
python manage.py backfill_seller_data

# Backfill upload dates from photo metadata
python manage.py backfill_upload_dates

# Backfill missing API fields (views, favorites, etc.)
python manage.py backfill_api_fields

# Clean up orphaned items not associated with any watch
python manage.py cleanup_orphaned_items
```

#### Clustering & Machine Learning
```bash
# Test clustering functionality on a specific watch
python manage.py test_clustering <watch_id>

# Example: Test clustering with custom parameters
python manage.py test_clustering 1 --eps 0.3 --min-samples 3
```

#### API Management & Testing
```bash
# Test Vinted API connectivity and responses
python manage.py test_vinted_api

# Test watch functionality with specific parameters
python manage.py test_watch <watch_id>

# Test URL parsing functionality
python manage.py test_url_parser

# Set session cookie manually (for debugging)
python manage.py set_session_cookie <cookie_value>
```

#### Service Management
```bash
# Start all monitoring services
python manage.py start_monitoring

# Start background services orchestrator
python manage.py start_services
```

## Production Infrastructure

### Docker Deployment
```bash
# Build and run with Docker Compose
docker-compose up -d

# Build custom image
docker build -t vinted-koopjes .

# Environment-specific deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Process Management (Supervisor)
```bash
# Production process management with Supervisor
supervisorctl start vinted-koopjes
supervisorctl status
supervisorctl restart vinted-koopjes

# Configuration file: supervisor.conf
# Manages Django server, background tasks, and monitoring
```

### Database Migration Scripts
```bash
# Migrate from SQLite to PostgreSQL
./migrate_to_postgresql.sh

# Full deployment pipeline
./deploy.sh

# Environment setup for multiple configurations
# - settings_spitsboog.py: Production PostgreSQL
# - settings_postgresql.py: Development PostgreSQL
# - settings.py: Default SQLite
```

### Production Settings
```python
# settings_spitsboog.py - Production configuration
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'vinted_koopjes',
        'HOST': 'spitsboog.org',
        # ... production database configuration
    }
}

# Email configuration for alerts
EMAIL_HOST = 'spitsboog.org'
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')

# Static files and media handling
STATIC_ROOT = '/path/to/static'
MEDIA_ROOT = '/path/to/media'
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

## Machine Learning Clustering Workflow

### Clustering Service Architecture
```python
from watches.clustering.clustering_service import ClusteringService
from watches.clustering.embedding_service import EmbeddingService

# Initialize clustering service
clustering_service = ClusteringService()

# Run clustering analysis on a price watch
analysis = clustering_service.perform_clustering(
    price_watch_id=1,
    eps=0.5,           # DBSCAN distance parameter
    min_samples=5      # Minimum items per cluster
)

# Get cluster summary with statistics
clusters = clustering_service.get_cluster_summary(analysis)
```

### Embedding Generation Process
```python
from watches.clustering.embedding_service import EmbeddingService

embedding_service = EmbeddingService()

# Generate embeddings for a single item
embeddings = embedding_service.get_item_embeddings(vinted_item)
# Returns: {
#   'title': [0.123, 0.456, ...],        # 384 dimensions
#   'description': [0.789, 0.012, ...],  # 384 dimensions  
#   'image': [0.345, 0.678, ...]         # 512 dimensions
# }

# Batch generate embeddings for multiple items
for item, embeddings in embedding_service.batch_generate_embeddings(items):
    ItemEmbedding.objects.create(
        item=item,
        title_embedding=embeddings['title'],
        description_embedding=embeddings['description'],
        image_embedding=embeddings['image'],
        embedding_version=embedding_service.embedding_version
    )
```

### Clustering UI Endpoints
```bash
# View clustering overview for a price watch
GET /watches/{id}/clusters/

# Run new clustering analysis
POST /watches/{id}/analyze-clusters/

# View specific cluster details
GET /clusters/{cluster_id}/?analysis={analysis_id}

# View noise items (unclustered)
GET /clusters/-1/?analysis={analysis_id}
```

### API Blocking Management
```python
from watches.models import BlockingState

# Check current API status
blocking_state = BlockingState.get_current_state()

if blocking_state.should_use_hourly_check():
    # API is blocked, wait 1 hour between checks
    schedule_delay = 3600
else:
    # API is working, check every 5 minutes
    schedule_delay = 300

# Mark API as blocked after failures
if consecutive_failures > 3:
    blocking_state.mark_blocked()

# Mark API as working after successful request
blocking_state.mark_unblocked()
```

## Scalability Notes
- Current design uses SQLite for development
- For production, consider PostgreSQL
- Add Redis for caching frequent calculations
- Implement proper logging and monitoring
- Consider API call optimization strategies
- Use django-background-tasks for job processing