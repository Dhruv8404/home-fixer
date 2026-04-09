from rest_framework.permissions import BasePermission

class IsAdminRole(BasePermission):
    def has_permission(self, request, view):
        return request.user and request.user.role == "ADMIN"
    

class IsAdminOrCustomer(BasePermission):
    def has_permission(self, request, view):
        return (
            request.user
            and request.user.is_authenticated
            and request.user.role in ["ADMIN", "CUSTOMER"]
        )
class IsServiceman(BasePermission):
    """Allow only users with role 'SERVICEMAN'."""
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.role == "SERVICEMAN"
