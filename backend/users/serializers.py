# 替换本地内容：完整的用户和档案序列化器
from rest_framework import serializers
from django.contrib.auth.password_validation import validate_password
from .models import User, Profile


class ProfileSerializer(serializers.ModelSerializer):
    """
    用户档案序列化器
    替换本地内容：支持完整的个人基本档案字段
    """
    class Meta:
        model = Profile
        fields = [
            'id', 'user', 'bio', 'location', 'birth_date',
            'age', 'gender', 'blood_type', 'height', 'weight_baseline',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate_age(self, value):
        """验证年龄范围"""
        if value and (value < 0 or value > 150):
            raise serializers.ValidationError("年龄必须在0-150之间")
        return value
    
    def validate_height(self, value):
        """验证身高范围"""
        if value and (value < 50 or value > 250):
            raise serializers.ValidationError("身高必须在50-250cm之间")
        return value
    
    def validate_weight_baseline(self, value):
        """验证体重范围"""
        if value and (value < 20 or value > 300):
            raise serializers.ValidationError("体重必须在20-300kg之间")
        return value


class UserSerializer(serializers.ModelSerializer):
    """
    用户序列化器
    替换本地内容：支持头像URL和档案信息
    """
    profile = ProfileSerializer(read_only=True)
    
    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'date_of_birth', 'phone', 'role', 'is_doctor', 'department',
            'avatar_url', 'profile', 'date_joined'
        ]
        read_only_fields = ['id', 'date_joined']
    
    def validate_username(self, value):
        """验证用户名唯一性"""
        if self.instance:
            # 更新时排除自己
            if User.objects.exclude(pk=self.instance.pk).filter(username=value).exists():
                raise serializers.ValidationError("该用户名已被使用")
        else:
            if User.objects.filter(username=value).exists():
                raise serializers.ValidationError("该用户名已被使用")
        return value


class RegistrationSerializer(serializers.ModelSerializer):
    """用户注册序列化器"""
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'email', 'first_name', 'last_name', 'role', 'department']
        extra_kwargs = {
            'role': {'required': False},
            'department': {'required': False},
        }

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "两次密码不一致"})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        validated_data.setdefault('role', 'user')
        user = User(**validated_data)
        user.set_password(password)
        user.save()
        # 自动创建档案
        Profile.objects.create(user=user)
        return user


class ChangePasswordSerializer(serializers.Serializer):
    """
    修改密码序列化器
    替换本地内容：支持密码修改功能
    """
    old_password = serializers.CharField(required=True, write_only=True)
    new_password = serializers.CharField(required=True, write_only=True, validators=[validate_password])
    new_password2 = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({"new_password": "两次密码不一致"})
        return attrs
    
    def validate_old_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError("原密码不正确")
        return value
