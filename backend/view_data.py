import os
import sys
import django
from datetime import datetime

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile
from measurements.models import Measurement

User = get_user_model()


def display_users():
    print("=" * 80)
    print("用户列表")
    print("=" * 80)
    
    users = User.objects.filter(role='user').order_by('id')
    
    print(f"{'用户ID':<10}{'用户名':<15}{'姓名':<10}{'邮箱':<30}{'年龄':<6}{'性别':<6}{'血型':<8}")
    print("-" * 80)
    
    for user in users:
        profile = user.profile
        gender = '男' if profile.gender == 'M' else '女' if profile.gender == 'F' else '其他'
        print(f"{user.id:<10}{user.username:<15}{user.first_name + user.last_name:<10}{user.email:<30}{profile.age or '-':<6}{gender:<6}{profile.blood_type:<8}")
    
    print(f"\n总计: {users.count()} 个用户\n")


def display_measurements_summary():
    print("=" * 80)
    print("健康测量数据统计")
    print("=" * 80)
    
    total = Measurement.objects.count()
    users = User.objects.filter(role='user')
    
    print(f"总测量记录数: {total}")
    print(f"用户数量: {users.count()}")
    print(f"平均每人测量次数: {total // users.count() if users.count() > 0 else 0}")
    print()


def display_user_measurements(username, limit=20):
    print("=" * 80)
    print(f"用户 {username} 的测量记录 (最近 {limit} 条)")
    print("=" * 80)
    
    try:
        user = User.objects.get(username=username)
        measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:limit]
        
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
        
        print(f"\n总计: {measurements.count()} 条记录 (显示最近 {limit} 条)\n")
        
    except User.DoesNotExist:
        print(f"用户 {username} 不存在\n")


def display_user_stats(username):
    print("=" * 80)
    print(f"用户 {username} 的健康数据统计")
    print("=" * 80)
    
    try:
        user = User.objects.get(username=username)
        measurements = Measurement.objects.filter(user=user)
        profile = user.profile
        
        if not measurements.exists():
            print("该用户暂无测量数据\n")
            return
        
        print(f"\n基本信息:")
        print(f"  姓名: {user.first_name + user.last_name}")
        print(f"  年龄: {profile.age or '-'}")
        print(f"  性别: {'男' if profile.gender == 'M' else '女' if profile.gender == 'F' else '其他'}")
        print(f"  血型: {profile.blood_type}")
        print(f"  身高: {profile.height_cm or '-'} cm")
        print(f"  基准体重: {profile.weight_baseline_kg or '-'} kg")
        
        print(f"\n健康指标统计:")
        
        weight_data = [m.weight_kg for m in measurements if m.weight_kg]
        if weight_data:
            print(f"  体重: 最小={min(weight_data):.1f}kg, 最大={max(weight_data):.1f}kg, 平均={sum(weight_data)/len(weight_data):.1f}kg")
        
        systolic_data = [m.systolic for m in measurements if m.systolic]
        if systolic_data:
            print(f"  收缩压: 最小={min(systolic_data)}, 最大={max(systolic_data)}, 平均={sum(systolic_data)/len(systolic_data):.0f}")
        
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        if diastolic_data:
            print(f"  舒张压: 最小={min(diastolic_data)}, 最大={max(diastolic_data)}, 平均={sum(diastolic_data)/len(diastolic_data):.0f}")
        
        glucose_data = [m.blood_glucose for m in measurements if m.blood_glucose]
        if glucose_data:
            print(f"  血糖: 最小={min(glucose_data):.1f}, 最大={max(glucose_data):.1f}, 平均={sum(glucose_data)/len(glucose_data):.1f}")
        
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        if heart_rate_data:
            print(f"  心率: 最小={min(heart_rate_data)}, 最大={max(heart_rate_data)}, 平均={sum(heart_rate_data)/len(heart_rate_data):.0f}")
        
        print(f"\n测量记录数: {measurements.count()}")
        print(f"最早记录: {measurements.earliest('measured_at').measured_at.strftime('%Y-%m-%d %H:%M')}")
        print(f"最新记录: {measurements.latest('measured_at').measured_at.strftime('%Y-%m-%d %H:%M')}")
        print()
        
    except User.DoesNotExist:
        print(f"用户 {username} 不存在\n")


def display_all():
    display_users()
    display_measurements_summary()
    
    users = User.objects.filter(role='user')
    for user in users[:3]:
        display_user_stats(user.username)
        display_user_measurements(user.username, 5)


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("健康数据查看工具")
    print("=" * 80)
    print("\n请选择操作:")
    print("1. 查看所有用户")
    print("2. 查看数据统计")
    print("3. 查看指定用户的测量记录")
    print("4. 查看指定用户的健康统计")
    print("5. 查看所有数据概览")
    print("0. 退出")
    
    while True:
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            display_users()
        elif choice == '2':
            display_measurements_summary()
        elif choice == '3':
            username = input("请输入用户名 (例如: user001): ").strip()
            limit = input("显示记录数 (默认20): ").strip()
            limit = int(limit) if limit.isdigit() else 20
            display_user_measurements(username, limit)
        elif choice == '4':
            username = input("请输入用户名 (例如: user001): ").strip()
            display_user_stats(username)
        elif choice == '5':
            display_all()
        else:
            print("无效选项，请重新输入")
