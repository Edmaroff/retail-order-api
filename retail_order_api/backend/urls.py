from django.urls import include, path

from backend.views import (
    CategoryListView,
    ShopListView,
    TestView,
    UserContactsView,
    UserShopDetailView,
)

app_name = 'backend'
urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path("test/", TestView.as_view(), name="test"),
    path("users/me/contacts/", UserContactsView.as_view(), name="user_contacts"),
    path("shops/", ShopListView.as_view(), name="shops"),
    path("categories/", CategoryListView.as_view(), name="categories"),
    path("users/me/shops/", UserShopDetailView.as_view(), name="user_shops"),
]
