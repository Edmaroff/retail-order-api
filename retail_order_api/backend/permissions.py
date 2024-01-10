from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsAuthenticatedAndShopUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.type != "shop":
            raise PermissionDenied(
                "Вы не являетесь магазином. У вас недостаточно прав."
            )
        return True
