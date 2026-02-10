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
