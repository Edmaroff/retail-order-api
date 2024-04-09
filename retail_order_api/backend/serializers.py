from os.path import splitext

from django.core.exceptions import ValidationError
from rest_framework import serializers

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)
from retail_order_api import settings


class ContactSerializer(serializers.ModelSerializer):
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Contact
        fields = [
            "id",
            "user",
            "phone",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"write_only": True}}


class CategoryListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ["id", "name"]
        read_only_fields = ["id"]


class ShopDetailSerializer(serializers.ModelSerializer):
    categories = CategoryListSerializer(many=True)
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = Shop
        fields = ["id", "name", "url", "user", "state", "categories"]
        read_only_fields = ["id"]


class ShopCreateUpdateSerializer(ShopDetailSerializer):
    categories = serializers.PrimaryKeyRelatedField(
        many=True, queryset=Category.objects.all()
    )

    def to_internal_value(self, data):
        raw_categories = data.get("categories")

        if not raw_categories:
            raise serializers.ValidationError(
                {"categories": ["Поле обязательно и не может быть пустым."]}
            )

        # Преобразование строки с категориями в список
        if isinstance(raw_categories, str) and "," in raw_categories:
            raw_categories = [cat_id.strip() for cat_id in raw_categories.split(",")]
        try:
            data._mutable = True
            data.setlist("categories", raw_categories)
            data._mutable = False
        except AttributeError:
            data["categories"] = raw_categories

        return super().to_internal_value(data)


class ShopListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ["id", "name"]
        read_only_fields = ["id"]
        ordering = ["name"]


class ProductWithoutImageSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "category"]
        read_only_fields = ["id"]


class ProductWithImageSerializer(serializers.ModelSerializer):
    image_small = serializers.ImageField(read_only=True)
    image_medium = serializers.ImageField(read_only=True)
    image_big = serializers.ImageField(read_only=True)
    category_name = serializers.CharField(source="category.name", read_only=True)

    class Meta:
        model = Product
        fields = [
            "id",
            "name",
            "category",
            "category_name",
            "image",
            "image_small",
            "image_medium",
            "image_big",
        ]

    def validate_image(self, image):
        if image is None:
            raise ValidationError("Изображение не было предоставлено.")
        if image.size > settings.IMAGE_MAX_SIZE_MB * 1024 * 1024:
            raise ValidationError(
                f"Максимальный размер изображения равен"
                f" {settings.IMAGE_MAX_SIZE_MB} МБ."
            )
        extension = splitext(image.name)[1]
        if extension not in settings.WHITELISTED_IMAGE_TYPES.keys():
            raise ValidationError(f"Формат изображения {extension} не поддерживается.")
        if image.content_type not in settings.WHITELISTED_IMAGE_TYPES.values():
            raise ValidationError(
                f"Недопустимый тип содержимого изображения: {image.content_type}."
            )
        return image


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ["parameter", "value"]


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductWithoutImageSerializer(read_only=True)
    product_parameters = ProductParameterSerializer(read_only=True, many=True)

    class Meta:
        model = ProductInfo
        fields = [
            "id",
            "model",
            "external_id",
            "quantity",
            "price",
            "price_rrp",
            "product",
            "shop",
            "product_parameters",
        ]
        read_only_fields = ["id"]


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ["id", "product_info", "quantity", "order"]
        read_only_fields = ["id"]
        extra_kwargs = {"order": {"write_only": True}}

    def validate(self, data):
        """
        Проверяет количество добавляемого в корзину продукта
        и доступное количество товара у продавца.
        """
        requested_quantity = data.get("quantity", settings.DEFAULT_QUANTITY_ORDER_ITEM)
        available_quantity = data.get("product_info").quantity

        if requested_quantity > available_quantity:
            raise serializers.ValidationError(
                {
                    "quantity": f"Превышено доступное количество "
                                f"товара — {available_quantity}.",
                    "product_info": data.get("product_info").pk,
                }
            )
        return data


class OrderItemCreateSerializer(OrderItemSerializer):
    product_info = ProductInfoSerializer(read_only=True)


class OrderSerializer(serializers.ModelSerializer):
    ordered_items = OrderItemCreateSerializer(read_only=True, many=True)
    total_sum = serializers.SerializerMethodField()
    contact = ContactSerializer(read_only=True)

    class Meta:
        model = Order
        fields = ["id", "ordered_items", "state", "date", "total_sum", "contact"]
        read_only_fields = ["id"]

    def get_total_sum(self, obj):
        # Общая сумма корзины
        total_sum = sum(
            [
                order_item.product_info.price * order_item.quantity
                for order_item in obj.ordered_items.all()
            ]
        )
        return total_sum
