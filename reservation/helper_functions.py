# reservation/helper_functions.py
from datetime import datetime, timedelta, date, time
from django.utils import timezone
from .models import Reservation, ReservationPolicy
from business.models import Service

from datetime import datetime, time, timedelta
from django.utils.timezone import make_aware


def get_available_slots(business, target_date, service_ids=None, party_size=1):
    """
    Return list of available start times for a given business and date.
    Optionally filter by services (to determine duration) and party size.
    """

    # -------------------------
    # Get reservation policy safely
    # -------------------------
    try:
        policy = business.reservationpolicy
    except ReservationPolicy.DoesNotExist:
        policy = None

    # -------------------------
    # Operating hours
    # -------------------------
    open_time = policy.operating_hours_start if policy and policy.operating_hours_start else time.min
    close_time = policy.operating_hours_end if policy and policy.operating_hours_end else time.max

    open_dt = make_aware(datetime.combine(target_date, open_time))
    close_dt = make_aware(datetime.combine(target_date, close_time))

    # -------------------------
    # Fetch reservations
    # -------------------------
    reservations = Reservation.objects.filter(
        business=business,
        reservation_date=target_date,
        status__in=['pending', 'confirmed']
    ).prefetch_related('services')

    # -------------------------
    # Build busy intervals
    # -------------------------
    busy_intervals = []

    for res in reservations:
        start_dt = make_aware(datetime.combine(target_date, res.reservation_time))

        if res.end_time:
            end_dt = make_aware(datetime.combine(target_date, res.end_time))
        else:
            duration = res.calculate_total_duration()
            end_dt = start_dt + duration

        busy_intervals.append((start_dt, end_dt))

    # -------------------------
    # Merge overlapping intervals
    # -------------------------
    busy_intervals.sort()
    merged = []

    for start, end in busy_intervals:
        if not merged or start > merged[-1][1]:
            merged.append([start, end])
        else:
            merged[-1][1] = max(merged[-1][1], end)

    busy_intervals = [(s, e) for s, e in merged]

    # -------------------------
    # Calculate required duration
    # -------------------------
    if service_ids:
        services = Service.objects.filter(id__in=service_ids, business=business)
        total_duration = sum((s.duration for s in services), timedelta())
    else:
        total_duration = timedelta(hours=1)  # fallback

    # -------------------------
    # Buffer time
    # -------------------------
    buffer = timedelta(minutes=policy.buffer_time_minutes) if policy else timedelta(0)

    # -------------------------
    # Generate slots
    # -------------------------
    slot_interval = timedelta(minutes=15)
    slots = []
    current = open_dt

    while current + total_duration + buffer <= close_dt:
        slot_end = current + total_duration + buffer

        overlaps = any(
            current < busy_end and slot_end > busy_start
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
    valid_services = Service.objects.filter(id__in=service_ids, business=business)
    if len(valid_services) != len(service_ids):
        return None, "One or more services are invalid."

    reservation = Reservation(
        business=business,
        customer_name=customer_data['name'],
        customer_email=customer_data['email'],
        customer_phone=customer_data['phone'],
        reservation_date=reservation_date,
        reservation_time=reservation_time,
        number_of_people=party_size,
        special_requests=special_requests,
        status='pending'
    )
    reservation.save()
    if valid_services:
        reservation.services.set(valid_services)
    return reservation, None