from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt
from business.models import Business, BusinessUser, BusinessSettings, RegisteredUser
from authentication.models import UserProfile
from django.contrib.auth.models import User
from django.utils import timezone
from datetime import datetime
import json

from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.authentication import SessionAuthentication, BasicAuthentication
from rest_framework.views import APIView
from rest_framework import generics, mixins, viewsets
from rest_framework import permissions  
# Create your views here.



class RegisterBusinessView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        try:
            request_data = request.data
        except Exception as e:
            return Response({"error": f"Invalid JSON: {e}"}, status=status.HTTP_400_BAD_REQUEST)

        username = request_data.get('username')
        password = request_data.get('password')
        first_name = request_data.get('first_name')
        last_name = request_data.get('last_name')
        name = request_data.get('name')
        description = request_data.get('description')
        address = request_data.get('address')
        phone_number = request_data.get('phone_number')
        email = request_data.get('email')

        if not all([username, password, first_name, last_name, name, description, address, phone_number, email]):
            return Response({"error": "All fields are required."}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(username=username).exists():
            return Response({"error": "Username already exists."}, status=status.HTTP_400_BAD_REQUEST)

        auth_user = User.objects.create_user(
            username=username,
            password=password,
            email=email
        )
        auth_user.first_name = first_name
        auth_user.last_name = last_name
        auth_user.save()

        user_profile = UserProfile.objects.create(
            user=auth_user,
            full_name=f"{first_name} {last_name}",
            phone_number=phone_number,
            is_business_user=True,
            is_registered_user=False,
            is_staff=False,
            is_active=True
        )

        business = Business.objects.create(
            name=name,
            description=description,
            address=address,
            phone_number=phone_number,
            email=email
        )

        business_user = BusinessUser.objects.create(
            user=auth_user,
            business=business,
            role='admin'
        )

        return Response({"message": f"Business {business.name} registered successfully!"}, status=status.HTTP_201_CREATED)




class ProtectedView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'message': f'Hello, {request.user.username}'})
