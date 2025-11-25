from django.urls import path, include
from .views import RegisterBusinessView, ProtectedView
urlpatterns = [
    # Add your API endpoints here, for example:
    # path('reservations/', include('reservations.urls')),
    path('register-business/', RegisterBusinessView.as_view, name='register_business'),
    path('protected/', ProtectedView.as_view(), name='protected_view'),

]