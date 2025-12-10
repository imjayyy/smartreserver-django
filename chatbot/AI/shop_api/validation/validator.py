import re
import phonenumbers
import logging
from typing import Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class DataValidator:
    """Validates user input data (phone, email, name, party size)."""
    
    def validate_phone_number(self, phone_number: str, country_code: str = "US") -> Tuple[bool, str]:
        """Validate phone number format."""
        try:
            if not phone_number or not phone_number.strip():
                return False, "Phone number cannot be empty"
            
            cleaned_phone = re.sub(r'[^\d]', '', phone_number.strip())
            
            if not cleaned_phone:
                return False, "Invalid phone number format"
            
            if len(cleaned_phone) < 10:
                return False, "Phone number too short (minimum 10 digits)"
            
            if len(cleaned_phone) > 13:
                return False, "Phone number too long (maximum 13 digits)"
            
            if len(cleaned_phone) == 10:
                formatted = f"+1 ({cleaned_phone[0:3]}) {cleaned_phone[3:6]}-{cleaned_phone[6:10]}"
            elif len(cleaned_phone) == 11:
                formatted = f"+{cleaned_phone[0]} ({cleaned_phone[1:4]}) {cleaned_phone[4:7]}-{cleaned_phone[7:11]}"
            else:
                formatted = f"+{cleaned_phone[0:2]} ({cleaned_phone[2:5]}) {cleaned_phone[5:8]}-{cleaned_phone[8:]}"
            
            return True, formatted
            
        except Exception as e:
            logger.error(f"Phone validation error: {e}")
            return False, f"Phone validation failed: {str(e)}"
    
    def validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate customer name."""
        try:
            if not name or not name.strip():
                return False, "Name cannot be empty"
            
            cleaned_name = name.strip()
            
            if len(cleaned_name) < 2:
                return False, "Name too short (minimum 2 characters)"
            
            if len(cleaned_name) > 50:
                return False, "Name too long (maximum 50 characters)"
            
            if not re.match(r'^[A-Za-z\s\-\'\.]+$', cleaned_name):
                return False, "Name contains invalid characters"
            
            if not re.search(r'[A-Za-z]', cleaned_name):
                return False, "Name must contain at least one letter"
            
            if re.search(r'[\-\'\\.]{2,}', cleaned_name):
                return False, "Name contains consecutive special characters"
            
            return True, cleaned_name.title()
            
        except Exception as e:
            logger.error(f"Name validation error: {e}")
            return False, f"Name validation failed: {str(e)}"
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email format."""
        try:
            if not email or not email.strip():
                return False, "Email cannot be empty"
            
            cleaned_email = email.strip().lower()
            
            pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
            
            if not re.match(pattern, cleaned_email):
                return False, "Invalid email format"
            
            return True, cleaned_email
            
        except Exception as e:
            logger.error(f"Email validation error: {e}")
            return False, f"Email validation failed: {str(e)}"
    
    def validate_party_size(self, party_size: int, max_size: Optional[int] = None) -> Tuple[bool, str]:
        """Validate party size."""
        try:
            if max_size is None:
                max_size = settings.MAX_PARTY_SIZE
                
            if not isinstance(party_size, int) or party_size < 1:
                return False, "Party size must be at least 1"
            
            if party_size > max_size:
                return False, f"Maximum party size is {max_size}"
            
            return True, "Valid party size"
            
        except Exception as e:
            logger.error(f"Party size validation error: {e}")
            return False, f"Party size validation failed: {str(e)}"