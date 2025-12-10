import threading
import logging
from typing import Dict, Any
from django.conf import settings
from .response_handler import ResponseHandler
from .reservation_handler import ReservationHandler
from .cancellation_handler import CancellationHandler
from .conversation_manager import ConversationManager
from ..validation.security_system import SecurityValidationSystem
from .utils import clean_ai_response

logger = logging.getLogger(__name__)


class UniversalShopAgent:
    """Main agent class coordinating all components."""
    
    def __init__(self, data_manager, session_manager=None):
        self.data_manager = data_manager
        self.session_manager = session_manager
        self.validation_system = None  # Will be imported lazily
        self._session_lock = threading.RLock()
        
        # Initialize components
        self.conversation_manager = ConversationManager()
        self.response_handler = ResponseHandler(self._init_openai_client())
        self.reservation_handler = None  # Will be initialized after validation_system
        self.cancellation_handler = CancellationHandler(data_manager, session_manager)
        
        # Lazy import validation_system to avoid circular imports
        from ..validation.security_system import SecurityValidationSystem
        self.validation_system = SecurityValidationSystem()
        self.reservation_handler = ReservationHandler(data_manager, self.validation_system, session_manager)
    
    def _init_openai_client(self):
        """Initialize OpenAI client with new settings."""
        try:
            import openai
            return openai.OpenAI(
                api_key=settings.LLMCALLKEY,  # Updated variable name
                base_url=settings.LLM_URL,     # Updated variable name
                timeout=30.0
            )
        except Exception as e:
            logger.error(f"OpenAI client initialization failed: {e}")
            return None
    
    def handle_shop_request(
        self,
        user_message: str,
        shop_id: str,
        session_id: str = None,
        user_agent: str = None,
        ip_address: str = None,
        user_email: str = None,
        user_name: str = None,
        user_phone: str = None
    ) -> Dict[str, Any]:
        """Main entry point for handling shop requests."""
        logger.info(f"New request: {user_message}")
        
        with self._session_lock:
            try:
                # Get or create session
                session = self.session_manager.get_session(
                    session_id, shop_id, user_agent, ip_address,
                    user_email, user_name, user_phone
                )
                
                logger.info(f"Session data: {session.get('user_name')} | {session.get('user_phone')}")
                
                # Add to conversation cache
                self.conversation_manager.add_to_conversation_cache(session_id, 'user', user_message)
                
                # Check for cancellation
                if self._is_cancellation_request(user_message):
                    return self.cancellation_handler.handle_cancellation(
                        shop_id, session_id, user_message, session,
                        self.conversation_manager, self.response_handler
                    )
                
                # Get current reservation state
                reservation_state, reservation_data = self.session_manager.get_reservation_state(session_id)
                
                # Extract data from user message
                extracted_data = self.validation_system.extract_reservation_data(user_message)
                logger.info(f"Extracted data: {extracted_data}")
                
                # Update reservation data
                if extracted_data:
                    if reservation_data:
                        reservation_data.update(extracted_data)
                    else:
                        reservation_data = extracted_data
                    
                    self.session_manager.set_reservation_state(session_id, "collecting_info", reservation_data)
                
                # Check if all required data is collected
                required_fields = ['date', 'time', 'party_size']
                has_all_data = all(reservation_data.get(field) for field in required_fields) if reservation_data else False
                
                # If all data collected and user confirms, move to confirmation
                if has_all_data and reservation_state == "collecting_info":
                    user_lower = user_message.lower()
                    confirmation_words = ['yes', 'confirm', 'ok', 'okay', 'sure', 'yep', 'yeah', 'go ahead', 'please do', 'book it', 'reserve']
                    
                    if any(word in user_lower for word in confirmation_words):
                        logger.info("User confirmed - Moving to confirmation...")
                        
                        shop_context = self.data_manager.load_shop_context(shop_id)
                        shop_details = shop_context['shop_details']
                        
                        # Prepare final reservation data
                        final_reservation_data = {
                            **reservation_data,
                            'customer_name': session.get('user_name', 'Customer'),
                            'email': session.get('user_email', ''),
                            'phone_number': session.get('user_phone', '')
                        }
                        
                        # Set as pending reservation
                        self.session_manager.set_pending_reservation(session_id, final_reservation_data)
                        self.session_manager.set_reservation_state(session_id, "awaiting_confirmation")
                        
                        # Generate summary
                        response = self.reservation_handler.generate_reservation_summary(
                            final_reservation_data, session, shop_details
                        )
                        
                        self.conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                        self.session_manager.update_conversation(session_id, user_message, response, "reservation")
                        
                        return {
                            "response": response,
                            "shop_id": shop_id,
                            "shop_name": shop_details.get('shop_name', 'Our Shop'),
                            "success": True,
                            "session_id": session_id,
                            "needs_confirmation": True
                        }
                
                # Handle confirmation response
                if reservation_state == "awaiting_confirmation":
                    logger.info("Processing confirmation response...")
                    return self.reservation_handler.process_reservation_confirmation(
                        user_message, shop_id, session_id, session,
                        self.conversation_manager, self.response_handler
                    )
                
                # Load shop context for AI response
                shop_context = self.data_manager.load_shop_context(shop_id)
                shop_details = shop_context['shop_details']
                services = shop_context['services']
                
                # Get conversation context
                conversation_context = self.conversation_manager.get_conversation_context(session_id)
                
                # Generate AI response
                response = self.response_handler.generate_ai_response(
                    user_message=user_message,
                    shop_details=shop_details,
                    services=services,
                    reservation_state=reservation_state,
                    reservation_data=reservation_data,
                    conversation_context=conversation_context,
                    session_data=session
                )
                
                logger.info(f"AI response: {response[:100]}...")
                
                # Save conversation
                self.conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                self.session_manager.update_conversation(session_id, user_message, response, "normal")
                
                # Return response
                return {
                    "response": response,
                    "shop_id": shop_id,
                    "shop_name": shop_details.get('shop_name', 'Our Shop'),
                    "success": True,
                    "session_id": session_id,
                    "agents_used": ["conversation"],
                    "model": "mistral-7b-instruct"
                }
            
            except Exception as e:
                logger.error(f"Error handling shop request: {e}", exc_info=True)
                emergency_response = self._generate_emergency_response(user_message, shop_id)
                self.conversation_manager.add_to_conversation_cache(session_id, 'assistant', emergency_response['response'])
                return emergency_response
    
    def _is_cancellation_request(self, user_message: str) -> bool:
        """Check if the message is a cancellation request."""
        cancellation_words = ['cancel', 'stop', 'nevermind', 'never mind', 'leave it', 
                            "don't want", 'cancel reservation', 'cancel booking', 'delete reservation']
        user_lower = user_message.lower().strip()
        return any(word in user_lower for word in cancellation_words)
    
    def _generate_emergency_response(self, user_message: str, shop_id: str) -> Dict[str, Any]:
        """Generate emergency response when something goes wrong."""
        try:
            shop_context = self.data_manager.load_shop_context(shop_id)
            shop_name = shop_context['shop_details'].get('shop_name', 'Our Shop')
        except:
            shop_name = "Our Shop"
        
        response = "I'm here to help. What can I assist you with today?"
        return {
            "response": response,
            "shop_id": shop_id,
            "shop_name": shop_name,
            "success": False,
            "session_id": "emergency-session",
            "agents_used": ["emergency_fallback"]
        }