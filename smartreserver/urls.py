"""
URL configuration for smartreserver project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""

#from django.contrib import admin
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.contrib import admin

from authentication.views import (
    RegisterBusinessUser,
    MyBusinessView,
    MyServiceViewSet,
    MySpecialOfferViewSet,
)

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView, SpectacularRedocView


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
    path('api/redoc/', SpectacularRedocView.as_view(url_name='schema'), name='redoc'),
    path('api/schema/', SpectacularAPIView.as_view(), name='schema'),
    path('api/docs/', SpectacularSwaggerView.as_view(url_name='schema')),
]