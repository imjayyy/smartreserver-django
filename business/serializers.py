from rest_framework import serializers
from .models import (
    Business,
    BusinessUser,
    Service,
    SpecialOffer,
    Staff
)
from django.contrib.auth import get_user_model

User = get_user_model()


# ======================================
# Business Serializer
# ======================================
class BusinessSerializer(serializers.ModelSerializer):
    """
    Serializes Business core information.
    """

    class Meta:
        model = Business
        fields = [
            "id",
            "name",
            "description",
            "address",
            "phone_number",
            "email",
            "domain",
            "timezone",
            "opening_time",
            "closing_time",
            "max_reservations_per_hour",
        ]


# ======================================
# Business User Serializer
# ======================================
class BusinessUserSerializer(serializers.ModelSerializer):
    """
    Links a system user with a business and role.
    """

    user_email = serializers.EmailField(source="user.email", read_only=True)
    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = BusinessUser
        fields = [
            "id",
            "business",
            "business_name",
            "user",
            "user_email",
            "role",
        ]


# ======================================
# Service Serializer
# ======================================
class ServiceSerializer(serializers.ModelSerializer):
    """
    Serializes services offered by a business.
    """

    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = Service
        fields = [
            "id",
            "business",
            "business_name",
            "name",
            "description",
            "price",
            "duration",
            "discount_percentage",
        ]


# ======================================
# Special Offer Serializer
# ======================================
class SpecialOfferSerializer(serializers.ModelSerializer):
    """
    Serializes promotional offers.
    """

    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = SpecialOffer
        fields = [
            "id",
            "business",
            "business_name",
            "title",
            "description",
            "discount_percentage",
            "start_date",
            "end_date",
        ]


# ======================================
# Staff Serializer
# ======================================
class StaffSerializer(serializers.ModelSerializer):
    """
    Serializes staff members belonging to a business.
    """

    business_name = serializers.CharField(source="business.name", read_only=True)

    class Meta:
        model = Staff
        fields = [
            "id",
            "business",
            "business_name",
            "name",
            "email",
            "phone",
            "position",
            "salary",
            "availability",
            "is_active",
        ]