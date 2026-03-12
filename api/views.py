from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers
from business.models import Business
from reservation.models import Reservation
from reservation.helper_functions import get_available_slots, create_reservation
from chatbot.helper_functions import AIService
from datetime import datetime

# ==========================
# Chat Endpoint
# ==========================
@api_view(['POST'])
def chat(request, business_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=404)

    message = request.data.get('message')
    if not message:
        return Response({'error': 'message field required'}, status=400)

    try:
        ai = AIService(business_id)
        reply = ai.process_message(message)
    except Exception as e:
        return Response({'error': f'AI processing failed: {str(e)}'}, status=500)

    return Response({'reply': reply}, status=200)


# ==========================
# Availability Endpoint
# ==========================
@api_view(['GET'])
def availability(request, business_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=404)

    date_str = request.GET.get('date')
    service_ids = request.GET.getlist('service_ids')  # e.g., ?service_ids=1&service_ids=2
    party_size_str = request.GET.get('party_size', '1')

    if not date_str:
        return Response({'error': 'date parameter required'}, status=400)

    try:
        target_date = datetime.strptime(date_str, '%Y-%m-%d').date()
    except ValueError:
        return Response({'error': 'Invalid date format, use YYYY-MM-DD'}, status=400)

    try:
        service_ids = [int(sid) for sid in service_ids]
        party_size = int(party_size_str)
    except ValueError:
        return Response({'error': 'Invalid service_ids or party_size'}, status=400)

    slots = get_available_slots(business, target_date, service_ids, party_size)
    return Response({'available_slots': [s.strftime('%H:%M') for s in slots]}, status=200)


# ==========================
# Serializer for Booking
# ==========================
class ReservationCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField()
    reservation_date = serializers.DateField()
    reservation_time = serializers.TimeField()
    service_ids = serializers.ListField(child=serializers.IntegerField(), required=False)
    number_of_people = serializers.IntegerField(default=1)
    special_requests = serializers.CharField(required=False, allow_blank=True)


# ==========================
# Booking Endpoint
# ==========================
@api_view(['POST'])
def book(request, business_id):
    try:
        business = Business.objects.get(id=business_id)
    except Business.DoesNotExist:
        return Response({'error': 'Business not found'}, status=404)

    serializer = ReservationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data

    reservation, error = create_reservation(
        business=business,
        customer_data={
            'name': data['customer_name'],
            'email': data['customer_email'],
            'phone': data['customer_phone']
        },
        service_ids=data.get('service_ids', []),
        reservation_date=data['reservation_date'],
        reservation_time=data['reservation_time'],
        party_size=data.get('number_of_people', 1),
        special_requests=data.get('special_requests', '')
    )

    if error:
        return Response({'error': error}, status=400)

    # Use DRF serializer if you have one, else just return fields
    return Response({
        'id': reservation.id,
        'customer_name': reservation.customer_name,
        'customer_email': reservation.customer_email,
        'customer_phone': reservation.customer_phone,
        'reservation_date': reservation.reservation_date.strftime('%Y-%m-%d'),
        'reservation_time': reservation.reservation_time.strftime('%H:%M'),
        'service_ids': [s.id for s in reservation.services.all()] if hasattr(reservation, 'services') else [],
        'number_of_people': reservation.party_size,
        'special_requests': reservation.special_requests,
    }, status=201)