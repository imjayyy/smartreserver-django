import json
from datetime import datetime, date
from openai import OpenAI
from django.conf import settings
from business.models import Business
from reservation.helper_functions import get_available_slots, create_reservation
from .prompts import get_system_prompt
from .memory import SessionMemory

# Initialize OpenAI client for OpenRouter
client = OpenAI(
    api_key=settings.OPENROUTER_API_KEY,
    base_url=settings.OPENROUTER_BASE_URL,
)

class Agent:
    def __init__(self, business_id, session_id, user_data=None):
        self.business_id = business_id
        self.session_id = session_id
        self.memory = SessionMemory(session_id)
        if user_data:
            self.memory.set_user_info(user_data)
        try:
            self.context = self._load_business_context()
        except Business.DoesNotExist:
            raise ValueError(f"Business with id {business_id} does not exist.")

    def _load_business_context(self):
        business = Business.objects.get(id=self.business_id)
        services = business.services.values('name', 'price', 'duration')
        offers = business.offers.filter(end_date__gte=date.today()).values('title', 'discount_percentage', 'end_date')
        staff = business.staff_members.filter(is_active=True).values('name')

        policy = {}
        if hasattr(business, 'reservationpolicy'):
            policy = {
                'buffer': business.reservationpolicy.buffer_time_minutes,
                'max_per_hour': business.max_reservations_per_hour,
            }
        else:
            policy = {
                'buffer': 0,
                'max_per_hour': business.max_reservations_per_hour,
            }

        return {
            'name': business.name,
            'services': list(services),
            'offers': list(offers),
            'staff': list(staff),
            'policy': policy,
            'hours': business.hours,   # JSON field with daily hours
        }

    def _get_tools(self):
        return [
            {
                "type": "function",
                "function": {
                    "name": "check_availability",
                    "description": "Check available slots for a given date and service",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "description": "Date in YYYY-MM-DD format"},
                            "service_id": {"type": "integer", "description": "ID of the service (optional)"},
                            "party_size": {"type": "integer", "description": "Number of people", "default": 1}
                        },
                        "required": ["date"]
                    }
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "create_reservation",
                    "description": "Create a reservation after user confirms",
                    "parameters": {
                        "type": "object",
                        "properties": {
                            "date": {"type": "string", "format": "date"},
                            "time": {"type": "string", "description": "Time in HH:MM format"},
                            "service_ids": {"type": "array", "items": {"type": "integer"}},
                            "number_of_people": {"type": "integer"},   # changed from party_size
                            "special_requests": {"type": "string", "default": ""}
                        },
                        "required": ["date", "time", "service_ids", "number_of_people"]
                    }
                }
            }
        ]
    def _execute_function(self, name, args):
        if name == "check_availability":
            business = Business.objects.get(id=self.business_id)
            target_date = datetime.strptime(args['date'], '%Y-%m-%d').date()
            service_id = args.get('service_id')
            party_size = args.get('party_size', 1)
            slots = get_available_slots(business, target_date, [service_id] if service_id else None, party_size)
            return {"available_slots": [s.strftime('%H:%M') for s in slots]}

        elif name == "create_reservation":
            business = Business.objects.get(id=self.business_id)
            user_info = self.memory.get_user_info()
            if not user_info:
                return {"success": False, "error": "User information missing. Please provide name, email, and phone."}
            res_date = datetime.strptime(args['date'], '%Y-%m-%d').date()
            res_time = datetime.strptime(args['time'], '%H:%M').time()
            reservation, error = create_reservation(
            business=business,
            customer_data=user_info,
            service_ids=args['service_ids'],
            reservation_date=res_date,
            reservation_time=res_time,
            party_size=args['number_of_people'],   # map to party_size parameter
            special_requests=args.get('special_requests', '')
            )
            if reservation:
                self.memory.set_last_reservation_id(reservation.id)
                return {"success": True, "reservation_id": reservation.id, "message": "Reservation created."}
            else:
                return {"success": False, "error": error}

        return {"error": "Unknown function"}

    def process_message(self, user_message):
        # Retrieve conversation history
        history = self.memory.get_history()
        user_info = self.memory.get_user_info()

        # Build messages
        system_prompt = get_system_prompt(self.context)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(history)
        messages.append({"role": "user", "content": user_message})

        tools = self._get_tools()

        try:
            response = client.chat.completions.create(
                model=settings.OPENROUTER_MODEL,
                messages=messages,
                tools=tools,
                tool_choice="auto",
                temperature=0.7,
                max_tokens=150
            )
        except Exception as e:
            return {"reply": f"Sorry, I'm having trouble connecting: {str(e)}", "reservation_id": None}

        reply_message = response.choices[0].message

        if reply_message.tool_calls:
            tool_call = reply_message.tool_calls[0]
            function_name = tool_call.function.name
            arguments = json.loads(tool_call.function.arguments)

            result = self._execute_function(function_name, arguments)

            messages.append(reply_message)
            messages.append({
                "role": "tool",
                "tool_call_id": tool_call.id,
                "content": json.dumps(result)
            })

            final_response = client.chat.completions.create(
                model="google/gemini-2.0-flash",
                messages=messages,
                temperature=0.7,
                max_tokens=150
            )
            reply = final_response.choices[0].message.content
        else:
            reply = reply_message.content

        # Store in memory
        self.memory.add_message("user", user_message)
        self.memory.add_message("assistant", reply)

        return {
            "reply": reply,
            "reservation_id": self.memory.get_last_reservation_id()
        }