import re
import logging
from datetime import datetime, timedelta
from dateutil.parser import parse
from typing import Dict, Any
from django.conf import settings

logger = logging.getLogger(__name__)


class DataExtractor:
    """Extracts reservation data from user messages with smart detection."""
    
    def __init__(self):
        self.max_party_size = settings.MAX_PARTY_SIZE
    
    def extract_reservation_data(self, message: str) -> Dict[str, Any]:
        """Extract reservation data from user message with smart party size detection."""
        extracted_data: Dict[str, Any] = {}
        message_lower = message.lower().strip()
        
        logger.info(f"Extracting data from message: {message}")
        
        # Extract service type
        self._extract_service_type(message_lower, extracted_data)
        
        # Extract party size with smart detection
        self._extract_party_size(message_lower, message, extracted_data)
        
        # Extract date and time
        self._extract_date_time(message_lower, message, extracted_data)
        
        logger.info(f"Extracted data: {extracted_data}")
        return extracted_data
    
    def _extract_service_type(self, message_lower: str, extracted_data: Dict[str, Any]):
        """Extract service type from message."""
        service_patterns = {
            'haircut|hair cut': 'Haircut',
            'beard|trim|shape': 'Beard Trim & Shape',
            'shave': 'Traditional Shave',
            'color|coloring': 'Hair Coloring',
            'treatment|keratin': 'Keratin Treatment',
            'classic': 'Classic Haircut',
            'massage': 'Massage',
            'dinner|dining': 'Dinner Reservation',
            'brunch': 'Weekend Brunch',
            'private|room': 'Private Dining Room',
            'appointment|booking|reservation': 'General Service'
        }
        
        for keyword, service in service_patterns.items():
            if re.search(keyword, message_lower):
                extracted_data['service_type'] = service
                logger.info(f"Extracted service: {service}")
                break
    
    def _extract_party_size(self, message_lower: str, original_message: str, extracted_data: Dict[str, Any]):
        """Extract party size with smart contextual detection."""
        party_size = None
        
        # ====== STRICT SOLO INDICATORS (definitely 1) ======
        strict_solo_patterns = [
            r'\balone\b',
            r'\bsolo\b',
            r'\bjust me\b',
            r'\bonly me\b',
            r'\bmyself\b',
            r'\bfor me\b(?!\s+and)',
            r'\bjust for me\b',
            r'\bsingle\b',
            r'\bone person\b',
            r'\bone\b(?!\s+more|\s+other|\s+extra)',
            r'\bby myself\b',
            r'\bon my own\b',
        ]
        
        for pattern in strict_solo_patterns:
            if re.search(pattern, message_lower):
                party_size = 1
                logger.info(f"Strict solo pattern detected -> party size = 1")
                break
        
        # ====== EXPLICIT NUMBERS ======
        if party_size is None:
            all_numbers = re.findall(r'\b(\d+)\b', original_message)
            party_context_words = ['people', 'persons', 'guests', 'person', 'adults', 'kids', 
                                 'children', 'group', 'party', 'size', 'for', 'of', 'with']
            
            for num_str in all_numbers:
                num = int(num_str)
                pattern = rf'\b{num}\b\s+(?:{"|".join(party_context_words)})'
                pattern_rev = rf'(?:{"|".join(party_context_words)})\s+\b{num}\b'
                
                if re.search(pattern, message_lower, re.IGNORECASE) or re.search(pattern_rev, message_lower, re.IGNORECASE):
                    if 1 <= num <= self.max_party_size:
                        party_size = num
                        logger.info(f"Found party size from explicit number: {party_size}")
                        break
        
        # ====== RELATIONSHIP INDICATORS ======
        if party_size is None:
            relationship_indicators = {
                'brother': 2, 'sister': 2, 'friend': 2, 'friends': 2,
                'partner': 2, 'wife': 2, 'husband': 2, 'child': 2,
                'children': 2, 'kids': 2, 'family': 3, 'parents': 3,
                'colleague': 2, 'co-worker': 2, 'cousin': 2,
                'mom': 2, 'dad': 2, 'mother': 2, 'father': 2,
            }
            
            for relationship, base_size in relationship_indicators.items():
                if relationship in message_lower:
                    count = len(re.findall(rf'\b{relationship}\b', message_lower))
                    party_size = base_size + (count - 1 if count > 1 else 0)
                    logger.info(f"Relationship '{relationship}' -> party size = {party_size}")
                    break
        
        # ====== GROUP INDICATORS WITHOUT EXPLICIT NUMBERS ======
        if party_size is None:
            group_indicators = [
                r'\bboth\b',
                r'\btogether\b',
                r'\bwe are\b',
                r'\bwe\'\sre\b',
                r'\bus\b',
                r'\ball of us\b',
                r'\beveryone\b',
            ]
            
            for indicator in group_indicators:
                if re.search(indicator, message_lower):
                    party_size = 2
                    logger.info(f"Group indicator detected -> party size = 2")
                    break
        
        # ====== CONTEXTUAL INFERENCE ======
        if party_size is None:
            has_booking_intent = any(word in message_lower for word in 
                                    ['book', 'reserve', 'appointment', 'schedule', 'booking'])
            
            if has_booking_intent:
                logger.info("Booking intent detected but NO party size specified")
            else:
                logger.info("Not a booking request - party size not needed")
        
        # Set party size if determined
        if party_size is not None:
            party_size = min(party_size, self.max_party_size)
            extracted_data['party_size'] = party_size
            logger.info(f"Final party size: {party_size}")
        else:
            logger.info("Party size not determined - AI should ask")
    
    def _extract_date_time(self, message_lower: str, original_message: str, extracted_data: Dict[str, Any]):
        """Extract date and time from message."""
        today = datetime.now()
        
        # Contextual date patterns
        if 'tonight' in message_lower or 'this evening' in message_lower:
            extracted_data['date'] = today.strftime('%Y-%m-%d')
            if 'time' not in extracted_data:
                extracted_data['time'] = '18:00'
            logger.info(f"Extracted date (tonight): {extracted_data['date']}")
        elif 'tomorrow' in message_lower:
            tomorrow = today + timedelta(days=1)
            extracted_data['date'] = tomorrow.strftime('%Y-%m-%d')
            logger.info(f"Extracted date (tomorrow): {extracted_data['date']}")
        elif 'next week' in message_lower:
            next_week = today + timedelta(days=7)
            extracted_data['date'] = next_week.strftime('%Y-%m-%d')
            logger.info(f"Extracted date (next week): {extracted_data['date']}")
        elif 'weekend' in message_lower:
            # Find next Saturday
            days_ahead = (5 - today.weekday()) % 7
            if days_ahead == 0:
                days_ahead = 7
            next_saturday = today + timedelta(days=days_ahead)
            extracted_data['date'] = next_saturday.strftime('%Y-%m-%d')
            logger.info(f"Extracted date (weekend): {extracted_data['date']}")
        else:
            # Try to find date patterns
            date_patterns = [
                r'(\d{1,2}[/-]\d{1,2}[/-]\d{2,4})',
                r'(\d{1,2}\s+(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{4})',
                r'(\d{1,2}\s+(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{4})',
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, original_message, re.IGNORECASE)
                if match:
                    try:
                        date_str = match.group(1)
                        parsed_date = parse(date_str)
                        extracted_data['date'] = parsed_date.strftime('%Y-%m-%d')
                        logger.info(f"Extracted date: {extracted_data['date']}")
                        break
                    except Exception as e:
                        logger.warning(f"Failed to parse date: {e}")
                        continue
        
        # Time extraction
        time_patterns = [
            r'(\d{1,2}:\d{2}\s*(?:AM|PM|am|pm)?)',
            r'(\d{1,2}\s*(?:AM|PM|am|pm))',
            r'\b(\d{1,2})\s*(?:o\'clock|oclock|clock)\b',
        ]
        
        for pattern in time_patterns:
            match = re.search(pattern, original_message, re.IGNORECASE)
            if match:
                time_str = match.group(1).lower()
                
                # Remove am/pm for parsing
                if 'am' in time_str:
                    time_str = time_str.replace('am', '').strip()
                    is_pm = False
                elif 'pm' in time_str:
                    time_str = time_str.replace('pm', '').strip()
                    is_pm = True
                else:
                    is_pm = False
                
                # Parse the time
                try:
                    if ':' in time_str:
                        hour, minute = map(int, time_str.split(':'))
                    else:
                        hour = int(time_str)
                        minute = 0
                    
                    # Convert to 24-hour format if pm
                    if is_pm and hour < 12:
                        hour += 12
                    elif not is_pm and hour == 12:
                        hour = 0
                    
                    extracted_data['time'] = f"{hour:02d}:{minute:02d}"
                    logger.info(f"Extracted time: {extracted_data['time']}")
                    break
                except Exception as e:
                    logger.warning(f"Failed to parse time: {e}")
                    continue