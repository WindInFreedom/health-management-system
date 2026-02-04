from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Measurement(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='measurements')
    measured_at = models.DateTimeField()
    weight_kg = models.DecimalField(max_digits=5, decimal_places=1, null=True, blank=True, help_text="体重 (kg)")
    systolic = models.IntegerField(null=True, blank=True, help_text="收缩压")
    diastolic = models.IntegerField(null=True, blank=True, help_text="舒张压")
    blood_glucose = models.DecimalField(max_digits=4, decimal_places=1, null=True, blank=True, help_text="血糖 (mmol/L)")
    heart_rate = models.IntegerField(null=True, blank=True, help_text="心率 (bpm)")
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-measured_at']
        verbose_name = "健康测量"
        verbose_name_plural = "健康测量"

    def __str__(self):
        return f"{self.user.username} - {self.measured_at.strftime('%Y-%m-%d %H:%M')}"


# 替换本地内容：新增MedicationRecord模型用于药物记录
class MedicationRecord(models.Model):
    """药物记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='medications')
    name = models.CharField(max_length=200, help_text="药物名称")
    dosage = models.CharField(max_length=100, help_text="剂量")
    frequency = models.CharField(max_length=100, help_text="服用频率")
    start_date = models.DateField(help_text="开始日期")
    end_date = models.DateField(null=True, blank=True, help_text="结束日期")
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        verbose_name = "药物记录"
        verbose_name_plural = "药物记录"
    
    def __str__(self):
        return f"{self.user.username} - {self.name}"


# 替换本地内容：新增SleepLog模型用于睡眠记录
class SleepLog(models.Model):
    """睡眠记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sleep_logs')
    start_time = models.DateTimeField(help_text="入睡时间")
    end_time = models.DateTimeField(help_text="起床时间")
    duration_minutes = models.IntegerField(editable=False, help_text="睡眠时长（分钟）")
    quality_rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        null=True,
        blank=True,
        help_text="睡眠质量评分 (1-10)"
    )
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_time']
        verbose_name = "睡眠记录"
        verbose_name_plural = "睡眠记录"
    
    def save(self, *args, **kwargs):
        """自动计算睡眠时长"""
        if self.start_time and self.end_time:
            delta = self.end_time - self.start_time
            self.duration_minutes = int(delta.total_seconds() / 60)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.user.username} - {self.start_time.strftime('%Y-%m-%d')} ({self.duration_minutes}分钟)"


# 替换本地内容：新增MoodLog模型用于情绪记录
class MoodLog(models.Model):
    """情绪记录模型"""
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='mood_logs')
    date = models.DateField(help_text="日期")
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(10)],
        help_text="情绪评分 (1-10, 1为非常低落，10为非常愉悦)"
    )
    notes = models.TextField(blank=True, help_text="备注")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-date']
        unique_together = ['user', 'date']
        verbose_name = "情绪记录"
        verbose_name_plural = "情绪记录"
    
    def __str__(self):
        return f"{self.user.username} - {self.date} (评分: {self.rating})"

