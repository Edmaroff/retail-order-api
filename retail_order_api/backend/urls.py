from django.urls import include, path

from backend.views import (
    BasketView,
    CategoryListView,
    OrderView,
    ProductDetailView,
    ProductListView,
    ShopDataView,
    ShopListView,
    ShopOrderView,
    UserContactsView,
    UserShopDetailView,
)

app_name = "backend"

shop_urls = [
    path("detail/", UserShopDetailView.as_view(), name="shop_detail"),
    path("data/", ShopDataView.as_view(), name="shop_data"),
    path("orders/", ShopOrderView.as_view(), name="shop_order"),
]

buyer_urls = [
    path("contacts/", UserContactsView.as_view(), name="buyer_contacts"),
    path('basket/', BasketView.as_view(), name='buyer_basket'),
    path('orders/', OrderView.as_view(), name='buyer_order'),
]

user_urls = [
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("shops/", ShopListView.as_view(), name="shops_list"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/detail/", ProductDetailView.as_view(), name="products_detail"),
]

djoser_urls = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.authtoken")),
]

urlpatterns = [
    path("shop/", include(shop_urls)),
    path("buyer/", include(buyer_urls)),
    path("", include(user_urls)),
    path("", include(djoser_urls)),
]
