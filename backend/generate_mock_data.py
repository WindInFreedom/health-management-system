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
from measurements.models import Measurement, SleepLog, MoodLog

User = get_user_model()


class HealthDataGenerator:
    def __init__(self):
        self.user_profiles = []
        self._init_user_profiles()

    def _init_user_profiles(self):
        self.user_profiles = [
            {
                'user_id': '001',
                'username': 'user001',
                'name': '张伟',
                'email': 'zhangwei001@example.com',
                'age': 35,
                'gender': 'M',
                'blood_type': 'A',
                'height_cm': 175.0,
                'weight_baseline_kg': 70.0,
                'conditions': ['高血压', '糖尿病前期'],
                'base_systolic': 135,
                'base_diastolic': 85,
                'base_glucose': 6.5,
                'base_heart_rate': 75,
            },
            {
                'user_id': '002',
                'username': 'user002',
                'name': '李娜',
                'email': 'lina002@example.com',
                'age': 28,
                'gender': 'F',
                'blood_type': 'B',
                'height_cm': 162.0,
                'weight_baseline_kg': 52.0,
                'conditions': ['健康'],
                'base_systolic': 110,
                'base_diastolic': 70,
                'base_glucose': 5.2,
                'base_heart_rate': 72,
            },
            {
                'user_id': '003',
                'username': 'user003',
                'name': '王强',
                'email': 'wangqiang003@example.com',
                'age': 45,
                'gender': 'M',
                'blood_type': 'O',
                'height_cm': 178.0,
                'weight_baseline_kg': 85.0,
                'conditions': ['高血压', '高血脂'],
                'base_systolic': 145,
                'base_diastolic': 92,
                'base_glucose': 5.8,
                'base_heart_rate': 78,
            },
            {
                'user_id': '004',
                'username': 'user004',
                'name': '刘芳',
                'email': 'liufang004@example.com',
                'age': 32,
                'gender': 'F',
                'blood_type': 'AB',
                'height_cm': 165.0,
                'weight_baseline_kg': 55.0,
                'conditions': ['健康'],
                'base_systolic': 108,
                'base_diastolic': 68,
                'base_glucose': 5.0,
                'base_heart_rate': 70,
            },
            {
                'user_id': '005',
                'username': 'user005',
                'name': '陈明',
                'email': 'chenming005@example.com',
                'age': 52,
                'gender': 'M',
                'blood_type': 'A',
                'height_cm': 172.0,
                'weight_baseline_kg': 78.0,
                'conditions': ['糖尿病', '高血压'],
                'base_systolic': 140,
                'base_diastolic': 88,
                'base_glucose': 8.2,
                'base_heart_rate': 80,
            },
            {
                'user_id': '006',
                'username': 'user006',
                'name': '杨丽',
                'email': 'yangli006@example.com',
                'age': 38,
                'gender': 'F',
                'blood_type': 'B',
                'height_cm': 160.0,
                'weight_baseline_kg': 58.0,
                'conditions': ['健康'],
                'base_systolic': 112,
                'base_diastolic': 72,
                'base_glucose': 5.3,
                'base_heart_rate': 74,
            },
            {
                'user_id': '007',
                'username': 'user007',
                'name': '赵军',
                'email': 'zhaojun007@example.com',
                'age': 41,
                'gender': 'M',
                'blood_type': 'O',
                'height_cm': 176.0,
                'weight_baseline_kg': 82.0,
                'conditions': ['高血脂'],
                'base_systolic': 125,
                'base_diastolic': 80,
                'base_glucose': 5.6,
                'base_heart_rate': 76,
            },
            {
                'user_id': '008',
                'username': 'user008',
                'name': '孙敏',
                'email': 'sunmin008@example.com',
                'age': 29,
                'gender': 'F',
                'blood_type': 'A',
                'height_cm': 168.0,
                'weight_baseline_kg': 50.0,
                'conditions': ['健康'],
                'base_systolic': 105,
                'base_diastolic': 65,
                'base_glucose': 4.9,
                'base_heart_rate': 68,
            },
            {
                'user_id': '009',
                'username': 'user009',
                'name': '周涛',
                'email': 'zhoutao009@example.com',
                'age': 48,
                'gender': 'M',
                'blood_type': 'AB',
                'height_cm': 174.0,
                'weight_baseline_kg': 88.0,
                'conditions': ['高血压', '糖尿病'],
                'base_systolic': 148,
                'base_diastolic': 95,
                'base_glucose': 7.8,
                'base_heart_rate': 82,
            },
            {
                'user_id': '010',
                'username': 'user010',
                'name': '吴静',
                'email': 'wujing010@example.com',
                'age': 33,
                'gender': 'F',
                'blood_type': 'O',
                'height_cm': 163.0,
                'weight_baseline_kg': 54.0,
                'conditions': ['健康'],
                'base_systolic': 108,
                'base_diastolic': 70,
                'base_glucose': 5.1,
                'base_heart_rate': 71,
            },
        ]

    def create_users(self):
        print("开始创建用户...")
        created_users = []
        
        for profile in self.user_profiles:
            try:
                user = User.objects.create_user(
                    username=profile['username'],
                    email=profile['email'],
                    password='password123',
                    first_name=profile['name'][0],
                    last_name=profile['name'][1:],
                    role='user'
                )
                
                user_profile = Profile.objects.create(
                    user=user,
                    age=profile['age'],
                    gender=profile['gender'],
                    blood_type=profile['blood_type'],
                    height_cm=profile['height_cm'],
                    weight_baseline_kg=profile['weight_baseline_kg'],
                    bio=f"用户编号: {profile['user_id']}, 疾病史: {', '.join(profile['conditions'])}"
                )
                
                created_users.append(user)
                print(f"  ✓ 创建用户: {profile['name']} ({profile['username']})")
            except Exception as e:
                print(f"  ✗ 创建用户失败 {profile['username']}: {e}")
        
        print(f"成功创建 {len(created_users)} 个用户\n")
        return created_users

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
                'systolic': 1.02,
                'diastolic': 1.01,
                'glucose': 1.05,
                'heart_rate': 1.01,
                'weight': 1.0,
            },
            'afternoon': {
                'systolic': 1.0,
                'diastolic': 1.0,
                'glucose': 1.0,
                'heart_rate': 1.0,
                'weight': 1.0,
            },
            'evening': {
                'systolic': 0.99,
                'diastolic': 0.99,
                'glucose': 0.98,
                'heart_rate': 0.99,
                'weight': 1.0,
            }
        }
        return value * factors[time_of_day].get(measurement_type, 1.0)

    def _generate_weight(self, profile, day_offset):
        base_weight = profile['weight_baseline_kg']
        # 减少波动范围，从±2.0kg改为±0.5kg
        variation = random.uniform(-0.5, 0.5)
        # 添加缓慢趋势，每天0.01kg的变化
        trend = 0.01 * day_offset
        seasonal_factor = 1.0 + 0.01 * (1 if day_offset > 180 else -1)
        weight = base_weight + variation + trend
        weight = weight * seasonal_factor
        return round(weight, 1)

    def _generate_blood_pressure(self, profile, time_of_day):
        systolic = self._generate_measurement_value(
            profile['base_systolic'], 0.05, min_value=90, max_value=180
        )
        diastolic = self._generate_measurement_value(
            profile['base_diastolic'], 0.05, min_value=60, max_value=120
        )
        
        systolic = self._adjust_for_time_of_day(systolic, time_of_day, 'systolic')
        diastolic = self._adjust_for_time_of_day(diastolic, time_of_day, 'diastolic')
        
        return int(systolic), int(diastolic)

    def _generate_blood_glucose(self, profile, time_of_day):
        base_glucose = profile['base_glucose']
        # 减少波动范围，从0.8-1.4改为0.95-1.05
        variation = random.uniform(0.95, 1.05)
        
        glucose = base_glucose * variation
        glucose = self._adjust_for_time_of_day(glucose, time_of_day, 'glucose')
        
        glucose = max(glucose, 3.5)
        glucose = min(glucose, 15.0)
        
        return round(glucose, 1)

    def _generate_heart_rate(self, profile, time_of_day):
        base_heart_rate = profile['base_heart_rate']
        # 减少波动范围，从0.85-1.2改为0.98-1.02
        variation = random.uniform(0.98, 1.02)
        
        heart_rate = base_heart_rate * variation
        heart_rate = self._adjust_for_time_of_day(heart_rate, time_of_day, 'heart_rate')
        
        heart_rate = max(heart_rate, 50)
        heart_rate = min(heart_rate, 120)
        
        return int(heart_rate)

    def generate_measurements(self, users):
        print("开始生成健康测量数据...")
        
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 12, 31)
        total_days = (end_date - start_date).days + 1
        
        measurement_times = [
            (8, 0),    # 早上8点
            (14, 0),   # 下午2点
            (20, 0),   # 晚上8点
        ]
        
        total_measurements = 0
        
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
                    
                    measurement = Measurement.objects.create(
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
        
        print(f"成功生成 {total_measurements} 条健康测量记录\n")
        return total_measurements

    def generate_sleep_logs(self, users):
        print("开始生成睡眠记录...")
        
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 12, 31)
        total_days = (end_date - start_date).days + 1
        
        total_sleep_logs = 0
        
        for user in users:
            # 为每个用户设置基础睡眠时间（8-9小时）
            base_sleep_hours = random.uniform(8, 9)
            
            for day_offset in range(total_days):
                sleep_date = start_date + timedelta(days=day_offset)
                
                # 计算睡眠时间，基础上有小波动
                sleep_hours = base_sleep_hours + random.uniform(-0.5, 0.5)
                
                # 10%的概率出现异常值
                if random.random() < 0.1:
                    if random.random() < 0.5:
                        # 睡眠不足
                        sleep_hours = random.uniform(5, 6.5)
                    else:
                        # 睡眠过多
                        sleep_hours = random.uniform(10, 11.5)
                
                # 确保睡眠时间在合理范围内
                sleep_hours = max(4, min(12, sleep_hours))
                sleep_minutes = int(sleep_hours * 60)
                
                # 计算入睡和起床时间
                # 通常在22:00-23:30之间入睡
                sleep_hour = random.randint(22, 23)
                sleep_minute = random.randint(0, 30)
                start_time = datetime.combine(sleep_date, datetime.min.time()) + timedelta(hours=sleep_hour, minutes=sleep_minute)
                
                # 起床时间 = 入睡时间 + 睡眠时长
                end_time = start_time + timedelta(minutes=sleep_minutes)
                
                # 根据睡眠时间计算睡眠质量评分
                if 7 <= sleep_hours <= 9:
                    quality_rating = random.randint(7, 9)
                elif 6 <= sleep_hours < 7 or 9 < sleep_hours <= 10:
                    quality_rating = random.randint(5, 7)
                else:
                    quality_rating = random.randint(3, 5)
                
                # 创建睡眠记录
                sleep_log = SleepLog.objects.create(
                    user=user,
                    sleep_date=sleep_date.date(),
                    start_time=start_time,
                    end_time=end_time,
                    duration_minutes=sleep_minutes,
                    quality_rating=quality_rating
                )
                
                total_sleep_logs += 1
            
            print(f"  ✓ 生成用户 {user.username} 的睡眠记录")
        
        print(f"成功生成 {total_sleep_logs} 条睡眠记录\n")
        return total_sleep_logs

    def generate_mood_logs(self, users):
        print("开始生成心情记录...")
        
        start_date = datetime(2025, 3, 1)
        end_date = datetime(2025, 12, 31)
        total_days = (end_date - start_date).days + 1
        
        total_mood_logs = 0
        
        for user in users:
            # 为每个用户设置基础心情评分（6-8分）
            base_mood_rating = random.randint(6, 8)
            
            for day_offset in range(total_days):
                log_date = start_date + timedelta(days=day_offset)
                
                # 计算心情评分，基础上有小波动
                mood_rating = base_mood_rating + random.randint(-1, 1)
                
                # 10%的概率出现异常值
                if random.random() < 0.1:
                    if random.random() < 0.5:
                        # 心情较差
                        mood_rating = random.randint(3, 4)
                    else:
                        # 心情很好
                        mood_rating = random.randint(9, 10)
                
                # 确保心情评分在1-10之间
                mood_rating = max(1, min(10, mood_rating))
                
                # 检查前一天的睡眠质量，影响当天的心情
                if day_offset > 0:
                    prev_date = log_date - timedelta(days=1)
                    prev_sleep = SleepLog.objects.filter(
                        user=user,
                        sleep_date=prev_date.date()
                    ).first()
                    
                    if prev_sleep:
                        # 睡眠质量好，心情+1
                        if prev_sleep.quality_rating >= 8:
                            mood_rating = min(10, mood_rating + 1)
                        # 睡眠质量差，心情-1
                        elif prev_sleep.quality_rating <= 4:
                            mood_rating = max(1, mood_rating - 1)
                
                # 创建心情记录
                mood_log = MoodLog.objects.create(
                    user=user,
                    log_date=log_date.date(),
                    mood_rating=mood_rating
                )
                
                total_mood_logs += 1
            
            print(f"  ✓ 生成用户 {user.username} 的心情记录")
        
        print(f"成功生成 {total_mood_logs} 条心情记录\n")
        return total_mood_logs

    def generate_all_data(self):
        print("=" * 60)
        print("健康数据生成器")
        print("=" * 60)
        print()
        
        users = self.create_users()
        if not users:
            print("错误：未能创建用户")
            return
        
        measurements_count = self.generate_measurements(users)
        sleep_logs_count = self.generate_sleep_logs(users)
        mood_logs_count = self.generate_mood_logs(users)
        
        print("=" * 60)
        print(f"数据生成完成！")
        print(f"用户数量: {len(users)}")
        print(f"测量记录数量: {measurements_count}")
        print(f"睡眠记录数量: {sleep_logs_count}")
        print(f"心情记录数量: {mood_logs_count}")
        print("=" * 60)

    def generate_only_sleep_and_mood(self):
        """
        只生成睡眠和心情记录，不重新创建用户和测量记录
        """
        print("=" * 60)
        print("生成睡眠和心情记录")
        print("=" * 60)
        print()
        
        # 获取所有现有用户
        users = User.objects.filter(role='user')
        if not users:
            print("错误：未找到用户，请先运行完整的数据生成")
            return
        
        print(f"找到 {len(users)} 个用户，开始生成睡眠和心情记录...")
        print()
        
        sleep_logs_count = self.generate_sleep_logs(users)
        mood_logs_count = self.generate_mood_logs(users)
        
        print("=" * 60)
        print(f"睡眠和心情记录生成完成！")
        print(f"用户数量: {len(users)}")
        print(f"睡眠记录数量: {sleep_logs_count}")
        print(f"心情记录数量: {mood_logs_count}")
        print("=" * 60)


if __name__ == '__main__':
    generator = HealthDataGenerator()
    # 只生成睡眠和心情记录
    generator.generate_only_sleep_and_mood()
