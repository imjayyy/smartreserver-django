from django.shortcuts import render
from django.http import HttpResponse
from django.contrib.auth.decorators import login_required
from rest_framework.views import APIView


# Create your views here.

class ChatBotBView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        return Response({"message": "ChatBotB response"}, status=status.HTTP_200_OK)
    
    def get(self, request):
        return super().get_authenticate_header(request)