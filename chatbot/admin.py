from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'session_id', 'started_at', 'last_activity')
    list_filter = ('business',)
    search_fields = ('session_id',)

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'timestamp')
    list_filter = ('role',)
    search_fields = ('content',)
    readonly_fields = ('timestamp',)