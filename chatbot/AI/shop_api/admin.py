# shop_api/admin.py
from django.contrib import admin
from .models import ConversationHistory, SessionMetadata, UserFeedback

@admin.register(ConversationHistory)
class ConversationHistoryAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'shop_id', 'timestamp']
    list_filter = ['shop_id', 'message_type']
    search_fields = ['session_id', 'user_message', 'shop_id']
    readonly_fields = ['timestamp']

@admin.register(SessionMetadata)
class SessionMetadataAdmin(admin.ModelAdmin):
    list_display = ['session_id', 'shop_id', 'user_email', 'user_name', 'created_at', 'last_activity', 'message_count']
    list_filter = ['shop_id', 'session_status']
    search_fields = ['session_id', 'shop_id', 'user_email', 'user_name']
    readonly_fields = ['created_at', 'last_activity']

@admin.register(UserFeedback)
class UserFeedbackAdmin(admin.ModelAdmin):
    list_display = ['session', 'rating', 'created_at', 'resolved']
    list_filter = ['rating', 'resolved']
    search_fields = ['session__session_id', 'feedback_text']