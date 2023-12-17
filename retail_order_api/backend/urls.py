from django.urls import include, path

from backend.views import TestView

app_name = 'backend'
urlpatterns = [
    path(r'auth/', include('djoser.urls')),
    path(r'auth/', include('djoser.urls.authtoken')),
    path("test/", TestView.as_view(), name="test"),
]
