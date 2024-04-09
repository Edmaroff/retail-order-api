import pytest
from django.core.exceptions import ObjectDoesNotExist
from django.urls import reverse
from model_bakery import baker
from rest_framework import status
from rest_framework.test import APIClient

from backend.models import (
    Category,
    Contact,
    CustomUser,
    Order,
    OrderItem,
    Product,
    ProductInfo,
    Shop,
)


@pytest.fixture
def client():
    return APIClient()


@pytest.fixture
def user_factory():
    def factory(*args, **kwargs):
        return baker.make(CustomUser, *args, **kwargs)

    return factory


@pytest.fixture
def authenticated_client_buyer(client, user_factory):
    user = user_factory(type="buyer")
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def authenticated_client_shop(client, user_factory):
    user = user_factory(type="shop")
    client.force_authenticate(user=user)
    return client, user


@pytest.fixture
def contact_factory():
    def factory(*args, **kwargs):
        return baker.make(Contact, *args, **kwargs)

    return factory


@pytest.fixture
def shop_factory():
    def factory(*args, **kwargs):
        return baker.make(Shop, *args, **kwargs)

    return factory


@pytest.fixture
def category_factory():
    def factory(*args, **kwargs):
        return baker.make(Category, *args, **kwargs)

    return factory


@pytest.fixture
def product_factory():
    def factory(category, *args, **kwargs):
        return baker.make(Product, category=category, *args, **kwargs)

    return factory


@pytest.fixture
def product_with_category_factory(category_factory):
    def factory(*args, **kwargs):
        return baker.make(Product, category=category_factory, *args, **kwargs)

    return factory


@pytest.fixture
def product_info_factory():
    def factory(*args, **kwargs):
        return baker.make(ProductInfo, *args, **kwargs)

    return factory


@pytest.fixture
def add_products_info(product_info_factory, product_with_category_factory):
    def _add_products_info(available_quantity=10):
        product_info = product_info_factory(
            _quantity=10,
            product=product_with_category_factory,
            quantity=available_quantity,
        )
        added_product_info_ids = [product.id for product in product_info[0:3]]
        return added_product_info_ids

    return _add_products_info


@pytest.fixture
def add_products_with_state(authenticated_client_buyer, add_products_info):
    def _add_products(state="basket", available_quantity=10, quantity_to_add=10):
        client, user = authenticated_client_buyer
        order = Order.objects.create(user=user, state=state)
        added_product_info_ids = add_products_info(available_quantity)

        for product_info_id in added_product_info_ids:
            OrderItem.objects.create(
                order=order, product_info_id=product_info_id, quantity=quantity_to_add
            )

        return client, order, added_product_info_ids

    return _add_products


@pytest.mark.django_db
@pytest.mark.parametrize(
    "url_name, model, factory",
    [
        ("shops", Shop, "shop_factory"),
        ("categories", Category, "category_factory"),
        ("products", Product, "product_with_category_factory"),
    ],
)
def test_list_view(client, url_name, model, factory, request):
    url = reverse(f"backend:{url_name}")
    instances = request.getfixturevalue(factory)(_quantity=3)

    response = client.get(url)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.data["results"], list)
    assert len(response.data["results"]) == len(instances)


@pytest.mark.django_db
class TestBuyerContactsView:
    """Тесты для BuyerContactsView."""

    url = reverse("backend:buyer_contacts")

    def test_get_contact(self, authenticated_client_buyer, contact_factory):
        client, user = authenticated_client_buyer
        contacts = contact_factory(user=user, _quantity=3)

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data["Data"]) == len(contacts)
        assert response.data["Status"] is True

    def test_post_contact(self, authenticated_client_buyer):
        client, user = authenticated_client_buyer
        data = {
            "user": user.id,
            "phone": "+78001234567",
            "city": "Иркутск",
            "street": "Ленина",
            "house": "16",
        }

        response = client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["Status"] is True

        contact = Contact.objects.filter(user=user).first()
        assert contact is not None

    def test_patch_contact(self, authenticated_client_buyer, contact_factory):
        client, user = authenticated_client_buyer
        contacts = contact_factory(user=user, _quantity=3)
        contact = contacts[0]
        data = {
            "id": str(contact.id),
            "phone": "+78001234567",
            "city": "Иркутск",
            "street": "Ленина",
            "house": "16",
        }

        response = client.patch(self.url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True

        updated_contact = Contact.objects.get(id=contact.id)

        assert updated_contact.phone == "+78001234567"
        assert updated_contact.city == "Иркутск"

    def test_delete_contact(self, authenticated_client_buyer, contact_factory):
        client, user = authenticated_client_buyer
        contacts = contact_factory(user=user, _quantity=3)
        contact = contacts[0]
        data = {
            "id": str(contact.id),
        }

        response = client.delete(self.url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True

        with pytest.raises(ObjectDoesNotExist):
            Contact.objects.get(id=contact.id)


@pytest.mark.django_db
class TestShopDetailView:
    """Тесты для ShopDetailView."""

    url = reverse("backend:shop_detail")

    def test_get_shop(self, authenticated_client_shop, shop_factory):
        client, user = authenticated_client_shop
        shop = shop_factory(user=user)

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True
        assert response.data["Data"]["name"] == shop.name

    def test_post_shop(self, authenticated_client_shop, category_factory):
        client, user = authenticated_client_shop
        categories = category_factory(_quantity=3)
        data = {
            "name": "Магазин",
            "categories": [category.id for category in categories],
        }

        response = client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_201_CREATED
        assert response.data["Status"] is True

        shop = Shop.objects.get(user=user)
        assert shop is not None
        assert shop.categories.count() == len(categories)

    def test_patch_shop(self, authenticated_client_shop, shop_factory):
        client, user = authenticated_client_shop
        shop = shop_factory(user=user)
        data = {
            "name": "Новый Магазин",
            "url": "https://example.com",
        }

        response = client.patch(self.url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True

        updated_shop = Shop.objects.get(id=shop.id)

        assert updated_shop.name == "Новый Магазин"
        assert updated_shop.url == "https://example.com"

    def test_delete_shop(self, authenticated_client_shop, shop_factory):
        client, user = authenticated_client_shop
        shop = shop_factory(user=user)

        response = client.delete(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True

        with pytest.raises(ObjectDoesNotExist):
            Shop.objects.get(id=shop.id)


@pytest.mark.django_db
class TestProductDetailView:
    """Тесты для ProductDetailView."""

    url = reverse("backend:products_in_shops")

    @staticmethod
    def assert_response(response, expected_ids):
        assert response.status_code == status.HTTP_200_OK
        response_ids = [product_info["id"] for product_info in response.data["results"]]
        assert sorted(response_ids) == sorted(expected_ids)

    def test_filter_products_by_shop_id(
        self,
        authenticated_client_buyer,
        shop_factory,
        product_info_factory,
        product_with_category_factory,
    ):
        client, _ = authenticated_client_buyer
        shop_1 = shop_factory(state=True)
        shop_2 = shop_factory(state=True)
        products_info_in_shop_1 = product_info_factory(
            _quantity=3, shop=shop_1, product=product_with_category_factory
        )
        product_info_factory(
            _quantity=2, shop=shop_2, product=product_with_category_factory
        )
        expected_product_info_ids = [
            product_info.id for product_info in products_info_in_shop_1
        ]
        filter_params = {
            "shop_id": shop_1.id,
        }

        response = client.get(self.url, filter_params)

        self.assert_response(response, expected_product_info_ids)

    def test_filter_products_by_category_id(
        self,
        authenticated_client_buyer,
        shop_factory,
        product_info_factory,
        category_factory,
        product_factory,
    ):
        client, _ = authenticated_client_buyer
        shop = shop_factory(state=True)

        category_1 = category_factory()
        category_2 = category_factory()

        products_info_with_category_1 = product_info_factory(
            _quantity=3, shop=shop, product=product_factory(category=category_1)
        )
        product_info_factory(
            _quantity=2, shop=shop, product=product_factory(category=category_2)
        )
        expected_product_info_ids = [
            product_info.id for product_info in products_info_with_category_1
        ]
        filter_params = {
            "category_id": category_1.id,
        }

        response = client.get(self.url, filter_params)

        self.assert_response(response, expected_product_info_ids)

    def test_filter_products_by_product_name(
        self,
        authenticated_client_buyer,
        shop_factory,
        product_with_category_factory,
        product_info_factory,
    ):
        client, _ = authenticated_client_buyer
        shop = shop_factory(state=True)

        product_1 = product_with_category_factory(name="Apple iPhone")
        product_2 = product_with_category_factory(name="Samsung Galaxy")
        product_3 = product_with_category_factory(name="Misapply Pixel")

        products_info = (
            product_info_factory(_quantity=2, shop=shop, product=product_1)
            + product_info_factory(_quantity=2, shop=shop, product=product_2)
            + product_info_factory(_quantity=1, shop=shop, product=product_3)
        )

        string_for_search = "ppl"
        expected_product_info_ids = [
            product_info.id
            for product_info in products_info
            if string_for_search in product_info.product.name.lower()
        ]
        filter_params = {
            "product": string_for_search,
        }

        response = client.get(self.url, filter_params)

        self.assert_response(response, expected_product_info_ids)


# -----------------------------------------------------


@pytest.mark.django_db
class TestBuyerBasketView:
    """Тесты для BuyerBasketView."""

    url = reverse("backend:buyer_basket")

    def test_get_basket(self, add_products_with_state):
        client, basket, added_product_info_ids = add_products_with_state()

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        response_product_info_ids = [
            ordered_item["product_info"]["id"]
            for ordered_item in response.data["Order"][0]["ordered_items"]
        ]
        assert sorted(response_product_info_ids) == sorted(added_product_info_ids)

    def test_post_basket_successful(
        self,
        authenticated_client_buyer,
        add_products_info,
    ):
        """Проверяет корректное добавление товаров в корзину покупателя."""

        client, user = authenticated_client_buyer
        added_product_info_ids = add_products_info(available_quantity=10)
        quantity_to_add = 3

        items_to_add = [
            {"product_info": product_info_id, "quantity": quantity_to_add}
            for product_info_id in added_product_info_ids
        ]
        data = {"items": items_to_add}

        response = client.post(self.url, data, format="json")

        product_info_ids_in_basket = OrderItem.objects.filter(
            order__user=user, order__state="basket"
        ).values_list("product_info_id", flat=True)

        assert sorted(added_product_info_ids) == sorted(product_info_ids_in_basket)
        assert response.status_code == status.HTTP_201_CREATED
        assert len(added_product_info_ids) == response.data["Создано объектов"]

    def test_post_basket_no_available_products(
        self,
        authenticated_client_buyer,
        product_info_factory,
        product_with_category_factory,
    ):
        """
        Проверяет обработку ошибки при попытке добавления товара в корзину покупателя
        с недостаточным количеством.
        """

        client, _ = authenticated_client_buyer
        available_quantity = 10
        product_info = product_info_factory(
            product=product_with_category_factory, quantity=available_quantity
        )
        data = {
            "items": [
                {"product_info": product_info.id, "quantity": available_quantity + 1}
            ]
        }

        response = client.post(self.url, data, format="json")

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["Status"] is False

    def test_patch_basket(self, add_products_with_state):
        client, basket, added_product_info_ids = add_products_with_state()
        order_item_ids_in_basket = OrderItem.objects.filter(
            order__user=basket.user, order__state="basket"
        ).values_list("id", flat=True)

        new_quantity = 5
        items_to_change = [
            {"id": order_item_id, "quantity": new_quantity}
            for order_item_id in order_item_ids_in_basket
        ]
        data = {"items": items_to_change}

        response = client.patch(self.url, data, format="json")

        assert response.status_code == status.HTTP_200_OK

        for order_item_id in order_item_ids_in_basket:
            updated_quantity = OrderItem.objects.get(id=order_item_id).quantity
            assert updated_quantity == new_quantity

    def test_delete_basket(self, add_products_with_state):
        client, basket, added_product_info_ids = add_products_with_state()
        order_item_ids_in_basket = OrderItem.objects.filter(
            order__user=basket.user, order__state="basket"
        ).values_list("id", flat=True)
        data = {"items": list(order_item_ids_in_basket)}

        response = client.delete(self.url, data, format="json")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True
        order_item_exist = OrderItem.objects.filter(
            order__user=basket.user, order__state="basket"
        ).exists()
        assert order_item_exist is False


@pytest.mark.django_db
class TestBuyerOrderView:
    """Тесты для BuyerOrderView."""

    url = reverse("backend:buyer_order")

    def test_get_order(self, add_products_with_state):
        client, _, added_product_info_ids = add_products_with_state(state="order")

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        response_product_info_ids = [
            ordered_item["product_info"]["id"]
            for ordered_item in response.data["Orders"][0]["ordered_items"]
        ]
        assert sorted(response_product_info_ids) == sorted(added_product_info_ids)

    def test_post_successful(self, contact_factory, add_products_with_state):
        available_quantity = 10
        quantity_to_add = 8
        client, order, added_product_info_ids = add_products_with_state(
            state="basket",
            available_quantity=available_quantity,
            quantity_to_add=quantity_to_add,
        )
        contact = contact_factory(user=order.user)
        data = {"contact_id": contact.id}

        response = client.post(self.url, data=data, format="json")

        assert response.status_code == status.HTTP_200_OK

        for product_info_id in added_product_info_ids:
            updated_available_quantity = ProductInfo.objects.get(
                id=product_info_id
            ).quantity
            expected_updated_quantity = available_quantity - quantity_to_add
            # Проверяем, что доступное количество товара уменьшилось
            # на количество товаров в заказе
            assert updated_available_quantity == expected_updated_quantity

    def test_post_no_available_products(self, contact_factory, add_products_with_state):
        """Проверка создания заказа, когда товары закончились у продавца."""
        available_quantity = 10
        quantity_to_add = 8
        client, order, added_product_info_ids = add_products_with_state(
            state="basket",
            available_quantity=available_quantity,
            quantity_to_add=quantity_to_add,
        )
        contact = contact_factory(user=order.user)

        # Помечаем все товары в корзине как недоступные
        for product_info_id in added_product_info_ids:
            product_info = ProductInfo.objects.get(id=product_info_id)
            product_info.quantity = 0
            product_info.save()

        data = {"contact_id": contact.id}

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_400_BAD_REQUEST
        assert response.data["Status"] is False
        assert "Errors" in response.data
        assert (
            "Товары в корзине закончились после проверки наличия в магазине."
            == response.data["Errors"]
        )

    def test_post_more_than_available_products(
        self, contact_factory, add_products_with_state
    ):
        """
        Проверка создания заказа с количеством товаров в корзине больше,
        чем доступно у продавца.
        """
        available_quantity = 10
        quantity_to_add = 15  # Добавляем больше товаров, чем доступно у продавца
        client, order, added_product_info_ids = add_products_with_state(
            state="basket",
            available_quantity=available_quantity,
            quantity_to_add=quantity_to_add,
        )
        contact = contact_factory(user=order.user)

        data = {"contact_id": contact.id}

        response = client.post(self.url, data=data)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True

        # Получаем обновленные товары в заказе
        ordered_items = order.ordered_items.all()

        # Проверяем, что количество товаров в заказе соответствует
        # доступному количеству товаров у продавца
        for ordered_item in ordered_items:
            assert ordered_item.quantity == min(available_quantity, quantity_to_add)

        # Проверяем, что товары закончились после оформления заказа
        quantities_after_order = ProductInfo.objects.filter(
            id__in=added_product_info_ids
        ).values_list("quantity", flat=True)
        assert all(quantity == 0 for quantity in quantities_after_order)


@pytest.mark.django_db
class TestShopOrderView:
    """Тесты для ShopOrderView."""

    url = reverse("backend:shop_order")

    @staticmethod
    def create_shop_with_orders(
        shop_factory,
        expected_order_count,
        product_info_factory,
        product_with_category_factory,
        user,
    ):
        """Создает магазин со списком заказов для тестирования."""
        shop = shop_factory(user=user)
        orders_for_shop = baker.make(Order, _quantity=expected_order_count, state="new")
        products_info = product_info_factory(
            _quantity=10,
            product=product_with_category_factory,
            quantity=10,
            shop=shop,
        )
        for index, order in enumerate(orders_for_shop):
            OrderItem.objects.create(order=order, product_info=products_info[index])

        return shop

    def test_get_order(
        self,
        authenticated_client_shop,
        shop_factory,
        product_info_factory,
        product_with_category_factory,
    ):
        client, user = authenticated_client_shop

        expected_order_count = 3

        # Создаем проверяемый магазин и заказы для него
        shop = self.create_shop_with_orders(
            shop_factory,
            expected_order_count,
            product_info_factory,
            product_with_category_factory,
            user=user,
        )

        # Создаем другой магазин и заказы для него
        self.create_shop_with_orders(
            shop_factory,
            expected_order_count,
            product_info_factory,
            product_with_category_factory,
            user=None,
        )

        response = client.get(self.url)

        assert response.status_code == status.HTTP_200_OK
        assert response.data["Status"] is True
        assert expected_order_count == len(response.data["Orders"])

        # Проверяем, что в ответе содержатся только заказы нужного магазина
        expected_order_ids = Order.objects.filter(
            ordered_items__product_info__shop=shop
        ).values_list("id", flat=True)
        response_order_ids = [order["id"] for order in response.data["Orders"]]
        assert sorted(expected_order_ids) == sorted(response_order_ids)
