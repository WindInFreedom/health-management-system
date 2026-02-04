from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
    # 替换本地内容：扩展User模型以支持头像存储
    ROLE_CHOICES = [
        ('admin', '管理员'),
        ('doctor', '医生'),
        ('user', '普通用户'),
    ]
    
    email = models.EmailField(unique=True)
    date_of_birth = models.DateField(null=True, blank=True)
    phone = models.CharField(max_length=20, blank=True)
    role = models.CharField(max_length=10, choices=ROLE_CHOICES, default='user')
    is_doctor = models.BooleanField(default=False)
    department = models.CharField(max_length=100, blank=True)
    avatar_url = models.URLField(max_length=500, blank=True, null=True, help_text="用户头像URL")
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    class Meta:
        db_table = 'auth_user'
    
    @property
    def is_admin_user(self):
        return self.role == 'admin' or self.is_superuser
    
    @property
    def is_doctor_user(self):
        return self.role == 'doctor' or self.is_doctor
    
    @property
    def is_regular_user(self):
        return self.role == 'user' and not self.is_superuser


class Profile(models.Model):
    # 替换本地内容：扩展Profile模型以支持完整的个人基本档案
    GENDER_CHOICES = [
        ('M', '男'),
        ('F', '女'),
        ('O', '其他'),
    ]
    
    BLOOD_TYPE_CHOICES = [
        ('A', 'A型'),
        ('B', 'B型'),
        ('AB', 'AB型'),
        ('O', 'O型'),
        ('UNKNOWN', '未知'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Original fields
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # 替换本地内容：新增个人基本档案字段
    age = models.PositiveIntegerField(null=True, blank=True, help_text="年龄")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, blank=True, help_text="性别")
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='UNKNOWN', help_text="血型")
    height = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="身高 (cm)")
    weight_baseline = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="基准体重 (kg)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
    
    class Meta:
        db_table = 'users_profile'
        verbose_name = '用户档案'
        verbose_name_plural = '用户档案'
