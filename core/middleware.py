from django.utils.deprecation import MiddlewareMixin
from .models import AuditTrail
import json

class AuditTrailMiddleware(MiddlewareMixin):
    def process_response(self, request, response):
        if not request.user.is_authenticated:
            return response

        # Skip logging for certain paths
        excluded_paths = ['/static/', '/media/', '/admin/jsi18n/']
        if any(request.path.startswith(path) for path in excluded_paths):
            return response

        # Determine action type
        action = 'VIEW'
        if request.method == 'POST':
            action = 'CREATE'
        elif request.method == 'PUT' or request.method == 'PATCH':
            action = 'UPDATE'
        elif request.method == 'DELETE':
            action = 'DELETE'

        # Get model name and object ID from URL
        path_parts = request.path.strip('/').split('/')
        if len(path_parts) >= 2:
            model_name = path_parts[1].replace('-', ' ').title().replace(' ', '')
            object_id = path_parts[2] if len(path_parts) > 2 else None

            # Create audit trail entry
            AuditTrail.objects.create(
                user=request.user,
                action=action,
                model_name=model_name,
                object_id=object_id or '',
                details={
                    'method': request.method,
                    'path': request.path,
                    'query_params': dict(request.GET.items()),
                    'body': json.loads(request.body) if request.body else None,
                },
                ip_address=request.META.get('REMOTE_ADDR')
            )

        return response 