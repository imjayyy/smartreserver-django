from .agent import Agent
from .prompts import get_business_system_prompt
from reservation.models import Reservation
from business.models import Service
from datetime import date, timedelta
from django.db.models import Count

class BusinessAgent(Agent):
    def __init__(self, business, session_id, user_data=None):
        self.business = business
        super().__init__(business.id, session_id, user_data)
        self.context = self._load_business_context()

    def _load_business_context(self):
        # Load business data for context
        services = self.business.services.all()
        offers = self.business.offers.filter(end_date__gte=date.today())
        return {
            'name': self.business.name,
            'services': list(services.values('name', 'price', 'duration')),
            'offers': list(offers.values('title', 'discount_percentage', 'end_date')),
            'hours': self.business.hours,
        }

    def _get_tools(self):
        # Override to add business‑specific tools
        base_tools = super()._get_tools()  # includes check_availability etc.
        admin_tools = [
            {
                "type": "function",
                "function": {
                    "name": "get_today_reservations",
                    "description": "Get all reservations for today",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            {
                "type": "function",
                "function": {
                    "name": "get_weekly_stats",
                    "description": "Get reservation statistics for the current week",
                    "parameters": {"type": "object", "properties": {}}
                }
            },
            # You can add more tools here
        ]
        return base_tools + admin_tools

    def _execute_function(self, name, args):
        if name == "get_today_reservations":
            today = date.today()
            reservations = Reservation.objects.filter(
                business=self.business,
                reservation_date=today,
                status__in=['pending', 'confirmed']
            ).values('customer_name', 'reservation_time', 'number_of_people')
            return list(reservations)

        elif name == "get_weekly_stats":
            today = date.today()
            start_of_week = today - timedelta(days=today.weekday())  # Monday
            end_of_week = start_of_week + timedelta(days=6)
            reservations = Reservation.objects.filter(
                business=self.business,
                reservation_date__range=[start_of_week, end_of_week]
            )
            total = reservations.count()
            per_day = reservations.values('reservation_date').annotate(count=Count('id')).order_by('reservation_date')
            most_popular_service = Service.objects.filter(
                business=self.business,
                reservation__in=reservations
            ).annotate(total=Count('reservation')).order_by('-total').first()
            return {
                'total_reservations': total,
                'per_day': list(per_day),
                'most_popular_service': most_popular_service.name if most_popular_service else None
            }

        # If not handled, fall back to base class (e.g., check_availability)
        return super()._execute_function(name, args)