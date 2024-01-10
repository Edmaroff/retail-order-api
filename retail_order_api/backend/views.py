from django.http import JsonResponse, QueryDict
from django.shortcuts import get_object_or_404
from rest_framework import filters, generics, permissions, status, views
from rest_framework.response import Response

from backend.models import Category, Contact, Shop
from backend.pagination import CategoryPagination, ShopPagination
from backend.permissions import IsAuthenticatedAndShopUser
from backend.serializers import (
    CategoryListSerializer,
    ContactSerializer,
    ShopCreateUpdateSerializer,
    ShopDetailSerializer,
    ShopListSerializer,
)


class UserContactsView(views.APIView):
    """Управление контактами пользователя."""

    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        contacts = Contact.objects.filter(user=request.user)

        if contacts.exists():
            serializer = ContactSerializer(contacts, many=True)
            return Response({"Status": True, "Data": serializer.data})

        return Response(
            {"Status": True, "Data": [], "Message": "У пользователя нет контактов."},
            status=status.HTTP_200_OK,
        )

    def post(self, request, *args, **kwargs):
        serializer = ContactSerializer(data=request.data, context={"request": request})

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

    def patch(self, request, *args, **kwargs):
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

    def delete(self, request, *args, **kwargs):
        contact_id = request.data.get("id")

        if not contact_id or not contact_id.isdigit():
            return Response(
                {"Status": False, "Errors": "id обязательное числовое поле."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            contact = Contact.objects.get(user=request.user, id=contact_id)
            contact.delete()
            return Response({"Status": True, "Message": "Контакт удален."})
        except Contact.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Контакт не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )


class ShopListView(generics.ListAPIView):
    """Просмотр списка активных магазинов."""

    queryset = Shop.objects.filter(state=True)
    serializer_class = ShopListSerializer
    pagination_class = ShopPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class UserShopDetailView(views.APIView):
    """Управление магазином пользователя."""

    permission_classes = [IsAuthenticatedAndShopUser]

    def get(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
            serializer = ShopDetailSerializer(shop)
            return Response({"Status": True, "Data": serializer.data})
        except Shop.DoesNotExist:
            return Response(
                {"Status": True, "Data": {}, "Message": "У пользователя нет магазина."},
                status=status.HTTP_200_OK,
            )

    def post(self, request, *args, **kwargs):
        user_shop = Shop.objects.filter(user=request.user).first()

        if user_shop:
            serializer = ShopDetailSerializer(user_shop)
            return Response(
                {
                    "Status": False,
                    "Message": "У пользователя уже существует магазин.",
                    "Data": serializer.data,
                }
            )

        serializer = ShopCreateUpdateSerializer(
            data=request.data, context={"request": request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {"status": True, "message": "Магазин создан.", "data": serializer.data},
                status=status.HTTP_201_CREATED,
            )
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def patch(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
        except Shop.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Магазин пользователя не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )

        serializer = ShopDetailSerializer(shop, data=request.data, partial=True)

        if serializer.is_valid():
            serializer.save()
            return Response({"Status": True, "Data": serializer.data})
        return Response(
            {"Status": False, "Errors": serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )

    def delete(self, request, *args, **kwargs):
        try:
            shop = Shop.objects.get(user=request.user)
            shop.delete()
            return Response({"Status": True, "Message": "Магазин удален."})
        except Shop.DoesNotExist:
            return Response(
                {"Status": False, "Errors": "Магазин пользователя не найден."},
                status=status.HTTP_404_NOT_FOUND,
            )


class CategoryListView(generics.ListAPIView):
    """Просмотр списка категорий."""

    queryset = Category.objects.all()
    serializer_class = CategoryListSerializer
    pagination_class = CategoryPagination
    filter_backends = [filters.SearchFilter]
    search_fields = ["name"]


class TestView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

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
