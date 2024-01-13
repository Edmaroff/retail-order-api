from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError
from django.db.models import Q
from django.http import JsonResponse
from django_filters import rest_framework
from requests import get
from rest_framework import filters, generics, permissions, status, views
from rest_framework.response import Response
from yaml import SafeLoader
from yaml import load as load_yaml
from yaml.error import YAMLError

from backend.filters import ProductFilter
from backend.models import (
    Category,
    Contact,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)
from backend.pagination import CategoryPagination, ProductPagination, ShopPagination
from backend.permissions import IsAuthenticatedAndShopUser
from backend.serializers import (
    CategoryListSerializer,
    ContactSerializer,
    ProductInfoSerializer,
    ProductListSerializer,
    ShopCreateUpdateSerializer,
    ShopDetailSerializer,
    ShopListSerializer,
)


class UserContactsView(views.APIView):
    """Управление контактами пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)

        if contacts.exists():
            serializer = ContactSerializer(contacts, many=True)
            return Response({"Status": True, "Data": serializer.data})

        return Response(
            {"Status": True, "Data": [], "Message": "У пользователя нет контактов."},
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data, context={"request": request})

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"Status": True, "Data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, *args, **kwargs):
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
            serializer = ContactSerializer(contact, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()

                return Response({"Status": True, "Data": serializer.data})
            return Response(
                {"Status": False, "Errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )

        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request, *args, **kwargs):
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
            contact.delete()
            return Response({"Status": True, "Message": "Контакт удален."})
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ShopListView(generics.ListAPIView):
    """Просмотр списка активных магазинов."""

    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopListSerializer
    pagination_class = ShopPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class UserShopDetailView(views.APIView):
    """Управление магазином пользователя."""

    permission_classes = [IsAuthenticatedAndShopUser]

    def get(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
            serializer = ShopDetailSerializer(shop)
            return Response({"Status": True, "Data": serializer.data})
        except Shop.DoesNotExist:
            return Response(
                {"Status": True, "Data": {}, "Message": "У пользователя нет магазина."},
                status=status.HTTP_200_OK,
            )

    def post(self, request, *args, **kwargs):
        user_shop = Shop.objects.filter(user=request.user).first()

        if user_shop:
            serializer = ShopDetailSerializer(user_shop)
            return Response(
                {
                    "Status": False,
                    "Message": "У пользователя уже существует магазин.",
                    "Data": serializer.data,
                }
            )

        serializer = ShopCreateUpdateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Магазин создан.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
        except Shop.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Магазин пользователя не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ShopDetailSerializer(shop, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"Status": True, "Data": serializer.data})
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
            shop.delete()
            return Response({"Status": True, "Message": "Магазин удален."})
        except Shop.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Магазин пользователя не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CategoryListView(generics.ListAPIView):
    """Просмотр списка категорий."""

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    pagination_class = CategoryPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class ShopDataView(views.APIView):
    """Загрузка и выгрузка товаров магазина."""

    permission_classes = [IsAuthenticatedAndShopUser]

    @staticmethod
    def _process_url(url):
        validate_url = URLValidator()

        if not url:
            return Response(
                {"Status": False, "Errors": "Не указан URL."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            validate_url(url)
        except ValidationError as error:
            return Response(
                {"Status": False, "Errors": str(error)},
                status=status.HTTP_400_BAD_REQUEST,
            )

    def get(self, request, *args, **kwargs):
        shop = Shop.objects.filter(user=request.user).first()

        if not shop:
            return Response(
                {"Status": False, "Errors": "Магазин не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Данные для выгрузки
        categories = list(shop.categories.values_list("name", flat=True))
        data = {
            "shop_name": shop.name,
            "categories": categories,
            "goods": [],
        }

        # Обработка информации о товарах
        products_info = ProductInfo.objects.filter(shop=shop)
        for product_info in products_info:
            product_data = {
                "id": product_info.external_id,
                "category": product_info.product.category.name,
                "name": product_info.product.name,
                "model": product_info.model,
                "price": product_info.price,
                "price_rrp": product_info.price_rrp,
                "quantity": product_info.quantity,
                "parameters": {},
            }

            # Обработка параметров товара
            products_parameter = ProductParameter.objects.filter(
                product_info=product_info
            )
            for product_parameter in products_parameter:
                product_data["parameters"][
                    product_parameter.parameter.name
                ] = product_parameter.value

            data["goods"].append(product_data)

        return Response({"Status": True, "Data": data})

    def post(self, request, *args, **kwargs):
        url = request.data.get("url")
        check_url = self._process_url(url)
        if check_url is not None:
            return check_url

        try:
            stream = get(url).content
            data = load_yaml(stream, Loader=SafeLoader)
        except YAMLError:
            return Response(
                {
                    "Status": False,
                    "Errors": f"Ошибка при загрузке данных из файла YAML.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            # # ОТЛАДКА - чтение файла с ПК
            # import os
            # url = "http://www.exmple100.ru"
            # stream = os.path.join(os.getcwd(), "data/shop_1.yaml")
            # with open(stream, encoding="utf-8") as file:
            #     data = load_yaml(file, Loader=SafeLoader)
            # # ОТЛАДКА - чтение файла с ПК

            # Создание или обновление магазина
            shop, _ = Shop.objects.update_or_create(
                user=request.user, defaults={"name": data.get("shop_name"), "url": url}
            )

            # Обработка категорий
            shop.categories.clear()  # Удаление существующих категорий
            category_name_to_id = {}  # Для создания товаров
            categories_data = data.get("categories", [])
            for category_name in categories_data:
                category_object, _ = Category.objects.get_or_create(name=category_name)
                category_object.shops.add(shop.id)
                category_name_to_id[category_name] = category_object.id

            # Обработка товаров
            ProductInfo.objects.filter(
                shop_id=shop.id
            ).delete()  # Удаление существующих товаров магазина
            products_data = data.get("goods", [])
            for product_data in products_data:
                # Попытка получить товар, если его нет — создание
                try:
                    product = Product.objects.get(name=product_data.get("name"))
                    # Проверка связи категории товара с магазином
                    if product.category.name not in category_name_to_id:
                        product.category.shops.add(shop.id)
                except Product.DoesNotExist:
                    category_id = category_name_to_id.get(product_data.get("category"))
                    product = Product.objects.create(
                        name=product_data.get("name"), category_id=category_id
                    )

                # Обработка информации о товаре
                product_info = ProductInfo.objects.create(
                    product_id=product.id,
                    shop_id=shop.id,
                    external_id=product_data.get("id"),
                    model=product_data.get("model"),
                    price=product_data.get("price"),
                    price_rrp=product_data.get("price_rrp"),
                    quantity=product_data.get("quantity"),
                )

                # Обработка параметров товара
                parameters_data = product_data.get("parameters", {})
                for param_name, param_value in parameters_data.items():
                    parameter, _ = Parameter.objects.get_or_create(name=param_name)
                    ProductParameter.objects.create(
                        product_info_id=product_info.id,
                        parameter=parameter,
                        value=param_value,
                    )

            return Response({"Status": True, "Message": "Магазин успешно обновлен."})
        except IntegrityError:
            return Response(
                {"Status": False, "Errors": "Не указаны все необходимые аргументы."},
                status=status.HTTP_400_BAD_REQUEST,
            )


class ProductListView(generics.ListAPIView):
    """Получение списка товаров."""

    queryset = Product.objects.all()
    serializer_class = ProductListSerializer
    pagination_class = ProductPagination
    filter_backends = [rest_framework.DjangoFilterBackend]
    filterset_class = ProductFilter


class ProductDetailView(views.APIView, ProductPagination):
    """Получение подробной информации о товарах на основе заданных фильтров."""

    pagination_class = ProductPagination
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        query = Q(shop__state=True)

        shop_id = request.query_params.get("shop_id")
        category_id = request.query_params.get("category_id")
        product = request.query_params.get("product")

        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        if product:
            query = query & Q(product__name__icontains=product)

        # Фильтруем и отбрасываем дубликаты
        queryset = (
            ProductInfo.objects.filter(query)
            .select_related("shop", "product__category")
            .prefetch_related("product_parameters__parameter")
            .distinct()
        )

        # Обработка пагинации
        paginated_queryset = self.paginate_queryset(queryset, request)
        serializer = ProductInfoSerializer(paginated_queryset, many=True)
        return self.get_paginated_response(serializer.data)


class TestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "Status": True,
                "HTTP_Method": request.method,
                "HTTP_Headers": dict(request.headers),
            }
        )

    def post(self, request, *args, **kwargs):
        print(request.data)
        return JsonResponse(
            {
                "Status": True,
                "HTTP_Method": request.method,
                "HTTP_Headers": dict(request.headers),
            }
        )
