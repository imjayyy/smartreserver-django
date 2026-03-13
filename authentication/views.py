# authentication/views.py
from rest_framework import viewsets, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.decorators import action
from rest_framework.response import Response
from drf_spectacular.utils import extend_schema
from business.models import Business, BusinessUser, Service, SpecialOffer, Staff
from business.serializers import (
    BusinessSerializer,   
    BusinessUserSerializer,
    ServiceSerializer,
    SpecialOfferSerializer,
    StaffSerializer)


# ==========================
# JWT Auth Endpoints
# ==========================
class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Endpoint: /api/token/
    Standard JWT token obtain view.
    """


class CustomTokenRefreshView(TokenRefreshView):
    """
    Endpoint: /api/token/refresh/
    Standard JWT token refresh view.
    """


# ==========================
# Business API ViewSet
# ==========================
class BusinessViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Business model.
    """
    queryset = Business.objects.all()
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    @extend_schema(
        summary="List all businesses", description="Returns authenticated user's businesses")
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)


# ==========================
# BusinessUser API ViewSet
# ==========================
class BusinessUserViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for BusinessUser model.
    """
    queryset = BusinessUser.objects.all()
    serializer_class = BusinessUserSerializer
    permission_classes = [permissions.IsAuthenticated]


# ==========================
# Service API ViewSet
# ==========================
class ServiceViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Service model.
    """
    queryset = Service.objects.all()
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]


# ==========================
# SpecialOffer API ViewSet
# ==========================
class SpecialOfferViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for SpecialOffer model.
    """
    queryset = SpecialOffer.objects.all()
    serializer_class = SpecialOfferSerializer
    permission_classes = [permissions.IsAuthenticated]


# ==========================
# Staff API ViewSet
# ==========================
class StaffViewSet(viewsets.ModelViewSet):
    """
    CRUD endpoints for Staff model.
    """
    queryset = Staff.objects.all()
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated]