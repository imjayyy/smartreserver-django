import threading
from datetime import datetime
from typing import Dict, Any, List
import logging

logger = logging.getLogger(__name__)


class ConversationManager:
    """Manages conversation cache and context."""
    
    def __init__(self, max_cache_size: int = 20):
        self.conversation_cache = {}
        self._lock = threading.RLock()
        self.max_cache_size = max_cache_size
    
    def get_conversation_context(self, session_id: str) -> str:
        """Get formatted conversation context for the given session."""
        try:
            with self._lock:
                if session_id not in self.conversation_cache:
                    self.conversation_cache[session_id] = []
                
                context_messages = self.conversation_cache[session_id][-10:]
                
                if not context_messages:
                    try:
                        from ..models import ConversationHistory
                        history = ConversationHistory.objects.filter(
                            session_id=session_id
                        ).order_by('timestamp')[:10]
                        
                        if history:
                            self.conversation_cache[session_id] = []
                            for turn in history:
                                self.conversation_cache[session_id].append({
                                    'role': 'user', 
                                    'content': turn.user_message,
                                    'timestamp': turn.timestamp
                                })
                                self.conversation_cache[session_id].append({
                                    'role': 'assistant', 
                                    'content': turn.assistant_response,
                                    'timestamp': turn.timestamp
                                })
                            context_messages = self.conversation_cache[session_id][-10:]
                    except Exception as e:
                        logger.error(f"Error loading history for context: {e}")
                
                context_lines = []
                for msg in context_messages:
                    if msg['role'] == 'user':
                        context_lines.append(f"Customer: {msg['content']}")
                    else:
                        context_lines.append(f"Assistant: {msg['content']}")
                
                logger.info(f"Using {len(context_lines)//2} previous messages for context")
                return "\n".join(context_lines)
        
        except Exception as e:
            logger.error(f"Error getting conversation context: {e}")
            return ""
    
    def add_to_conversation_cache(self, session_id: str, role: str, content: str):
        """Add a message to the conversation cache."""
        with self._lock:
            if session_id not in self.conversation_cache:
                self.conversation_cache[session_id] = []
            
            self.conversation_cache[session_id].append({
                'role': role,
                'content': content,
                'timestamp': datetime.now()
            })
            
            # Limit cache size
            if len(self.conversation_cache[session_id]) > self.max_cache_size:
                self.conversation_cache[session_id] = self.conversation_cache[session_id][-self.max_cache_size:]
    
    def clear_conversation_cache(self, session_id: str):
        """Clear the conversation cache for a fresh start."""
        with self._lock:
            if session_id in self.conversation_cache:
                # Keep only the last message for context
                if len(self.conversation_cache[session_id]) > 1:
                    self.conversation_cache[session_id] = self.conversation_cache[session_id][-1:]
                else:
                    self.conversation_cache[session_id] = []
    
    def reset_conversation_context(self, session_id: str):
        """Reset conversation context for fresh interaction."""
        self.clear_conversation_cache(session_id)
        # Add a fresh greeting
        fresh_greeting = 'How can I help you today?'
        self.add_to_conversation_cache(session_id, 'assistant', fresh_greeting)