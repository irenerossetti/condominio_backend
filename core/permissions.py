from rest_framework.permissions import BasePermission

class IsAdmin(BasePermission):
    def has_permission(self, request, view):
        u = request.user
        if not u or not u.is_authenticated: return False
        if hasattr(u, "profile"): return u.profile.role == "ADMIN"
        return u.is_staff or u.is_superuser
