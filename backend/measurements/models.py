from django.db import models
from django.contrib.auth import get_user_model

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
