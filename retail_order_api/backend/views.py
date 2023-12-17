from django.contrib.auth.backends import ModelBackend
from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.http import JsonResponse
from requests import get
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView
from yaml import Loader
from yaml import load as load_yaml

from backend.models import (
    Category,
    Contact,
    Order,
    OrderItem,
    Parameter,
    Product,
    ProductInfo,
    ProductParameter,
    Shop,
)


class TestView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, *args, **kwargs):
        return JsonResponse(
            {
                "Status": True,
                "HTTP_Method": request.method,
                "HTTP_Headers": dict(request.headers),
            }
        )

    def post(self, request, *args, **kwargs):
        permission_classes = [IsAuthenticated]

        print(request.data)
        return JsonResponse(
            {
                "Status": True,
                "HTTP_Method": request.method,
                "HTTP_Headers": dict(request.headers),
            }
        )


# class PartnerUpdate(APIView):
#     """
#     Класс для обновления прайса от поставщика
#     """
#
#     def post(self, request, *args, **kwargs):
#         # if not request.user.is_authenticated:
#         #     return JsonResponse({'Status': False, 'Error': 'Log in required'}, status=403)
#         #
#         # if request.user.type != 'shop':
#         #     return JsonResponse({'Status': False, 'Error': 'Только для магазинов'}, status=403)
#
#         url = request.data.get("url")
#         print(url)
#         if url:
#             validate_url = URLValidator()
#             try:
#                 validate_url(url)
#             except ValidationError as e:
#                 return JsonResponse({"Status": False, "Error": str(e)})
#             else:
#                 stream = get(url).content
#
#                 data = load_yaml(stream, Loader=Loader)
#
#                 shop, _ = Shop.objects.get_or_create(
#                     name=data["shop"], user_id=request.user.id
#                 )
#                 print(shop, _)
#                 for category in data["categories"]:
#                     category_object, _ = Category.objects.get_or_create(
#                         id=category["id"], name=category["name"]
#                     )
#                     category_object.shops.add(shop.id)
#                     category_object.save()
#                 ProductInfo.objects.filter(shop_id=shop.id).delete()
#                 for item in data["goods"]:
#                     product, _ = Product.objects.get_or_create(
#                         name=item["name"], category_id=item["category"]
#                     )
#
#                     product_info = ProductInfo.objects.create(
#                         product_id=product.id,
#                         external_id=item["id"],
#                         model=item["model"],
#                         price=item["price"],
#                         price_rrp=item["price_rrp"],
#                         quantity=item["quantity"],
#                         shop_id=shop.id,
#                     )
#                     for name, value in item["parameters"].items():
#                         parameter_object, _ = Parameter.objects.get_or_create(name=name)
#                         ProductParameter.objects.create(
#                             product_info_id=product_info.id,
#                             parameter_id=parameter_object.id,
#                             value=value,
#                         )
#
#                 return JsonResponse({"Status": True})
#
#         return JsonResponse(
#             {"Status": False, "Errors": "Не указаны все необходимые аргументы"}
#         )
