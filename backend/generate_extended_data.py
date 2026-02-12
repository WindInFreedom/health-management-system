import os
import sys
import django
from datetime import datetime, timedelta
import random
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile
from measurements.models import Measurement

User = get_user_model()


class ExtendedHealthDataGenerator:
    def __init__(self):
        self.user_profiles = []
        self._init_user_profiles()

    def _init_user_profiles(self):
        self.user_profiles = [
            {
                'user_id': '001',
                'username': 'user001',
                'name': '张伟',
                'age': 35,
                'gender': 'M',
                'base_systolic': 135,
                'base_diastolic': 85,
                'base_glucose': 6.5,
                'base_heart_rate': 75,
                'base_weight': 70.0,
            },
            {
                'user_id': '002',
                'username': 'user002',
                'name': '李娜',
                'age': 28,
                'gender': 'F',
                'base_systolic': 110,
                'base_diastolic': 70,
                'base_glucose': 5.2,
                'base_heart_rate': 72,
                'base_weight': 52.0,
            },
            {
                'user_id': '003',
                'username': 'user003',
                'name': '王强',
                'age': 45,
                'gender': 'M',
                'base_systolic': 145,
                'base_diastolic': 92,
                'base_glucose': 5.8,
                'base_heart_rate': 78,
                'base_weight': 85.0,
            },
            {
                'user_id': '004',
                'username': 'user004',
                'name': '刘芳',
                'age': 32,
                'gender': 'F',
                'base_systolic': 108,
                'base_diastolic': 68,
                'base_glucose': 5.0,
                'base_heart_rate': 70,
                'base_weight': 55.0,
            },
            {
                'user_id': '005',
                'username': 'user005',
                'name': '陈明',
                'age': 52,
                'gender': 'M',
                'base_systolic': 140,
                'base_diastolic': 88,
                'base_glucose': 8.2,
                'base_heart_rate': 80,
                'base_weight': 78.0,
            },
            {
                'user_id': '006',
                'username': 'user006',
                'name': '杨丽',
                'age': 38,
                'gender': 'F',
                'base_systolic': 112,
                'base_diastolic': 72,
                'base_glucose': 5.3,
                'base_heart_rate': 74,
                'base_weight': 58.0,
            },
            {
                'user_id': '007',
                'username': 'user007',
                'name': '赵军',
                'age': 41,
                'gender': 'M',
                'base_systolic': 125,
                'base_diastolic': 80,
                'base_glucose': 5.6,
                'base_heart_rate': 76,
                'base_weight': 82.0,
            },
            {
                'user_id': '008',
                'username': 'user008',
                'name': '孙敏',
                'age': 29,
                'gender': 'F',
                'base_systolic': 105,
                'base_diastolic': 65,
                'base_glucose': 4.9,
                'base_heart_rate': 68,
                'base_weight': 50.0,
            },
            {
                'user_id': '009',
                'username': 'user009',
                'name': '周涛',
                'age': 48,
                'gender': 'M',
                'base_systolic': 148,
                'base_diastolic': 95,
                'base_glucose': 7.8,
                'base_heart_rate': 82,
                'base_weight': 88.0,
            },
            {
                'user_id': '010',
                'username': 'user010',
                'name': '吴静',
                'age': 33,
                'gender': 'F',
                'base_systolic': 108,
                'base_diastolic': 70,
                'base_glucose': 5.1,
                'base_heart_rate': 71,
                'base_weight': 54.0,
            },
        ]

    def _generate_measurement_value(self, base_value, variation_percent, min_value=None, max_value=None):
        variation = base_value * variation_percent
        value = base_value + random.uniform(-variation, variation)
        
        if min_value is not None:
            value = max(value, min_value)
        if max_value is not None:
            value = min(value, max_value)
        
        return value

    def _get_time_of_day_factor(self, hour):
        if 6 <= hour < 12:
            return 'morning'
        elif 12 <= hour < 18:
            return 'afternoon'
        else:
            return 'evening'

    def _adjust_for_time_of_day(self, value, time_of_day, measurement_type):
        factors = {
            'morning': {
                'systolic': 1.05,
                'diastolic': 1.03,
                'glucose': 1.15,
                'heart_rate': 1.02,
                'weight': 1.0,
            },
            'afternoon': {
                'systolic': 1.0,
                'diastolic': 1.0,
                'glucose': 0.95,
                'heart_rate': 1.0,
                'weight': 0.99,
            },
            'evening': {
                'systolic': 0.98,
                'diastolic': 0.97,
                'glucose': 0.9,
                'heart_rate': 0.98,
                'weight': 0.98,
            }
        }
        return value * factors[time_of_day].get(measurement_type, 1.0)

    def _generate_weight(self, profile, day_offset):
        base_weight = profile['base_weight']
        variation = random.uniform(-2.0, 2.0)
        seasonal_factor = 1.0 + 0.02 * (1 if day_offset > 180 else -1)
        weight = base_weight + variation
        weight = weight * seasonal_factor
        return round(weight, 1)

    def _generate_blood_pressure(self, profile, time_of_day):
        systolic = self._generate_measurement_value(
            profile['base_systolic'], 0.15, min_value=90, max_value=180
        )
        diastolic = self._generate_measurement_value(
            profile['base_diastolic'], 0.12, min_value=60, max_value=120
        )
        
        systolic = self._adjust_for_time_of_day(systolic, time_of_day, 'systolic')
        diastolic = self._adjust_for_time_of_day(diastolic, time_of_day, 'diastolic')
        
        return int(systolic), int(diastolic)

    def _generate_blood_glucose(self, profile, time_of_day):
        base_glucose = profile['base_glucose']
        variation = random.uniform(0.8, 1.4)
        
        glucose = base_glucose * variation
        glucose = self._adjust_for_time_of_day(glucose, time_of_day, 'glucose')
        
        glucose = max(glucose, 3.5)
        glucose = min(glucose, 15.0)
        
        return round(glucose, 1)

    def _generate_heart_rate(self, profile, time_of_day):
        base_heart_rate = profile['base_heart_rate']
        variation = random.uniform(0.85, 1.2)
        
        heart_rate = base_heart_rate * variation
        heart_rate = self._adjust_for_time_of_day(heart_rate, time_of_day, 'heart_rate')
        
        heart_rate = max(heart_rate, 50)
        heart_rate = min(heart_rate, 120)
        
        return int(heart_rate)

    def generate_extended_measurements(self):
        print("=" * 80)
        print("生成扩展健康测量数据 (2025-03-01 至 2026-02-10)")
        print("=" * 80)
        
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2026, 2, 10)
        total_days = (end_date - start_date).days + 1
        
        measurement_times = [
            (8, 0),    # 早上8点
            (14, 0),   # 下午2点
            (20, 0),   # 晚上8点
        ]
        
        users = User.objects.filter(role='user')
        total_measurements = 0
        error_count = 0
        
        for user in users:
            profile = next(p for p in self.user_profiles if p['username'] == user.username)
            
            for day_offset in range(total_days):
                current_date = start_date + timedelta(days=day_offset)
                
                for hour, minute in measurement_times:
                    measured_at = datetime.combine(current_date, datetime.min.time()) + timedelta(hours=hour, minutes=minute)
                    time_of_day = self._get_time_of_day_factor(hour)
                    
                    weight = self._generate_weight(profile, day_offset)
                    systolic, diastolic = self._generate_blood_pressure(profile, time_of_day)
                    glucose = self._generate_blood_glucose(profile, time_of_day)
                    heart_rate = self._generate_heart_rate(profile, time_of_day)
                    
                    # 以2%的概率生成错误数据
                    if random.random() < 0.02:
                        error_type = random.choice(['weight', 'systolic', 'diastolic', 'glucose', 'heart_rate'])
                        
                        if error_type == 'weight':
                            weight = random.choice([15.0, 25.0, 300.0, 500.0])
                        elif error_type == 'systolic':
                            systolic = random.choice([40, 50, 220, 280])
                        elif error_type == 'diastolic':
                            diastolic = random.choice([20, 30, 160, 200])
                        elif error_type == 'glucose':
                            glucose = random.choice([0.5, 1.0, 25.0, 35.0])
                        elif error_type == 'heart_rate':
                            heart_rate = random.choice([15, 20, 220, 250])
                        
                        error_count += 1
                    
                    Measurement.objects.create(
                        user=user,
                        measured_at=measured_at,
                        weight_kg=Decimal(str(weight)),
                        systolic=systolic,
                        diastolic=diastolic,
                        blood_glucose=Decimal(str(glucose)),
                        heart_rate=heart_rate
                    )
                    
                    total_measurements += 1
            
            print(f"  ✓ 生成用户 {user.username} 的测量数据")
        
        print(f"成功生成 {total_measurements} 条健康测量记录 (包含 {error_count} 条错误数据)\n")
        return total_measurements

    def generate_sleep_logs(self):
        print("=" * 80)
        print("生成睡眠记录 (近一年)")
        print("=" * 80)
        
        start_date = datetime(2025, 2, 10)
        end_date = datetime(2026, 2, 10)
        total_days = (end_date - start_date).days + 1
        
        users = User.objects.filter(role='user')
        total_sleep_logs = 0
        error_count = 0
        
        for user in users:
            profile = next(p for p in self.user_profiles if p['username'] == user.username)
            
            for day_offset in range(total_days):
                sleep_date = start_date + timedelta(days=day_offset)
                
                sleep_start_hour = random.randint(21, 23)
                sleep_start_minute = random.randint(0, 59)
                sleep_start = datetime.combine(sleep_date, datetime.min.time()) + timedelta(hours=sleep_start_hour, minutes=sleep_start_minute)
                
                sleep_duration_hours = random.uniform(6, 9)
                sleep_end = sleep_start + timedelta(hours=sleep_duration_hours)
                
                duration_minutes = int(sleep_duration_hours * 60)
                
                quality_rating = random.randint(5, 9)
                
                notes_list = [
                    "睡眠质量良好",
                    "睡眠一般",
                    "睡眠质量不错",
                    "睡眠充足",
                    "睡眠正常",
                    "睡眠质量很好",
                    "睡眠充足，精神饱满",
                    "睡眠时间适中",
                    "睡眠质量优秀",
                    "睡眠时间偏短",
                    "睡眠时间偏长",
                    "睡眠质量一般",
                    "睡眠质量良好，精力充沛",
                ]
                notes = random.choice(notes_list)
                
                # 以2%的概率生成错误数据
                if random.random() < 0.02:
                    error_type = random.choice(['duration', 'quality', 'time'])
                    
                    if error_type == 'duration':
                        duration_minutes = random.choice([30, 60, 720, 900])
                    elif error_type == 'quality':
                        quality_rating = random.choice([0, 15, 20])
                    elif error_type == 'time':
                        sleep_end = sleep_start + timedelta(hours=-2)
                    
                    error_count += 1
                
                try:
                    from users.models import SleepLog
                    SleepLog.objects.create(
                        user=user,
                        sleep_date=sleep_date.date(),
                        start_time=sleep_start,
                        end_time=sleep_end,
                        duration_minutes=duration_minutes,
                        quality_rating=quality_rating,
                        notes=notes
                    )
                    total_sleep_logs += 1
                except Exception as e:
                    print(f"  ✗ 创建睡眠记录失败: {e}")
            
            print(f"  ✓ 生成用户 {user.username} 的睡眠记录")
        
        print(f"成功生成 {total_sleep_logs} 条睡眠记录 (包含 {error_count} 条错误数据)\n")
        return total_sleep_logs

    def generate_mood_logs(self):
        print("=" * 80)
        print("生成心情记录 (近一年)")
        print("=" * 80)
        
        start_date = datetime(2025, 2, 10)
        end_date = datetime(2026, 2, 10)
        total_days = (end_date - start_date).days + 1
        
        users = User.objects.filter(role='user')
        total_mood_logs = 0
        error_count = 0
        
        for user in users:
            for day_offset in range(total_days):
                log_date = start_date + timedelta(days=day_offset)
                
                mood_rating = random.randint(4, 9)
                
                notes_list = [
                    "心情不错",
                    "心情一般",
                    "心情很好",
                    "心情愉悦",
                    "心情平静",
                    "心情有些低落",
                    "心情很好，精力充沛",
                    "心情不错，状态良好",
                    "心情一般，有些疲惫",
                    "心情很好，充满活力",
                    "心情平静，状态稳定",
                    "心情愉悦，心情舒畅",
                    "心情一般，有些压力",
                ]
                notes = random.choice(notes_list)
                
                # 以2%的概率生成错误数据
                if random.random() < 0.02:
                    mood_rating = random.choice([0, 15, 20])
                    error_count += 1
                
                try:
                    from users.models import MoodLog
                    MoodLog.objects.create(
                        user=user,
                        log_date=log_date.date(),
                        mood_rating=mood_rating,
                        notes=notes
                    )
                    total_mood_logs += 1
                except Exception as e:
                    print(f"  ✗ 创建心情记录失败: {e}")
            
            print(f"  ✓ 生成用户 {user.username} 的心情记录")
        
        print(f"成功生成 {total_mood_logs} 条心情记录 (包含 {error_count} 条错误数据)\n")
        return total_mood_logs

    def generate_all_extended_data(self):
        print("\n" + "=" * 80)
        print("扩展健康数据生成器")
        print("=" * 80)
        print()
        
        measurements_count = self.generate_extended_measurements()
        sleep_logs_count = self.generate_sleep_logs()
        mood_logs_count = self.generate_mood_logs()
        
        print("=" * 80)
        print(f"扩展数据生成完成！")
        print(f"健康测量记录: {measurements_count}")
        print(f"睡眠记录: {sleep_logs_count}")
        print(f"心情记录: {mood_logs_count}")
        print("=" * 80)


if __name__ == '__main__':
    generator = ExtendedHealthDataGenerator()
    generator.generate_all_extended_data()
