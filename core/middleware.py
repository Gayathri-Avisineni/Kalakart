# core/middleware.py
from django.utils.deprecation import MiddlewareMixin
from django.utils.cache import add_never_cache_headers

class NoCacheMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        # Disable caching for login, register, view_cart, checkout, etc.
        if request.path.startswith(('/login', '/register', '/cart')):
            add_never_cache_headers(response)
        return response
