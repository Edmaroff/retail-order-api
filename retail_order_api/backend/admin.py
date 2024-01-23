from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _

from backend.models import (
    Category,
    Contact,
    CustomUser,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """
    Панель управления пользователями
    """

    list_display = [
        "id",
        "email",
        "type",
        "last_name",
        "first_name",
        "patronymic",
        "company",
        "is_active",
    ]
    list_filter = ["type", "is_active"]
    search_fields = ["first_name", "patronymic", "last_name", "email", "company"]
    ordering = ["email"]

    fieldsets = [
        (None, {"fields": ("email", "password", "type", "username")}),
        (
            _("Personal info"),
            {
                "fields": (
                    "last_name",
                    "first_name",
                    "patronymic",
                    "company",
                    "position",
                )
            },
        ),
        (
            _("Permissions"),
            {"fields": ("is_active", "is_superuser", "groups", "user_permissions")},
        ),
        (_("Important dates"), {"fields": ("last_login", "date_joined")}),
    ]

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": (
                    "email",
                    "password1",
                    "password2",
                    "username",
                    "last_name",
                    "first_name",
                    "patronymic",
                    "company",
                    "position",
                ),
            },
        ),
    )

    filter_horizontal = (
        "groups",
        "user_permissions",
    )


@admin.register(Contact)
class ContactAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "phone", "city", "street", "house"]
    list_filter = ["city"]
    search_fields = ["user__email", "phone"]
    fieldsets = [
        (None, {"fields": ["user"]}),
        (
            "Адрес",
            {
                "fields": [
                    "city",
                    "street",
                    "house",
                    "structure",
                    "building",
                    "apartment",
                ]
            },
        ),
        ("Контактная информация", {"fields": ["phone"]}),
    ]


@admin.register(Shop)
class ShopAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "url", "state", "user"]
    list_filter = ["state"]
    search_fields = ["name", "user__email"]
    fieldsets = [
        (None, {"fields": ["name", "url", "state"]}),
        ("Пользователь", {"fields": ["user"]}),
    ]


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]
    filter_horizontal = ["shops"]


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "category"]
    search_fields = ["name", "category__name"]
    list_filter = ["category"]


class ProductParameterInline(admin.TabularInline):
    model = ProductParameter
    extra = 1


@admin.register(ProductInfo)
class ProductInfoAdmin(admin.ModelAdmin):
    list_display = [
        "id",
        "product",
        "shop",
        "model",
        "external_id",
        "quantity",
        "price",
        "price_rrp",
    ]
    search_fields = ["product__name", "shop__name", "model"]
    list_filter = ["shop"]

    fieldsets = [
        (None, {"fields": ["product", "shop"]}),
        (
            "Основная информация",
            {"fields": ["model", "external_id", "quantity"]},
        ),
        ("Цены", {"fields": ["price", "price_rrp"]}),
    ]

    inlines = [ProductParameterInline]


@admin.register(Parameter)
class ParameterAdmin(admin.ModelAdmin):
    list_display = ["id", "name"]
    search_fields = ["name"]


@admin.register(ProductParameter)
class ProductParameterAdmin(admin.ModelAdmin):
    list_display = ["id", "product_info", "parameter", "value"]
    search_fields = ["product_info__product__name", "parameter__name"]
    list_filter = [
        "product_info__shop__name",
        "parameter__name",
        "product_info__product__category__name",
    ]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 1


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ["id", "user", "contact", "date", "state"]
    search_fields = ["user__email"]
    list_filter = ["state"]
    inlines = [OrderItemInline]
