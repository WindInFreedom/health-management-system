import os
import sys
import django
from datetime import datetime
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from users.models import Profile
from measurements.models import Measurement

User = get_user_model()


def modify_user_info():
    print("=" * 80)
    print("修改用户信息")
    print("=" * 80)
    
    username = input("请输入要修改的用户名 (例如: user001): ").strip()
    
    try:
        user = User.objects.get(username=username)
        profile = user.profile
        
        print(f"\n当前用户信息:")
        print(f"  用户名: {user.username}")
        print(f"  姓名: {user.first_name + user.last_name}")
        print(f"  邮箱: {user.email}")
        print(f"  年龄: {profile.age or '-'}")
        print(f"  性别: {'男' if profile.gender == 'M' else '女' if profile.gender == 'F' else '其他'}")
        print(f"  血型: {profile.blood_type}")
        print(f"  身高: {profile.height_cm or '-'} cm")
        print(f"  基准体重: {profile.weight_baseline_kg or '-'} kg")
        print(f"  简介: {profile.bio or '-'}")
        
        print("\n请选择要修改的字段:")
        print("1. 姓名")
        print("2. 邮箱")
        print("3. 年龄")
        print("4. 性别")
        print("5. 血型")
        print("6. 身高")
        print("7. 基准体重")
        print("8. 简介")
        print("0. 取消")
        
        choice = input("\n请输入选项 (0-8): ").strip()
        
        if choice == '1':
            name = input("请输入新姓名: ").strip()
            if name:
                user.first_name = name[0]
                user.last_name = name[1:] if len(name) > 1 else ''
                user.save()
                print("✓ 姓名修改成功")
        
        elif choice == '2':
            email = input("请输入新邮箱: ").strip()
            if email:
                user.email = email
                user.save()
                print("✓ 邮箱修改成功")
        
        elif choice == '3':
            age = input("请输入新年龄: ").strip()
            if age.isdigit():
                profile.age = int(age)
                profile.save()
                print("✓ 年龄修改成功")
        
        elif choice == '4':
            print("性别选项: M=男, F=女, O=其他")
            gender = input("请输入新性别: ").strip().upper()
            if gender in ['M', 'F', 'O']:
                profile.gender = gender
                profile.save()
                print("✓ 性别修改成功")
        
        elif choice == '5':
            print("血型选项: A, B, AB, O")
            blood_type = input("请输入新血型: ").strip().upper()
            if blood_type in ['A', 'B', 'AB', 'O']:
                profile.blood_type = blood_type
                profile.save()
                print("✓ 血型修改成功")
        
        elif choice == '6':
            height = input("请输入新身高: ").strip()
            try:
                profile.height_cm = Decimal(height)
                profile.save()
                print("✓ 身高修改成功")
            except:
                print("✗ 输入无效")
        
        elif choice == '7':
            weight = input("请输入新基准体重: ").strip()
            try:
                profile.weight_baseline_kg = Decimal(weight)
                profile.save()
                print("✓ 基准体重修改成功")
            except:
                print("✗ 输入无效")
        
        elif choice == '8':
            bio = input("请输入新简介: ").strip()
            profile.bio = bio
            profile.save()
            print("✓ 简介修改成功")
        
        elif choice == '0':
            print("取消修改")
        
        else:
            print("无效选项")
        
        print()
        
    except User.DoesNotExist:
        print(f"✗ 用户 {username} 不存在\n")


def modify_measurement():
    print("=" * 80)
    print("修改健康测量数据")
    print("=" * 80)
    
    username = input("请输入用户名 (例如: user001): ").strip()
    
    try:
        user = User.objects.get(username=username)
        measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:10]
        
        if not measurements.exists():
            print("该用户暂无测量数据\n")
            return
        
        print(f"\n最近10条测量记录:")
        for i, m in enumerate(measurements, 1):
            measured_at = m.measured_at.strftime('%Y-%m-%d %H:%M')
            print(f"{i}. {measured_at} - 体重:{m.weight_kg}kg 血压:{m.systolic}/{m.diastolic} 血糖:{m.blood_glucose} 心率:{m.heart_rate}")
        
        choice = input("\n请输入要修改的记录编号 (1-10), 或输入0取消: ").strip()
        
        if choice == '0':
            print("取消修改\n")
            return
        
        if choice.isdigit() and 1 <= int(choice) <= len(measurements):
            measurement = measurements[int(choice) - 1]
            
            print(f"\n当前记录信息:")
            print(f"  测量时间: {measurement.measured_at}")
            print(f"  体重: {measurement.weight_kg} kg")
            print(f"  收缩压: {measurement.systolic}")
            print(f"  舒张压: {measurement.diastolic}")
            print(f"  血糖: {measurement.blood_glucose} mmol/L")
            print(f"  心率: {measurement.heart_rate} bpm")
            print(f"  备注: {measurement.notes or '-'}")
            
            print("\n请选择要修改的字段:")
            print("1. 体重")
            print("2. 收缩压")
            print("3. 舒张压")
            print("4. 血糖")
            print("5. 心率")
            print("6. 备注")
            print("0. 取消")
            
            field_choice = input("\n请输入选项 (0-6): ").strip()
            
            if field_choice == '1':
                value = input("请输入新体重: ").strip()
                try:
                    measurement.weight_kg = Decimal(value)
                    measurement.save()
                    print("✓ 体重修改成功")
                except:
                    print("✗ 输入无效")
            
            elif field_choice == '2':
                value = input("请输入新收缩压: ").strip()
                if value.isdigit():
                    measurement.systolic = int(value)
                    measurement.save()
                    print("✓ 收缩压修改成功")
                else:
                    print("✗ 输入无效")
            
            elif field_choice == '3':
                value = input("请输入新舒张压: ").strip()
                if value.isdigit():
                    measurement.diastolic = int(value)
                    measurement.save()
                    print("✓ 舒张压修改成功")
                else:
                    print("✗ 输入无效")
            
            elif field_choice == '4':
                value = input("请输入新血糖: ").strip()
                try:
                    measurement.blood_glucose = Decimal(value)
                    measurement.save()
                    print("✓ 血糖修改成功")
                except:
                    print("✗ 输入无效")
            
            elif field_choice == '5':
                value = input("请输入新心率: ").strip()
                if value.isdigit():
                    measurement.heart_rate = int(value)
                    measurement.save()
                    print("✓ 心率修改成功")
                else:
                    print("✗ 输入无效")
            
            elif field_choice == '6':
                value = input("请输入新备注: ").strip()
                measurement.notes = value
                measurement.save()
                print("✓ 备注修改成功")
            
            elif field_choice == '0':
                print("取消修改")
            
            else:
                print("无效选项")
            
            print()
        
        else:
            print("✗ 无效的记录编号\n")
        
    except User.DoesNotExist:
        print(f"✗ 用户 {username} 不存在\n")


def add_measurement():
    print("=" * 80)
    print("添加健康测量数据")
    print("=" * 80)
    
    username = input("请输入用户名 (例如: user001): ").strip()
    
    try:
        user = User.objects.get(username=username)
        
        print(f"\n用户: {user.first_name + user.last_name}")
        
        measured_at = input("请输入测量时间 (格式: YYYY-MM-DD HH:MM, 留空使用当前时间): ").strip()
        if measured_at:
            try:
                measured_at = datetime.strptime(measured_at, '%Y-%m-%d %H:%M')
            except:
                print("✗ 时间格式错误，使用当前时间")
                measured_at = datetime.now()
        else:
            measured_at = datetime.now()
        
        weight = input("请输入体重: ").strip()
        systolic = input("请输入收缩压: ").strip()
        diastolic = input("请输入舒张压: ").strip()
        glucose = input("请输入血糖: ").strip()
        heart_rate = input("请输入心率: ").strip()
        notes = input("请输入备注 (可选): ").strip()
        
        measurement = Measurement.objects.create(
            user=user,
            measured_at=measured_at,
            weight_kg=Decimal(weight) if weight else None,
            systolic=int(systolic) if systolic else None,
            diastolic=int(diastolic) if diastolic else None,
            blood_glucose=Decimal(glucose) if glucose else None,
            heart_rate=int(heart_rate) if heart_rate else None,
            notes=notes
        )
        
        print("✓ 测量记录添加成功\n")
        
    except User.DoesNotExist:
        print(f"✗ 用户 {username} 不存在\n")
    except Exception as e:
        print(f"✗ 添加失败: {e}\n")


def delete_user():
    print("=" * 80)
    print("删除用户")
    print("=" * 80)
    
    username = input("请输入要删除的用户名: ").strip()
    
    try:
        user = User.objects.get(username=username)
        
        print(f"\n用户信息:")
        print(f"  用户名: {user.username}")
        print(f"  姓名: {user.first_name + user.last_name}")
        print(f"  邮箱: {user.email}")
        
        confirm = input("\n确认删除该用户及其所有数据? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            user.delete()
            print("✓ 用户及其所有数据已删除\n")
        else:
            print("取消删除\n")
        
    except User.DoesNotExist:
        print(f"✗ 用户 {username} 不存在\n")


def delete_measurements():
    print("=" * 80)
    print("删除健康测量数据")
    print("=" * 80)
    
    username = input("请输入用户名: ").strip()
    
    try:
        user = User.objects.get(username=username)
        count = Measurement.objects.filter(user=user).count()
        
        print(f"\n用户 {username} 共有 {count} 条测量记录")
        
        confirm = input("\n确认删除该用户的所有测量数据? (yes/no): ").strip().lower()
        
        if confirm == 'yes':
            Measurement.objects.filter(user=user).delete()
            print(f"✓ 已删除 {count} 条测量记录\n")
        else:
            print("取消删除\n")
        
    except User.DoesNotExist:
        print(f"✗ 用户 {username} 不存在\n")


if __name__ == '__main__':
    print("\n" + "=" * 80)
    print("健康数据修改工具")
    print("=" * 80)
    
    while True:
        print("\n请选择操作:")
        print("1. 修改用户信息")
        print("2. 修改健康测量数据")
        print("3. 添加健康测量数据")
        print("4. 删除用户")
        print("5. 删除用户的测量数据")
        print("0. 退出")
        
        choice = input("\n请输入选项 (0-5): ").strip()
        
        if choice == '0':
            print("退出程序")
            break
        elif choice == '1':
            modify_user_info()
        elif choice == '2':
            modify_measurement()
        elif choice == '3':
            add_measurement()
        elif choice == '4':
            delete_user()
        elif choice == '5':
            delete_measurements()
        else:
            print("无效选项，请重新输入")
