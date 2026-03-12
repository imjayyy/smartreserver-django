# reservation/helper_functions.py
from datetime import datetime, timedelta, date, time
from django.utils import timezone
from .models import Reservation, ReservationPolicy
from business.models import Service

def get_available_slots(business, target_date, service_ids=None, party_size=1):
    """
    Return list of available start times for a given business and date.
    Optionally filter by services (to determine duration) and party size.
    """
    try:
        policy = business.reservationpolicy
    except ReservationPolicy.DoesNotExist:
        # No policy defined → assume 24/7 with no restrictions
        policy = None

    # If no operating hours, assume whole day
    if policy and policy.operating_hours_start and policy.operating_hours_end:
        open_dt = datetime.combine(target_date, policy.operating_hours_start)
        close_dt = datetime.combine(target_date, policy.operating_hours_end)
    else:
        open_dt = datetime.combine(target_date, time.min)
        close_dt = datetime.combine(target_date, time.max)

    # Fetch all confirmed/pending reservations for that day
    reservations = Reservation.objects.filter(
        business=business,
        reservation_date=target_date,
        status__in=['pending', 'confirmed']
    ).prefetch_related('services')

    # Build busy intervals (start_time → end_time)
    busy_intervals = []
    for res in reservations:
        # Calculate end time from reservation's own end_time if stored, else compute
        if res.end_time:
            end_dt = datetime.combine(target_date, res.end_time)
        else:
            duration = res.calculate_total_duration()
            start_dt = datetime.combine(target_date, res.reservation_time)
            end_dt = start_dt + duration
        busy_intervals.append((start_dt, end_dt))

    # Determine required duration for the new booking
    if service_ids:
        services = Service.objects.filter(id__in=service_ids, business=business)
        total_duration = sum((s.duration for s in services), timedelta())
    else:
        # If no service selected, use a default duration (maybe from policy or 1 hour)
        total_duration = timedelta(hours=1)  # fallback

    # Add buffer time
    buffer = timedelta(minutes=policy.buffer_time_minutes if policy else 0)

    # Generate slots every 15 minutes
    slot_interval = timedelta(minutes=15)
    slots = []
    current = open_dt
    while current + total_duration + buffer <= close_dt:
        # Check if slot overlaps any busy interval
        slot_end = current + total_duration + buffer
        overlaps = any(
            (current < busy_end and slot_end > busy_start)
            for busy_start, busy_end in busy_intervals
        )
        if not overlaps:
            slots.append(current.time())
        current += slot_interval

    return slots


def create_reservation(business, customer_data, service_ids, reservation_date, reservation_time, party_size=1, special_requests=''):
    """
    Attempt to create a reservation after checking availability.
    Returns (reservation, error_message).
    """
    # Re-check availability (to avoid race condition)
    available_slots = get_available_slots(business, reservation_date, service_ids, party_size)
    if reservation_time not in available_slots:
        return None, "Selected time is no longer available."

    # Create reservation (status = pending or confirmed depending on policy)
    reservation = Reservation(
        business=business,
        customer_name=customer_data['name'],
        customer_email=customer_data['email'],
        customer_phone=customer_data['phone'],
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        number_of_people=party_size,
        special_requests=special_requests,
        status='pending'  # maybe auto-confirm if no payment required
    )
    reservation.save()
    if service_ids:
        reservation.services.set(service_ids)
    # end_time will be auto-calculated in save()
    return reservation, None