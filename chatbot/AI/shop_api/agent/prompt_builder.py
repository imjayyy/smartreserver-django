from typing import Dict, Any, Optional
from .utils import format_operating_hours, format_services, format_user_context


class PromptBuilder:
    """Professional prompt builder for AI responses."""
    
    @staticmethod
    def build_chat_prompt(
        user_message: str,
        shop_details: Dict[str, Any],
        services: Dict[str, Any],
        reservation_state: Optional[str],
        reservation_data: Optional[Dict[str, Any]],
        conversation_context: str,
        session_data: Optional[Dict[str, Any]]
    ) -> str:
        """Build professional chat prompt without emojis."""
        shop_name = shop_details.get('shop_name', 'Our Shop')
        shop_hours = shop_details.get('operating_hours', {})
        
        # Party size analysis
        party_analysis = PromptBuilder._analyze_party_size(user_message, reservation_data)
        
        # Check for completed reservations
        if "RESERVATION CONFIRMED" in conversation_context or "cancelled successfully" in conversation_context.lower():
            conversation_context = "Previous conversation completed. Starting fresh."
        
        prompt = f"""You are an AI assistant for {shop_name}, a {shop_details.get('category', 'business')}.

SHOP OPERATING HOURS (STRICTLY ENFORCE):
{format_operating_hours(shop_hours)}

CUSTOMER INFORMATION:
{format_user_context(session_data) if session_data else "No customer information available yet."}

SERVICES AVAILABLE:
{format_services(services.get('services', []))}

PARTY SIZE ANALYSIS:
{party_analysis}

CONVERSATION CONTEXT:
{conversation_context if conversation_context else "Starting fresh conversation."}

CURRENT RESERVATION STATUS:
- Active: {'Yes' if reservation_state else 'No'}
- Data collected: {reservation_data if reservation_data else 'None yet'}

CRITICAL RULES:
1. PARTY SIZE: Do not assume party size. If unsure, ask "How many people will be joining?"
2. TIME CONSTRAINTS: Only suggest times within the shop hours listed above.
3. CONTACT INFO: You already have customer contact information. Do not ask for name, email, or phone.
4. AFTER COMPLETION: Start fresh conversations after reservations or cancellations.
5. PROFESSIONALISM: Maintain professional, helpful tone at all times.

EXAMPLE RESPONSES:
- Customer: "I want you to book my reservation"
  Response: "I'd be happy to help. How many people will be joining?"

- Customer: "Book for me and my brother"
  Response: "Understood. For two people then. What date works for you both?"

- Customer: "Cancel my reservation"
  Response: "I can help with that. Do you have your Reservation ID, or should I use your phone or email to find it?"

- Customer suggests time outside hours: "8 PM tomorrow"
  Response: "Our closing time is 7 PM. Would 6 PM work for you instead?"

Customer says: "{user_message}"

Your professional response:"""
        
        return prompt
    
    @staticmethod
    def _analyze_party_size(user_message: str, reservation_data: Optional[Dict[str, Any]]) -> str:
        """Analyze party size context for prompt."""
        user_lower = user_message.lower()
        
        # Check for solo indicators
        solo_indicators = ['alone', 'solo', 'just me', 'only me', 'myself', 'single', 'by myself']
        has_solo = any(indicator in user_lower for indicator in solo_indicators)
        
        # Check for group indicators
        group_indicators = ['brother', 'sister', 'friend', 'friends', 'family', 'together', 'both', 'partner', 'we', 'us']
        has_group = any(indicator in user_lower for indicator in group_indicators)
        
        # Current known party size
        current_party_size = reservation_data.get('party_size') if reservation_data else None
        
        if current_party_size:
            return f"Customer has already specified party size: {current_party_size}"
        elif has_solo:
            return "Customer indicated solo booking (said 'alone', 'just me', etc.). Party size is 1."
        elif has_group:
            return "Customer mentioned others (brother, friend, etc.). Likely 2 or more people."
        else:
            return "Party size not mentioned. Must ask: 'How many people will be joining?'"
    
    @staticmethod
    def build_reservation_summary_prompt(
        reservation_data: Dict[str, Any],
        session_data: Dict[str, Any],
        shop_details: Dict[str, Any]
    ) -> str:
        """Build reservation summary prompt."""
        shop_name = shop_details.get('shop_name', 'Our Shop')
        user_name = session_data.get('user_name', 'Customer')
        user_email = session_data.get('user_email', 'Not provided')
        user_phone = session_data.get('user_phone', 'Not provided')
        
        return f"""Reservation Summary for {shop_name}

Customer Information:
- Name: {user_name}
- Email: {user_email}
- Phone: {user_phone}

Appointment Details:
- Date: {reservation_data.get('date', 'To be confirmed')}
- Time: {reservation_data.get('time', 'To be confirmed')}
- Party Size: {reservation_data.get('party_size', 1)} people

Please reply 'YES' to confirm this reservation, or 'NO' to make changes."""
    
    @staticmethod
    def build_cancellation_prompt(cancellation_type: str, shop_name: str, user_message: str) -> str:
        """Build cancellation prompt."""
        prompts = {
            "ongoing": f"The customer wants to cancel their ongoing reservation process at {shop_name}. Respond professionally and let them know the process has been cancelled.",
            "need_info": f"""The customer wants to cancel a reservation at {shop_name} but didn't provide enough information.
Ask them professionally for one of these:
1. Reservation ID (starts with RES...), OR
2. Phone number, OR
3. Email address
Explain that you need one of these to locate their reservation.""",
            "not_found": f"The customer provided information but no reservation was found at {shop_name}. Inform them professionally and ask them to verify their information or contact the shop directly.",
            "cancellation_error": f"There was an error processing cancellation at {shop_name}. Apologize professionally and suggest they try again or contact the shop directly.",
            "success": f"The reservation was successfully cancelled at {shop_name}. Inform the customer professionally and ask if you can assist with anything else."
        }
        
        return prompts.get(cancellation_type, "Respond professionally to the customer's cancellation request.")