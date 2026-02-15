"""
Django 管理命令：生成 PyHealth 数据

使用方法:
    python manage.py generate_pyhealth_data
    python manage.py generate_pyhealth_data --users 20 --records 500
    python manage.py generate_pyhealth_data --no-import
"""

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from measurements.models import Measurement
from users.models import Profile
import sys
import os
from decimal import Decimal
import pandas as pd

# 添加 data_generation 模块到路径
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from data_generation.pyhealth_generator import PyHealthDataGenerator

User = get_user_model()


class Command(BaseCommand):
    help = '生成 PyHealth 2.0 风格的高质量医疗数据并导入数据库'
    
    def add_arguments(self, parser):
        parser.add_argument(
            '--users',
            type=int,
            default=10,
            help='生成的用户数量 (默认: 10)'
        )
        parser.add_argument(
            '--records',
            type=int,
            default=1000,
            help='每个用户的记录数 (默认: 1000)'
        )
        parser.add_argument(
            '--no-import',
            action='store_true',
            help='只生成CSV文件，不导入数据库'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='data_generation/output',
            help='输出目录 (默认: data_generation/output)'
        )
        parser.add_argument(
            '--seed',
            type=int,
            default=42,
            help='随机种子 (默认: 42)'
        )
    
    def handle(self, *args, **options):
        num_users = options['users']
        records_per_user = options['records']
        no_import = options['no_import']
        output_dir = options['output_dir']
        seed = options['seed']
        
        self.stdout.write(self.style.SUCCESS('=' * 70))
        self.stdout.write(self.style.SUCCESS('PyHealth 数据生成工具'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
        
        # Step 1: 生成数据
        self.stdout.write(f'\n配置:')
        self.stdout.write(f'  用户数: {num_users}')
        self.stdout.write(f'  每用户记录数: {records_per_user}')
        self.stdout.write(f'  总记录数: {num_users * records_per_user}')
        self.stdout.write(f'  随机种子: {seed}')
        self.stdout.write(f'  输出目录: {output_dir}\n')
        
        generator = PyHealthDataGenerator(
            num_users=num_users,
            records_per_user=records_per_user,
            random_seed=seed
        )
        
        df_users, df_measurements = generator.generate_all_data()
        generator.save_to_csv(df_users, df_measurements, output_dir)
        
        if no_import:
            self.stdout.write(self.style.SUCCESS('\n✓ 数据生成完成 (未导入数据库)'))
            return
        
        # Step 2: 导入数据库
        self.stdout.write(self.style.WARNING('\n开始导入数据库...'))
        
        user_mapping = {}
        imported_users = 0
        
        # 导入用户
        for _, row in df_users.iterrows():
            username = row['username']
            
            user, created = User.objects.get_or_create(
                username=username,
                defaults={
                    'email': f"{username}@example.com",
                    'first_name': row['full_name'],
                }
            )
            
            if created:
                user.set_password('password123')
                user.save()
                
                profile, _ = Profile.objects.get_or_create(user=user)
                profile.age = int(row['age'])
                profile.gender = row['gender']
                profile.height_cm = float(row['height_cm'])
                profile.blood_type = row['blood_type']
                profile.save()
                
                imported_users += 1
                self.stdout.write(f"  ✓ 创建用户: {username} ({row['full_name']})")
            else:
                self.stdout.write(f"  - 用户已存在: {username}")
            
            user_mapping[username] = user
        
        # 清理旧数据
        self.stdout.write('\n清理旧测量数据...')
        for username, user in user_mapping.items():
            old_count = Measurement.objects.filter(user=user).count()
            if old_count > 0:
                Measurement.objects.filter(user=user).delete()
                self.stdout.write(f"  - 删除 {username} 的 {old_count} 条旧记录")
        
        # 批量导入测量数据
        self.stdout.write('\n导入测量数据...')
        measurements_to_create = []
        batch_size = 1000
        imported_count = 0
        total_records = len(df_measurements)
        
        for idx, row in df_measurements.iterrows():
            username = row['username']
            user = user_mapping.get(username)
            
            if user is None:
                continue
            
            measured_at = pd.to_datetime(row['measured_at'])
            
            measurement = Measurement(
                user=user,
                measured_at=measured_at,
                blood_glucose=Decimal(str(round(row['blood_glucose'], 1))),
                heart_rate=int(row['heart_rate']),
                systolic=int(row['systolic']),
                diastolic=int(row['diastolic']),
                weight_kg=Decimal(str(round(row['weight_kg'], 1))),
                notes='PyHealth generated data'
            )
            
            measurements_to_create.append(measurement)
            
            if len(measurements_to_create) >= batch_size:
                Measurement.objects.bulk_create(measurements_to_create)
                imported_count += len(measurements_to_create)
                self.stdout.write(
                    f"  ✓ 进度: {imported_count}/{total_records} "
                    f"({imported_count/total_records*100:.1f}%)"
                )
                measurements_to_create = []
        
        # 插入剩余数据
        if measurements_to_create:
            Measurement.objects.bulk_create(measurements_to_create)
            imported_count += len(measurements_to_create)
        
        self.stdout.write(self.style.SUCCESS('\n' + '=' * 70))
        self.stdout.write(self.style.SUCCESS('导入完成！'))
        self.stdout.write(self.style.SUCCESS(f'  新增用户: {imported_users}'))
        self.stdout.write(self.style.SUCCESS(f'  导入记录: {imported_count}'))
        self.stdout.write(self.style.SUCCESS('=' * 70))
