# business/mixins.py
from django.contrib.auth.mixins import UserPassesTestMixin
from django.shortcuts import redirect
from .models import BusinessUser

class BusinessOwnerMixin(UserPassesTestMixin):
    def test_func(self):
        return BusinessUser.objects.filter(user=self.request.user, role='admin').exists()

    def handle_no_permission(self):
        return redirect('business:no_access')