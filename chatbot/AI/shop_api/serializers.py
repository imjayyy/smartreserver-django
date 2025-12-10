# shop_api/serializers.py
from rest_framework import serializers
from .models import ConversationHistory, SessionMetadata, UserFeedback

# Model serializers
class ConversationHistorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ConversationHistory
        fields = '__all__'

class SessionMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = SessionMetadata
        fields = '__all__'

class UserFeedbackSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserFeedback
        fields = '__all__'

# Chat request serializer
class ChatRequestSerializer(serializers.Serializer):
    message = serializers.CharField(max_length=1000, required=True)
    session_id = serializers.CharField(required=False, allow_blank=True, default="")
    user_email = serializers.EmailField(required=False, allow_blank=True, default="")
    user_name = serializers.CharField(max_length=100, required=False, allow_blank=True, default="")
    user_phone = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")

    def validate_message(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Message cannot be empty")
        return value.strip()
    
    def validate_user_email(self, value):
        if value == "":
            return None  # Convert empty string to None
        return value
    
    def validate_user_phone(self, value):
        if value == "":
            return None  # Convert empty string to None
        return value

# JSON data serializers (for your JSON files)
class ShopDetailsSerializer(serializers.Serializer):
    shop_id = serializers.CharField(max_length=50)
    shop_name = serializers.CharField(max_length=255)
    address = serializers.CharField()
    phone = serializers.CharField(max_length=20)
    operating_hours = serializers.DictField()
    reservation_policy = serializers.DictField()
    timezone = serializers.CharField()

class ServiceSerializer(serializers.Serializer):
    service_id = serializers.CharField(max_length=50)
    name = serializers.CharField(max_length=255)
    description = serializers.CharField(required=False, allow_blank=True)
    price = serializers.DecimalField(max_digits=10, decimal_places=2)
    currency = serializers.CharField(max_length=10, default='USD')
    duration_minutes = serializers.IntegerField()
    special_offer = serializers.DictField(required=False)

class ServicesSerializer(serializers.Serializer):
    services = ServiceSerializer(many=True)