# from django.urls import path, include
# from rest_framework.routers import DefaultRouter
# from .views import (
#     RegisterBusinessUser,
#     MyBusinessView,
#     MyServiceViewSet,
#     MySpecialOfferViewSet
# )

# router = DefaultRouter()
# router.register("services", MyServiceViewSet, basename="my-services")
# router.register("offers", MySpecialOfferViewSet, basename="my-offers")

# urlpatterns = [
#     path("register/", RegisterBusinessUser.as_view()),
#     path("my-business/", MyBusinessView.as_view()),
#     path("", include(router.urls)),
# ]