from django.db import models

# Create your models here.

class Business(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    address = models.CharField(max_length=255, blank=True, null=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)    

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = "Business"
        verbose_name_plural = "Businesses"
        ordering = ['name']

class BusinessUser(models.Model):
    business = models.ForeignKey(Business, on_delete=models.CASCADE)
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    role = models.CharField(max_length=50, choices=[('admin', 'Admin'), ('staff', 'Staff')], default='staff')

    def __str__(self):
        return f"{self.user.username} - {self.business.name} ({self.role})"

    class Meta:
        unique_together = ('business', 'user')
        verbose_name = "Business User"
        verbose_name_plural = "Business Users"
        ordering = ['business__name', 'user__username']

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
    user = models.ForeignKey('auth.User', on_delete=models.CASCADE)
    registration_date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.user.username} registered for {self.business.name}"

    class Meta:
        unique_together = ('business', 'user')
        verbose_name = "Registered User"
        verbose_name_plural = "Registered Users"
        ordering = ['business__name', 'user__username']









