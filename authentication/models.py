from django.db import models
# Create your models here.

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings


# 1. Custom Manager
class CustomUserManager(BaseUserManager):
    # Overrides create_user and create_superuser to use email as the identifier

    def create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError(_("The Email must be set"))
        email = self.normalize_email(email) # Normalizes the domain part of the email
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save()
        return user
    
    # ... create_superuser method (omitted for brevity, but needed)

# 2. Custom User Model
class CustomUser(AbstractUser):
    username = None  # Remove username field
    email = models.EmailField(_("email address"), unique=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = []  # No other fields are required besides the USERNAME_FIELD
    
    objects = CustomUserManager()

    def __str__(self):
        return self.email
    

class UserProfile(models.Model):
    """
    Custom user model that extends the default Django user model.
    """
    user = models.OneToOneField(CustomUser, on_delete=models.CASCADE, related_name='profile')
    full_name = models.CharField(max_length=255, blank=True, null=True, help_text="Full name of the user.")
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    is_business_user = models.BooleanField(default=False, help_text="Designates whether the user is a business user.")
    is_registered_user = models.BooleanField(default=False, help_text="Designates whether the user is a registered user.")
    is_staff = models.BooleanField(default=False, help_text="Designates whether the user can log into this admin site.")
    is_active = models.BooleanField(default=True, help_text="Designates whether this user should be treated as active. Unselect this instead of deleting accounts.")


    def __str__(self):
        return self.user.email or self.full_name or "UserProfile for {}".format(self.user.email)
    
