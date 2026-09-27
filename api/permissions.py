from rest_framework.permissions import BasePermission
from .models import Company


class IsAdminUser(BasePermission):
    """
    Custom permission to only allow access to users whose associated company
    has the ADMIN role. Does not rely on Django's is_staff or is_superuser.
    """
    message = "Admin access required. Your company role does not have admin permissions."

    def has_permission(self, request, view):
        if not (request.user and request.user.is_authenticated):
            return False

        try:
            return request.user.company.role == Company.Role.ADMIN
        except (AttributeError, Company.DoesNotExist):
            return False
