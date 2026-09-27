from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Company, KBEntry, QueryLog


class RegisterSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150, required=True)
    password = serializers.CharField(write_only=True, required=True)
    company_name = serializers.CharField(max_length=255, required=True)
    email = serializers.EmailField(required=True)

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A company with this username already exists.")
        return value


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True)


class KBEntrySerializer(serializers.ModelSerializer):
    class Meta:
        model = KBEntry
        fields = ['id', 'question', 'answer', 'category']


class KBSearchSerializer(serializers.Serializer):
    search = serializers.CharField(required=True, allow_blank=False, trim_whitespace=True)

    def validate_search(self, value):
        if not value or not value.strip():
            raise serializers.ValidationError("Search field cannot be empty or blank.")
        return value.strip()
