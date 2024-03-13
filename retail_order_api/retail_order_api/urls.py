# from django.contrib import admin
from baton.autodiscover import admin

from django.urls import include, path
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

from retail_order_api import settings

urlpatterns = [
    path("admin/", admin.site.urls),
    path('baton/', include('baton.urls')),
    path("api/v1/", include("backend.urls", namespace="backend")),
    path("api/v1/schema/", SpectacularAPIView.as_view(), name="schema"),
    path("api/v1/schema/docs/", SpectacularSwaggerView.as_view(url_name="schema")),
]

if settings.DEBUG:
    urlpatterns += [path("__debug__/", include("debug_toolbar.urls"))]
