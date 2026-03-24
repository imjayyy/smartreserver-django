#api/urls.py
from django.urls import path
from . import views

urlpatterns = [
    path('business/<int:business_id>/availability/', views.availability, name='availability'),
    path('business/<int:business_id>/book/', views.book, name='book'),
    path('business/<int:business_id>/chat/', views.chat, name='chat'),
]