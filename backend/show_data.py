import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile
from measurements.models import Measurement

User = get_user_model()

print("=" * 80)
print("用户列表")
print("=" * 80)

users = User.objects.filter(role='user').order_by('id')

print(f"{'用户ID':<10}{'用户名':<15}{'姓名':<10}{'年龄':<6}{'性别':<6}{'血型':<8}{'身高':<10}{'体重':<10}")
print("-" * 80)

for user in users:
    profile = user.profile
    gender = '男' if profile.gender == 'M' else '女' if profile.gender == 'F' else '其他'
    height = f"{profile.height_cm}cm" if profile.height_cm else '-'
    weight = f"{profile.weight_baseline_kg}kg" if profile.weight_baseline_kg else '-'
    print(f"{user.id:<10}{user.username:<15}{user.first_name + user.last_name:<10}{profile.age or '-':<6}{gender:<6}{profile.blood_type:<8}{height:<10}{weight:<10}")

print(f"\n总计: {users.count()} 个用户")

print("\n" + "=" * 80)
print("健康测量数据统计")
print("=" * 80)

total = Measurement.objects.count()
print(f"总测量记录数: {total}")
print(f"用户数量: {users.count()}")
print(f"平均每人测量次数: {total // users.count() if users.count() > 0 else 0}")

print("\n" + "=" * 80)
print("用户 user001 的最近5条测量记录")
print("=" * 80)

user = User.objects.get(username='user001')
measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:5]

print(f"{'测量时间':<20}{'体重(kg)':<12}{'收缩压':<10}{'舒张压':<10}{'血糖':<12}{'心率':<10}")
print("-" * 80)

for m in measurements:
    measured_at = m.measured_at.strftime('%Y-%m-%d %H:%M')
    weight = f"{m.weight_kg}" if m.weight_kg else '-'
    systolic = f"{m.systolic}" if m.systolic else '-'
    diastolic = f"{m.diastolic}" if m.diastolic else '-'
    glucose = f"{m.blood_glucose}" if m.blood_glucose else '-'
    heart_rate = f"{m.heart_rate}" if m.heart_rate else '-'
    
    print(f"{measured_at:<20}{weight:<12}{systolic:<10}{diastolic:<10}{glucose:<12}{heart_rate:<10}")

print("\n" + "=" * 80)
print("用户 user001 的健康数据统计")
print("=" * 80)

profile = user.profile
measurements = Measurement.objects.filter(user=user)

print(f"\n基本信息:")
print(f"  姓名: {user.first_name + user.last_name}")
print(f"  年龄: {profile.age or '-'}")
print(f"  性别: {'男' if profile.gender == 'M' else '女' if profile.gender == 'F' else '其他'}")
print(f"  血型: {profile.blood_type}")
print(f"  身高: {profile.height_cm or '-'} cm")
print(f"  基准体重: {profile.weight_baseline_kg or '-'} kg")

print(f"\n健康指标统计:")

weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
if weight_data:
    print(f"  体重: 最小={min(weight_data):.1f}kg, 最大={max(weight_data):.1f}kg, 平均={sum(weight_data)/len(weight_data):.1f}kg")

systolic_data = [m.systolic for m in measurements if m.systolic]
if systolic_data:
    print(f"  收缩压: 最小={min(systolic_data)}, 最大={max(systolic_data)}, 平均={sum(systolic_data)/len(systolic_data):.0f}")

diastolic_data = [m.diastolic for m in measurements if m.diastolic]
if diastolic_data:
    print(f"  舒张压: 最小={min(diastolic_data)}, 最大={max(diastolic_data)}, 平均={sum(diastolic_data)/len(diastolic_data):.0f}")

glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
if glucose_data:
    print(f"  血糖: 最小={min(glucose_data):.1f}, 最大={max(glucose_data):.1f}, 平均={sum(glucose_data)/len(glucose_data):.1f}")

heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
if heart_rate_data:
    print(f"  心率: 最小={min(heart_rate_data)}, 最大={max(heart_rate_data)}, 平均={sum(heart_rate_data)/len(heart_rate_data):.0f}")

print(f"\n测量记录数: {measurements.count()}")
print(f"最早记录: {measurements.earliest('measured_at').measured_at.strftime('%Y-%m-%d %H:%M')}")
print(f"最新记录: {measurements.latest('measured_at').measured_at.strftime('%Y-%m-%d %H:%M')}")

print("\n" + "=" * 80)
print("数据查看完成！")
print("=" * 80)
print("\n使用以下命令进行交互式操作:")
print("  - 查看数据: python view_data.py")
print("  - 修改数据: python modify_data.py")
print("=" * 80)
