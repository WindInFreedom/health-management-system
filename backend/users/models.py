from django.contrib.auth.models import AbstractUser
from django.db import models


class User(AbstractUser):
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
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(max_length=500, blank=True)
    location = models.CharField(max_length=30, blank=True)
    birth_date = models.DateField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.user.username}'s profile"
