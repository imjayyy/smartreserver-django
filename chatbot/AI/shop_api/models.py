# shop_api/models.py
from django.db import models
import json

class ConversationHistory(models.Model):
    session_id = models.CharField(max_length=100)
    shop_id = models.CharField(max_length=50)  # Changed from ForeignKey to CharField
    user_message = models.TextField()
    assistant_response = models.TextField()
    message_type = models.CharField(max_length=50, default='normal')
    metadata = models.JSONField(default=dict)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['session_id']),
            models.Index(fields=['shop_id']),
            models.Index(fields=['timestamp']),
        ]
    
    def __str__(self):
        return f"{self.session_id} - {self.timestamp}"

class SessionMetadata(models.Model):
    session_id = models.CharField(max_length=100, primary_key=True)
    shop_id = models.CharField(max_length=50)  # Changed from ForeignKey to CharField
    user_agent = models.TextField(blank=True, null=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_preferences = models.JSONField(default=dict)
    user_email = models.EmailField(blank=True, null=True)
    user_name = models.CharField(max_length=100, blank=True, null=True)
    user_phone = models.CharField(max_length=20, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    last_activity = models.DateTimeField(auto_now=True)
    message_count = models.IntegerField(default=0)
    session_status = models.CharField(max_length=20, default='active')
    reservation_state = models.CharField(max_length=50, blank=True, null=True)
    reservation_data = models.JSONField(default=dict)
    pending_reservation = models.JSONField(default=dict, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['shop_id']),
            models.Index(fields=['created_at']),
            models.Index(fields=['user_email']),
        ]
    
    def __str__(self):
        return f"{self.session_id} - {self.shop_id}"

class UserFeedback(models.Model):
    session = models.ForeignKey(SessionMetadata, on_delete=models.CASCADE)
    rating = models.IntegerField()
    feedback_text = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    resolved = models.BooleanField(default=False)

    def __str__(self):
        return f"Rating: {self.rating} - Session: {self.session.session_id}"