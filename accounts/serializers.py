from rest_framework import serializers
from django.contrib.auth.models import User
from .models import PetReport, Profile, Pet, ClaimRequest, ClaimMessage, Notification
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


class PetSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pet
        fields = [
            'id',
            'name',
            'species',
            'breed',
            'age',
            'color',
            'gender',
            'weight',
            'chip',
            'notes',
            'emoji',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']


#Pet Report Serializer
class PetReportSerializer(serializers.ModelSerializer):
    author = serializers.ReadOnlyField(source='author.username')
    reviewed_by = serializers.ReadOnlyField(source='reviewed_by.username')
    like_count = serializers.SerializerMethodField()
    liked_by_me = serializers.SerializerMethodField()

    class Meta:
        model = PetReport
        fields = [
            'id',
            'author',
            'type',
            'name',
            'breed',
            'color',
            'location',
            'contact_info',
            'description',
            'image',
            'report_type',
            'status',
            'admin_note',
            'reviewed_by',
            'reviewed_at',
            'like_count',
            'liked_by_me',
            'created_at',
        ]
        extra_kwargs = {
            'type': {'required': False, 'allow_blank': True},
            'location': {'required': False, 'allow_blank': True},
            'contact_info': {'required': False, 'allow_blank': True},
            'name': {'required': False, 'allow_null': True, 'allow_blank': True},
            'breed': {'required': False, 'allow_blank': True},
            'color': {'required': False, 'allow_blank': True},
            'description': {'required': False, 'allow_blank': True},
            'image': {'required': False, 'allow_null': True},
            'admin_note': {'required': False, 'allow_blank': True},
        }

    def validate(self, attrs):
        report_type = attrs.get('report_type')
        location = attrs.get('location', '')
        contact_info = attrs.get('contact_info', '')
        pet_type = attrs.get('type', '')

        if report_type in ['lost', 'found']:
            if not location.strip():
                raise serializers.ValidationError({'location': 'Location is required for lost/found reports.'})
            if not contact_info.strip():
                raise serializers.ValidationError({'contact_info': 'Contact info is required for lost/found reports.'})

        if not pet_type.strip():
            attrs['type'] = 'Pet'

        if report_type in ['text', 'photo']:
            if not location.strip():
                attrs['location'] = 'Community Feed'
            if not contact_info.strip():
                attrs['contact_info'] = 'Not provided'

        return attrs

    def get_like_count(self, obj):
        return obj.likes.count()

    def get_liked_by_me(self, obj):
        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if not user or not user.is_authenticated:
            return False
        return obj.likes.filter(user=user).exists()


class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = [
            'id',
            'title',
            'message',
            'is_read',
            'related_report',
            'related_claim',
            'created_at',
        ]


class ClaimMessageSerializer(serializers.ModelSerializer):
    sender = serializers.ReadOnlyField(source='sender.username')

    class Meta:
        model = ClaimMessage
        fields = ['id', 'claim', 'sender', 'message', 'created_at']
        read_only_fields = ['id', 'claim', 'sender', 'created_at']


class ClaimRequestSerializer(serializers.ModelSerializer):
    claimant = serializers.ReadOnlyField(source='claimant.username')
    report_owner = serializers.ReadOnlyField(source='report.author.username')
    report_type = serializers.ReadOnlyField(source='report.report_type')
    initial_message = serializers.CharField(write_only=True, required=False, allow_blank=True)

    class Meta:
        model = ClaimRequest
        fields = [
            'id',
            'report',
            'report_owner',
            'report_type',
            'claimant',
            'pet_name',
            'pet_details',
            'proof',
            'status',
            'admin_reply',
            'initial_message',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'report_owner',
            'report_type',
            'claimant',
            'status',
            'admin_reply',
            'created_at',
            'updated_at',
        ]

    def validate(self, attrs):
        report = attrs.get('report')
        if report and report.report_type not in ['lost', 'found']:
            raise serializers.ValidationError({'report': 'Claims can only be raised on lost/found posts.'})

        request = self.context.get('request')
        user = getattr(request, 'user', None)
        if report and user and user.is_authenticated:
            if ClaimRequest.objects.filter(report=report, claimant=user).exists():
                raise serializers.ValidationError({'detail': 'You already raised a claim for this post.'})
        return attrs
