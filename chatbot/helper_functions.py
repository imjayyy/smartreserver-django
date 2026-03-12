# chatbot/helper_functions.py
import requests
from datetime import date
from django.conf import settings
from business.models import Business, Service, SpecialOffer
from reservation.models import Reservation
from reservation.helper_functions import get_available_slots, create_reservation

class AIService:
    def __init__(self, business_id):
        self.business = Business.objects.get(id=business_id)
        self.context = self._build_context()

    def _build_context(self):
        """Gather all relevant business data for the AI prompt."""
        services = Service.objects.filter(business=self.business)
        offers = SpecialOffer.objects.filter(business=self.business, end_date__gte=date.today())
        policy = getattr(self.business, 'reservationpolicy', None)

        # Format services list
        services_list = "\n".join([
            f"- {s.name}: ${s.price} ({s.duration})" for s in services
        ]) if services else "No services listed."

        # Format offers list
        offers_list = "\n".join([
            f"- {o.title}: {o.discount_percentage}% off until {o.end_date}" for o in offers
        ]) if offers else "No current special offers."

        # Policy info
        if policy:
            policy_info = f"""
- Operating hours: {policy.operating_hours_start} to {policy.operating_hours_end}
- Buffer between reservations: {policy.buffer_time_minutes} minutes
- Max reservations per day: {policy.max_reservations_per_day or 'No limit'}
"""
        else:
            policy_info = "- No specific reservation policy set."

        context = f"""
You are an AI assistant for {self.business.name}. 
Business info: {self.business.description}
Address: {self.business.address}
Phone: {self.business.phone_number}
Email: {self.business.email}

Services:
{services_list}

Current special offers:
{offers_list}

Reservation policy:
{policy_info}

Today's date: {date.today().isoformat()}

You must help customers with:
- Checking availability for a specific date and time (or finding the next available slot)
- Making a reservation (collect name, email, phone, date, time, party size, and optionally services)
- Modifying or canceling existing reservations (if they provide their reservation UUID)
- Answering questions about services, offers, or business details

When a user wants to book, first confirm the details (date, time, party size, services) and then create the reservation. Always be friendly, concise, and professional.
"""
        return context

    def _call_ai(self, user_message):
        """Send prompt to OpenRouter (Gemini 2.0 Flash) and return response."""
        api_key = getattr(settings, 'OPENROUTER_API_KEY', None)
        if not api_key:
            return "AI service is not configured. Please set OPENROUTER_API_KEY in settings."

        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        payload = {
            'model': 'google/gemini-2.0-flash',  # or use a setting
            'messages': [
                {'role': 'system', 'content': self.context},
                {'role': 'user', 'content': user_message}
            ],
            'temperature': 0.7,
        }
        try:
            response = requests.post(
                'https://openrouter.ai/api/v1/chat/completions',
                headers=headers,
                json=payload,
                timeout=10
            )
            response.raise_for_status()
            data = response.json()
            return data['choices'][0]['message']['content']
        except requests.exceptions.RequestException as e:
            # Log error here if you have logging set up
            return f"I'm having trouble connecting right now. Please try again later. (Error: {str(e)})"

    def process_message(self, user_message):
        """
        Main entry point from the chatbot view.
        For now, we simply call AI and return response.
        In a more advanced version, you could parse intents or use function calling.
        """
        ai_response = self._call_ai(user_message)
        return ai_response