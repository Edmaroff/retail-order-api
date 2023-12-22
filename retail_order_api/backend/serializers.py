from rest_framework import serializers

from backend.models import Contact, CustomUser


class ContactSerializer(serializers.ModelSerializer):
    class Meta:
        model = Contact
        fields = [
            "id",
            "user",
            "phone",
            "city",
            "street",
            "house",
            "structure",
            "building",
            "apartment",
        ]
        read_only_fields = ["id"]
        extra_kwargs = {"user": {"write_only": True}}
