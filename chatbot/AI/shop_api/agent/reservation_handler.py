import logging
from datetime import datetime
from typing import Dict, Any
from django.conf import settings
from .prompt_builder import PromptBuilder
from .utils import format_operating_hours

logger = logging.getLogger(__name__)


class ReservationHandler:
    """Handles reservation confirmation and processing."""
    
    def __init__(self, data_manager, validation_system, session_manager):
        self.data_manager = data_manager
        self.validation_system = validation_system
        self.session_manager = session_manager
    
    def process_reservation_confirmation(
        self,
        user_message: str,
        shop_id: str,
        session_id: str,
        session_data: Dict[str, Any],
        conversation_manager,
        response_handler
    ) -> Dict[str, Any]:
        """Process reservation confirmation with shop hours validation."""
        try:
            shop_context = self.data_manager.load_shop_context(shop_id)
            shop_details = shop_context['shop_details']
            shop_hours = shop_details.get('operating_hours', {})
            
            pending_reservation = self.session_manager.get_pending_reservation(session_id)
            
            if not pending_reservation:
                response = "I don't see a pending reservation. Let's start over."
                conversation_manager.clear_conversation_cache(session_id)
                conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                self.session_manager.update_conversation(session_id, user_message, response, "reservation")
                return {
                    "response": response,
                    "shop_id": shop_id,
                    "shop_name": shop_details.get('shop_name', 'Our Shop'),
                    "success": False,
                    "session_id": session_id
                }
            
            user_lower = user_message.lower()
            
            if any(word in user_lower for word in ['yes', 'yep', 'confirm', 'yeah', 'sure', 'ok', 'okay', 'please']):
                logger.info("User confirmed - Saving reservation to database...")
                
                # Check shop hours
                if shop_hours and 'date' in pending_reservation and 'time' in pending_reservation:
                    try:
                        date_str = pending_reservation['date']
                        time_str = pending_reservation['time']
                        datetime_str = f"{date_str} {time_str}"
                        requested_dt = datetime.strptime(datetime_str, "%Y-%m-%d %H:%M")
                        
                        day_of_week = requested_dt.strftime('%A').lower()
                        hours_for_day = shop_hours.get(day_of_week, '')
                        
                        if hours_for_day:
                            is_valid, message = self.validation_system._check_within_shop_hours(requested_dt, hours_for_day)
                            if not is_valid:
                                date_obj = datetime.strptime(date_str, "%Y-%m-%d")
                                day_name = date_obj.strftime('%A')
                                shop_hours_for_day = shop_hours.get(day_of_week, 'Not available')
                                response = f"I'm sorry, but {message}. Our hours for {day_name} are: {shop_hours_for_day}. Would you like to choose a different time?"
                                conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                                self.session_manager.update_conversation(session_id, user_message, response, "reservation_error")
                                return {
                                    "response": response,
                                    "shop_id": shop_id,
                                    "shop_name": shop_details.get('shop_name', 'Our Shop'),
                                    "success": False,
                                    "session_id": session_id
                                }
                    except Exception as e:
                        logger.error(f"Error checking shop hours: {e}")
                
                # Check availability
                if not self.data_manager.check_availability(shop_id, pending_reservation.get('date'), pending_reservation.get('time')):
                    response = "That time slot is no longer available. Would you like to try a different time?"
                    self.session_manager.clear_reservation_state(session_id)
                    conversation_manager.clear_conversation_cache(session_id)
                    conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                    self.session_manager.update_conversation(session_id, user_message, response, "reservation_error")
                    return {
                        "response": response,
                        "shop_id": shop_id,
                        "shop_name": shop_details.get('shop_name', 'Our Shop'),
                        "success": False,
                        "session_id": session_id
                    }
                
                # Ensure we have user info
                if not pending_reservation.get('phone_number') and session_data.get('user_phone'):
                    pending_reservation['phone_number'] = session_data.get('user_phone')
                if not pending_reservation.get('customer_name') and session_data.get('user_name'):
                    pending_reservation['customer_name'] = session_data.get('user_name', 'Customer')
                if not pending_reservation.get('email') and session_data.get('user_email'):
                    pending_reservation['email'] = session_data.get('user_email', '')
                
                # Save reservation
                save_result = self.data_manager.save_reservation(shop_id, pending_reservation)
                logger.info(f"Database save result: {save_result}")
                
                if save_result['success']:
                    response = f"""RESERVATION CONFIRMED

Your appointment has been booked successfully.

Reservation ID: {save_result['reservation_id']}
Date: {pending_reservation.get('date', 'To be confirmed')}
Time: {pending_reservation.get('time', 'To be confirmed')}
Party Size: {pending_reservation.get('party_size', 1)} people

Please save your Reservation ID: {save_result['reservation_id']} for any changes or cancellations.

We look forward to seeing you."""
                    
                    self.session_manager.clear_reservation_state(session_id)
                    conversation_manager.clear_conversation_cache(session_id)
                    conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                    self.session_manager.update_conversation(session_id, user_message, response, "reservation_confirmed")
                    
                    # Start fresh for next interaction
                    conversation_manager.reset_conversation_context(session_id)
                    
                    return {
                        "response": response,
                        "shop_id": shop_id,
                        "shop_name": shop_details.get('shop_name', 'Our Shop'),
                        "success": True,
                        "session_id": session_id,
                        "agents_used": ["reservation"],
                        "reservation_id": save_result['reservation_id']
                    }
                else:
                    response = "Sorry, we encountered an error while saving your reservation. Please try again."
                    self.session_manager.clear_reservation_state(session_id)
                    conversation_manager.clear_conversation_cache(session_id)
                    conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                    self.session_manager.update_conversation(session_id, user_message, response, "reservation_error")
                    return {
                        "response": response,
                        "shop_id": shop_id,
                        "shop_name": shop_details.get('shop_name', 'Our Shop'),
                        "success": False,
                        "session_id": session_id
                    }
            else:
                response = "No problem. Let me know if you'd like to change anything or start over."
                self.session_manager.clear_reservation_state(session_id)
                conversation_manager.clear_conversation_cache(session_id)
                conversation_manager.add_to_conversation_cache(session_id, 'assistant', response)
                self.session_manager.update_conversation(session_id, user_message, response, "reservation_cancelled")
                
                # Start fresh
                conversation_manager.reset_conversation_context(session_id)
                
                return {
                    "response": response,
                    "shop_id": shop_id,
                    "shop_name": shop_details.get('shop_name', 'Our Shop'),
                    "success": True,
                    "session_id": session_id
                }
        
        except Exception as e:
            logger.error(f"Error processing reservation confirmation: {e}")
            self.session_manager.clear_reservation_state(session_id)
            conversation_manager.clear_conversation_cache(session_id)
            raise
    
    def generate_reservation_summary(
        self,
        reservation_data: Dict[str, Any],
        session_data: Dict[str, Any],
        shop_details: Dict[str, Any]
    ) -> str:
        """Generate reservation summary using PromptBuilder."""
        return PromptBuilder.build_reservation_summary_prompt(
            reservation_data=reservation_data,
            session_data=session_data,
            shop_details=shop_details
        )