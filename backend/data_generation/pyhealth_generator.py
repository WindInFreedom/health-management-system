"""
PyHealth 2.0 风格的医疗数据生成器

生成符合医学标准的高质量时间序列健康数据
支持生成：
- 血糖 (blood_glucose): 3.9-6.1 mmol/L (正常), 可能异常
- 心率 (heart_rate): 60-100 bpm (正常), 可能异常  
- 收缩压 (systolic): 90-120 mmHg (正常), 可能异常
- 舒张压 (diastolic): 60-80 mmHg (正常), 可能异常
- 体重 (weight_kg): 根据BMI计算, 可能变化趋势

作者: Health Management System Team
日期: 2026-02-15
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
import random


class PyHealthDataGenerator:
    """
    PyHealth 2.0 风格的医疗数据生成器
    
    生成 10 个用户 × 1000 条记录的时间序列健康数据
    """
    
    # 医学正常范围定义
    NORMAL_RANGES = {
        'blood_glucose': {'min': 3.9, 'max': 6.1, 'unit': 'mmol/L'},
        'heart_rate': {'min': 60, 'max': 100, 'unit': 'bpm'},
        'systolic': {'min': 90, 'max': 120, 'unit': 'mmHg'},
        'diastolic': {'min': 60, 'max': 80, 'unit': 'mmHg'},
        'weight_kg': {'min': 45, 'max': 100, 'unit': 'kg'},
    }
    
    # 血型分布 (根据中国人口统计)
    BLOOD_TYPES = ['A', 'B', 'O', 'AB']
    BLOOD_TYPE_WEIGHTS = [0.28, 0.29, 0.35, 0.08]
    
    # 姓名库
    SURNAMES = ['王', '李', '张', '刘', '陈', '杨', '赵', '黄', '周', '吴',
                '徐', '孙', '胡', '朱', '高', '林', '何', '郭', '马', '罗']
    GIVEN_NAMES_MALE = ['伟', '强', '磊', '军', '勇', '杰', '涛', '明', '超', '峰',
                        '浩', '鹏', '宇', '凯', '博', '翔', '辉', '鑫', '俊', '豪']
    GIVEN_NAMES_FEMALE = ['芳', '娜', '秀', '丽', '敏', '静', '慧', '婷', '霞', '红',
                          '梅', '玲', '莉', '琳', '萍', '燕', '洁', '雪', '倩', '蕾']
    
    def __init__(self, num_users: int = 10, records_per_user: int = 1000, random_seed: int = 42):
        """
        初始化数据生成器
        
        Args:
            num_users: 生成的用户数量
            records_per_user: 每个用户的记录数
            random_seed: 随机种子，用于复现
        """
        self.num_users = num_users
        self.records_per_user = records_per_user
        self.random_seed = random_seed
        
        # 设置随机种子
        np.random.seed(random_seed)
        random.seed(random_seed)
        
        # 用户配置文件
        self.user_profiles = []
        
    def generate_user_profile(self, user_id: int) -> Dict:
        """
        生成单个用户的个人信息
        
        Args:
            user_id: 用户ID
            
        Returns:
            用户配置字典
        """
        # 生成性别
        gender = random.choice(['M', 'F'])
        
        # 生成姓名
        surname = random.choice(self.SURNAMES)
        if gender == 'M':
            given_name = ''.join(random.sample(self.GIVEN_NAMES_MALE, 2))
        else:
            given_name = ''.join(random.sample(self.GIVEN_NAMES_FEMALE, 2))
        full_name = f"{surname}{given_name}"
        
        # 生成年龄 (18-80岁)
        age = random.randint(18, 80)
        
        # 生成身高 (cm)
        if gender == 'M':
            height_cm = round(random.normalvariate(172, 7), 1)
            height_cm = max(155, min(195, height_cm))
        else:
            height_cm = round(random.normalvariate(160, 6), 1)
            height_cm = max(145, min(180, height_cm))
        
        # 生成理想体重 (使用BMI在正常范围 18.5-24)
        ideal_bmi = random.uniform(20, 23)
        ideal_weight = round(ideal_bmi * (height_cm / 100) ** 2, 1)
        
        # 生成血型
        blood_type = random.choices(self.BLOOD_TYPES, weights=self.BLOOD_TYPE_WEIGHTS)[0]
        
        # 生成基础生理指标 (作为该用户的"正常值")
        # 年龄越大，指标可能偏高
        age_factor = (age - 18) / 62  # 0-1之间
        
        base_blood_glucose = 4.5 + age_factor * 0.8 + random.uniform(-0.3, 0.3)
        base_heart_rate = 70 + random.uniform(-8, 8)
        base_systolic = 100 + age_factor * 15 + random.uniform(-5, 5)
        base_diastolic = 70 + age_factor * 8 + random.uniform(-3, 3)
        
        # 决定是否有慢性疾病 (年龄越大概率越高)
        has_hypertension = random.random() < (age_factor * 0.3)
        has_diabetes = random.random() < (age_factor * 0.2)
        
        # 如果有疾病，调整基础值
        if has_hypertension:
            base_systolic += random.uniform(10, 25)
            base_diastolic += random.uniform(5, 15)
        
        if has_diabetes:
            base_blood_glucose += random.uniform(1.5, 3.0)
        
        profile = {
            'user_id': user_id,
            'username': f'user{user_id:02d}',
            'full_name': full_name,
            'gender': gender,
            'age': age,
            'height_cm': height_cm,
            'blood_type': blood_type,
            'ideal_weight': ideal_weight,
            'has_hypertension': has_hypertension,
            'has_diabetes': has_diabetes,
            'base_values': {
                'blood_glucose': base_blood_glucose,
                'heart_rate': base_heart_rate,
                'systolic': base_systolic,
                'diastolic': base_diastolic,
                'weight_kg': ideal_weight,
            }
        }
        
        return profile
    
    def generate_time_series_for_user(self, profile: Dict, start_date: datetime) -> pd.DataFrame:
        """
        为单个用户生成时间序列数据
        
        Args:
            profile: 用户配置
            start_date: 开始日期
            
        Returns:
            DataFrame containing time series data
        """
        records = []
        base_values = profile['base_values']
        
        # 生成长期趋势 (用于模拟体重变化等)
        weight_trend = np.random.choice(['stable', 'gain', 'loss'], p=[0.6, 0.25, 0.15])
        
        for i in range(self.records_per_user):
            # 计算当前日期时间 (每天1-3次测量)
            days_offset = i // 2  # 平均每天2次
            hours = random.choice([7, 8, 9, 14, 15, 19, 20, 21])  # 早中晚
            minutes = random.randint(0, 59)
            
            measured_at = start_date + timedelta(days=days_offset, hours=hours, minutes=minutes)
            
            # 计算当前天数进度 (0-1)
            progress = i / self.records_per_user
            
            # 生成各项指标
            # 1. 血糖 (考虑餐前餐后)
            is_fasting = hours < 10  # 早上测量视为空腹
            glucose_base = base_values['blood_glucose']
            if not is_fasting:
                glucose_base += random.uniform(0.5, 1.5)  # 餐后升高
            
            # 添加日常波动和长期趋势
            daily_noise = np.random.normal(0, 0.3)
            long_term_trend = 0
            if profile['has_diabetes']:
                long_term_trend = progress * random.uniform(-0.5, 0.3)  # 可能改善也可能恶化
            
            blood_glucose = glucose_base + daily_noise + long_term_trend
            blood_glucose = round(max(3.0, min(15.0, blood_glucose)), 1)  # 限制在合理范围
            
            # 2. 心率 (考虑时间和活动)
            hr_base = base_values['heart_rate']
            time_factor = 5 if hours > 18 else 0  # 晚上可能略高
            activity_noise = np.random.normal(0, 5)
            
            heart_rate = hr_base + time_factor + activity_noise
            heart_rate = int(max(45, min(130, heart_rate)))
            
            # 3. 血压 (收缩压和舒张压有关联)
            sys_base = base_values['systolic']
            dia_base = base_values['diastolic']
            
            # 血压在一天内有波动
            time_bp_factor = 0
            if 6 <= hours < 12:
                time_bp_factor = random.uniform(0, 5)  # 早上略高
            elif hours >= 20:
                time_bp_factor = random.uniform(-5, 0)  # 晚上略低
            
            bp_noise = np.random.normal(0, 4)
            long_term_bp = 0
            if profile['has_hypertension']:
                long_term_bp = progress * random.uniform(-5, 2)  # 治疗可能改善
            
            systolic = sys_base + time_bp_factor + bp_noise + long_term_bp
            systolic = int(max(80, min(200, systolic)))
            
            # 舒张压与收缩压相关
            diastolic = dia_base + time_bp_factor * 0.5 + bp_noise * 0.5 + long_term_bp * 0.5
            diastolic = int(max(50, min(120, diastolic)))
            
            # 4. 体重 (长期趋势)
            weight_base = base_values['weight_kg']
            
            if weight_trend == 'gain':
                weight_change = progress * random.uniform(2, 8)
            elif weight_trend == 'loss':
                weight_change = -progress * random.uniform(2, 6)
            else:
                weight_change = np.sin(progress * 4 * np.pi) * random.uniform(0.5, 1.5)  # 周期波动
            
            daily_weight_noise = np.random.normal(0, 0.3)
            weight_kg = weight_base + weight_change + daily_weight_noise
            weight_kg = round(max(40, min(150, weight_kg)), 1)
            
            # 组装记录
            record = {
                'user_id': profile['user_id'],
                'username': profile['username'],
                'measured_at': measured_at,
                'blood_glucose': blood_glucose,
                'heart_rate': heart_rate,
                'systolic': systolic,
                'diastolic': diastolic,
                'weight_kg': weight_kg,
            }
            
            records.append(record)
        
        df = pd.DataFrame(records)
        df = df.sort_values('measured_at').reset_index(drop=True)
        
        return df
    
    def generate_all_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        生成所有用户的数据
        
        Returns:
            (用户信息DataFrame, 测量数据DataFrame)
        """
        print(f"开始生成数据: {self.num_users} 个用户 × {self.records_per_user} 条记录")
        print("=" * 60)
        
        all_measurements = []
        all_users = []
        
        start_date = datetime(2024, 1, 1)  # 数据起始日期
        
        for i in range(1, self.num_users + 1):
            print(f"[{i}/{self.num_users}] 生成用户 user{i:02d} 的数据...")
            
            # 生成用户配置
            profile = self.generate_user_profile(i)
            self.user_profiles.append(profile)
            
            # 生成时间序列数据
            user_data = self.generate_time_series_for_user(profile, start_date)
            all_measurements.append(user_data)
            
            # 保存用户信息
            user_info = {
                'user_id': profile['user_id'],
                'username': profile['username'],
                'full_name': profile['full_name'],
                'gender': profile['gender'],
                'age': profile['age'],
                'height_cm': profile['height_cm'],
                'blood_type': profile['blood_type'],
                'has_hypertension': profile['has_hypertension'],
                'has_diabetes': profile['has_diabetes'],
            }
            all_users.append(user_info)
            
            print(f"  ✓ 生成 {len(user_data)} 条记录")
            print(f"    个人信息: {profile['full_name']}, {profile['age']}岁, "
                  f"{profile['gender']}, 血型{profile['blood_type']}")
            print(f"    健康状况: 高血压={profile['has_hypertension']}, "
                  f"糖尿病={profile['has_diabetes']}")
        
        # 合并所有数据
        df_measurements = pd.concat(all_measurements, ignore_index=True)
        df_users = pd.DataFrame(all_users)
        
        print("=" * 60)
        print(f"数据生成完成！")
        print(f"  总用户数: {len(df_users)}")
        print(f"  总记录数: {len(df_measurements)}")
        print(f"  时间跨度: {df_measurements['measured_at'].min()} 至 "
              f"{df_measurements['measured_at'].max()}")
        
        # 统计信息
        print("\n指标统计:")
        for metric in ['blood_glucose', 'heart_rate', 'systolic', 'diastolic', 'weight_kg']:
            values = df_measurements[metric]
            print(f"  {metric}: 均值={values.mean():.2f}, "
                  f"标准差={values.std():.2f}, "
                  f"范围=[{values.min():.1f}, {values.max():.1f}]")
        
        return df_users, df_measurements
    
    def save_to_csv(self, df_users: pd.DataFrame, df_measurements: pd.DataFrame, 
                    output_dir: str = 'data_generation/output'):
        """
        保存数据到CSV文件
        
        Args:
            df_users: 用户信息DataFrame
            df_measurements: 测量数据DataFrame
            output_dir: 输出目录
        """
        import os
        os.makedirs(output_dir, exist_ok=True)
        
        users_file = os.path.join(output_dir, 'users.csv')
        measurements_file = os.path.join(output_dir, 'measurements.csv')
        
        df_users.to_csv(users_file, index=False, encoding='utf-8-sig')
        df_measurements.to_csv(measurements_file, index=False, encoding='utf-8-sig')
        
        print(f"\n数据已保存:")
        print(f"  用户信息: {users_file}")
        print(f"  测量数据: {measurements_file}")


if __name__ == '__main__':
    # 测试数据生成
    generator = PyHealthDataGenerator(num_users=10, records_per_user=1000)
    df_users, df_measurements = generator.generate_all_data()
    generator.save_to_csv(df_users, df_measurements)
