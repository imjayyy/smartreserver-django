from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import ListView, CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from .models import Service, SpecialOffer
from reservation.models import Reservation

class DashboardMixin(LoginRequiredMixin):
    def get_queryset(self):
        # Filter by businesses the logged-in user is associated with
        user_businesses = self.request.user.businessuser_set.values_list('business', flat=True)
        return super().get_queryset().filter(business__in=user_businesses)

class ServiceListView(DashboardMixin, ListView):
    model = Service
    template_name = 'business/service_list.html'
    context_object_name = 'services'

class ServiceCreateView(DashboardMixin, CreateView):
    model = Service
    fields = ['name', 'description', 'price', 'duration', 'discount_percentage']
    template_name = 'business/service_form.html'
    success_url = reverse_lazy('service-list')

    def form_valid(self, form):
        # Set business from the user's first business (or let user choose)
        # For simplicity, assume user belongs to one business
        form.instance.business = self.request.user.businessuser_set.first().business
        return super().form_valid(form)
