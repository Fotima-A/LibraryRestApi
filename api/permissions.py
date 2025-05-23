from rest_framework import permissions
from .models import UserRole

class RoleBasedPermission(permissions.BasePermission):
    def __init__(self, allowed_roles=None):
        self.allowed_roles = allowed_roles if allowed_roles is not None else []

    def has_permission(self, request, view):
        # Agar foydalanuvchi autentifikatsiyalanmagan bo‘lsa, ruxsat yo‘q
        if not request.user.is_authenticated:
            return False

        # Admin har doim barcha ruxsatlarga ega
        if request.user.role == UserRole.ADMIN:
            return True

        if not self.allowed_roles:
            return True

        user_role = request.user.role
        return user_role in [role.value for role in self.allowed_roles]

    def has_object_permission(self, request, view, obj):
        # Obyekt darajasidagi ruxsatni ham admin uchun har doim beramiz
        if request.user.is_authenticated and request.user.role == UserRole.ADMIN:
            return True
        return self.has_permission(request, view)

