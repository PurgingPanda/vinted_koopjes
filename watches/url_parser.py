import urllib.parse
from typing import Dict, Any, Optional


class VintedURLParser:
    """Parse Vinted catalog URLs and extract search parameters"""
    
    def __init__(self):
        # Map URL parameters to our form fields
        self.param_mapping = {
            'search_text': 'search_text',
            'catalog[]': 'catalog_ids',
            'catalog_ids[]': 'catalog_ids',
            'price_to': 'price_to',
            'brand_ids[]': 'brand_ids',
            'status_ids[]': 'status_ids',
            'size_ids[]': 'size_ids',
            'color_ids[]': 'color_ids',
            'material_ids[]': 'material_ids',
            'patterns_ids[]': 'patterns_ids',
        }
    
    def parse_vinted_url(self, url: str) -> Dict[str, Any]:
        """
        Parse a Vinted catalog URL and extract search parameters
        
        Args:
            url: Vinted catalog URL (e.g., https://www.vinted.be/catalog?search_text=barbour...)
            
        Returns:
            Dict containing parsed parameters suitable for our form
        """
        if not url or not isinstance(url, str):
            return {}
        
        try:
            # Parse the URL
            parsed_url = urllib.parse.urlparse(url.strip())
            
            # Check if it's a Vinted catalog URL
            if not self._is_vinted_catalog_url(parsed_url):
                return {}
            
            # Parse query parameters
            query_params = urllib.parse.parse_qs(parsed_url.query)
            
            # Extract and convert parameters
            form_data = {}
            
            for url_param, form_field in self.param_mapping.items():
                values = query_params.get(url_param, [])
                
                if not values:
                    continue
                
                if form_field == 'search_text':
                    # Single text value
                    form_data[form_field] = values[0] if values else ''
                elif form_field == 'price_to':
                    # Single decimal value
                    try:
                        form_data[form_field] = float(values[0]) if values else None
                    except (ValueError, IndexError):
                        continue
                else:
                    # Array values (IDs) - join with commas
                    if values:
                        # Remove empty values and convert to string
                        clean_values = [str(v) for v in values if v]
                        if clean_values:
                            form_data[form_field] = ','.join(clean_values)
            
            # Also check for 'catalog' parameter (without brackets)
            if 'catalog' in query_params and 'catalog_ids' not in form_data:
                catalog_values = query_params['catalog']
                if catalog_values:
                    clean_values = [str(v) for v in catalog_values if v]
                    if clean_values:
                        form_data['catalog_ids'] = ','.join(clean_values)
            
            return form_data
            
        except Exception as e:
            # If parsing fails, return empty dict
            return {}
    
    def _is_vinted_catalog_url(self, parsed_url) -> bool:
        """Check if the URL is a valid Vinted catalog URL"""
        # Check domain
        if not parsed_url.netloc.endswith('vinted.be') and not parsed_url.netloc.endswith('vinted.com'):
            return False
        
        # Check path - should be /catalog or contain catalog
        path = parsed_url.path.lower()
        return path == '/catalog' or '/catalog' in path
    
    def generate_search_preview(self, form_data: Dict[str, Any]) -> str:
        """Generate a human-readable preview of the search parameters"""
        preview_parts = []
        
        if form_data.get('search_text'):
            preview_parts.append(f'Search: "{form_data["search_text"]}"')
        
        if form_data.get('price_to'):
            preview_parts.append(f'Max Price: €{form_data["price_to"]}')
        
        if form_data.get('catalog_ids'):
            catalog_count = len(form_data['catalog_ids'].split(','))
            preview_parts.append(f'Categories: {catalog_count} selected')
        
        if form_data.get('brand_ids'):
            brand_count = len(form_data['brand_ids'].split(','))
            preview_parts.append(f'Brands: {brand_count} selected')
        
        if form_data.get('status_ids'):
            status_ids = form_data['status_ids'].split(',')
            conditions = []
            for status_id in status_ids:
                if status_id.strip() == '6':
                    conditions.append('As new with tag')
                elif status_id.strip() == '1':
                    conditions.append('As new')
                elif status_id.strip() == '2':
                    conditions.append('Very good')
                elif status_id.strip() == '3':
                    conditions.append('Good')
                elif status_id.strip() == '4':
                    conditions.append('Heavily used')
            
            if conditions:
                preview_parts.append(f'Conditions: {", ".join(conditions)}')
        
        if form_data.get('size_ids'):
            size_count = len(form_data['size_ids'].split(','))
            preview_parts.append(f'Sizes: {size_count} selected')
        
        if form_data.get('color_ids'):
            color_count = len(form_data['color_ids'].split(','))
            preview_parts.append(f'Colors: {color_count} selected')
        
        return ' • '.join(preview_parts) if preview_parts else 'No search parameters found'


# Global parser instance
vinted_parser = VintedURLParser()