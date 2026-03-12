import uuid
from django.db import models
from business.models import Business, Service

class ReservationPolicy(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE)
    policy_name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    max_reservations_per_day = models.IntegerField(default=10, null=True, blank=True)
    cancellation_deadline_hours = models.IntegerField(default=24)
    operating_hours_start = models.TimeField(null=True, blank=True)
    operating_hours_end = models.TimeField(null=True, blank=True)
    buffer_time_minutes = models.IntegerField(default=0, help_text="Minutes between reservations")
    # new: advance notice (hours before booking)
    advance_notice_hours = models.IntegerField(default=0, help_text="Minimum hours before booking")

    def __str__(self):
        return f"Policy for {self.business.name}"

class Reservation(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('canceled', 'Canceled'),
        ('completed', 'Completed'),
    ]

    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    customer_name = models.CharField(max_length=100)
    customer_email = models.EmailField()
    customer_phone = models.CharField(max_length=15)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    number_of_people = models.IntegerField(default=1)
    special_requests = models.TextField(blank=True)
    services = models.ManyToManyField(Service, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    created_at = models.DateTimeField(auto_now_add=True)
    # computed end time (filled on save)
    end_time = models.TimeField(blank=True, null=True)

    def save(self, *args, **kwargs):
        # Calculate end_time based on services durations + buffer
        if not self.end_time:
            total_duration = self.calculate_total_duration()
            # Add buffer from policy
            buffer = self.business.reservationpolicy.buffer_time_minutes if hasattr(self.business, 'reservationpolicy') else 0
            # convert to datetime for addition, then back to time
            from datetime import datetime, timedelta
            start_dt = datetime.combine(self.reservation_date, self.reservation_time)
            end_dt = start_dt + total_duration + timedelta(minutes=buffer)
            self.end_time = end_dt.time()
        super().save(*args, **kwargs)

    def calculate_total_duration(self):
        from datetime import timedelta
        total = timedelta()
        for service in self.services.all():
            total += service.duration
        return total

    def __str__(self):
        return f"{self.customer_name} - {self.reservation_date} {self.reservation_time}"

    class Meta:
        ordering = ['reservation_date', 'reservation_time']
        # optional: add constraints to prevent double-booking (will be handled in logic)