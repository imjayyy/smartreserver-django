from django.urls import path, include
from .views import ChatBotBView

urlpatterns = [
    # Add your API endpoints here, for example:
    # path('reservations/', include('reservations.urls')),
    path('/', ChatBotBView.as_view(), name='chatbot_bot_view'),

]