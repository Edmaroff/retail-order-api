from rest_framework import serializers

from backend.models import Category, Contact, CustomUser, Shop


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
