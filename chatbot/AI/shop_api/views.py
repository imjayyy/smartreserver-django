# shop_api/views.py
import os
import time
import logging
from datetime import datetime
from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
from django.utils.decorators import method_decorator
from django.views import View
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .models import ConversationHistory, SessionMetadata
from .serializers import ChatRequestSerializer, ShopDetailsSerializer, ServiceSerializer, ServicesSerializer
from .agent.base_agent import UniversalShopAgent
from .validation.security_system import SecurityValidationSystem
from .session_manager import EnhancedSessionManager
from .database_manager import DatabaseManager


logger = logging.getLogger(__name__)

# Initialize managers
data_manager = DatabaseManager()
validation_system = SecurityValidationSystem()
session_manager = EnhancedSessionManager()
universal_agent = UniversalShopAgent(data_manager=data_manager, session_manager=session_manager)

class HealthCheckView(APIView):
    def get(self, request):
        current_time = time.time()
        start_time = getattr(HealthCheckView, '_start_time', current_time)
        uptime_seconds = current_time - start_time
        
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "uptime_seconds": uptime_seconds,
            "version": "2.0.0",
            "environment": "development" if os.getenv("DEBUG") == "true" else "production",
        }
        
        # Check shops database connectivity
        try:
            shops = data_manager.list_all_shops()
            health_status["shops_database"] = {
                "status": "healthy",
                "total_shops": len(shops)
            }
        except Exception as e:
            health_status["shops_database"] = {
                "status": "unhealthy",
                "error": str(e)
            }
        
        return Response(health_status)

class ShopMessageView(APIView):
    def post(self, request, shop_id):
        try:
            print(f"DEBUG: Request data received: {request.data}")
            print(f"DEBUG: Request content type: {request.content_type}")
            print(f"DEBUG: Headers: {dict(request.headers)}")
            
            # Validate shop exists
            if not data_manager.shop_exists(shop_id):
                return Response(
                    {"success": False, "error": f"Shop {shop_id} not found."},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Validate request data
            serializer = ChatRequestSerializer(data=request.data)
            print(f"DEBUG: Serializer initial data: {request.data}")
            
            if not serializer.is_valid():
                print(f"DEBUG: Serializer errors: {serializer.errors}")
                print(f"DEBUG: Raw request body: {request.body}")
                return Response(
                    {"success": False, "error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Validate request data
            serializer = ChatRequestSerializer(data=request.data)   
            if not serializer.is_valid():
                return Response(
                    {"success": False, "error": serializer.errors},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            data = serializer.validated_data
            user_message = data['message']
            session_id = data.get('session_id') or f"session_{shop_id}_{int(time.time())}"
            user_email = data.get('user_email', '')
            user_name = data.get('user_name', '')
            user_phone = data.get('user_phone', '')
            
            # Get client IP
            client_ip = self.get_client_ip(request)
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            
            # Print user information to console
            if user_name and user_email:
                print("=" * 50)
                print("USER INFORMATION DETECTED!")
                print(f"User Email: {user_email}")
                print(f"User Name: {user_name}")
                print(f"User Phone: {user_phone}")
                print(f"Session ID: {session_id}")
                print(f"Shop ID: {shop_id}")
                print(f"Message: {user_message}")
                print("=" * 50)
            
            # Process message through agent
            response = universal_agent.handle_shop_request(
                user_message=user_message,
                shop_id=shop_id,
                session_id=session_id,
                user_agent=user_agent,
                ip_address=client_ip,
                user_email=user_email,
                user_name=user_name,
                user_phone=user_phone
            )
            
            return Response({
                "response": response["response"],
                "shop_id": shop_id,
                "shop_name": response.get("shop_name", "Unknown Shop"),
                "success": True,
                "session_id": session_id,
                "agents_used": response.get("agents_used", []),
                "model": response.get("model", "unknown"),
                "timestamp": datetime.now().isoformat(),
                "user_authenticated": bool(user_email and user_name),
                "user_name": user_name if user_name else None
            })
            
        except Exception as e:
            logger.error(f"Error handling shop message: {e}")
            return Response(
                {"success": False, "error": "Internal server error"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip

class ShopServicesView(APIView):
    def get(self, request, shop_id):
        try:
            if not data_manager.shop_exists(shop_id):
                return Response(
                    {"success": False, "error": f"Shop {shop_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            shop_context = data_manager.load_shop_context(shop_id)
            shop_details = shop_context['shop_details']
            services_data = shop_context['services']
            
            return Response({
                "shop_name": shop_details.get('shop_name', 'Unknown Shop'),
                "services": services_data.get('services', []),
                "success": True,
                "timestamp": datetime.now().isoformat()
            })
        except Exception as e:
            logger.error(f"Error getting shop services: {e}")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ShopInfoView(APIView):
    def get(self, request, shop_id):
        try:
            if not data_manager.shop_exists(shop_id):
                return Response(
                    {"success": False, "error": f"Shop {shop_id} not found"},
                    status=status.HTTP_404_NOT_FOUND
                )
            
            shop_context = data_manager.load_shop_context(shop_id)
            shop_details = shop_context['shop_details']
            
            # Validate with serializer
            serializer = ShopDetailsSerializer(data=shop_details)
            if serializer.is_valid():
                return Response({
                    "shop_details": serializer.data,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
            else:
                return Response({
                    "shop_details": shop_details,
                    "success": True,
                    "timestamp": datetime.now().isoformat()
                })
        except Exception as e:
            logger.error(f"Error getting shop info: {e}")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_404_NOT_FOUND
            )

class AllShopsView(APIView):
    def get(self, request):
        try:
            shops = data_manager.list_all_shops()
            
            # Validate each shop with serializer
            valid_shops = []
            for shop in shops:
                serializer = ShopDetailsSerializer(data=shop)
                if serializer.is_valid():
                    valid_shops.append(serializer.data)
                else:
                    valid_shops.append(shop)
            
            return Response({
                "shops": valid_shops,
                "total_shops": len(valid_shops),
                "success": True
            })
        except Exception as e:
            logger.error(f"Error listing shops: {e}")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

class ConversationHistoryView(APIView):
    def get(self, request, shop_id, session_id):
        try:
            history = ConversationHistory.objects.filter(
                session_id=session_id, 
                shop_id=shop_id
            ).order_by('timestamp')[:20]
            
            history_data = []
            for entry in history:
                history_data.append({
                    'user': entry.user_message,
                    'assistant': entry.assistant_response,
                    'timestamp': entry.timestamp.isoformat(),
                    'type': entry.message_type,
                    'metadata': entry.metadata
                })
            
            return Response({
                "session_id": session_id,
                "shop_id": shop_id,
                "conversation_history": history_data,
                "success": True
            })
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            return Response(
                {"success": False, "error": str(e)},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(csrf_exempt, name='dispatch')
class DebugExtractionView(View):
    def post(self, request, shop_id):
        try:
            import json
            data = json.loads(request.body)
            message = data.get("message", "")
            
            extracted_data = validation_system.extract_reservation_data(message)
            
            return JsonResponse({
                "message": message,
                "extracted_data": extracted_data,
                "success": True
            })
        except Exception as e:
            logger.error(f"Debug extraction error: {e}")
            return JsonResponse({"success": False, "error": str(e)})

def frontend_view(request):
    """Enhanced frontend view with shop data"""
    try:
        # Get shops for the template
        shops = data_manager.list_all_shops()
        
        # Prepare shop data for template
        shop_data = []
        for shop in shops:
            shop_data.append({
                'id': shop.get('shop_id'),
                'name': shop.get('shop_name', 'Unknown Shop'),
                'address': shop.get('address', ''),
                'phone': shop.get('phone', ''),
                'category': shop.get('category', 'Shop')
            })
        
        return render(request, 'index.html', {
            'shops': shop_data,
            'total_shops': len(shops),
            'app_name': 'SmartReserver',
            'year': datetime.now().year
        })
    except Exception as e:
        logger.error(f"Error loading frontend: {e}")
        return render(request, 'index.html', {
            'shops': [],
            'app_name': 'SmartReserver',
            'year': datetime.now().year
        })

def chat_view(request):
    return render(request, 'chat.html')

def ping_view(request):
    print("Frontend hit the server!")
    return JsonResponse({"message": "pong"})