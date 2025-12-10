import re
import pytz
import logging
from datetime import datetime, timedelta, time as dt_time
from dateutil.parser import parse
from typing import Dict, Any, List, Tuple, Optional
from django.conf import settings

logger = logging.getLogger(__name__)


class DateTimeHandler:
    """Handles date/time validation and alternative slot generation."""
    
    def __init__(self):
        self.timezone = pytz.timezone('UTC')
    
    def validate_date_time(self, date_str: str, time_str: str, 
                         min_hours_from_now: Optional[int] = None, 
                         max_days_in_future: Optional[int] = None,
                         shop_hours: Optional[Dict[str, str]] = None) -> Tuple[bool, str, Optional[datetime]]:
        """Validate date and time with shop hours."""
        try:
            # Use settings if not provided
            if min_hours_from_now is None:
                min_hours_from_now = settings.MIN_BOOKING_HOURS_ADVANCE
            if max_days_in_future is None:
                max_days_in_future = settings.MAX_ADVANCE_BOOKING_DAYS
            
            datetime_str = f"{date_str} {time_str}"
            
            try:
                requested_dt = parse(datetime_str)
            except Exception:
                return False, "Invalid date or time format", None
            
            if not requested_dt.tzinfo:
                requested_dt = requested_dt.replace(tzinfo=self.timezone)
            
            current_dt = datetime.now(self.timezone)
            
            if requested_dt < current_dt:
                return False, "Cannot book in the past", None
            
            min_time = current_dt + timedelta(hours=min_hours_from_now)
            if requested_dt < min_time:
                return False, f"Booking must be at least {min_hours_from_now} hour(s) in advance", None
            
            max_time = current_dt + timedelta(days=max_days_in_future)
            if requested_dt > max_time:
                return False, f"Cannot book more than {max_days_in_future} days in advance", None
            
            # Check shop operating hours
            if shop_hours:
                day_of_week = requested_dt.strftime('%A').lower()
                
                if day_of_week not in shop_hours:
                    return False, f"We're closed on {day_of_week.capitalize()}", None
                
                hours_str = shop_hours[day_of_week]
                if not hours_str or hours_str.lower() == 'closed':
                    return False, f"We're closed on {day_of_week.capitalize()}", None
                
                is_valid, message = self._check_within_shop_hours(requested_dt, hours_str)
                if not is_valid:
                    return False, message, None
            
            return True, "Valid datetime", requested_dt
            
        except Exception as e:
            logger.error(f"DateTime validation error: {e}")
            return False, f"Date/time validation failed: {str(e)}", None
    
    def _check_within_shop_hours(self, requested_dt: datetime, hours_str: str) -> Tuple[bool, str]:
        """Check if requested time is within shop operating hours."""
        try:
            # Parse hours string like "9:00 AM - 7:00 PM"
            open_close = hours_str.split('-')
            if len(open_close) != 2:
                return True, ""  # If can't parse, don't block
            
            open_time_str = open_close[0].strip()
            close_time_str = open_close[1].strip()
            
            # Convert to 24-hour time
            open_time = self._parse_time_string(open_time_str)
            close_time = self._parse_time_string(close_time_str)
            
            if not open_time or not close_time:
                return True, ""  # If can't parse, don't block
            
            # Check if requested time is within hours
            requested_time = requested_dt.time()
            
            # Handle cases where close time might be next day (e.g., 11:00 PM - 2:00 AM)
            if close_time < open_time:
                # Shop closes after midnight
                if requested_time >= open_time or requested_time <= close_time:
                    return True, ""
                else:
                    return False, f"Time must be between {open_time_str} and {close_time_str}"
            else:
                # Normal hours
                if open_time <= requested_time <= close_time:
                    return True, ""
                else:
                    return False, f"Time must be between {open_time_str} and {close_time_str}"
                    
        except Exception as e:
            logger.error(f"Error checking shop hours: {e}")
            return True, ""  # Don't block if error
    
    def _parse_time_string(self, time_str: str) -> Optional[dt_time]:
        """Parse time string like '9:00 AM' to datetime.time."""
        try:
            from dateutil import parser
            dt = parser.parse(time_str)
            return dt.time()
        except Exception:
            try:
                # Try manual parsing
                time_str = time_str.strip().upper()
                original_str = time_str
                
                if 'AM' in time_str:
                    time_str = time_str.replace('AM', '').strip()
                    is_pm = False
                elif 'PM' in time_str:
                    time_str = time_str.replace('PM', '').strip()
                    is_pm = True
                else:
                    is_pm = False
                
                parts = time_str.split(':')
                hour = int(parts[0])
                minute = int(parts[1]) if len(parts) > 1 else 0
                
                if is_pm and hour != 12:
                    hour += 12
                elif not is_pm and hour == 12:
                    hour = 0
                    
                return dt_time(hour, minute)
            except Exception:
                return None
    
    def generate_alternative_slots(self, base_datetime: datetime, 
                                 shop_hours: Optional[Dict[str, str]] = None,
                                 available_slots: Optional[List[datetime]] = None) -> List[datetime]:
        """Generate alternative time slots within shop hours."""
        try:
            alternatives = []
            current_dt = datetime.now(self.timezone)
            
            # Try same day, different times
            if shop_hours:
                day_of_week = base_datetime.strftime('%A').lower()
                if day_of_week in shop_hours:
                    hours_str = shop_hours[day_of_week]
                    if hours_str and hours_str.lower() != 'closed':
                        open_time = self._parse_time_string(hours_str.split('-')[0].strip())
                        close_time = self._parse_time_string(hours_str.split('-')[1].strip())
                        
                        if open_time and close_time:
                            # Generate slots every hour
                            hour = open_time.hour
                            while hour < close_time.hour:
                                slot = base_datetime.replace(hour=hour, minute=0)
                                if slot > current_dt and slot not in alternatives:
                                    alternatives.append(slot)
                                hour += 1
            
            # If no shop hours or not enough slots, use default logic
            if len(alternatives) < 3:
                # Try next few days at reasonable times
                for days_ahead in [1, 2, 3, 7]:
                    if len(alternatives) >= 4:
                        break
                    
                    new_date = base_datetime + timedelta(days=days_ahead)
                    new_day = new_date.strftime('%A').lower()
                    
                    if shop_hours and new_day in shop_hours:
                        hours_str = shop_hours[new_day]
                        if hours_str and hours_str.lower() != 'closed':
                            slot = new_date.replace(hour=14, minute=0)  # 2 PM
                            if slot > current_dt and slot not in alternatives:
                                alternatives.append(slot)
            
            # Sort and return
            alternatives.sort()
            return alternatives[:4]
            
        except Exception as e:
            logger.error(f"Alternative slots generation error: {e}")
            return []
    
    def format_alternative_slots(self, slots: List[datetime]) -> str:
        """Format alternative slots for display."""
        if not slots:
            return "No alternative slots available."
        
        formatted = []
        for i, slot in enumerate(slots, 1):
            day_name = slot.strftime("%A")
            date_str = slot.strftime("%B %d, %Y")
            time_str = slot.strftime("%I:%M %p").lstrip('0')
            formatted.append(f"{i}. {day_name}, {date_str} at {time_str}")
        
        return "\n".join(formatted)