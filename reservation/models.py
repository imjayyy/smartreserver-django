from django.db import models

# Create your models here.

class ReservationPolicy(models.Model):
    business = models.OneToOneField('business.Business', on_delete=models.CASCADE)
    policy_name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    max_reservations_per_day = models.IntegerField(default=10)
    cancellation_deadline_hours = models.IntegerField(default=24)
    operating_hours_start = models.TimeField(null=True, blank=True)
    operating_hours_end = models.TimeField(null=True, blank=True)

    def __str__(self):
        return f"{self.policy_name} for {self.business.name}"

    class Meta:
        verbose_name = "Reservation Policy"
        verbose_name_plural = "Reservation Policies"
        ordering = ['business__name', 'policy_name']

class Reservation(models.Model):
    business = models.ForeignKey('business.Business', on_delete=models.CASCADE)
    user = models.ForeignKey('authentication.CustomUser', on_delete=models.CASCADE)
    reservation_date = models.DateField()
    reservation_time = models.TimeField()
    special_requests = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    services = models.ManyToManyField('business.Services', blank=True) 
    number_of_people = models.IntegerField(default=1)
    status = models.CharField(max_length=20, choices=[
            ('pending', 'Pending'),
            ('confirmed', 'Confirmed'),
            ('canceled', 'Canceled'),
            ('completed', 'Completed')
        ], default='pending')
    
    def __str__(self):
        return f"Reservation for {self.user.username} at {self.business.name} on {self.reservation_date} {self.reservation_time}"

    class Meta:
        verbose_name = "Reservation"
        verbose_name_plural = "Reservations"
        ordering = ['reservation_date', 'reservation_time']






