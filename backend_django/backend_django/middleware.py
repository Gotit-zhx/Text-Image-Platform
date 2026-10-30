import uuid

from django.conf import settings
from django.http import HttpResponse
import ipaddress


class RequestIdMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        request.request_id = request.headers.get('X-Request-Id') or uuid.uuid4().hex
        response = self.get_response(request)
        response['X-Request-Id'] = request.request_id
        return response


class DevCorsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not settings.DEBUG:
            return self.get_response(request)
        if request.method == 'OPTIONS':
            response = HttpResponse(status=204)
        else:
            response = self.get_response(request)

        origin = request.headers.get('Origin', '')
        if origin.startswith('http://localhost:') or origin.startswith('http://127.0.0.1:'):
            response['Access-Control-Allow-Origin'] = origin
            response['Vary'] = 'Origin'
            response['Access-Control-Allow-Credentials'] = 'true'
            response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization, X-CSRFToken'
            response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'

        return response


class CommunityWritePolicyMiddleware:
    """Reject malformed JSON and enforce account restrictions on existing sessions."""
    def __init__(self,get_response):
        self.get_response=get_response
    def __call__(self,request):
        from community.http import api_error
        if request.path.startswith('/api/') and request.method not in {'GET','HEAD','OPTIONS'}:
            if request.content_type=='application/json' and request.body:
                import json
                try:
                    payload=json.loads(request.body)
                    if not isinstance(payload,dict):return api_error(request,'请求必须是JSON对象')
                except (ValueError,UnicodeDecodeError):return api_error(request,'请求JSON格式错误')
            if request.user.is_authenticated and request.path.startswith(('/api/community/','/api/media','/api/reports','/api/appeals')):
                from community.social import write_denial
                denial=write_denial(request)
                if denial:return denial
        return self.get_response(request)


class TrustedProxyMiddleware:
    """Caddy overwrites X-Real-IP; never enable on an exposed application port."""
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if getattr(settings, 'TIP_TRUST_PROXY', False):
            try:
                request.META['REMOTE_ADDR'] = str(ipaddress.ip_address(request.META.get('HTTP_X_REAL_IP', '')))
            except ValueError:
                pass
        return self.get_response(request)
