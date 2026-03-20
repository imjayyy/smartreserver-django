from django.core.cache import cache

class SessionMemory:
    def __init__(self, session_id, ttl=3600):
        self.session_id = session_id
        self.ttl = ttl

    def _key(self, suffix):
        return f"chat:{self.session_id}:{suffix}"

    def get_history(self):
        history = cache.get(self._key('history'), [])
        # Keep last 10 messages to avoid token limits
        return history[-10:]

    def add_message(self, role, content):
        history = self.get_history()
        history.append({"role": role, "content": content})
        cache.set(self._key('history'), history, self.ttl)

    def set_user_info(self, user_data):
        cache.set(self._key('user'), user_data, self.ttl)

    def get_user_info(self):
        return cache.get(self._key('user'), {})

    def set_last_reservation_id(self, reservation_id):
        cache.set(self._key('last_reservation'), reservation_id, self.ttl)

    def get_last_reservation_id(self):
        return cache.get(self._key('last_reservation'))

    def clear(self):
        cache.delete(self._key('history'))
        cache.delete(self._key('user'))
        cache.delete(self._key('last_reservation'))