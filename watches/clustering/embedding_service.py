import numpy as np
import requests
from PIL import Image
from io import BytesIO
import logging
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_distances
from django.conf import settings
import torch

logger = logging.getLogger(__name__)


class EmbeddingService:
    """Service for generating text and image embeddings for clustering analysis"""
    
    def __init__(self):
        self.text_model = None
        self.image_model = None
        self.embedding_version = "v1.0"  # Track model versions
        self._initialize_models()
    
    def _initialize_models(self):
        """Initialize the sentence transformer models"""
        try:
            # Use CPU if CUDA is not available or to avoid memory issues
            device = 'cpu'
            
            # Text model for titles and descriptions
            logger.info("Loading text embedding model...")
            self.text_model = SentenceTransformer('all-MiniLM-L6-v2', device=device)
            
            # Image model for product photos
            logger.info("Loading image embedding model...")
            self.image_model = SentenceTransformer('clip-ViT-B-32', device=device)
            
            logger.info("Embedding models loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize embedding models: {e}")
            raise
    
    def get_text_embedding(self, text):
        """
        Generate embedding for text (title or description)
        
        Args:
            text (str): Text to embed
            
        Returns:
            list: Embedding vector as list
        """
        if not text or not isinstance(text, str):
            # Return zero vector for missing text
            return [0.0] * 384  # all-MiniLM-L6-v2 has 384 dimensions
        
        try:
            # Clean and limit text length
            text = text.strip()[:512]  # Limit to 512 characters
            
            if not text:
                return [0.0] * 384
            
            # Generate embedding
            embedding = self.text_model.encode(text, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.error(f"Failed to generate text embedding: {e}")
            return [0.0] * 384
    
    def get_image_embedding(self, image_url):
        """
        Generate embedding for image from URL
        
        Args:
            image_url (str): URL of the image
            
        Returns:
            list: Embedding vector as list
        """
        if not image_url:
            # Return zero vector for missing image
            return [0.0] * 512  # CLIP ViT-B-32 has 512 dimensions
        
        try:
            # Download image with timeout
            response = requests.get(image_url, timeout=10, stream=True)
            response.raise_for_status()
            
            # Open image with PIL
            image = Image.open(BytesIO(response.content))
            
            # Convert to RGB if needed
            if image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Generate embedding
            embedding = self.image_model.encode(image, convert_to_numpy=True)
            return embedding.tolist()
            
        except Exception as e:
            logger.warning(f"Failed to generate image embedding for {image_url}: {e}")
            return [0.0] * 512
    
    def calculate_combined_distance(self, embeddings1, embeddings2):
        """
        Calculate combined distance between two sets of embeddings
        
        Args:
            embeddings1 (dict): {'title': list, 'description': list, 'image': list}
            embeddings2 (dict): {'title': list, 'description': list, 'image': list}
            
        Returns:
            float: Combined distance (0.0 = identical, higher = more different)
        """
        try:
            # Calculate individual distances
            title_dist = cosine_distances([embeddings1['title']], [embeddings2['title']])[0][0]
            desc_dist = cosine_distances([embeddings1['description']], [embeddings2['description']])[0][0]
            image_dist = cosine_distances([embeddings1['image']], [embeddings2['image']])[0][0]
            
            # Balanced weighting as specified in the plan
            combined_distance = 0.33 * title_dist + 0.33 * desc_dist + 0.33 * image_dist
            
            return float(combined_distance)
            
        except Exception as e:
            logger.error(f"Failed to calculate combined distance: {e}")
            return 1.0  # Maximum distance on error
    
    def get_item_embeddings(self, item):
        """
        Generate all embeddings for a VintedItem
        
        Args:
            item (VintedItem): The item to process
            
        Returns:
            dict: {'title': list, 'description': list, 'image': list}
        """
        # Get photo URL from API response
        image_url = None
        try:
            api_response = item.api_response
            if api_response and 'photos' in api_response and api_response['photos']:
                # Use the first photo's high resolution URL
                photo = api_response['photos'][0]
                if 'high_resolution' in photo:
                    image_url = photo['high_resolution']['url']
                elif 'url' in photo:
                    image_url = photo['url']
        except (KeyError, IndexError, TypeError):
            pass
        
        # Generate embeddings
        embeddings = {
            'title': self.get_text_embedding(item.title or ''),
            'description': self.get_text_embedding(item.description or ''),
            'image': self.get_image_embedding(image_url)
        }
        
        return embeddings
    
    def batch_generate_embeddings(self, items, batch_size=10):
        """
        Generate embeddings for multiple items in batches
        
        Args:
            items (QuerySet): VintedItem objects to process
            batch_size (int): Number of items to process at once
            
        Yields:
            tuple: (item, embeddings_dict)
        """
        for i, item in enumerate(items):
            try:
                logger.info(f"Processing item {i+1}/{len(items)}: {item}")
                embeddings = self.get_item_embeddings(item)
                yield item, embeddings
                
                # Memory cleanup every batch
                if (i + 1) % batch_size == 0:
                    torch.cuda.empty_cache() if torch.cuda.is_available() else None
                    
            except Exception as e:
                logger.error(f"Failed to process item {item}: {e}")
                continue