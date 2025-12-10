from django.urls import path
from . import views

urlpatterns = [
    path('api/v1/health/', views.HealthCheckView.as_view(), name='health_check'),
    path('api/v1/<str:shop_id>/message/', views.ShopMessageView.as_view(), name='shop_message'),
    path('api/v1/<str:shop_id>/services/', views.ShopServicesView.as_view(), name='shop_services'),
    path('api/v1/<str:shop_id>/info/', views.ShopInfoView.as_view(), name='shop_info'),
    path('api/v1/shops/', views.AllShopsView.as_view(), name='all_shops'),
    path('api/v1/<str:shop_id>/sessions/<str:session_id>/history/', 
         views.ConversationHistoryView.as_view(), name='conversation_history'),
    path('api/v1/<str:shop_id>/debug-extraction/', 
         views.DebugExtractionView.as_view(), name='debug_extraction'),
    path('ping/', views.ping_view, name='ping'),
    path('', views.frontend_view, name='frontend'),
    path('chat/', views.chat_view, name='chat'),
]