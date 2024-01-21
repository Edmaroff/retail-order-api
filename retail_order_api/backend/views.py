from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django_filters import rest_framework
from requests import get
from rest_framework import filters, generics, permissions, status, views
from rest_framework.response import Response
from ujson import loads as load_json
from yaml import SafeLoader
from yaml import load as load_yaml
from yaml.error import YAMLError

from backend.filters import ProductFilter
from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)
from backend.pagination import CategoryPagination, ProductPagination, ShopPagination
from backend.permissions import IsAuthenticatedAndBuyerUser, IsAuthenticatedAndShopUser
from backend.serializers import (
    CategoryListSerializer,
    ContactSerializer,
    OrderItemSerializer,
    OrderSerializer,
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
                {"Status": True, "Message": "Магазин создан.", "Data": serializer.data},
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

        if isinstance(check_url, Response):
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
        with transaction.atomic():
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
                    user=request.user,
                    defaults={"name": data.get("shop_name"), "url": url},
                )

                # Обработка категорий
                shop.categories.clear()  # Удаление существующих категорий
                category_name_to_id = {}  # Для создания товаров
                categories_data = data.get("categories", [])
                for category_name in categories_data:
                    category_object, _ = Category.objects.get_or_create(
                        name=category_name
                    )
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
                        category_id = category_name_to_id.get(
                            product_data.get("category")
                        )
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

                return Response(
                    {"Status": True, "Message": "Магазин успешно обновлен."}
                )
            except IntegrityError:
                return Response(
                    {
                        "Status": False,
                        "Errors": "Не указаны все необходимые аргументы.",
                    },
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


class BasketView(views.APIView):
    """Управление корзиной пользователя."""

    permission_classes = [IsAuthenticatedAndBuyerUser]

    @staticmethod
    def _process_items(items):
        if not items:
            return Response(
                {
                    "Status": False,
                    "Errors": "Необходимо передать список товаров items.",
                },
                status=status.HTTP_400_BAD_REQUEST,
            )
        if isinstance(items, str):
            try:
                items = load_json(items)
            except ValueError:
                return Response(
                    {"Status": False, "Errors": "Неверный формат запроса."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        if not isinstance(items, list):
            return Response(
                {"Status": False, "Errors": "items должен быть списком."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return items

    def get(self, request, *args, **kwargs):
        basket = (
            Order.objects.filter(user_id=request.user.id, state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .distinct()
        )

        if not basket:
            return Response(
                {"Status": False, "Errors": "Корзина не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = OrderSerializer(basket, many=True)
        return Response({"Status": True, "Order": serializer.data})

    def post(self, request, *args, **kwargs):
        items = request.data.get("items")
        items = self._process_items(items)
        if isinstance(items, Response):
            return items

        with transaction.atomic():
            order, _ = Order.objects.get_or_create(
                user_id=request.user.id, state="basket"
            )
            objects_created = 0
            for order_item_data in items:
                order_item_data["order"] = order.id
                serializer = OrderItemSerializer(data=order_item_data)

                if serializer.is_valid():
                    try:
                        serializer.save()
                        objects_created += 1
                    except IntegrityError as error:
                        return Response(
                            {"Status": False, "Errors": str(error)},
                            status=status.HTTP_400_BAD_REQUEST,
                        )
                else:
                    transaction.set_rollback(True)  # Откатываем транзакцию
                    return Response(
                        {"Status": False, "Errors": serializer.errors},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

        return Response(
            {"Status": True, "Создано объектов": objects_created},
            status=status.HTTP_201_CREATED,
        )

    def patch(self, request, *args, **kwargs):
        items = request.data.get("items")
        items = self._process_items(items)
        if isinstance(items, Response):
            return items

        try:
            order = Order.objects.get(user_id=request.user.id, state="basket")
        except Order.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Корзина не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        objects_updated = 0
        with transaction.atomic():
            for basket_item in items:
                order_item_id = basket_item.get("id")
                new_quantity = basket_item.get("quantity")

                # Проверка передаваемых данные
                if not (
                    isinstance(order_item_id, int) and isinstance(new_quantity, int)
                ):
                    transaction.set_rollback(True)  # Откатываем транзакцию
                    return Response(
                        {"Status": False, "Errors": "Неверный формат данных."},
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                try:
                    order_item = OrderItem.objects.select_related("product_info").get(
                        id=order_item_id, order=order
                    )
                except OrderItem.DoesNotExist:
                    transaction.set_rollback(True)  # Откатываем транзакцию
                    return Response(
                        {
                            "Status": False,
                            "Errors": f"Товар с id {order_item_id} не найден в корзине.",
                        },
                        status=status.HTTP_404_NOT_FOUND,
                    )

                # Проверка доступного количества в магазине
                available_quantity = order_item.product_info.quantity
                if new_quantity > available_quantity:
                    transaction.set_rollback(True)  # Откатываем транзакцию
                    return Response(
                        {
                            "Status": False,
                            "Errors": {
                                "quantity": [
                                    f"Превышено доступное количество товара — {available_quantity}."
                                ],
                                "id": [order_item_id],
                            },
                        },
                        status=status.HTTP_400_BAD_REQUEST,
                    )

                order_item.quantity = new_quantity
                order_item.save()
                objects_updated += 1

            return Response({"Status": True, "Обновлено объектов": objects_updated})

    def delete(self, request, *args, **kwargs):
        order_item_ids = request.data.get("items")

        if not order_item_ids:
            return Response(
                {"Status": False, "Errors": "Не переданы ID товаров для удаления."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            if isinstance(order_item_ids, str) and "," in order_item_ids:
                order_item_ids = [
                    int(cat_id.strip()) for cat_id in order_item_ids.split(",")
                ]
            else:
                order_item_ids = [int(order_item_ids)]
        except ValueError:
            return Response(
                {"Status": False, "Errors": "items должен быть списком чисел."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.get(user_id=request.user.id, state="basket")
        except Order.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Корзина не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        deleted_count, _ = OrderItem.objects.filter(
            order_id=order.id, id__in=order_item_ids
        ).delete()

        if deleted_count == 0:
            return Response(
                {"Status": False, "Errors": "Не найдены товары для удаления."},
                status=status.HTTP_404_NOT_FOUND,
            )

        return Response({"Status": True, "Удалено товаров": deleted_count})


class OrderView(views.APIView):

    """Управление заказом пользователя."""

    permission_classes = [IsAuthenticatedAndBuyerUser]

    def get(self, request, *args, **kwargs):
        order = (
            Order.objects.filter(user_id=request.user.id)
            .exclude(state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .distinct()
        )

        serializer = OrderSerializer(order, many=True)
        return Response({"Status": True, "Orders": serializer.data})

    def post(self, request, *args, **kwargs):
        try:
            order = Order.objects.get(user_id=request.user.id, state="basket")
            if not order.ordered_items.exists():
                return Response(
                    {"Status": False, "Errors": "Нет товаров в корзине."},
                    status=status.HTTP_400_BAD_REQUEST,
                )
        except Order.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Корзина не найдена."},
                status=status.HTTP_404_NOT_FOUND,
            )

        contact_id = request.data.get("contact_id")

        if not contact_id:
            return Response(
                {"Status": False, "Errors": "Не передан ID контакта для заказа."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(id=contact_id, user=request.user)
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Проверка доступного количества товара у продавца
        with transaction.atomic():
            remaining_items = []  # Товары корзины после проверки наличия

            for order_item in order.ordered_items.all():
                available_quantity = order_item.product_info.quantity

                if available_quantity == 0:
                    # Удаляем товар из корзины, если 0 шт. у магазина
                    order_item.delete()
                    continue

                # Уменьшение количества в корзине до доступного
                order_item.quantity = min(order_item.quantity, available_quantity)
                order_item.save()

                # Уменьшение доступного количество товара у продавца
                order_item.product_info.quantity = F("quantity") - order_item.quantity
                order_item.product_info.save()
                remaining_items.append(order_item)

            if remaining_items:
                # Получаем обновленные данные заказа
                updated_basket = (
                    Order.objects.filter(user_id=request.user.id, state="basket")
                    .prefetch_related(
                        "ordered_items__product_info__product__category",
                        "ordered_items__product_info__product_parameters__parameter",
                    )
                    .select_related("contact")
                    .distinct()
                )

                serializer = OrderSerializer(updated_basket, many=True)
                data = serializer.data
                # Изменяем статус заказа
                order.contact = contact
                order.state = "new"
                order.save()

                return Response(
                    {
                        "Status": True,
                        "Message": "Заказ успешно оформлен. "
                        "Состав заказа мог измениться из-за отсутствия "
                        "доступного количества товара у продавца.",
                        "Order": data,
                    }
                )

            else:
                # Если нет оставшихся товаров, возвращаем ошибку
                return Response(
                    {
                        "Status": False,
                        "Errors": "Товары в корзине закончились после проверки наличия в магазине.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


class ShopOrderView(views.APIView):
    """Получение заказов магазина."""

    permission_classes = [IsAuthenticatedAndShopUser]

    def get(self, request, *args, **kwargs):
        orders = (
            Order.objects.filter(
                ordered_items__product_info__shop__user_id=request.user.id
            )
            .exclude(state="basket")
            .prefetch_related(
                "ordered_items__product_info__product__category",
                "ordered_items__product_info__product_parameters__parameter",
            )
            .select_related("contact")
            .distinct()
        )

        serializer = OrderSerializer(orders, many=True)
        return Response({"Status": True, "Orders": serializer.data})
