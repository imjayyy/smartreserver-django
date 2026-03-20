from rest_framework import status, viewsets
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.contrib.auth import get_user_model
from drf_spectacular.utils import extend_schema, extend_schema_view
from django.shortcuts import get_object_or_404
from business.models import Business, BusinessUser, Service, SpecialOffer
from business.serializers import (
    BusinessSerializer,
    ServiceSerializer,
    SpecialOfferSerializer)

User = get_user_model()

# Register Business User
@extend_schema(
    summary="Create Business User",
    request={
        "application/json": {
            "type": "object",
            "properties": {
                "email": {"type": "string"},
                "password": {"type": "string"},
                "business_name": {"type": "string"},
                },
            "required": ["email", "password", "business_name"],
        }
    },
    responses={201: None},
)
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

        user = User.objects.create(email=email)
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

# Business View
@extend_schema_view(
    get=extend_schema(
        summary="Get Your Business",
        responses=BusinessSerializer
    ),
    put=extend_schema(
        summary="Update Business",
        request=BusinessSerializer,
        responses=BusinessSerializer
    ),
    patch=extend_schema(
        summary="Partial Update Business",
        request=BusinessSerializer,
        responses=BusinessSerializer
    ),
)
class MyBusinessView(APIView):
    permission_classes = [IsAuthenticated]

    def get_object(self, request):
        business_user = get_object_or_404(
            BusinessUser,
            user=request.user
        )
        return business_user.business

    def get(self, request):
        business = self.get_object(request)
        serializer = BusinessSerializer(business)
        return Response(serializer.data)


    def put(self, request):
        business = self.get_object(request)
        serializer = BusinessSerializer(business, data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

    def patch(self, request):
        business = self.get_object(request)
        serializer = BusinessSerializer(
            business,
            data=request.data,
            partial=True
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)

# Services
@extend_schema_view(
    list=extend_schema(summary="List My Services", responses=ServiceSerializer(many=True)),
    retrieve=extend_schema(summary="Retrieve Service", responses=ServiceSerializer),
    create=extend_schema(summary="Create Service", request=ServiceSerializer, responses=ServiceSerializer),
    update=extend_schema(summary="Update Service", request=ServiceSerializer, responses=ServiceSerializer),
    partial_update=extend_schema(summary="Partial Update Service", request=ServiceSerializer, responses=ServiceSerializer),
    destroy=extend_schema(summary="Delete Service"),
)
class MyServiceViewSet(viewsets.ModelViewSet):
    serializer_class = ServiceSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_user = get_object_or_404(
            BusinessUser,
            user=self.request.user
        )
        return Service.objects.filter(business=business_user.business)

    def perform_create(self, serializer):
        business_user = get_object_or_404(
            BusinessUser,
            user=self.request.user
        )
        serializer.save(business=business_user.business)

# Special Offers
@extend_schema_view(
    list=extend_schema(summary="List My Special Offers", responses=SpecialOfferSerializer(many=True)),
    retrieve=extend_schema(summary="Retrieve Special Offer", responses=SpecialOfferSerializer),
    create=extend_schema(summary="Create Special Offer", request=SpecialOfferSerializer, responses=SpecialOfferSerializer),
    update=extend_schema(summary="Update Special Offer", request=SpecialOfferSerializer, responses=SpecialOfferSerializer),
    partial_update=extend_schema(summary="Partial Update Special Offer", request=SpecialOfferSerializer, responses=SpecialOfferSerializer),
    destroy=extend_schema(summary="Delete Special Offer"),
)
class MySpecialOfferViewSet(viewsets.ModelViewSet):
    serializer_class = SpecialOfferSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        business_user = get_object_or_404(
            BusinessUser,
            user=self.request.user
        )
        return SpecialOffer.objects.filter(business=business_user.business)

    def perform_create(self, serializer):
        business_user = get_object_or_404(
            BusinessUser,
            user=self.request.user
        )
        serializer.save(business=business_user.business)