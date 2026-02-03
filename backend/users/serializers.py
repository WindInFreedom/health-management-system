from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Profile

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_of_birth', 'phone']
        read_only_fields = ['id']


class ProfileSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Profile
        fields = ['id', 'user', 'bio', 'location', 'birth_date', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']
# ---------- 新增：RegistrationSerializer ----------
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