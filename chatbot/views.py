from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import UserRateThrottle
from django.shortcuts import get_object_or_404

from business.models import Business
from .agent import Agent
from .agent.memory import SessionMemory


class ChatRateThrottle(UserRateThrottle):
    rate = "10/min"


@api_view(["POST"])
@throttle_classes([ChatRateThrottle])
def chat(request):
    """
    Main AI Chat Endpoint
    Expects JSON:
    {
        "business_id": 1,
        "session_id": "unique-session-id",
        "user": {  // optional on first message
            "name": "John Doe",
            "email": "john@example.com",
            "phone": "+1234567890"
        },
        "message": "I'd like a haircut tomorrow at 3pm"
    }
    """
    business_id = request.data.get("business_id")
    session_id = request.data.get("session_id")
    user_data = request.data.get("user", {})
    message_text = request.data.get("message")

    if not business_id or not session_id or not message_text:
        return Response(
            {"error": "business_id, session_id, and message are required"},
            status=400,
        )

    # Validate business exists
    business = get_object_or_404(Business, id=business_id)

    # Load session memory
    memory = SessionMemory(session_id)
    existing_user = memory.get_user_info()

    # Require user info on first message
    if not existing_user:
        if (
            not user_data
            or not user_data.get("name")
            or not user_data.get("email")
            or not user_data.get("phone")
        ):
            return Response(
                {"error": "First message requires user name, email, and phone"},
                status=400,
            )
        memory.set_user_info(user_data)

    # Create agent and process message
    agent = Agent(business_id, session_id, user_data if user_data else None)

    try:
        result = agent.process_message(message_text)
    except Exception as e:
        return Response({"error": f"AI failed: {str(e)}"}, status=500)

    return Response(result)