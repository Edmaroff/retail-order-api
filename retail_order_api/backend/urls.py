from django.urls import include, path, re_path

from backend.views import (
    BuyerBasketView,
    BuyerContactsView,
    BuyerOrderView,
    CategoryListView,
    CeleryTaskResultView,
    CustomProviderAuthView,
    ProductDetailView,
    ProductListView,
    RedirectSocial,
    ShopDataView,
    ShopDetailView,
    ShopListView,
    ShopOrderView,
)

app_name = "backend"

shop_urls = [
    path("detail/", ShopDetailView.as_view(), name="shop_detail"),
    path("data/", ShopDataView.as_view(), name="shop_data"),
    path("orders/", ShopOrderView.as_view(), name="shop_order"),
]

buyer_urls = [
    path("contacts/", BuyerContactsView.as_view(), name="buyer_contacts"),
    path("basket/", BuyerBasketView.as_view(), name="buyer_basket"),
    path("orders/", BuyerOrderView.as_view(), name="buyer_order"),
]

user_urls = [
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("shops/", ShopListView.as_view(), name="shops"),
    path("products/", ProductListView.as_view(), name="products"),
    path("products/detail/", ProductDetailView.as_view(), name="products_detail"),
]

# URL для просмотра результатов задач Celery
task_urls = [
    path(
        "task-result/<str:task_id>/", CeleryTaskResultView.as_view(), name="task-result"
    ),
]

djoser_urls = [
    path("auth/", include("djoser.urls")),
    path("auth/", include("djoser.urls.jwt")),
    path('auth/social/redirect/', RedirectSocial.as_view()),
    re_path(
        r"^auth/social/(?P<provider>\S+)/$",
        CustomProviderAuthView.as_view(),
        name="provider-auth",
    ),
]

urlpatterns = [
    path("shop/", include(shop_urls)),
    path("buyer/", include(buyer_urls)),
    path("", include(user_urls)),
    path("", include(task_urls)),
    path("", include(djoser_urls)),
]
