import numpy as np
import time
import logging
from sklearn.cluster import DBSCAN
from sklearn.metrics.pairwise import cosine_distances
from django.db import transaction
from django.utils import timezone

from watches.models import (
    VintedItem, ItemEmbedding, ClusterAnalysis, ItemCluster, PriceWatch
)
from .embedding_service import EmbeddingService

logger = logging.getLogger(__name__)


class ClusteringService:
    """Service for performing clustering analysis on items"""
    
    def __init__(self):
        self.embedding_service = EmbeddingService()
    
    def generate_embeddings_batch(self, items):
        """
        Generate and cache embeddings for items
        
        Args:
            items (QuerySet): VintedItem objects to process
            
        Returns:
            dict: {item_id: embeddings_dict}
        """
        embeddings_data = {}
        existing_embeddings = {}
        
        # Get existing embeddings
        existing = ItemEmbedding.objects.filter(
            item__in=items,
            embedding_version=self.embedding_service.embedding_version
        ).select_related('item')
        
        for emb in existing:
            existing_embeddings[emb.item.id] = {
                'title': emb.title_embedding,
                'description': emb.description_embedding,
                'image': emb.image_embedding
            }
        
        # Generate new embeddings for items that don't have them
        items_to_process = [item for item in items if item.id not in existing_embeddings]
        
        if items_to_process:
            logger.info(f"Generating embeddings for {len(items_to_process)} items...")
            
            for item, embeddings in self.embedding_service.batch_generate_embeddings(items_to_process):
                # Save to database
                ItemEmbedding.objects.update_or_create(
                    item=item,
                    defaults={
                        'title_embedding': embeddings['title'],
                        'description_embedding': embeddings['description'], 
                        'image_embedding': embeddings['image'],
                        'embedding_version': self.embedding_service.embedding_version
                    }
                )
                existing_embeddings[item.id] = embeddings
        
        return existing_embeddings
    
    def calculate_distance_matrix(self, embeddings_dict):
        """
        Calculate pairwise distance matrix for clustering
        
        Args:
            embeddings_dict (dict): {item_id: embeddings}
            
        Returns:
            tuple: (distance_matrix, item_ids_list)
        """
        item_ids = list(embeddings_dict.keys())
        n_items = len(item_ids)
        distance_matrix = np.zeros((n_items, n_items))
        
        logger.info(f"Calculating distance matrix for {n_items} items...")
        
        for i, id1 in enumerate(item_ids):
            for j, id2 in enumerate(item_ids):
                if i != j:
                    distance = self.embedding_service.calculate_combined_distance(
                        embeddings_dict[id1], embeddings_dict[id2]
                    )
                    distance_matrix[i][j] = distance
        
        return distance_matrix, item_ids
    
    def select_representatives(self, cluster_items, embeddings_dict, max_representatives=3):
        """
        Select representative items for a cluster
        
        Args:
            cluster_items (list): List of item IDs in the cluster
            embeddings_dict (dict): Embeddings for all items
            max_representatives (int): Maximum number of representatives to select
            
        Returns:
            list: Item IDs of representative items
        """
        if len(cluster_items) <= max_representatives:
            return cluster_items
        
        # Calculate cluster centroid
        title_embeddings = [embeddings_dict[item_id]['title'] for item_id in cluster_items]
        desc_embeddings = [embeddings_dict[item_id]['description'] for item_id in cluster_items]  
        image_embeddings = [embeddings_dict[item_id]['image'] for item_id in cluster_items]
        
        centroid = {
            'title': np.mean(title_embeddings, axis=0).tolist(),
            'description': np.mean(desc_embeddings, axis=0).tolist(),
            'image': np.mean(image_embeddings, axis=0).tolist()
        }
        
        # Calculate distances to centroid
        distances = []
        for item_id in cluster_items:
            distance = self.embedding_service.calculate_combined_distance(
                embeddings_dict[item_id], centroid
            )
            distances.append((item_id, distance))
        
        # Sort by distance and return closest items
        distances.sort(key=lambda x: x[1])
        return [item_id for item_id, _ in distances[:max_representatives]]
    
    def perform_clustering(self, price_watch_id, eps=0.5, min_samples=5):
        """
        Main clustering workflow
        
        Args:
            price_watch_id (int): ID of the PriceWatch to cluster
            eps (float): DBSCAN eps parameter
            min_samples (int): DBSCAN min_samples parameter
            
        Returns:
            ClusterAnalysis: The created analysis object
        """
        start_time = time.time()
        
        try:
            # Get the price watch
            price_watch = PriceWatch.objects.get(id=price_watch_id)
            
            # Get items for this watch
            items = list(price_watch.items.filter(is_active=True))
            
            if len(items) < 10:
                raise ValueError(f"Insufficient items for clustering: {len(items)} (minimum 10 required)")
            
            logger.info(f"Starting clustering analysis for {len(items)} items in watch '{price_watch.name}'")
            
            # Create analysis record
            analysis = ClusterAnalysis.objects.create(
                price_watch=price_watch,
                total_items=len(items),
                eps_parameter=eps,
                min_samples=min_samples,
                total_clusters=0,
                noise_items=0,
                execution_time=0,
                status='running'
            )
            
            try:
                # Step 1: Generate embeddings
                embeddings_dict = self.generate_embeddings_batch(items)
                
                # Step 2: Calculate distance matrix
                distance_matrix, item_ids = self.calculate_distance_matrix(embeddings_dict)
                
                # Step 3: Run DBSCAN clustering
                logger.info(f"Running DBSCAN with eps={eps}, min_samples={min_samples}")
                clustering = DBSCAN(eps=eps, min_samples=min_samples, metric='precomputed')
                cluster_labels = clustering.fit_predict(distance_matrix)
                
                # Step 4: Process results
                unique_clusters = set(cluster_labels)
                noise_count = np.sum(cluster_labels == -1)
                cluster_count = len(unique_clusters) - (1 if -1 in unique_clusters else 0)
                
                logger.info(f"Found {cluster_count} clusters and {noise_count} noise items")
                
                # Step 5: Save cluster assignments
                with transaction.atomic():
                    for idx, cluster_id in enumerate(cluster_labels):
                        item_id = item_ids[idx]
                        item = VintedItem.objects.get(id=item_id)
                        
                        # Calculate distance to centroid (0 for noise items)
                        distance_to_centroid = 0.0
                        if cluster_id != -1:
                            cluster_item_ids = [item_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                            if len(cluster_item_ids) > 1:
                                # Calculate centroid and distance
                                title_embeddings = [embeddings_dict[iid]['title'] for iid in cluster_item_ids]
                                desc_embeddings = [embeddings_dict[iid]['description'] for iid in cluster_item_ids]
                                image_embeddings = [embeddings_dict[iid]['image'] for iid in cluster_item_ids]
                                
                                centroid = {
                                    'title': np.mean(title_embeddings, axis=0).tolist(),
                                    'description': np.mean(desc_embeddings, axis=0).tolist(),
                                    'image': np.mean(image_embeddings, axis=0).tolist()
                                }
                                
                                distance_to_centroid = self.embedding_service.calculate_combined_distance(
                                    embeddings_dict[item_id], centroid
                                )
                        
                        ItemCluster.objects.create(
                            price_watch=price_watch,
                            cluster_analysis=analysis,
                            item=item,
                            cluster_id=cluster_id,
                            distance_to_centroid=distance_to_centroid,
                            is_representative=False  # Will be set later
                        )
                    
                    # Step 6: Select representatives for each cluster
                    for cluster_id in unique_clusters:
                        if cluster_id == -1:  # Skip noise
                            continue
                        
                        cluster_item_ids = [item_ids[i] for i, label in enumerate(cluster_labels) if label == cluster_id]
                        representatives = self.select_representatives(cluster_item_ids, embeddings_dict)
                        
                        # Mark representative items
                        ItemCluster.objects.filter(
                            cluster_analysis=analysis,
                            cluster_id=cluster_id,
                            item_id__in=representatives
                        ).update(is_representative=True)
                    
                    # Step 7: Update analysis record
                    execution_time = time.time() - start_time
                    analysis.total_clusters = cluster_count
                    analysis.noise_items = noise_count
                    analysis.execution_time = execution_time
                    analysis.status = 'completed'
                    analysis.save()
                
                logger.info(f"Clustering completed in {execution_time:.2f} seconds")
                return analysis
                
            except Exception as e:
                # Mark analysis as failed
                execution_time = time.time() - start_time
                analysis.status = 'failed'
                analysis.error_message = str(e)
                analysis.execution_time = execution_time
                analysis.save()
                raise
                
        except Exception as e:
            logger.error(f"Clustering failed for watch {price_watch_id}: {e}")
            raise
    
    def get_cluster_summary(self, analysis):
        """
        Get summary information about clusters
        
        Args:
            analysis (ClusterAnalysis): The analysis to summarize
            
        Returns:
            list: List of cluster summary dicts
        """
        clusters = ItemCluster.objects.filter(
            cluster_analysis=analysis,
            cluster_id__gte=0  # Exclude noise items
        ).values('cluster_id').distinct().order_by('cluster_id')
        
        summary = []
        for cluster in clusters:
            cluster_id = cluster['cluster_id']
            
            cluster_items = ItemCluster.objects.filter(
                cluster_analysis=analysis,
                cluster_id=cluster_id
            ).select_related('item')
            
            representatives = cluster_items.filter(is_representative=True)
            
            prices = [ci.item.price for ci in cluster_items]
            
            summary.append({
                'cluster_id': cluster_id,
                'item_count': len(cluster_items),
                'avg_price': np.mean(prices),
                'min_price': min(prices),
                'max_price': max(prices),
                'representatives': list(representatives),
                'all_items': list(cluster_items)
            })
        
        return summary