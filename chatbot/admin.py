
# Register your models here.
from django.contrib import admin
from .models import Conversation, Message

@admin.register(Conversation)
class ConversationAdmin(admin.ModelAdmin):
    list_display = ('id', 'business', 'session_id', 'started_at', 'last_activity')
    list_filter = ('business', 'started_at')
    search_fields = ('session_id', 'business__name')

@admin.register(Message)
class MessageAdmin(admin.ModelAdmin):
    list_display = ('id', 'conversation', 'role', 'timestamp')
    list_filter = ('role', 'timestamp')
    search_fields = ('content',)