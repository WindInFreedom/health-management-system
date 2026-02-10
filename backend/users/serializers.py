from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile, MedicationRecord, SleepLog, MoodLog

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    avatar_url = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_of_birth', 
                  'phone', 'role', 'avatar', 'avatar_url']
        read_only_fields = ['id']
        extra_kwargs = {'password': {'write_only': True}}
    
    def get_avatar_url(self, obj):
        if obj.avatar:
            request = self.context.get('request')
            if request:
                return request.build_absolute_uri(obj.avatar.url)
            return obj.avatar.url
        return None


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'location', 'birth_date', 'age', 'gender', 
                  'blood_type', 'height_cm', 'weight_baseline_kg', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class MedicationRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicationRecord
        fields = ['id', 'user', 'medication_name', 'dosage', 'frequency', 
                  'start_date', 'end_date', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class SleepLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = SleepLog
        fields = ['id', 'user', 'sleep_date', 'start_time', 'end_time', 
                  'duration_minutes', 'quality_rating', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'duration_minutes', 'created_at', 'updated_at']


class MoodLogSerializer(serializers.ModelSerializer):
    class Meta:
        model = MoodLog
        fields = ['id', 'user', 'log_date', 'mood_rating', 'notes', 'created_at', 'updated_at']
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class ChangePasswordSerializer(serializers.Serializer):
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, min_length=8)
    confirm_password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "两次输入的新密码不一致"})
        return attrs


# ---------- Existing RegistrationSerializer ----------
from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()

class RegistrationSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, min_length=8)
    password2 = serializers.CharField(write_only=True, required=True, min_length=8)

    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'password', 'password2', 'role', 'department')
        extra_kwargs = {
            'role': {'required': False},
            'department': {'required': False},
        }

    def validate(self, attrs):
        if attrs.get('password') != attrs.get('password2'):
            raise serializers.ValidationError({"password": "两次输入的密码不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2', None)
        password = validated_data.pop('password')
        # 默认角色为普通用户，除非显式指定
        validated_data.setdefault('role', 'user')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # 如果项目使用 Profile，可在这里创建默认 Profile（可选）
        # from .models import Profile
        # Profile.objects.create(user=user)
        return user
# --------------------------------------------------
