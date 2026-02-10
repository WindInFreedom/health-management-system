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


class MedicationRecord(models.Model):
    """
    Medication tracking for users.
    Stores information about medications taken by users.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medication_records')
    medication_name = models.CharField(max_length=200, help_text="药物名称")
    dosage = models.CharField(max_length=100, help_text="剂量")
    frequency = models.CharField(max_length=100, help_text="用药频率，例如: 每日3次")
    start_date = models.DateField(help_text="开始日期")
    end_date = models.DateField(null=True, blank=True, help_text="结束日期")
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "用药记录"
        verbose_name_plural = "用药记录"
    
    def __str__(self):
        return f"{self.user.username} - {self.medication_name} ({self.start_date})"


class SleepLog(models.Model):
    """
    Sleep tracking for users.
    Records sleep start/end times and automatically calculates duration.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='user_sleeplogs')
    sleep_date = models.DateField(help_text="睡眠日期")
    start_time = models.DateTimeField(help_text="入睡时间")
    end_time = models.DateTimeField(help_text="起床时间")
    duration_minutes = models.IntegerField(help_text="睡眠时长（分钟）")
    quality_rating = models.IntegerField(null=True, blank=True, help_text="睡眠质量评分 (1-10)")
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-sleep_date']
        verbose_name = "睡眠记录"
        verbose_name_plural = "睡眠记录"
    
    def __str__(self):
        return f"{self.user.username} - {self.sleep_date} ({self.duration_minutes}分钟)"
    
    def save(self, *args, **kwargs):
        # Auto-calculate duration if not set
        if self.start_time and self.end_time and not self.duration_minutes:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)


class MoodLog(models.Model):
    """
    Daily mood tracking for users.
    Records daily mood ratings with notes.
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE,  related_name='user_moodlogs')
    log_date = models.DateField(help_text="记录日期")
    mood_rating = models.IntegerField(help_text="心情评分 (1-10，1=很差，10=很好)")
    notes = models.TextField(blank=True, help_text="心情备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-log_date']
        unique_together = [['user', 'log_date']]
        verbose_name = "心情记录"
        verbose_name_plural = "心情记录"
    
    def __str__(self):
        return f"{self.user.username} - {self.log_date} (评分: {self.mood_rating})"

