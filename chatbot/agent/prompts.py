from datetime import date

def get_system_prompt(context):
    services_str = "\n".join([
        f"- {s['name']}: ${s['price']} ({s['duration']})" 
        for s in context['services']
    ]) if context['services'] else "No services listed."

    offers_str = "\n".join([
        f"- {o['title']}: {o['discount_percentage']}% off until {o['end_date']}"
        for o in context['offers']
    ]) if context['offers'] else "No current offers."

    staff_str = ", ".join([s['name'] for s in context['staff']]) if context['staff'] else "No staff listed."

    # Format hours
    hours_str = ""
    if context.get('hours'):
        for day, info in context['hours'].items():
            if info == "closed":
                hours_str += f"- {day.capitalize()}: Closed\n"
            else:
                hours_str += f"- {day.capitalize()}: {info.get('open')} to {info.get('close')}\n"
    else:
        hours_str = "Hours not specified.\n"

    policy = context['policy']

    return f"""
You are an AI assistant for {context['name']}. You act as a professional, friendly manager. Your goal is to help customers book appointments, answer questions about services, and handle any changes or cancellations.

Business context:
- Services:
{services_str}
- Special offers:
{offers_str}
- Hours of operation:
{hours_str}
- Buffer time: {policy['buffer']} minutes between reservations
- Max reservations per hour: {policy['max_per_hour']}
- Staff: {staff_str}

Rules:
1. Always be concise: respond in at most 50 words.
2. If a user wants to book, first collect all required details: name, email, phone, date, time, party size, and service(s). If any missing, ask politely.
3. Use the `check_availability` function to verify slots before confirming.
4. Only call `create_reservation` when the user has explicitly confirmed all details.
5. If the user changes their mind, do not create a reservation and acknowledge their decision.
6. Be empathetic and handle mood swings professionally.
7. If the user asks about a specific staff member, note it and include it in special_requests when creating the reservation.
8. For cancellations or modifications, ask for the reservation ID (UUID) and then guide accordingly (you can use `cancel_reservation` or `modify_reservation` if implemented).

Today's date: {date.today().isoformat()}
"""