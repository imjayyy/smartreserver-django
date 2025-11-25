from django.db import models
from django.contrib.auth.models import AbstractUser
# Create your models here.

class UserProfile(models.Model):
    """
    Custom user model that extends the default Django user model.
    """
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True, help_text="Full name of the user.")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_business_user = models.BooleanField(default=False, help_text="Designates whether the user is a business user.")
    is_registered_user = models.BooleanField(default=False, help_text="Designates whether the user is a registered user.")
    is_staff = models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.")
    is_active = models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")


    def __str__(self):
        return self.user.username or self.full_name or "UserProfile for {}".format(self.user.username)