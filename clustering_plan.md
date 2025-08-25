# Clustering Implementation Plan for Vinted Price Watch

## 🎯 **Project Objective**

**Goal**: Price optimization through clustering - find underpriced items within specific subcategories (e.g., drills within Bosch power tools)

**Use Case**: User creates broad watch for "Bosch power tools" and wants to analyze most underpriced drills specifically within that category.

## 🧠 **Technical Strategy**

### **Distance Metric & Feature Engineering**
- **Semantic embeddings** on titles, descriptions, and images
- **Combined distance**: `total_distance = 0.33 * title_distance + 0.33 * description_distance + 0.33 * image_distance`
- **Generic approach**: Works across all product categories (clothing, books, power tools, etc.)

### **Clustering Algorithm**
- **Algorithm**: DBSCAN for handling noise and variable cluster sizes
- **Parameters**: eps=0.5, min_samples=5 (moderate clustering)
- **Cluster type**: Strict clustering for precise price comparisons

### **Models & Technology Stack**
- **Text embeddings**: `sentence-transformers/all-MiniLM-L6-v2` (fast, good quality)
- **Image embeddings**: `openai/clip-vit-base-patch32` (proven for product images)
- **Clustering**: `sklearn.cluster.DBSCAN` with custom distance metric

## 🗺️ **Implementation Plan**

### **Phase 1: Foundation Setup** *(~2-3 days)*

**1.1 Dependencies & Environment**
```bash
pip install scikit-learn sentence-transformers torch Pillow numpy
```

**1.2 Database Schema**
```python
class ItemCluster(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    cluster_id = models.IntegerField()  # -1 for noise/outliers
    cluster_analysis = models.ForeignKey('ClusterAnalysis', on_delete=models.CASCADE)
    item = models.ForeignKey(VintedItem, on_delete=models.CASCADE)
    distance_to_centroid = models.FloatField()
    is_representative = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

class ClusterAnalysis(models.Model):
    price_watch = models.ForeignKey(PriceWatch, on_delete=models.CASCADE)
    total_items = models.IntegerField()
    total_clusters = models.IntegerField()
    noise_items = models.IntegerField()  # Items that didn't cluster
    eps_parameter = models.FloatField(default=0.5)
    min_samples = models.IntegerField(default=5)
    execution_time = models.FloatField()  # seconds
    created_at = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=20, choices=[
        ('running', 'Running'),
        ('completed', 'Completed'),
        ('failed', 'Failed')
    ])
    error_message = models.TextField(blank=True)

class ItemEmbedding(models.Model):
    item = models.OneToOneField(VintedItem, on_delete=models.CASCADE)
    title_embedding = models.JSONField()  # Store as list
    description_embedding = models.JSONField()
    image_embedding = models.JSONField()
    embedding_version = models.CharField(max_length=50)  # Track model versions
    created_at = models.DateTimeField(auto_now_add=True)
```

**1.3 Core Embedding Infrastructure**
```python
# watches/clustering/embedding_service.py
class EmbeddingService:
    def __init__(self):
        self.text_model = SentenceTransformer('all-MiniLM-L6-v2')
        self.image_model = SentenceTransformer('clip-ViT-B-32')
    
    def get_text_embedding(self, text):
        # Implementation for title/description embeddings
        pass
    
    def get_image_embedding(self, image_url):
        # Implementation for image embeddings with error handling
        pass
    
    def calculate_combined_distance(self, item1_embeddings, item2_embeddings):
        # Weighted distance calculation
        pass
```

### **Phase 2: Clustering Engine** *(~3-4 days)*

**2.1 Embedding Generation**
```python
# watches/clustering/clustering_service.py
class ClusteringService:
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def generate_embeddings_batch(self, items):
        # Batch process items for efficiency
        # Cache embeddings in database
        # Handle missing images gracefully
        pass
    
    def perform_clustering(self, price_watch_id, eps=0.5, min_samples=5):
        # Main clustering workflow
        # 1. Get or generate embeddings
        # 2. Calculate distance matrix
        # 3. Run DBSCAN
        # 4. Select representatives
        # 5. Save results
        pass
```

**2.2 DBSCAN Implementation**
- Custom distance metric for combined embeddings
- Representative selection: items closest to cluster centroid
- Cluster quality metrics and validation

**2.3 Management Command for Testing**
```python
# watches/management/commands/test_clustering.py
class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('watch_id', type=int)
        parser.add_argument('--eps', type=float, default=0.5)
        parser.add_argument('--min-samples', type=int, default=5)
    
    def handle(self, *args, **options):
        # Test clustering on specific watch
        pass
```

### **Phase 3: User Interface** *(~2-3 days)*

**3.1 Cluster Analysis Trigger**
- Add "Analyze Clusters" button to watch detail page (`watches/templates/watches/detail.html`)
- AJAX endpoint for triggering clustering: `/watches/<id>/analyze-clusters/`
- Progress tracking with WebSocket or polling

**3.2 Cluster Overview Page**
```html
<!-- Template: watches/templates/watches/clusters.html -->
<div class="cluster-grid">
    {% for cluster in clusters %}
    <div class="cluster-card">
        <h3>Cluster {{ cluster.cluster_id }} ({{ cluster.item_count }} items)</h3>
        <div class="representative-items">
            {% for item in cluster.representatives %}
                <img src="{{ item.photo_url }}" alt="{{ item.title }}">
            {% endfor %}
        </div>
        <p>Avg Price: €{{ cluster.avg_price }}</p>
        <a href="{% url 'cluster_detail' cluster.id %}">View Details</a>
    </div>
    {% endfor %}
</div>
```

**3.3 URL Configuration**
```python
# watches/urls.py additions
path('watches/<int:pk>/clusters/', views.ClusterOverviewView.as_view(), name='cluster_overview'),
path('watches/<int:watch_id>/analyze-clusters/', views.analyze_clusters, name='analyze_clusters'),
path('clusters/<int:cluster_id>/', views.ClusterDetailView.as_view(), name='cluster_detail'),
```

### **Phase 4: Integration & Polish** *(~2 days)*

**4.1 Performance Optimization**
- Embedding caching strategy with version control
- Background task processing (Celery or django-rq)
- Database indexes on clustering tables

**4.2 Error Handling**
- Minimum item thresholds (need 10+ items for meaningful clustering)
- Image loading failures and fallbacks
- Network timeout handling for embeddings

**4.3 User Experience**
- Loading indicators during clustering
- Clear messaging for failed clustering attempts
- Progress updates for long-running operations

## 📊 **User Interface Design**

### **Cluster Card Layout**
```
┌─────────────────────────────────────┐
│ Cluster 1 (23 items)               │
│ ┌─────┐ ┌─────┐ ┌─────┐            │
│ │ IMG │ │ IMG │ │ IMG │            │
│ │  1  │ │  2  │ │  3  │            │
│ └─────┘ └─────┘ └─────┘            │
│ Avg Price: €45 (Range: €25-€78)    │
│ [View 23 items in cluster]          │
└─────────────────────────────────────┘
```

### **Navigation Flow**
1. Watch Detail Page → "Analyze Clusters" button
2. Clustering Progress → "Analysis complete"
3. Cluster Overview → Paginated cards (10 per page, sorted by size)
4. Cluster Detail → Items within specific cluster with underpricing analysis

## 🔧 **Technical Implementation Details**

### **Combined Distance Calculation**
```python
def calculate_combined_distance(emb1, emb2):
    title_dist = cosine_distance(emb1['title'], emb2['title'])
    desc_dist = cosine_distance(emb1['description'], emb2['description'])
    img_dist = cosine_distance(emb1['image'], emb2['image'])
    
    # Balanced weighting
    return 0.33 * title_dist + 0.33 * desc_dist + 0.33 * img_dist
```

### **Representative Item Selection**
```python
def select_representatives(cluster_items, embeddings):
    # Calculate cluster centroid
    centroid = np.mean([embeddings[item.id] for item in cluster_items], axis=0)
    
    # Find items closest to centroid
    distances = [(item, cosine_distance(embeddings[item.id], centroid)) 
                 for item in cluster_items]
    distances.sort(key=lambda x: x[1])
    
    # Return top 3 closest items
    return [item for item, _ in distances[:3]]
```

### **Caching Strategy**
- Cache embeddings in database with model version tracking
- Invalidate cache when embedding models are updated
- Reuse embeddings across multiple clustering runs

## 📈 **Future Enhancements (Phase 5)**

### **Cluster-Aware Underpricing**
- Modify price statistics to be cluster-relative instead of watch-wide
- Show "most underpriced per cluster" instead of per entire watch
- Generate alerts for cluster-specific deals

### **Smart Parameter Tuning**
- Auto-suggest optimal eps/min_samples based on watch characteristics
- A/B test different parameters and learn from user feedback
- Category-specific embedding weights (images more important for clothing, text for books)

### **Advanced Analytics**
- Cluster trend analysis over time
- Cross-watch cluster comparison ("similar drill clusters in different brands")
- Export cluster data for external analysis

## ⚡ **Performance Considerations**

### **Scalability Limits**
- **Memory**: DBSCAN requires O(n²) distance matrix for n items
- **Compute**: Image embedding generation is CPU/GPU intensive
- **Storage**: Embeddings are ~1KB per item (3 vectors of ~300-500 dimensions each)

### **Optimization Strategies**
- Batch embedding generation (process 50-100 items at once)
- Use approximate nearest neighbor for large clusters (if n > 1000)
- Implement progressive clustering (cluster subsets, then merge)

## 🎯 **Success Metrics**

### **Technical Metrics**
- Clustering completes within 2 minutes for 500 items
- >90% of clusters contain intuitively similar items
- Representative items clearly identify cluster category

### **Business Metrics**
- Users successfully find underpriced items in specific subcategories
- Reduced time to identify relevant deals within broad searches
- Increased precision in price monitoring

## 🚀 **Deployment Timeline**

**Week 1**: Phase 1 + Phase 2 (Foundation + Clustering Engine)
**Week 2**: Phase 3 + Phase 4 (UI + Polish)
**Week 3**: Testing, refinement, and Phase 5 planning

**Total Estimated Time**: 2-3 weeks for full implementation

---

## 💡 **Key Design Decisions Made**

1. **Balanced embedding weighting** (33/33/33) for generic cross-category approach
2. **DBSCAN with moderate parameters** (eps=0.5, min_samples=5) for quality clusters
3. **On-demand clustering** to control compute costs and timing
4. **Centroid-based representatives** for most typical cluster examples
5. **Paginated card layout** for intuitive cluster browsing
6. **Strict clustering** for precise price comparisons within subcategories

This plan provides a complete roadmap for implementing clustering-based price optimization while maintaining flexibility for future enhancements.