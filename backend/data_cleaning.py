import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from measurements.models import Measurement
from users.models import SleepLog, MoodLog

User = get_user_model()


class DataCleaner:
    def __init__(self):
        self.clean_stats = {
            'measurements_removed': 0,
            'measurements_fixed': 0,
            'sleep_logs_removed': 0,
            'sleep_logs_fixed': 0,
            'mood_logs_removed': 0,
            'mood_logs_fixed': 0,
        }

    def clean_measurements(self):
        print("=" * 80)
        print("清洗健康测量数据")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        
        print(f"总记录数: {measurements.count()}")
        
        for measurement in measurements:
            cleaned = False
            
            if measurement.weight_kg:
                if measurement.weight_kg <= 0 or measurement.weight_kg > 300:
                    print(f"  ✗ 删除无效体重: {measurement.weight_kg}kg at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1
                    cleaned = True
            
            if measurement.systolic:
                if measurement.systolic < 50 or measurement.systolic > 250:
                    print(f"  ✗ 删除无效收缩压: {measurement.systolic} at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1
                    cleaned = True
            
            if measurement.diastolic:
                if measurement.diastolic < 30 or measurement.diastolic > 150:
                    print(f"  ✗ 删除无效舒张压: {measurement.diastolic} at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1
                    cleaned = True
            
            if measurement.blood_glucose:
                if measurement.blood_glucose < 1 or measurement.blood_glucose > 30:
                    print(f"  ✗ 删除无效血糖: {measurement.blood_glucose} at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1
                    cleaned = True
            
            if measurement.heart_rate:
                if measurement.heart_rate < 30 or measurement.heart_rate > 200:
                    print(f"  ✗ 删除无效心率: {measurement.heart_rate} at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1
                    cleaned = True
            
            if not cleaned:
                if not measurement.weight_kg and not measurement.systolic and not measurement.diastolic and not measurement.blood_glucose and not measurement.heart_rate:
                    print(f"  ✗ 删除空记录 at {measurement.measured_at}")
                    measurement.delete()
                    self.clean_stats['measurements_removed'] += 1

    def clean_sleep_logs(self):
        print("\n" + "=" * 80)
        print("清洗睡眠记录")
        print("=" * 80)
        
        sleep_logs = SleepLog.objects.all()
        
        print(f"总记录数: {sleep_logs.count()}")
        
        for log in sleep_logs:
            cleaned = False
            
            if log.duration_minutes:
                if log.duration_minutes < 60 or log.duration_minutes > 720:
                    print(f"  ✗ 删除无效睡眠时长: {log.duration_minutes}分钟 at {log.sleep_date}")
                    log.delete()
                    self.clean_stats['sleep_logs_removed'] += 1
                    cleaned = True
            
            if log.quality_rating:
                if log.quality_rating < 1 or log.quality_rating > 10:
                    print(f"  ✓ 修正睡眠质量评分: {log.quality_rating} at {log.sleep_date}")
                    log.quality_rating = max(1, min(10, log.quality_rating))
                    log.save()
                    self.clean_stats['sleep_logs_fixed'] += 1
                    cleaned = True
            
            if not cleaned:
                if not log.duration_minutes:
                    print(f"  ✗ 删除空睡眠记录 at {log.sleep_date}")
                    log.delete()
                    self.clean_stats['sleep_logs_removed'] += 1

    def clean_mood_logs(self):
        print("\n" + "=" * 80)
        print("清洗心情记录")
        print("=" * 80)
        
        mood_logs = MoodLog.objects.all()
        
        print(f"总记录数: {mood_logs.count()}")
        
        for log in mood_logs:
            cleaned = False
            
            if log.mood_rating:
                if log.mood_rating < 1 or log.mood_rating > 10:
                    print(f"  ✓ 修正心情评分: {log.mood_rating} at {log.log_date}")
                    log.mood_rating = max(1, min(10, log.mood_rating))
                    log.save()
                    self.clean_stats['mood_logs_fixed'] += 1
                    cleaned = True
            
            if not cleaned:
                if not log.mood_rating:
                    print(f"  ✗ 删除空心情记录 at {log.log_date}")
                    log.delete()
                    self.clean_stats['mood_logs_removed'] += 1

    def remove_duplicates(self):
        print("\n" + "=" * 80)
        print("删除重复记录")
        print("=" * 80)
        
        users = User.objects.filter(role='user')
        duplicates_removed = 0
        
        for user in users:
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            seen = set()
            
            for measurement in measurements:
                key = (measurement.measured_at, measurement.weight_kg, measurement.systolic, measurement.diastolic)
                
                if key in seen:
                    print(f"  ✗ 删除重复记录: {measurement.measured_at}")
                    measurement.delete()
                    duplicates_removed += 1
                else:
                    seen.add(key)
        
        self.clean_stats['measurements_removed'] += duplicates_removed
        print(f"删除了 {duplicates_removed} 条重复记录")

    def fix_missing_values(self):
        print("\n" + "=" * 80)
        print("修复缺失值")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        fixed_count = 0
        
        for measurement in measurements:
            fixed = False
            
            if not measurement.weight_kg:
                user_measurements = Measurement.objects.filter(user=measurement.user).exclude(weight_kg__isnull=True)
                if user_measurements.exists():
                    recent_weight = user_measurements.order_by('-measured_at').first()
                    if recent_weight and recent_weight.weight_kg:
                        measurement.weight_kg = recent_weight.weight_kg
                        measurement.save()
                        fixed_count += 1
                        fixed = True
            
            if not measurement.heart_rate:
                user_measurements = Measurement.objects.filter(user=measurement.user).exclude(heart_rate__isnull=True)
                if user_measurements.exists():
                    recent_hr = user_measurements.order_by('-measured_at').first()
                    if recent_hr and recent_hr.heart_rate:
                        measurement.heart_rate = recent_hr.heart_rate
                        measurement.save()
                        fixed_count += 1
                        fixed = True
            
            if fixed:
                print(f"  ✓ 修复缺失值 at {measurement.measured_at}")
        
        self.clean_stats['measurements_fixed'] += fixed_count
        print(f"修复了 {fixed_count} 条记录的缺失值")

    def validate_data_consistency(self):
        print("\n" + "=" * 80)
        print("验证数据一致性")
        print("=" * 80)
        
        users = User.objects.filter(role='user')
        inconsistent_count = 0
        
        for user in users:
            measurements = Measurement.objects.filter(user=user)
            
            if measurements.exists():
                first_measurement = measurements.earliest('measured_at')
                last_measurement = measurements.latest('measured_at')
                
                if first_measurement and last_measurement:
                    time_diff = last_measurement.measured_at - first_measurement.measured_at
                    
                    if time_diff.days < 0:
                        print(f"  ⚠ 时间顺序异常: {user.username}")
                        inconsistent_count += 1
        
        print(f"发现 {inconsistent_count} 个时间顺序异常")

    def run_cleaning(self):
        print("\n" + "=" * 80)
        print("数据清洗流程")
        print("=" * 80)
        print()
        
        self.clean_measurements()
        self.clean_sleep_logs()
        self.clean_mood_logs()
        self.remove_duplicates()
        self.fix_missing_values()
        self.validate_data_consistency()
        
        print("\n" + "=" * 80)
        print("数据清洗完成")
        print("=" * 80)
        print(f"\n清洗统计:")
        print(f"  健康测量记录删除: {self.clean_stats['measurements_removed']}")
        print(f"  健康测量记录修复: {self.clean_stats['measurements_fixed']}")
        print(f"  睡眠记录删除: {self.clean_stats['sleep_logs_removed']}")
        print(f"  睡眠记录修复: {self.clean_stats['sleep_logs_fixed']}")
        print(f"  心情记录删除: {self.clean_stats['mood_logs_removed']}")
        print(f"  心情记录修复: {self.clean_stats['mood_logs_fixed']}")
        print("=" * 80)


if __name__ == '__main__':
    cleaner = DataCleaner()
    cleaner.run_cleaning()
