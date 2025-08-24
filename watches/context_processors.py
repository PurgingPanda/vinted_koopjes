from django.core.cache import cache


def token_status(request):
    """Add token status information to all templates"""
    if not request.user.is_authenticated:
        return {}
    
    try:
        # The vinted_scraper handles everything automatically
        # Only show status if user explicitly needs to know something
        has_session_cookie = bool(cache.get('vinted_access_token'))
        
        # Don't show warnings by default since vinted_scraper handles cookies automatically
        has_invalid_tokens = False
        token_errors = []
        needs_attention = False
        
        # Only show information if there are manual cookies set
        if has_session_cookie:
            token_errors.append("Using manually set session cookie (optional - vinted_scraper can work without this)")
        
        return {
            'global_token_status': {
                'has_invalid_tokens': has_invalid_tokens,
                'token_errors': token_errors,
                'needs_attention': needs_attention,
            }
        }
        
    except Exception:
        # If there's any error, don't break the site
        return {'global_token_status': {'has_invalid_tokens': False, 'token_errors': [], 'needs_attention': False}}