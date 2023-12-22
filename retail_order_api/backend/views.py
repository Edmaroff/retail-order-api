from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from backend.models import Contact
from backend.serializers import ContactSerializer


class UserContactsView(APIView):
    """Управление контактами пользователя"""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)
        serializer = ContactSerializer(contacts, many=True)

        return Response({"Status": True, "Data": serializer.data})

    def post(self, request):
        request.data._mutable = True
        request.data["user"] = request.user.id
        request.data._mutable = False

        serializer = ContactSerializer(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"Status": True, "Data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request):
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )
        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
            serializer = ContactSerializer(contact, data=request.data, partial=True)

            if serializer.is_valid():
                serializer.save()
                return Response({"Status": True, "Data": serializer.data})
            return Response(
                {"Status": False, "Errors": serializer.errors},
                status=status.HTTP_400_BAD_REQUEST,
            )
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

    def delete(self, request):
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
            contact.delete()
            return Response({"Status": True, "Data": "Контакт удален"})
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
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
