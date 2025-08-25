from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from watches.models import PriceWatch, ClusterAnalysis
from watches.clustering.clustering_service import ClusteringService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Test clustering functionality on a specific price watch'
    
    def add_arguments(self, parser):
        parser.add_argument(
            'watch_id', 
            type=int, 
            help='ID of the price watch to cluster'
        )
        parser.add_argument(
            '--eps',
            type=float,
            default=0.5,
            help='DBSCAN eps parameter (default: 0.5)'
        )
        parser.add_argument(
            '--min-samples',
            type=int,
            default=5,
            help='DBSCAN min_samples parameter (default: 5)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually running clustering'
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output'
        )
    
    def handle(self, *args, **options):
        watch_id = options['watch_id']
        eps = options['eps']
        min_samples = options['min_samples']
        dry_run = options['dry_run']
        verbose = options['verbose']
        
        if verbose:
            logging.basicConfig(level=logging.INFO)
        
        try:
            # Get the price watch
            try:
                watch = PriceWatch.objects.get(id=watch_id)
            except PriceWatch.DoesNotExist:
                raise CommandError(f'Price watch with ID {watch_id} does not exist.')
            
            # Get item count
            item_count = watch.items.filter(is_active=True).count()
            
            self.stdout.write(f"\n📊 Clustering Analysis Test")
            self.stdout.write(f"{'='*50}")
            self.stdout.write(f"Watch: {watch.name} (ID: {watch.id})")
            self.stdout.write(f"Owner: {watch.user.username}")
            self.stdout.write(f"Active items: {item_count}")
            self.stdout.write(f"DBSCAN parameters: eps={eps}, min_samples={min_samples}")
            
            if item_count < 10:
                self.stdout.write(
                    self.style.ERROR(f"❌ Insufficient items: {item_count} (minimum 10 required)")
                )
                return
            
            if dry_run:
                self.stdout.write(f"\n🔍 DRY RUN - No clustering will be performed")
                self.stdout.write(f"Would cluster {item_count} items from watch '{watch.name}'")
                return
            
            # Check for existing recent analysis
            recent_analysis = ClusterAnalysis.objects.filter(
                price_watch=watch,
                status='completed'
            ).order_by('-created_at').first()
            
            if recent_analysis:
                self.stdout.write(f"\n📋 Recent Analysis Found:")
                self.stdout.write(f"  Date: {recent_analysis.created_at}")
                self.stdout.write(f"  Clusters: {recent_analysis.total_clusters}")
                self.stdout.write(f"  Noise items: {recent_analysis.noise_items}")
                self.stdout.write(f"  Execution time: {recent_analysis.execution_time:.2f}s")
            
            # Initialize clustering service
            self.stdout.write(f"\n🤖 Initializing clustering service...")
            clustering_service = ClusteringService()
            
            # Perform clustering
            self.stdout.write(f"🔄 Starting clustering analysis...")
            self.stdout.write(f"   This may take a few minutes for {item_count} items...")
            
            try:
                analysis = clustering_service.perform_clustering(
                    price_watch_id=watch_id,
                    eps=eps,
                    min_samples=min_samples
                )
                
                # Display results
                self.stdout.write(f"\n✅ Clustering completed successfully!")
                self.stdout.write(f"{'='*50}")
                self.stdout.write(f"Analysis ID: {analysis.id}")
                self.stdout.write(f"Total items analyzed: {analysis.total_items}")
                self.stdout.write(f"Clusters found: {analysis.total_clusters}")
                self.stdout.write(f"Noise items: {analysis.noise_items}")
                self.stdout.write(f"Execution time: {analysis.execution_time:.2f} seconds")
                
                if verbose and analysis.total_clusters > 0:
                    # Show cluster summary
                    summary = clustering_service.get_cluster_summary(analysis)
                    
                    self.stdout.write(f"\n📈 Cluster Summary:")
                    self.stdout.write(f"{'Cluster':<8} {'Items':<6} {'Avg Price':<10} {'Price Range':<15} {'Representatives'}")
                    self.stdout.write(f"{'-'*70}")
                    
                    for cluster in summary:
                        price_range = f"€{cluster['min_price']:.2f}-€{cluster['max_price']:.2f}"
                        rep_count = len(cluster['representatives'])
                        
                        self.stdout.write(
                            f"{cluster['cluster_id']:<8} "
                            f"{cluster['item_count']:<6} "
                            f"€{cluster['avg_price']:.2f}{'':3} "
                            f"{price_range:<15} "
                            f"{rep_count} items"
                        )
                
                self.stdout.write(f"\n🌐 View results at: /watches/{watch.id}/clusters/")
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"❌ Clustering failed: {str(e)}")
                )
                raise
                
        except Exception as e:
            raise CommandError(f'Command failed: {str(e)}')
        
        self.stdout.write(
            self.style.SUCCESS(f"\n🎉 Test completed successfully!")
        )