from django.db import models
from django.conf import settings
from django.contrib.auth import get_user_model

# Create your models here.
user_model = get_user_model()

class Business(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)    
    domain = models.CharField(max_length=100, blank=True, null=True)
    
    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        ordering = ['name']

class BusinessUser(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user = models.ForeignKey(user_model, on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('staff', 'Staff')], default='staff')

    def __str__(self):
        return f"{self.user.username} - {self.business.name} ({self.role})"

    class Meta:
        unique_together = ('business', 'user')
        verbose_name = "Business User"
        verbose_name_plural = "Business Users"
        ordering = ['business__name', 'user__email']

class BusinessSettings(models.Model):
    business = models.OneToOneField(Business, on_delete=models.CASCADE)
    timezone = models.CharField(max_length=50, default='UTC')
    currency = models.CharField(max_length=10, default='USD')
    language = models.CharField(max_length=50, default='en')

    def __str__(self):
        return f"Settings for {self.business.name}"

    class Meta:
        verbose_name = "Business Settings"
        verbose_name_plural = "Business Settings"
        ordering = ['business__name']

class RegisteredUser(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE )
    user = models.ForeignKey(user_model, on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} registered for {self.business.name}"

    class Meta:
        unique_together = ('business', 'user')
        verbose_name = "Registered User"
        verbose_name_plural = "Registered Users"
        ordering = ['business__name', 'user__email']


class Services(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    time_duration = models.DurationField(null=True, blank=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.00, null=True, blank=True)

    def __str__(self):
        return f"{self.name} - {self.business.name}"

    class Meta:
        verbose_name = "Service"
        verbose_name_plural = "Services"
        ordering = ['business__name', 'name']


class SpecialOffers(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    title = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    discount_percentage = models.DecimalField(max_digits=5, decimal_places=2)
    start_date = models.DateField()
    end_date = models.DateField()

    def __str__(self):
        return f"{self.title} - {self.business.name}"

    class Meta:
        verbose_name = "Special Offer"
        verbose_name_plural = "Special Offers"
        ordering = ['business__name', 'title']



