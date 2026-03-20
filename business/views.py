from rest_framework import viewsets, permissions
from .models import Business, Service, SpecialOffer, Staff
from .serializers import BusinessSerializer, ServiceSerializer, SpecialOfferSerializer, StaffSerializer
from .helper_functions import get_user_business

class BusinessViewSet(viewsets.ModelViewSet):
    serializer_class = BusinessSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Return only the business of the logged-in user (assumes one business per user)
        business = get_user_business(self.request.user)
        return Business.objects.filter(id=business.id)

    def perform_update(self, serializer):
        # Ensure the business being updated belongs to the user
        business = get_user_business(self.request.user)
        serializer.save(id=business.id)  # id is unchanged, but we force it

class ServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = get_user_business(self.request.user)
        return Service.objects.filter(business=business)

    def perform_create(self, serializer):
        business = get_user_business(self.request.user)
        serializer.save(business=business)

class SpecialOfferViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialOfferSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = get_user_business(self.request.user)
        return SpecialOffer.objects.filter(business=business)

    def perform_create(self, serializer):
        business = get_user_business(self.request.user)
        serializer.save(business=business)

class StaffViewSet(viewsets.ModelViewSet):
    serializer_class = StaffSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        business = get_user_business(self.request.user)
        return Staff.objects.filter(business=business)

    def perform_create(self, serializer):
        business = get_user_business(self.request.user)
        serializer.save(business=business)