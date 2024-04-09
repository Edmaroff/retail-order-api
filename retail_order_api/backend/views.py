from celery.result import AsyncResult
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import IntegrityError, transaction
from django.db.models import F, Q
from django.http import JsonResponse
from django.urls import reverse
from django.views import View
from django_filters import rest_framework
from djoser.social.views import ProviderAuthView
from drf_spectacular.utils import extend_schema
from rest_framework import filters, generics, permissions, status, views
from rest_framework.response import Response
from social_django.utils import load_backend, load_strategy
from ujson import loads as load_json

from backend.filters import ProductFilter
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
from backend.pagination import (
    CategoryPagination,
    ProductPagination,
    ProductShopPagination,
    ShopPagination,
)
from backend.permissions import IsBuyerUser, IsShopUser
from backend.serializers import (
    CategoryListSerializer,
    ContactSerializer,
    OrderItemSerializer,
    OrderSerializer,
    ProductInfoSerializer,
    ProductWithImageSerializer,
    ShopCreateUpdateSerializer,
    ShopDetailSerializer,
    ShopListSerializer,
)
from backend.signals import new_order
from backend.tasks import delete_cached_files_celery, do_import_celery
from retail_order_api import settings


class CustomProviderAuthView(ProviderAuthView):
    def get(self, request, *args, **kwargs):
        """
        Метод является модифицированной версией ProviderAuthView.get
        Получает URL для авторизации через социальную сеть.

        Изменения:
        - Для получения redirect_uri используются
        настройки проекта вместо GET-параметров.
        """
        redirect_uri = settings.DJOSER.get("SOCIAL_AUTH_ALLOWED_REDIRECT_URIS")[0]
        strategy = load_strategy(request)
        strategy.session_set("redirect_uri", redirect_uri)

        backend_name = self.kwargs["provider"]
        backend = load_backend(strategy, backend_name, redirect_uri=redirect_uri)

        authorization_url = backend.auth_url()
        return Response(data={"authorization_url": authorization_url})


class RedirectSocialView(View):
    """Редирект после успешной социальной аутентификации."""

    def get(self, request, *args, **kwargs):
        code, state = str(request.GET["code"]), str(request.GET["state"])
        json_obj = {"code": code, "state": state}
        return JsonResponse(json_obj)


@extend_schema(tags=["Celery результат"])
class CeleryTaskResultView(views.APIView):
    """Получение результата задачи celery по идентификатору."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, task_id):
        task_result = AsyncResult(task_id)
        result = {
            "task_id": task_id,
            "task_status": task_result.status,
            "task_result": task_result.result,
        }
        return Response(result)


@extend_schema(tags=["Магазин"])
class ShopListView(generics.ListAPIView):
    """
    Получение списка магазинов с пагинацией
    и фильтрацией с помощью GET-параметра search.
    """

    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopListSerializer
    pagination_class = ShopPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


@extend_schema(tags=["Категории"])
class CategoryListView(generics.ListAPIView):
    """
    Получение списка категорий с пагинацией
    и фильтрацией с помощью GET-параметра search.
    """

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    pagination_class = CategoryPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


@extend_schema(tags=["Продукт"])
class ProductListView(generics.ListAPIView):
    """
    Получение списка продуктов с пагинацией и фильтрацией с помощью GET-параметров:
    - product - поиск продуктов по подстроке в их названии;
    - category - поиск продуктов по подстроке в названии категории.
    """

    queryset = Product.objects.all()
    serializer_class = ProductWithImageSerializer
    pagination_class = ProductPagination
    filter_backends = [rest_framework.DjangoFilterBackend]
    filterset_class = ProductFilter


@extend_schema(tags=["Контакты покупателя"])
class BuyerContactsView(views.APIView):
    """Управление контактами покупателя."""

    permission_classes = [IsBuyerUser]

    def get(self, request):
        """Получает список контактов покупателя."""

        contacts = Contact.objects.filter(user=request.user)

        if contacts.exists():
            serializer = ContactSerializer(contacts, many=True)
            return Response({"Status": True, "Data": serializer.data})

        return Response(
            {"Status": True, "Data": [], "Message": "У пользователя нет контактов."},
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        """Создает контакт покупателя."""
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
        """Обновляет существующий контакт покупателя."""
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ContactSerializer(contact, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"Status": True, "Data": serializer.data})

        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, *args, **kwargs):
        """Удаляет контакт покупателя."""
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


@extend_schema(tags=["Магазин"])
class ShopDetailView(views.APIView):
    """Управление магазином пользователя."""

    permission_classes = [IsShopUser]

    def get(self, request, *args, **kwargs):
        """Получает магазин пользователя."""
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
        """Создает магазин пользователя."""
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
        """Обновляет магазин пользователя."""
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
        """Удаляет магазин пользователя."""
        try:
            shop = Shop.objects.get(user=request.user)
            shop.delete()
            return Response({"Status": True, "Message": "Магазин удален."})
        except Shop.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Магазин пользователя не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )


@extend_schema(tags=["Магазин"])
class ShopDataView(views.APIView):
    """Загрузка и выгрузка товаров магазина."""

    pagination_class = ProductShopPagination
    permission_classes = [IsShopUser]

    @staticmethod
    def _process_url(url):
        """Валидация URL."""
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
        """Получает информацию о всех товарах магазина."""

        shop = (
            Shop.objects.filter(user=request.user)
            .prefetch_related("categories")
            .first()
        )

        if not shop:
            return Response(
                {"Status": False, "Errors": "Магазин не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        products_info = ProductInfo.objects.filter(shop=shop).select_related(
            "product__category"
        )
        product_parameters = ProductParameter.objects.filter(
            product_info__shop=shop
        ).select_related("parameter")

        # Применяем пагинацию
        paginator = self.pagination_class()
        result_page = paginator.paginate_queryset(products_info, request)

        # Данные для выгрузки
        data = {
            "shop_name": shop.name,
            "categories": list(shop.categories.values_list("name", flat=True)),
            "goods": [],
        }

        # Обработка параметров товара
        product_parameters_dict = {}
        for parameter in product_parameters:
            product_info_id = parameter.product_info_id
            if product_info_id not in product_parameters_dict:
                product_parameters_dict[product_info_id] = {}
            product_parameters_dict[product_info_id][
                parameter.parameter.name
            ] = parameter.value

        # Обработка информации о товарах
        for product_info in result_page:
            product_data = {
                "id": product_info.external_id,
                "category": product_info.product.category.name,
                "name": product_info.product.name,
                "model": product_info.model,
                "price": product_info.price,
                "price_rrp": product_info.price_rrp,
                "quantity": product_info.quantity,
                "parameters": product_parameters_dict.get(product_info.id, {}),
            }

            data["goods"].append(product_data)

        # Возвращаем результат с учетом пагинации
        return paginator.get_paginated_response({"Status": True, "Data": data})

    def post(self, request, *args, **kwargs):
        """Загрузить товары магазина из файла .yaml с использованием Celery."""
        url = request.data.get("url")
        check_url = self._process_url(url)

        if isinstance(check_url, Response):
            return check_url

        # Вызов Celery задачи
        task_result = do_import_celery.delay(url, request.user.id)
        task_id = task_result.id

        # Создание URL для просмотра результатов
        result_url = reverse("backend:task-result", kwargs={"task_id": task_id})

        return Response(
            {
                "Status": True,
                "Message": "Начали обрабатывать данные.",
                "result_url": result_url,
            }
        )


@extend_schema(tags=["Продукт"])
class ProductInShopView(views.APIView, ProductPagination):

    pagination_class = ProductPagination
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, *args, **kwargs):
        """
        Получение подробной информации о товарах в магазинах
        на основе заданных фильтров.
        """
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


@extend_schema(tags=["Корзина"])
class BuyerBasketView(views.APIView):
    """Управление корзиной покупателя."""

    permission_classes = [IsBuyerUser]

    @staticmethod
    def _process_items(items):
        """Валидация и обработка списка продуктов в корзине покупателя."""
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
        """Получает список товаров в корзине покупателя."""
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
        """Добавляет товары в корзину покупателя."""
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
        """Изменяет количество товаров в корзине покупателя."""
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
                            "Errors": f"Товар с id {order_item_id} "
                                      f"не найден в корзине.",
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
                                    f"Превышено доступное количество товара — "
                                    f"{available_quantity}."
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
        """Удаляет товары из корзины покупателя."""
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
            elif isinstance(order_item_ids, str):
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


@extend_schema(tags=["Заказы покупателя"])
class BuyerOrderView(views.APIView):
    """Управление заказом покупателя."""

    permission_classes = [IsBuyerUser]

    def get(self, request, *args, **kwargs):
        """Получает список заказов покупателя."""
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
        """Создает новый заказ покупателя."""
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

                order_id = order.id

                # Отправляем письмо покупателю
                new_order.send(
                    sender=self.__class__, user_id=request.user.id, order_id=order_id
                )

                return Response(
                    {
                        "Status": True,
                        "Message": "Заказ успешно оформлен. "
                        "Состав заказа мог измениться из-за отсутствия "
                        "требуемого количества товара у продавца.",
                        "Order": data,
                    }
                )

            else:
                # Если нет оставшихся товаров, возвращаем ошибку
                return Response(
                    {
                        "Status": False,
                        "Errors": "Товары в корзине закончились "
                                  "после проверки наличия в магазине.",
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )


@extend_schema(tags=["Заказы магазина"])
class ShopOrderView(views.APIView):
    """Получение заказов магазина."""

    permission_classes = [IsShopUser]

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


@extend_schema(tags=["Продукт"])
class ProductDetailView(views.APIView):
    """Управление продуктом."""

    permission_classes = [IsShopUser]

    def get(self, request, *args, **kwargs):
        """Получает информацию о продукте."""
        product_id = request.data.get("product_id")

        if not product_id or not product_id.isdigit():
            return Response(
                {"Status": False, "Errors": "product_id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Продукт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ProductWithImageSerializer(product, context={"request": request})
        return Response({"Status": True, "Data": serializer.data})

    def post(self, request, *args, **kwargs):
        """Создает продукт."""
        serializer = ProductWithImageSerializer(
            data=request.data, context={"request": request}
        )
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

    def patch(self, request):
        """Изменяет продукт."""
        product_id = request.data.get("product_id")

        if not product_id or not product_id.isdigit():
            return Response(
                {"Status": False, "Errors": "product_id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            product = Product.objects.get(id=product_id)
        except Product.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Продукт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        if request.data.get("image"):
            # product.delete_cached_files()  # Без Celery
            # Запуск Celery задачи для удаления файлов
            delete_cached_files_celery.delay(
                product.id, product._meta.app_label, product._meta.model_name
            )

        serializer = ProductWithImageSerializer(
            product, data=request.data, partial=True, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response({"Status": True, "Data": serializer.data})

        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
