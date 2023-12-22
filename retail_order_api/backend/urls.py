from django.urls import include, path

from backend.views import TestView, UserContactsView

app_name = 'backend'
urlpatterns = [
    path('', include('djoser.urls')),
    path('', include('djoser.urls.authtoken')),
    path("test/", TestView.as_view(), name="test"),
    path("users/me/contacts/", UserContactsView.as_view(), name="test"),
]
