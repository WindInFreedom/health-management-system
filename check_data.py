import os
import sys
import django

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

# 设置Django环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from measurements.models import Measurement

User = get_user_model()

# 获取第一个用户
user = User.objects.first()
if not user:
    print("没有找到用户")
    exit()

# 获取用户的测量数据
measurements = Measurement.objects.filter(user=user).order_by('measured_at')
print(f'总记录数: {measurements.count()}')

if measurements.count() > 0:
    first_measurement = measurements.first()
    last_measurement = measurements.last()
    print(f'最早记录: {first_measurement.measured_at}')
    print(f'最近记录: {last_measurement.measured_at}')
    
    # 计算数据跨度
    delta = last_measurement.measured_at - first_measurement.measured_at
    print(f'数据跨度: {delta.days} 天')
    
    # 检查各指标的数据量
    print('\n各指标数据量:')
    metrics = ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']
    for metric in metrics:
        count = measurements.exclude(**{metric: None}).count()
        print(f'{metric}: {count} 条')
else:
    print("没有找到测量数据")