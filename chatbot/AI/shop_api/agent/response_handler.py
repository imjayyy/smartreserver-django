import logging
from typing import Dict, Any
from django.conf import settings
from .prompt_builder import PromptBuilder
from .utils import clean_ai_response

logger = logging.getLogger(__name__)


class ResponseHandler:
    """Handles AI response generation and fallback."""
    
    def __init__(self, openai_client):
        self.openai_client = openai_client
    
    def generate_ai_response(
        self,
        user_message: str,
        shop_details: Dict[str, Any],
        services: Dict[str, Any],
        reservation_state: str = None,
        reservation_data: Dict[str, Any] = None,
        conversation_context: str = "",
        session_data: Dict[str, Any] = None
    ) -> str:
        """Generate AI response using the prompt builder."""
        try:
            if not self.openai_client:
                return self._generate_context_aware_fallback(user_message, shop_details, services, conversation_context)
            
            prompt = PromptBuilder.build_chat_prompt(
                user_message=user_message,
                shop_details=shop_details,
                services=services,
                reservation_state=reservation_state,
                reservation_data=reservation_data,
                conversation_context=conversation_context,
                session_data=session_data
            )
            
            try:
                response = self.openai_client.chat.completions.create(
                    model=settings.AI_MODEL,
                    messages=[
                        {"role": "system", "content": "You are a professional shop assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=300,
                    stop=None
                )
                
                response_text = response.choices[0].message.content.strip()
                response_text = clean_ai_response(response_text)
                
                logger.info(f"AI Response length: {len(response_text)} characters")
                
                if not response_text or len(response_text) < 10:
                    logger.warning(f"AI response too short: '{response_text}'")
                    return self._generate_context_aware_fallback(user_message, shop_details, services, conversation_context)
                
                return response_text
            
            except Exception as api_error:
                logger.error(f"OpenAI API error: {api_error}")
                return self._generate_context_aware_fallback(user_message, shop_details, services, conversation_context)
            
        except Exception as e:
            logger.error(f"Error generating AI response: {e}")
            return self._generate_context_aware_fallback(user_message, shop_details, services, conversation_context)
    
    def _generate_context_aware_fallback(self, user_message: str, shop_details: dict, services: dict, conversation_context: str) -> str:
        """Generate fallback response when AI service is unavailable."""
        try:
            shop_name = shop_details.get('shop_name', 'Our Shop')
            user_lower = user_message.lower()
            
            if "haircut" in user_lower or "hair cut" in user_lower:
                services_list = services.get('services', [])
                haircut_services = [s for s in services_list if 'hair' in s.get('name', '').lower()]
                
                if haircut_services:
                    price_list = "\n".join([f"- {s.get('name')}: ${s.get('price', 0):.2f}" 
                                          for s in haircut_services[:3]])
                    return f"At {shop_name}, we offer these haircut services:\n{price_list}\n\nHow many people will be joining?"
                else:
                    return f"We offer haircut services at {shop_name}. How many people will be joining?"
            
            elif "book" in user_lower or "reserve" in user_lower or "appointment" in user_lower:
                return f"I'd be happy to help you make a reservation at {shop_name}. How many people will be joining?"
            
            elif "price" in user_lower or "cost" in user_lower or "rate" in user_lower or "how much" in user_lower:
                services_list = services.get('services', [])
                if services_list:
                    price_list = "\n".join([f"- {s.get('name', 'Service')}: ${s.get('price', 0):.2f}" 
                                          for s in services_list[:3]])
                    return f"Here are our rates at {shop_name}:\n{price_list}\n\nWhich service interests you?"
                else:
                    return f"I'd be happy to share our rates. What service are you interested in?"
            
            elif "time" in user_lower or "hour" in user_lower or "open" in user_lower:
                from .utils import format_operating_hours
                operating_hours = format_operating_hours(shop_details.get('operating_hours', {}))
                return f"Our hours at {shop_name} are:\n{operating_hours}\n\nHow many people will be joining?"
            
            elif "service" in user_lower or "offer" in user_lower or "do you" in user_lower:
                services_list = services.get('services', [])
                if services_list:
                    service_names = "\n".join([f"- {s.get('name', 'Service')}" for s in services_list[:5]])
                    return f"At {shop_name}, we offer:\n{service_names}\n\nWhat would you like to know more about?"
                else:
                    return f"We offer various services at {shop_name}. What specifically are you looking for?"
            
            elif "hello" in user_lower or "hi" in user_lower or "hey" in user_lower:
                return f"Hello. Welcome to {shop_name}. How can I assist you today?"
            
            else:
                return f"I'd love to help you with that at {shop_name}. Could you tell me a bit more about what you're looking for?"
        
        except Exception as e:
            logger.error(f"Context-aware fallback error: {e}")
            return f"I'm here to help. What can I assist you with today at {shop_details.get('shop_name', 'our shop')}?"