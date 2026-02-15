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
    # New field for user avatar
    avatar = models.ImageField(upload_to='avatars/', null=True, blank=True, help_text="用户头像")
    
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
    """
    Extended user profile with health-related information.
    Enhanced to include age, gender, blood type, height, and weight baseline.
    """
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
        ('Unknown', '未知'),
    ]
    
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    
    # Original fields
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    
    # New fields for personal health profile
    age = models.IntegerField(null=True, blank=True, help_text="年龄")
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True, help_text="性别")
    blood_type = models.CharField(max_length=10, choices=BLOOD_TYPE_CHOICES, default='Unknown', help_text="血型")
    height_cm = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="身高 (cm)")
    weight_baseline_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="基准体重 (kg)")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"


