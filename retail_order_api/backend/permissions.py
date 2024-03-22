from rest_framework import permissions
from rest_framework.exceptions import PermissionDenied


class IsShopUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.type != "shop":
            raise PermissionDenied(
                detail={
                    "Status": False,
                    "Errors": "Вы не являетесь магазином. У вас недостаточно прав.",
                }
            )
        return True


class IsBuyerUser(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if request.user.type != "buyer":
            raise PermissionDenied(
                detail={
                    "Status": False,
                    "Errors": "Вы не являетесь покупателем. У вас недостаточно прав.",
                }
            )
        return True
