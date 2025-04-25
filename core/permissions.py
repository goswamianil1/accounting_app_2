from rest_framework import permissions

class RoleBasedPermission(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
            
        # Get the required permission from the view
        required_permission = getattr(view, 'required_permission', 'view')
        
        # Check if user has the required permission based on their role
        return request.user.has_permission(required_permission)
        
    def has_object_permission(self, request, view, obj):
        # Get the required permission from the view
        required_permission = getattr(view, 'required_permission', 'view')
        
        # Check if user has the required permission based on their role
        return request.user.has_permission(required_permission)

class IsAdminOrReadOnly(permissions.BasePermission):
    """
    Custom permission to only allow admins to edit objects.
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to any request,
        # so we'll always allow GET, HEAD or OPTIONS requests.
        if request.method in permissions.SAFE_METHODS:
            return True

        # Write permissions are only allowed to admins
        return request.user and request.user.is_staff 