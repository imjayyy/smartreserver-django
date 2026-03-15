from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password

from business.models import Business, BusinessUser, Service, SpecialOffer
from business.serializers import (
    BusinessSerializer,
    ServiceSerializer,
    SpecialOfferSerializer
)

User = get_user_model()


# =========================
# Register Business User
# =========================
class RegisterBusinessUser(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")
        business_name = request.data.get("business_name")

        if not email or not password or not business_name:
            return Response(
                {"error": "email, password, business_name required"},
                status=status.HTTP_400_BAD_REQUEST
            )
            

        if User.objects.filter(email=email).exists():
            return Response(
                {"error": "User already exists"},
                status=status.HTTP_400_BAD_REQUEST
            )

        user = User.objects.create(email=email,)
        user.set_password(str(password))
        user.save()

        business = Business.objects.create(
            name=business_name,
            email=email
        )

        BusinessUser.objects.create(
            user=user,
            business=business,
            role="admin"
        )

        return Response(
            {"message": "Business user created"},
            status=status.HTTP_201_CREATED
        )


# =========================
# Business View
# =========================
class MyBusinessView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        business_user = BusinessUser.objects.get(user=request.user)
        serializer = BusinessSerializer(business_user.business)
        return Response(serializer.data)


# =========================
# Services for Business
# =========================
class MyServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_user = BusinessUser.objects.get(user=self.request.user)
        return Service.objects.filter(business=business_user.business)

    def perform_create(self, serializer):
        business_user = BusinessUser.objects.get(user=self.request.user)
        serializer.save(business=business_user.business)


# =========================
# Special Offers for Business
# =========================
class MySpecialOfferViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_user = BusinessUser.objects.get(user=self.request.user)
        return SpecialOffer.objects.filter(business=business_user.business)

    def perform_create(self, serializer):
        business_user = BusinessUser.objects.get(user=self.request.user)
        serializer.save(business=business_user.business)