from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import pandas as pd
import os

User = get_user_model()


class Command(BaseCommand):
    help = '导出用户健康数据为CSV格式'

    def add_arguments(self, parser):
        parser.add_argument(
            '--user-id',
            type=int,
            required=True,
            help='用户ID'
        )
        parser.add_argument(
            '--output-dir',
            type=str,
            default='exported_data',
            help='输出目录'
        )

    def handle(self, *args, **options):
        user_id = options['user_id']
        output_dir = options['output_dir']
        
        os.makedirs(output_dir, exist_ok=True)
        
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            self.stdout.write(self.style.ERROR(f'用户 {user_id} 不存在'))
            return
        
        from measurements.models import Measurement
        
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        data = list(measurements.values(
            'measured_at',
            'weight_kg',
            'systolic',
            'diastolic',
            'heart_rate',
            'blood_glucose',
            'notes'
        ))
        
        if not data:
            self.stdout.write(self.style.WARNING(f'用户 {user_id} 没有测量数据'))
            return
        
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        
        output_file = os.path.join(output_dir, f'user_{user_id}_health_data.csv')
        df.to_csv(output_file, index=False, encoding='utf-8-sig')
        
        self.stdout.write(self.style.SUCCESS(f'数据已导出到: {output_file}'))
        self.stdout.write(self.style.SUCCESS(f'总记录数: {len(df)}'))
        self.stdout.write(self.style.SUCCESS(f'时间范围: {df["measured_at"].min()} 到 {df["measured_at"].max()}'))
