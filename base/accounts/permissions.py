from rest_framework import permissions


class IsAdminOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return request.user and (
            request.user.is_account_admin or request.user.is_superuser
        )


class IsOwnerOrAdmin(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if request.user.is_account_admin or request.user.is_superuser:
            return True
        return obj == request.user


class CanAccessUser(permissions.BasePermission):
    message = "Você não tem acesso a este usuário."

    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.is_account_admin or request.user.is_superuser:
            return True
        return not request.user.is_blocked
