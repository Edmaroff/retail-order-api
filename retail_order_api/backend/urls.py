from django.urls import include, path

from backend.views import (
    CategoryListView,
    ShopListView,
    TestView,
    UserContactsView,
    UserShopDetailView, ShopDataView,
)

app_name = 'backend'
urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path("test/", TestView.as_view(), name="test"),
    path("users/me/contacts/", UserContactsView.as_view(), name="user_contacts"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("shops/", ShopListView.as_view(), name="shops_list"),
    path("users/me/shops/", UserShopDetailView.as_view(), name="user_shops"),
    path("users/me/shops/data/", ShopDataView.as_view(), name="shops_data"),
]
