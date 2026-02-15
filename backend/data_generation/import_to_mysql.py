"""
MySQL 数据导入脚本

将 PyHealth 生成的数据导入到 Django MySQL 数据库
使用现有的 Measurement 模型和 User 模型
"""

import os
import sys
import django
import pandas as pd
from datetime import datetime
from decimal import Decimal

# 设置 Django 环境
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from measurements.models import Measurement
from users.models import Profile

User = get_user_model()


class DataImporter:
    """数据导入器"""
    
    def __init__(self, users_csv: str, measurements_csv: str):
        """
        初始化导入器
        
        Args:
            users_csv: 用户信息CSV文件路径
            measurements_csv: 测量数据CSV文件路径
        """
        self.users_csv = users_csv
        self.measurements_csv = measurements_csv
        self.user_mapping = {}  # username -> User对象映射
        
    def import_users(self) -> int:
        """
        导入用户数据
        
        Returns:
            导入的用户数量
        """
        print("正在导入用户数据...")
        
        df_users = pd.read_csv(self.users_csv)
        imported_count = 0
        
        for _, row in df_users.iterrows():
            username = row['username']
            
            # 检查用户是否已存在
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@example.com",
                    'first_name': row['full_name'],
                }
            )
            
            if created:
                # 设置密码
                user.set_password('password123')
                user.save()
                
                # 创建或更新 Profile
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.age = int(row['age'])
                profile.gender = row['gender']
                profile.height_cm = float(row['height_cm'])
                profile.blood_type = row['blood_type']
                profile.save()
                
                imported_count += 1
                print(f"  ✓ 创建用户: {username} ({row['full_name']})")
            else:
                print(f"  - 用户已存在: {username}")
            
            # 保存映射
            self.user_mapping[username] = user
        
        print(f"用户导入完成: 新增 {imported_count} 个用户\n")
        return imported_count
    
    def import_measurements(self, batch_size: int = 1000) -> int:
        """
        批量导入测量数据
        
        Args:
            batch_size: 批量插入大小
            
        Returns:
            导入的记录数量
        """
        print("正在导入测量数据...")
        
        df_measurements = pd.read_csv(self.measurements_csv)
        total_records = len(df_measurements)
        imported_count = 0
        
        # 删除该用户的旧数据（可选）
        print("  清理旧数据...")
        for username in self.user_mapping.keys():
            user = self.user_mapping[username]
            old_count = Measurement.objects.filter(user=user).count()
            if old_count > 0:
                Measurement.objects.filter(user=user).delete()
                print(f"  - 删除 {username} 的 {old_count} 条旧记录")
        
        # 批量插入
        measurements_to_create = []
        
        for idx, row in df_measurements.iterrows():
            username = row['username']
            user = self.user_mapping.get(username)
            
            if user is None:
                print(f"  ! 警告: 找不到用户 {username}, 跳过记录")
                continue
            
            # 转换数据类型
            measured_at = pd.to_datetime(row['measured_at'])
            
            measurement = Measurement(
                user=user,
                measured_at=measured_at,
                blood_glucose=Decimal(str(round(row['blood_glucose'], 1))),
                heart_rate=int(row['heart_rate']),
                systolic=int(row['systolic']),
                diastolic=int(row['diastolic']),
                weight_kg=Decimal(str(round(row['weight_kg'], 1))),
                notes=f'PyHealth generated data'
            )
            
            measurements_to_create.append(measurement)
            
            # 批量插入
            if len(measurements_to_create) >= batch_size:
                Measurement.objects.bulk_create(measurements_to_create)
                imported_count += len(measurements_to_create)
                print(f"  ✓ 已导入 {imported_count}/{total_records} 条记录 "
                      f"({imported_count/total_records*100:.1f}%)")
                measurements_to_create = []
        
        # 插入剩余数据
        if measurements_to_create:
            Measurement.objects.bulk_create(measurements_to_create)
            imported_count += len(measurements_to_create)
        
        print(f"测量数据导入完成: 共 {imported_count} 条记录\n")
        return imported_count
    
    def run(self):
        """执行完整的导入流程"""
        print("=" * 60)
        print("PyHealth 数据导入工具")
        print("=" * 60)
        print(f"用户数据文件: {self.users_csv}")
        print(f"测量数据文件: {self.measurements_csv}")
        print()
        
        # 检查文件是否存在
        if not os.path.exists(self.users_csv):
            print(f"错误: 找不到用户数据文件 {self.users_csv}")
            return False
        
        if not os.path.exists(self.measurements_csv):
            print(f"错误: 找不到测量数据文件 {self.measurements_csv}")
            return False
        
        # 导入用户
        user_count = self.import_users()
        
        # 导入测量数据
        measurement_count = self.import_measurements()
        
        print("=" * 60)
        print("导入完成！")
        print(f"  用户数: {user_count}")
        print(f"  测量记录数: {measurement_count}")
        print("=" * 60)
        
        return True


if __name__ == '__main__':
    # 默认路径
    users_csv = 'data_generation/output/users.csv'
    measurements_csv = 'data_generation/output/measurements.csv'
    
    # 支持命令行参数
    if len(sys.argv) > 1:
        users_csv = sys.argv[1]
    if len(sys.argv) > 2:
        measurements_csv = sys.argv[2]
    
    importer = DataImporter(users_csv, measurements_csv)
    importer.run()
