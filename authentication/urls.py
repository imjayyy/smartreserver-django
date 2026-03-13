# authentication/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CustomTokenObtainPairView,
    CustomTokenRefreshView,
    BusinessViewSet,
    BusinessUserViewSet,
    ServiceViewSet,
    SpecialOfferViewSet,
    StaffViewSet,
)

router = DefaultRouter()
router.register(r'businesses', BusinessViewSet, basename='business')
router.register(r'business-users', BusinessUserViewSet, basename='businessuser')
router.register(r'services', ServiceViewSet, basename='service')
router.register(r'special-offers', SpecialOfferViewSet, basename='specialoffer')
router.register(r'staff', StaffViewSet, basename='staff')

urlpatterns = [
    # JWT auth endpoints
    path('token/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    
    # Business-related API endpoints
    path('', include(router.urls)),
]