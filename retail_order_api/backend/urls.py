from django.urls import include, path

from backend.views import (
    BasketView,
    CategoryListView,
    OrderView,
    ProductDetailView,
    ProductListView,
    ShopDataView,
    ShopListView,
    TestView,
    UserContactsView,
    UserShopDetailView,
)

app_name = "backend"
urlpatterns = [
    path("", include("djoser.urls")),
    path("", include("djoser.urls.authtoken")),
    path("test/", TestView.as_view(), name="test"),
    path("users/me/contacts/", UserContactsView.as_view(), name="user_contacts"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("shops/", ShopListView.as_view(), name="shops_list"),
    path("users/me/shop/", UserShopDetailView.as_view(), name="user_shops"),
    path("users/me/shop/data/", ShopDataView.as_view(), name="shops_data"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/detail/", ProductDetailView.as_view(), name="products_detail"),
    path('basket/', BasketView.as_view(), name='basket'),
    path('order/', OrderView.as_view(), name='order'),
]
