import logging
from typing import Dict, Any, Optional
from .utils import extract_reservation_id, extract_phone_number, extract_email

logger = logging.getLogger(__name__)


class CancellationHandler:
    """Handles reservation cancellations with multiple search methods."""
    
    def __init__(self, data_manager, session_manager):
        self.data_manager = data_manager
        self.session_manager = session_manager
    
    def handle_cancellation(
        self,
        shop_id: str,
        session_id: str,
        user_message: str,
        session_data: Dict[str, Any],
        conversation_manager,
        response_handler
    ) -> Dict[str, Any]:
        """Handle cancellation request."""
        try:
            reservation_state, reservation_data = self.session_manager.get_reservation_state(session_id)
            
            if reservation_state:
                return self.cancel_ongoing_reservation(shop_id, session_id, conversation_manager)
            else:
                return self.cancel_existing_reservation_enhanced(
                    shop_id, session_id, user_message, session_data, conversation_manager
                )
        
        except Exception as e:
            logger.error(f"Error handling cancellation: {e}")
            response = "Okay, I've stopped what we were doing. How can I help you now?"
            conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
            return {
                "response": response,
                "shop_id": shop_id,
                "shop_name": "Our Shop",
                "success": True,
                "session_id": session_id
            }
    
    def cancel_ongoing_reservation(self, shop_id: str, session_id: str, conversation_manager) -> Dict[str, Any]:
        """Cancel an ongoing reservation process."""
        self.session_manager.clear_reservation_state(session_id)
        shop_context = self.data_manager.load_shop_context(shop_id)
        shop_name = shop_context['shop_details'].get('shop_name', 'Our Shop')
        
        response = "I've cancelled your ongoing reservation process. Let me know if you'd like to start over."
        conversation_manager.clear_conversation_cache(session_id)
        conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
        
        self.session_manager.update_conversation(session_id, "User: Cancellation request", response, "cancellation")
        
        return {
            "response": response,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "success": True,
            "session_id": session_id,
            "agents_used": ["cancellation_handler"]
        }
    
    def cancel_existing_reservation_enhanced(
        self,
        shop_id: str,
        session_id: str,
        user_message: str,
        session_data: Dict[str, Any],
        conversation_manager
    ) -> Dict[str, Any]:
        """Enhanced cancellation that searches by multiple methods."""
        try:
            # Extract possible identifiers
            reservation_id = extract_reservation_id(user_message)
            phone_number = extract_phone_number(user_message)
            email = extract_email(user_message)
            
            logger.info(f"Cancellation search - Reservation ID: {reservation_id}, Phone: {phone_number}, Email: {email}")
            
            # If no identifiers in message, check session data
            if not any([reservation_id, phone_number, email]):
                if session_data.get('user_phone'):
                    phone_number = session_data.get('user_phone')
                    logger.info(f"Using phone from session: {phone_number}")
                elif session_data.get('user_email'):
                    email = session_data.get('user_email')
                    logger.info(f"Using email from session: {email}")
            
            # If still no identifiers, ask for them
            if not any([reservation_id, phone_number, email]):
                response = """I need some information to find your reservation. Please provide:
1. Your Reservation ID (starts with RES...), OR
2. Your phone number, OR
3. Your email address

Which would you like to use?"""
                
                conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                self.session_manager.update_conversation(session_id, user_message, response, "cancellation")
                return {
                    "response": response,
                    "shop_id": shop_id,
                    "shop_name": "Our Shop",
                    "success": True,
                    "session_id": session_id,
                    "needs_more_info": True
                }
            
            # Try to cancel with available info
            result = self.data_manager.cancel_reservation_enhanced(
                shop_id, reservation_id, phone_number, email
            )
            
            logger.info(f"Cancellation result: {result}")
            
            if result['success']:
                response = f"""CANCELLATION SUCCESSFUL

Your reservation has been cancelled:

Reservation ID: {result['reservation_id']}
Name: {result.get('customer_name', 'Customer')}
Date: {result.get('date', 'Not specified')}
Time: {result.get('time', 'Not specified')}

We hope to see you another time."""
                
                # Clear any session reservation state
                self.session_manager.clear_reservation_state(session_id)
                conversation_manager.clear_conversation_cache(session_id)
            
            else:
                search_method = ""
                if reservation_id:
                    search_method = f"Reservation ID: {reservation_id}"
                elif phone_number:
                    search_method = f"phone number: {phone_number}"
                elif email:
                    search_method = f"email: {email}"
                
                response = f"""RESERVATION NOT FOUND

I couldn't find an active reservation with the {search_method}.

Please check your information and try again, or contact the shop directly."""
            
            conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
            self.session_manager.update_conversation(session_id, user_message, response, "cancellation")
            return {
                "response": response,
                "shop_id": shop_id,
                "shop_name": "Our Shop",
                "success": result.get('success', False),
                "session_id": session_id
            }
        
        except Exception as e:
            logger.error(f"Error cancelling existing reservation: {e}")
            response = "Sorry, there was an error processing your cancellation. Please try again or contact the shop directly."
            conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
            self.session_manager.update_conversation(session_id, user_message, response, "cancellation_error")
            return {
                "response": response,
                "shop_id": shop_id,
                "shop_name": "Our Shop",
                "success": False,
                "session_id": session_id
            }