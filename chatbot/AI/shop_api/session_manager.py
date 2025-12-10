# shop_api/session_manager.py
import time
import logging
from datetime import datetime, timedelta
from threading import Lock
import threading
from .models import SessionMetadata, ConversationHistory
import uuid

logger = logging.getLogger(__name__)

class EnhancedSessionManager:
    def __init__(self, session_timeout_minutes: int = 60):
        self.sessions = {}
        self.session_timeout = timedelta(minutes=session_timeout_minutes)
        self._lock = Lock()
        self._session_locks = {}
        self._cleanup_lock = threading.RLock()
        logger.info("Enhanced Session Manager Initialized")
    
    def get_session(self, session_id, shop_id, user_agent=None, ip_address=None, 
                user_email=None, user_name=None, user_phone=None):
        self._cleanup_expired_sessions()
    
        with self._lock:
            if session_id not in self.sessions:
                try:
                # Try to load from database
                    db_session = SessionMetadata.objects.get(session_id=session_id)
                    self.sessions[session_id] = {
                    'shop_id': db_session.shop_id,
                    'conversation_history': [],
                    'user_preferences': db_session.user_preferences,
                    'created_at': db_session.created_at,
                    'last_activity': db_session.last_activity,
                    'message_count': db_session.message_count,
                    'reservation_state': db_session.reservation_state,
                    'reservation_data': db_session.reservation_data,
                    'pending_reservation': db_session.pending_reservation,
                    'user_email': user_email or db_session.user_email,
                    'user_name': user_name or db_session.user_name,
                    'user_phone': user_phone or db_session.user_phone
                    }
                except SessionMetadata.DoesNotExist:
                # Create new session
                    db_session = SessionMetadata.objects.create(
                        session_id=session_id,
                        shop_id=shop_id,
                        user_agent=user_agent,
                        ip_address=ip_address,
                        user_preferences={}
                    )

                    self.sessions[session_id] = {
                        'shop_id': shop_id,
                        'conversation_history': [],
                        'user_preferences': {},
                        'created_at': datetime.now(),
                        'last_activity': datetime.now(),
                        'message_count': 0,
                        'reservation_state': None,
                        'reservation_data': {},
                        'pending_reservation': None,
                        'user_email': user_email,
                        'user_name': user_name,
                        'user_phone': user_phone
                    }
                except Exception as e:
                    # If database error (table doesn't exist), use in-memory session
                    logger.warning(f"Database error, using in-memory session: {e}")
                    self.sessions[session_id] = {
                    'shop_id': shop_id,
                    'conversation_history': [],
                    'user_preferences': {},
                    'created_at': datetime.now(),
                    'last_activity': datetime.now(),
                    'message_count': 0,
                    'reservation_state': None,
                    'reservation_data': {},
                    'pending_reservation': None,
                    'user_email': user_email,
                    'user_name': user_name,
                    'user_phone': user_phone
                    }
            else:
                self.sessions[session_id]['last_activity'] = datetime.now()
                self.sessions[session_id]['message_count'] += 1
                if user_email:
                    self.sessions[session_id]['user_email'] = user_email
                if user_name:
                    self.sessions[session_id]['user_name'] = user_name
                if user_phone:
                    self.sessions[session_id]['user_phone'] = user_phone

            return self.sessions[session_id].copy()
    
    def update_conversation(self, session_id, user_message, assistant_response, message_type="normal"):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            session['last_activity'] = datetime.now()
            
            # Save to database
            try:
                ConversationHistory.objects.create(
                    session_id=session_id,
                    shop_id=session['shop_id'],  # Use shop_id directly
                    user_message=user_message[:4000],
                    assistant_response=assistant_response[:4000],
                    message_type=message_type,
                    metadata={'agents_used': ['conversation']}
                )
                
                # Update session metadata
                db_session = SessionMetadata.objects.get(session_id=session_id)
                db_session.last_activity = datetime.now()
                db_session.message_count += 1
                if 'user_email' in session:
                    db_session.user_email = session['user_email']
                if 'user_name' in session:
                    db_session.user_name = session['user_name']
                if 'user_phone' in session:
                    db_session.user_phone = session['user_phone']
                db_session.save()
                
            except Exception as e:
                logger.error(f"Error saving conversation to database: {e}")
    
    def set_reservation_state(self, session_id, state, data=None):
        if session_id in self.sessions:
            self.sessions[session_id]['reservation_state'] = state
            if data:
                # Update existing data
                self.sessions[session_id]['reservation_data'].update(data)
            
            # Update database
            try:
                db_session = SessionMetadata.objects.get(session_id=session_id)
                db_session.reservation_state = state
                db_session.reservation_data = self.sessions[session_id]['reservation_data']
                db_session.save()
            except Exception as e:
                logger.error(f"Error updating reservation state in database: {e}")
    
    def get_reservation_state(self, session_id):
        if session_id in self.sessions:
            session = self.sessions[session_id]
            return session['reservation_state'], session['reservation_data'].copy()
        return None, {}
    
    def clear_reservation_state(self, session_id):
        if session_id in self.sessions:
            self.sessions[session_id]['reservation_state'] = None
            self.sessions[session_id]['reservation_data'] = {}
            self.sessions[session_id]['pending_reservation'] = None
            
            # Update database
            try:
                db_session = SessionMetadata.objects.get(session_id=session_id)
                db_session.reservation_state = None
                db_session.reservation_data = {}
                db_session.pending_reservation = None
                db_session.save()
            except Exception as e:
                logger.error(f"Error clearing reservation state in database: {e}")
    
    def set_pending_reservation(self, session_id, reservation_data):
        if session_id in self.sessions:
            self.sessions[session_id]['pending_reservation'] = reservation_data
            
            # Update database
            try:
                db_session = SessionMetadata.objects.get(session_id=session_id)
                db_session.pending_reservation = reservation_data
                db_session.save()
            except Exception as e:
                logger.error(f"Error setting pending reservation in database: {e}")
    
    def get_pending_reservation(self, session_id):
        if session_id in self.sessions:
            return self.sessions[session_id].get('pending_reservation')
        return None
    
    def _cleanup_expired_sessions(self):
        current_time = datetime.now()
        expired_sessions = []
        
        with self._lock:
            for session_id, session_data in list(self.sessions.items()):
                if current_time - session_data['last_activity'] > self.session_timeout:
                    expired_sessions.append(session_id)
            
            for session_id in expired_sessions:
                del self.sessions[session_id]