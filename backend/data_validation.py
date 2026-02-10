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


class DataValidator:
    def __init__(self):
        self.validation_results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
        }

    def validate_measurements(self):
        print("=" * 80)
        print("验证健康测量数据")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        
        if not measurements.exists():
            print("没有找到测量数据\n")
            return
        
        print(f"总记录数: {measurements.count()}")
        
        users = User.objects.filter(role='user')
        
        for user in users:
            user_measurements = measurements.filter(user=user)
            
            if not user_measurements.exists():
                continue
            
            self._validate_user_measurements(user, user_measurements)
        
        self._print_validation_summary()

    def _validate_user_measurements(self, user, measurements):
        print(f"\n用户: {user.username}")
        
        count = measurements.count()
        if count < 100:
            print(f"  ⚠ 警告: 测量记录数过少 ({count}条)")
            self.validation_results['warnings'] += 1
        else:
            print(f"  ✓ 测量记录数: {count}条")
            self.validation_results['passed'] += 1
        
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        if weight_data:
            avg_weight = sum(weight_data) / len(weight_data)
            if avg_weight < 30 or avg_weight > 200:
                print(f"  ✗ 错误: 平均体重异常 ({avg_weight:.1f}kg)")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均体重: {avg_weight:.1f}kg")
        
        systolic_data = [m.systolic for m in measurements if m.systolic]
        if systolic_data:
            avg_systolic = sum(systolic_data) / len(systolic_data)
            if avg_systolic < 70 or avg_systolic > 180:
                print(f"  ✗ 错误: 平均收缩压异常 ({avg_systolic:.0f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均收缩压: {avg_systolic:.0f}")
        
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        if diastolic_data:
            avg_diastolic = sum(diastolic_data) / len(diastolic_data)
            if avg_diastolic < 40 or avg_diastolic > 120:
                print(f"  ✗ 错误: 平均舒张压异常 ({avg_diastolic:.0f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均舒张压: {avg_diastolic:.0f}")
        
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        if glucose_data:
            avg_glucose = sum(glucose_data) / len(glucose_data)
            if avg_glucose < 2 or avg_glucose > 20:
                print(f"  ✗ 错误: 平均血糖异常 ({avg_glucose:.1f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均血糖: {avg_glucose:.1f}")
        
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        if heart_rate_data:
            avg_heart_rate = sum(heart_rate_data) / len(heart_rate_data)
            if avg_heart_rate < 40 or avg_heart_rate > 120:
                print(f"  ✗ 错误: 平均心率异常 ({avg_heart_rate:.0f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均心率: {avg_heart_rate:.0f}")

    def validate_sleep_logs(self):
        print("\n" + "=" * 80)
        print("验证睡眠记录")
        print("=" * 80)
        
        sleep_logs = SleepLog.objects.all()
        
        if not sleep_logs.exists():
            print("没有找到睡眠记录\n")
            return
        
        print(f"总记录数: {sleep_logs.count()}")
        
        users = User.objects.filter(role='user')
        
        for user in users:
            user_logs = sleep_logs.filter(user=user)
            
            if not user_logs.exists():
                continue
            
            self._validate_user_sleep_logs(user, user_logs)
        
        self._print_validation_summary()

    def _validate_user_sleep_logs(self, user, logs):
        print(f"\n用户: {user.username}")
        
        count = logs.count()
        if count < 100:
            print(f"  ⚠ 警告: 睡眠记录数过少 ({count}条)")
            self.validation_results['warnings'] += 1
        else:
            print(f"  ✓ 睡眠记录数: {count}条")
            self.validation_results['passed'] += 1
        
        duration_data = [log.duration_minutes for log in logs if log.duration_minutes]
        if duration_data:
            avg_duration = sum(duration_data) / len(duration_data)
            if avg_duration < 240 or avg_duration > 600:
                print(f"  ✗ 错误: 平均睡眠时长异常 ({avg_duration:.0f}分钟)")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均睡眠时长: {avg_duration:.0f}分钟 ({avg_duration/60:.1f}小时)")
        
        quality_data = [log.quality_rating for log in logs if log.quality_rating]
        if quality_data:
            avg_quality = sum(quality_data) / len(quality_data)
            if avg_quality < 1 or avg_quality > 10:
                print(f"  ✗ 错误: 平均睡眠质量评分异常 ({avg_quality:.1f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均睡眠质量: {avg_quality:.1f}")

    def validate_mood_logs(self):
        print("\n" + "=" * 80)
        print("验证心情记录")
        print("=" * 80)
        
        mood_logs = MoodLog.objects.all()
        
        if not mood_logs.exists():
            print("没有找到心情记录\n")
            return
        
        print(f"总记录数: {mood_logs.count()}")
        
        users = User.objects.filter(role='user')
        
        for user in users:
            user_logs = mood_logs.filter(user=user)
            
            if not user_logs.exists():
                continue
            
            self._validate_user_mood_logs(user, user_logs)
        
        self._print_validation_summary()

    def _validate_user_mood_logs(self, user, logs):
        print(f"\n用户: {user.username}")
        
        count = logs.count()
        if count < 100:
            print(f"  ⚠ 警告: 心情记录数过少 ({count}条)")
            self.validation_results['warnings'] += 1
        else:
            print(f"  ✓ 心情记录数: {count}条")
            self.validation_results['passed'] += 1
        
        rating_data = [log.mood_rating for log in logs if log.mood_rating]
        if rating_data:
            avg_rating = sum(rating_data) / len(rating_data)
            if avg_rating < 1 or avg_rating > 10:
                print(f"  ✗ 错误: 平均心情评分异常 ({avg_rating:.1f})")
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 平均心情评分: {avg_rating:.1f}")

    def validate_data_completeness(self):
        print("\n" + "=" * 80)
        print("验证数据完整性")
        print("=" * 80)
        
        users = User.objects.filter(role='user')
        incomplete_users = 0
        
        for user in users:
            has_measurements = Measurement.objects.filter(user=user).exists()
            has_sleep_logs = SleepLog.objects.filter(user=user).exists()
            has_mood_logs = MoodLog.objects.filter(user=user).exists()
            
            if not has_measurements:
                print(f"  ✗ 用户 {user.username} 缺少测量数据")
                incomplete_users += 1
            elif not has_sleep_logs:
                print(f"  ✗ 用户 {user.username} 缺少睡眠记录")
                incomplete_users += 1
            elif not has_mood_logs:
                print(f"  ✗ 用户 {user.username} 缺少心情记录")
                incomplete_users += 1
            else:
                print(f"  ✓ 用户 {user.username} 数据完整")
                self.validation_results['passed'] += 1
        
        if incomplete_users > 0:
            print(f"\n  ⚠ 警告: {incomplete_users} 个用户数据不完整")
            self.validation_results['warnings'] += incomplete_users

    def validate_temporal_consistency(self):
        print("\n" + "=" * 80)
        print("验证时间一致性")
        print("=" * 80)
        
        users = User.objects.filter(role='user')
        inconsistent_users = 0
        
        for user in users:
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            
            if measurements.count() < 2:
                continue
            
            prev_time = None
            inconsistencies = 0
            
            for measurement in measurements:
                if prev_time:
                    time_diff = measurement.measured_at - prev_time
                    
                    if time_diff.total_seconds() < 0:
                        inconsistencies += 1
                
                prev_time = measurement.measured_at
            
            if inconsistencies > 0:
                print(f"  ✗ 用户 {user.username} 存在 {inconsistencies} 个时间顺序异常")
                inconsistent_users += 1
                self.validation_results['failed'] += 1
            else:
                print(f"  ✓ 用户 {user.username} 时间顺序正常")
                self.validation_results['passed'] += 1
        
        if inconsistent_users > 0:
            print(f"\n  ⚠ 警告: {inconsistent_users} 个用户存在时间顺序异常")

    def _print_validation_summary(self):
        print("\n" + "=" * 80)
        print("验证总结")
        print("=" * 80)
        print(f"通过: {self.validation_results['passed']}")
        print(f"失败: {self.validation_results['failed']}")
        print(f"警告: {self.validation_results['warnings']}")
        print("=" * 80)

    def run_validation(self):
        print("\n" + "=" * 80)
        print("数据验证流程")
        print("=" * 80)
        print()
        
        self.validate_measurements()
        self.validate_sleep_logs()
        self.validate_mood_logs()
        self.validate_data_completeness()
        self.validate_temporal_consistency()
        
        print("\n" + "=" * 80)
        print("数据验证完成")
        print("=" * 80)
        print()
        self._print_validation_summary()


if __name__ == '__main__':
    validator = DataValidator()
    validator.run_validation()
