from django.db import models
from django.conf import settings

User = settings.AUTH_USER_MODEL

class Business(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    address = models.CharField(max_length=255, blank=True)
    phone_number = models.CharField(max_length=15, blank=True)
    email = models.EmailField(blank=True)
    domain = models.CharField(max_length=100, blank=True)
    # new: timezone for the business
    timezone = models.CharField(max_length=50, default='UTC')

    def __str__(self):
        return self.name

    class Meta:
        ordering = ['name']

class BusinessUser(models.Model):
    ROLE_CHOICES = [('admin', 'Admin'), ('staff', 'Staff')]
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='staff')

    class Meta:
        unique_together = ('business', 'user')

    def __str__(self):
        return f"{self.user.email} - {self.business.name} ({self.role})"

class Service(models.Model):   # renamed from Services for consistency
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration = models.DurationField(help_text="Time required for this service")
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00)

    def __str__(self):
        return f"{self.name} - {self.business.name}"

    class Meta:
        ordering = ['business__name', 'name']

class SpecialOffer(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.business.name}"

    class Meta:
        ordering = ['business__name', 'title']