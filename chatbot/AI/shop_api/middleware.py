import time
from django.utils.deprecation import MiddlewareMixin
from django.http import JsonResponse

request_times = {}

class RateLimitMiddleware(MiddlewareMixin):
    def process_request(self, request):
        # Skip rate limiting for non-API routes and routes without shop_id
        if not request.resolver_match or 'shop_id' not in request.resolver_match.kwargs:
            return None
            
        shop_id = request.resolver_match.kwargs.get('shop_id', 'unknown')
        client_ip = self.get_client_ip(request)
        
        if not self.check_rate_limit(shop_id, client_ip):
            return JsonResponse(
                {"success": False, "error": "Rate limit exceeded"}, 
                status=429
            )
        return None
    
    def check_rate_limit(self, shop_id, client_ip, max_requests=50):
        current_time = time.time()
        minute_ago = current_time - 60
        rate_limit_key = f"{shop_id}_{client_ip}"
        
        if rate_limit_key not in request_times:
            request_times[rate_limit_key] = []
        
        request_times[rate_limit_key] = [t for t in request_times[rate_limit_key] if t > minute_ago]
        
        if len(request_times[rate_limit_key]) >= max_requests:
            return False
        
        request_times[rate_limit_key].append(current_time)
        return True
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class SecurityHeadersMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        response['Strict-Transport-Security'] = "max-age=31536000; includeSubDomains"
        response['X-Content-Type-Options'] = "nosniff"
        response['X-XSS-Protection'] = "1; mode=block"
        response['Referrer-Policy'] = "strict-origin-when-cross-origin"
        response['Permissions-Policy'] = "geolocation=(), microphone=(), camera=()"
        return response