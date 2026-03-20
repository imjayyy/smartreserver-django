from django.contrib import admin
from .models import ReservationPolicy, Reservation

@admin.register(ReservationPolicy)
class ReservationPolicyAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'policy_name', 'max_reservations_per_day', 'cancellation_deadline_hours', 'buffer_time_minutes')
    list_filter = ('business',)
    search_fields = ('business__name', 'policy_name')

@admin.register(Reservation)
class ReservationAdmin(admin.ModelAdmin):
    list_display = ('id', 'uuid', 'customer_name', 'business', 'reservation_date', 'reservation_time', 'status')
    list_filter = ('business', 'status', 'reservation_date')
    search_fields = ('customer_name', 'customer_email', 'uuid')
    readonly_fields = ('uuid', 'created_at', 'end_time')