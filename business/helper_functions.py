# business/helper_functions.py
from .models import BusinessUser

def get_user_business(user):
    """Return the business associated with the user (assuming one business per user for simplicity)."""
    try:
        return BusinessUser.objects.get(user=user).business
    except BusinessUser.DoesNotExist:
        return None