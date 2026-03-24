from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView

from authentication.views import (
    RegisterBusinessUser,
    MyBusinessView,
    MyServiceViewSet,
    MySpecialOfferViewSet,
)
from authentication.views import BusinessAdminChat

router = DefaultRouter()
router.register(r'services', MyServiceViewSet, basename='services')
router.register(r'offers', MySpecialOfferViewSet, basename='offers')

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/register/', RegisterBusinessUser.as_view()),
    path('api/token/', TokenObtainPairView.as_view()),
    path('api/token/refresh/', TokenRefreshView.as_view()),
    path('api/my-business/', MyBusinessView.as_view()),
    path('api/', include(router.urls)),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema'), name='docs'),
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),

    path('', include('chatbot.urls')),
    path('api/business/admin/chat/', BusinessAdminChat.as_view(), name='business_admin_chat'),
]