from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PetReport, Profile
class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)
    phone_number = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'phone_number']

    #check if email is already in use

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Email is already in use")
        return value



    def create(self, validated_data):
        phone_number = validated_data.pop('phone_number')
        user = User.objects.create_user(**validated_data)
        Profile.objects.create(user=user, phone_number=phone_number)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

#Pet Report Serializer
class PetReportSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    class Meta:
        model = PetReport
        fields = ['id', 'author', 'type', 'name', 'breed', 'color', 'location', 'contact_info', 'description', 'image', 'report_type', 'status', 'created_at']
