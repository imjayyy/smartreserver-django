from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status, serializers
from django.shortcuts import get_object_or_404

from business.models import Business
from reservation.models import Reservation
from reservation.helper_functions import get_available_slots, create_reservation

from datetime import datetime


# ===================================
# Availability Endpoint
# ===================================
@api_view(["GET"])
def availability(request, business_id):
    business = get_object_or_404(Business, id=business_id)

    date_str = request.GET.get("date")
    service_ids = request.GET.getlist("service_ids")
    party_size = request.GET.get("party_size", 1)

    if not date_str:
        return Response({"error": "date parameter required"}, status=400)

    try:
        target_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        service_ids = [int(x) for x in service_ids]
        party_size = int(party_size)
    except ValueError:
        return Response({"error": "Invalid date format or service_ids/party_size"}, status=400)

    # Validate that service_ids belong to this business
    if service_ids:
        valid_services = business.services.filter(id__in=service_ids).values_list('id', flat=True)
        if set(service_ids) != set(valid_services):
            return Response({"error": "One or more service IDs are invalid for this business"}, status=400)

    slots = get_available_slots(business, target_date, service_ids, party_size)

    return Response(
        {"available_slots": [s.strftime("%H:%M") for s in slots]}, status=200
    )


# ===================================
# Reservation Serializer
# ===================================
class ReservationCreateSerializer(serializers.Serializer):
    customer_name = serializers.CharField()
    customer_email = serializers.EmailField()
    customer_phone = serializers.CharField()
    reservation_date = serializers.DateField()
    reservation_time = serializers.TimeField()
    service_ids = serializers.ListField(
        child=serializers.IntegerField(), required=False, default=list
    )
    number_of_people = serializers.IntegerField(default=1)
    special_requests = serializers.CharField(required=False, allow_blank=True)


# ===================================
# Booking Endpoint
# ===================================
@api_view(["POST"])
def book(request, business_id):
    business = get_object_or_404(Business, id=business_id)

    serializer = ReservationCreateSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=400)

    data = serializer.validated_data

    # Validate service_ids belong to this business
    service_ids = data.get("service_ids", [])
    if service_ids:
        valid_services = business.services.filter(id__in=service_ids).values_list('id', flat=True)
        if set(service_ids) != set(valid_services):
            return Response({"error": "One or more service IDs are invalid for this business"}, status=400)

    reservation, error = create_reservation(
        business=business,
        customer_data={
            "name": data["customer_name"],
            "email": data["customer_email"],
            "phone": data["customer_phone"],
        },
        service_ids=service_ids,
        reservation_date=data["reservation_date"],
        reservation_time=data["reservation_time"],
        party_size=data["number_of_people"],
        special_requests=data.get("special_requests", ""),
    )

    if error:
        return Response({"error": error}, status=400)

    return Response(
        {
            "id": reservation.id,
            "uuid": str(reservation.uuid),
            "customer_name": reservation.customer_name,
            "customer_email": reservation.customer_email,
            "customer_phone": reservation.customer_phone,
            "reservation_date": reservation.reservation_date.strftime("%Y-%m-%d"),
            "reservation_time": reservation.reservation_time.strftime("%H:%M"),
            "service_ids": [s.id for s in reservation.services.all()],
            "number_of_people": reservation.number_of_people,
            "special_requests": reservation.special_requests,
            "status": reservation.status,
        },
        status=201,
    )