from rest_framework import serializers

from backend.models import (
    Category,
    Contact,
    CustomUser,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


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


class ProductListSerializer(serializers.ModelSerializer):
    category = serializers.StringRelatedField()

    class Meta:
        model = Product
        fields = ["id", "name", "category"]
        read_only_fields = ["id"]


class ProductParameterSerializer(serializers.ModelSerializer):
    parameter = serializers.StringRelatedField()

    class Meta:
        model = ProductParameter
        fields = ["parameter", "value"]


class ProductInfoSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
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
