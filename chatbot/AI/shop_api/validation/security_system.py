import logging
from typing import Dict, Any, List, Tuple
from .data_extractor import DataExtractor
from .validator import DataValidator
from .date_time_handler import DateTimeHandler
from datetime import datetime, timedelta, time

logger = logging.getLogger(__name__)


class SecurityValidationSystem:
    """Main security validation system coordinating all components."""
    
    def __init__(self):
        self.extractor = DataExtractor()
        self.validator = DataValidator()
        self.date_time_handler = DateTimeHandler()
    
    def extract_reservation_data(self, message: str) -> Dict[str, Any]:
        """Extract reservation data from user message."""
        return self.extractor.extract_reservation_data(message)
    
    def validate_phone_number(self, phone_number: str, country_code: str = "US") -> Tuple[bool, str]:
        """Validate phone number."""
        return self.validator.validate_phone_number(phone_number, country_code)
    
    def validate_name(self, name: str) -> Tuple[bool, str]:
        """Validate customer name."""
        return self.validator.validate_name(name)
    
    def validate_email(self, email: str) -> Tuple[bool, str]:
        """Validate email."""
        return self.validator.validate_email(email)
    
    def validate_date_time(self, date_str: str, time_str: str, 
                         min_hours_from_now: int = None, 
                         max_days_in_future: int = None,
                         shop_hours: Dict = None) -> Tuple[bool, str, datetime]:
        """Validate date and time."""
        return self.date_time_handler.validate_date_time(
            date_str, time_str, min_hours_from_now, max_days_in_future, shop_hours
        )
    
    def validate_party_size(self, party_size: int, max_size: int = None) -> Tuple[bool, str]:
        """Validate party size."""
        return self.validator.validate_party_size(party_size, max_size)
    
    def generate_alternative_slots(self, base_datetime: datetime, 
                                 shop_hours: Dict = None,
                                 available_slots: List[datetime] = None) -> List[datetime]:
        """Generate alternative time slots."""
        return self.date_time_handler.generate_alternative_slots(base_datetime, shop_hours, available_slots)
    
    def format_alternative_slots(self, slots: List[datetime]) -> str:
        """Format alternative slots for display."""
        return self.date_time_handler.format_alternative_slots(slots)
    
    def _check_within_shop_hours(self, requested_dt: datetime, hours_str: str) -> Tuple[bool, str]:
        """Check if requested time is within shop hours."""
        return self.date_time_handler._check_within_shop_hours(requested_dt, hours_str)
    
    def comprehensive_reservation_validation(self, reservation_data: Dict[str, Any], 
                                          shop_hours: Dict = None) -> Dict[str, Any]:
        """Comprehensive validation of reservation data."""
        validation_results = {
            'is_valid': True,
            'errors': [],
            'warnings': [],
            'corrected_data': {},
            'alternative_slots': []
        }
        
        try:
            if 'customer_name' in reservation_data:
                name_valid, name_corrected = self.validate_name(reservation_data['customer_name'])
                if not name_valid:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(f"Name: {name_corrected}")
                else:
                    validation_results['corrected_data']['customer_name'] = name_corrected
            
            if 'phone_number' in reservation_data:
                phone_valid, phone_corrected = self.validate_phone_number(reservation_data['phone_number'])
                if not phone_valid:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(f"Phone: {phone_corrected}")
                else:
                    validation_results['corrected_data']['phone_number'] = phone_corrected
            
            if 'email' in reservation_data and reservation_data['email']:
                email_valid, email_corrected = self.validate_email(reservation_data['email'])
                if not email_valid:
                    validation_results['warnings'].append(f"Email: {email_corrected}")
                else:
                    validation_results['corrected_data']['email'] = email_corrected
            
            if 'date' in reservation_data and 'time' in reservation_data:
                dt_valid, dt_message, validated_dt = self.validate_date_time(
                    reservation_data['date'], 
                    reservation_data['time'],
                    shop_hours=shop_hours
                )
                
                if not dt_valid:
                    validation_results['is_valid'] = False
                    validation_results['errors'].append(f"Date/Time: {dt_message}")
                    
                    if validated_dt:
                        alternatives = self.generate_alternative_slots(validated_dt, shop_hours)
                        validation_results['alternative_slots'] = alternatives
                else:
                    validation_results['corrected_data']['datetime'] = validated_dt
                    validation_results['corrected_data']['date'] = validated_dt.strftime("%Y-%m-%d")
                    validation_results['corrected_data']['time'] = validated_dt.strftime("%H:%M")
            
            if 'party_size' in reservation_data:
                try:
                    party_size = int(reservation_data['party_size'])
                    party_valid, party_message = self.validate_party_size(party_size)
                    if not party_valid:
                        validation_results['is_valid'] = False
                        validation_results['errors'].append(f"Party Size: {party_message}")
                    else:
                        validation_results['corrected_data']['party_size'] = party_size
                except (ValueError, TypeError):
                    validation_results['is_valid'] = False
                    validation_results['errors'].append("Party Size: Must be a valid number")
            
            if ('datetime' in validation_results['corrected_data'] and 
                not validation_results['alternative_slots']):
                base_dt = validation_results['corrected_data']['datetime']
                validation_results['alternative_slots'] = self.generate_alternative_slots(base_dt, shop_hours)
            
            return validation_results
            
        except Exception as e:
            logger.error(f"Comprehensive validation error: {e}")
            validation_results['is_valid'] = False
            validation_results['errors'].append(f"Validation system error: {str(e)}")
            return validation_results