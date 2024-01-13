import django_filters

from backend.models import Product


class ProductFilter(django_filters.FilterSet):
    product = django_filters.CharFilter(
        field_name="name", lookup_expr="icontains", label="Название продукта"
    )
    category = django_filters.CharFilter(
        field_name="category__name", lookup_expr="icontains", label="Название категории"
    )

    class Meta:
        model = Product
        fields = ["product", "category"]
