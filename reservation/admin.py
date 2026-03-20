# from django.contrib import admin
# from .models import Reservation, ReservationPolicy


# @admin.register(Reservation)
# class ReservationAdmin(admin.ModelAdmin):
#     list_display = ('id', 'business', 'user', 'services__name', 'reservation_date', 'status')
#     search_fields = ('business__name', 'user__username', 'services__name', 'status')
#     ordering = ('-reservation_date',)
#     list_filter = ('status', 'business__name')

# @admin.register(ReservationPolicy)
# class ReservationPolicyAdmin(admin.ModelAdmin):
#     list_display = ('business', 'policy_name', 'max_reservations_per_day', 'cancellation_deadline_hours')
#     search_fields = ('business__name', 'policy_name')
#     ordering = ('business__name',)
#     list_filter = ('business__name',)
# # Register your models here.
from django.contrib import admin
from .models import ReservationPolicy, Reservation

@admin.register(ReservationPolicy)
class ReservationPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'policy_name', 'max_reservations_per_day', 'buffer_time_minutes')
    list_filter = ('business',)
    search_fields = ('business__name', 'policy_name')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'customer_name', 'business', 'reservation_date', 'reservation_time', 'status')
    list_filter = ('business', 'status', 'reservation_date')
    search_fields = ('customer_name', 'customer_email', 'business__name')
    readonly_fields = ('uuid', 'created_at')  # prevent editing of these fields