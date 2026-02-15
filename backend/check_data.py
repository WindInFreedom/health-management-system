import os
import django

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from measurements.models import Measurement, SleepLog, MoodLog, MedicationRecord

print("=== 数据库数据检查 ===")
print(f"SleepLog 记录数: {SleepLog.objects.count()}")
print(f"MoodLog 记录数: {MoodLog.objects.count()}")
print(f"Measurement 记录数: {Measurement.objects.count()}")
print(f"MedicationRecord 记录数: {MedicationRecord.objects.count()}")

print("\n=== 最近的5条睡眠记录 ===")
sleep_logs = SleepLog.objects.all().order_by('-sleep_date')[:5]
for log in sleep_logs:
    print(f"ID: {log.id}, Date: {log.sleep_date}, Duration: {log.duration_minutes}, Quality: {log.quality_rating}")

print("\n=== 最近的5条心情记录 ===")
mood_logs = MoodLog.objects.all().order_by('-log_date')[:5]
for log in mood_logs:
    print(f"ID: {log.id}, Date: {log.log_date}, Rating: {log.mood_rating}")

print("\n=== 最近的5条健康测量记录 ===")
measurements = Measurement.objects.all().order_by('-measured_at')[:5]
for m in measurements:
    print(f"ID: {m.id}, Date: {m.measured_at}, User: {m.user.id}, Weight: {m.weight_kg}, Systolic: {m.systolic}")
