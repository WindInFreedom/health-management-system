import os
import sys
import django
from datetime import datetime, timedelta
from decimal import Decimal

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

from django.contrib.auth import get_user_model
from measurements.models import Measurement

User = get_user_model()


class DataPreprocessor:
    def __init__(self):
        self.stats = {}

    def analyze_data(self):
        print("=" * 80)
        print("数据分析 - 健康测量数据")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        
        if not measurements.exists():
            print("没有找到测量数据\n")
            return
        
        print(f"总记录数: {measurements.count()}")
        
        users = User.objects.filter(role='user')
        print(f"用户数量: {users.count()}")
        
        for user in users:
            user_measurements = measurements.filter(user=user)
            if user_measurements.exists():
                self._analyze_user_data(user, user_measurements)
        
        self._print_global_statistics(measurements)

    def _analyze_user_data(self, user, measurements):
        profile = user.profile
        
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        systolic_data = [m.systolic for m in measurements if m.systolic]
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        
        print(f"\n用户: {user.username} ({user.first_name + user.last_name})")
        print(f"  测量记录数: {measurements.count()}")
        
        if weight_data:
            print(f"  体重 - 最小: {min(weight_data):.1f}kg, 最大: {max(weight_data):.1f}kg, 平均: {sum(weight_data)/len(weight_data):.1f}kg")
        
        if systolic_data:
            print(f"  收缩压 - 最小: {min(systolic_data)}, 最大: {max(systolic_data)}, 平均: {sum(systolic_data)/len(systolic_data):.0f}")
        
        if diastolic_data:
            print(f"  舒张压 - 最小: {min(diastolic_data)}, 最大: {max(diastolic_data)}, 平均: {sum(diastolic_data)/len(diastolic_data):.0f}")
        
        if glucose_data:
            print(f"  血糖 - 最小: {min(glucose_data):.1f}, 最大: {max(glucose_data):.1f}, 平均: {sum(glucose_data)/len(glucose_data):.1f}")
        
        if heart_rate_data:
            print(f"  心率 - 最小: {min(heart_rate_data)}, 最大: {max(heart_rate_data)}, 平均: {sum(heart_rate_data)/len(heart_rate_data):.0f}")

    def _print_global_statistics(self, measurements):
        print("\n" + "=" * 80)
        print("全局统计")
        print("=" * 80)
        
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        systolic_data = [m.systolic for m in measurements if m.systolic]
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        
        if weight_data:
            print(f"\n体重统计:")
            print(f"  总记录数: {len(weight_data)}")
            print(f"  范围: {min(weight_data):.1f}kg - {max(weight_data):.1f}kg")
            print(f"  平均值: {sum(weight_data)/len(weight_data):.1f}kg")
            print(f"  中位数: {sorted(weight_data)[len(weight_data)//2]:.1f}kg")
        
        if systolic_data and diastolic_data:
            print(f"\n血压统计:")
            print(f"  收缩压 - 范围: {min(systolic_data)} - {max(systolic_data)}, 平均: {sum(systolic_data)/len(systolic_data):.0f}")
            print(f"  舒张压 - 范围: {min(diastolic_data)} - {max(diastolic_data)}, 平均: {sum(diastolic_data)/len(diastolic_data):.0f}")
        
        if glucose_data:
            print(f"\n血糖统计:")
            print(f"  总记录数: {len(glucose_data)}")
            print(f"  范围: {min(glucose_data):.1f} - {max(glucose_data):.1f} mmol/L")
            print(f"  平均值: {sum(glucose_data)/len(glucose_data):.1f} mmol/L")
        
        if heart_rate_data:
            print(f"\n心率统计:")
            print(f"  总记录数: {len(heart_rate_data)}")
            print(f"  范围: {min(heart_rate_data)} - {max(heart_rate_data)} bpm")
            print(f"  平均值: {sum(heart_rate_data)/len(heart_rate_data):.0f} bpm")

    def normalize_data(self):
        print("\n" + "=" * 80)
        print("数据标准化")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        
        for user in User.objects.filter(role='user'):
            user_measurements = measurements.filter(user=user)
            profile = user.profile
            
            if not user_measurements.exists():
                continue
            
            print(f"\n处理用户: {user.username}")
            
            for measurement in user_measurements:
                if measurement.weight_kg and profile.weight_baseline_kg:
                    weight_diff = float(measurement.weight_kg) - float(profile.weight_baseline_kg)
                    weight_change_percent = (weight_diff / float(profile.weight_baseline_kg)) * 100
                    measurement.notes = f"体重变化: {weight_change_percent:+.1f}%"
                    measurement.save()
            
            print(f"  ✓ 标准化完成")

    def detect_anomalies(self):
        print("\n" + "=" * 80)
        print("异常检测")
        print("=" * 80)
        
        measurements = Measurement.objects.all()
        anomalies_found = 0
        
        for user in User.objects.filter(role='user'):
            user_measurements = measurements.filter(user=user)
            
            if not user_measurements.exists():
                continue
            
            weight_data = [float(m.weight_kg) for m in user_measurements if m.weight_kg]
            systolic_data = [m.systolic for m in user_measurements if m.systolic]
            diastolic_data = [m.diastolic for m in user_measurements if m.diastolic]
            glucose_data = [float(m.blood_glucose) for m in user_measurements if m.blood_glucose]
            heart_rate_data = [m.heart_rate for m in user_measurements if m.heart_rate]
            
            print(f"\n用户: {user.username}")
            
            if weight_data:
                mean_weight = sum(weight_data) / len(weight_data)
                std_weight = (sum((x - mean_weight) ** 2 for x in weight_data) / len(weight_data)) ** 0.5
                
                for measurement in user_measurements:
                    if measurement.weight_kg:
                        z_score = (float(measurement.weight_kg) - mean_weight) / std_weight if std_weight > 0 else 0
                        if abs(z_score) > 3:
                            print(f"  ⚠ 异常体重: {measurement.weight_kg}kg (Z-score: {z_score:.2f}) at {measurement.measured_at}")
                            anomalies_found += 1
            
            if systolic_data:
                mean_systolic = sum(systolic_data) / len(systolic_data)
                for measurement in user_measurements:
                    if measurement.systolic and measurement.systolic > 180:
                        print(f"  ⚠ 异常收缩压: {measurement.systolic} at {measurement.measured_at}")
                        anomalies_found += 1
            
            if glucose_data:
                for measurement in user_measurements:
                    if measurement.blood_glucose and float(measurement.blood_glucose) > 15:
                        print(f"  ⚠ 异常血糖: {measurement.blood_glucose} at {measurement.measured_at}")
                        anomalies_found += 1
            
            if heart_rate_data:
                for measurement in user_measurements:
                    if measurement.heart_rate and (measurement.heart_rate < 40 or measurement.heart_rate > 120):
                        print(f"  ⚠ 异常心率: {measurement.heart_rate} at {measurement.measured_at}")
                        anomalies_found += 1
        
        print(f"\n总计发现 {anomalies_found} 个异常值")

    def calculate_health_scores(self):
        print("\n" + "=" * 80)
        print("健康评分计算")
        print("=" * 80)
        
        for user in User.objects.filter(role='user'):
            user_measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:30]
            
            if not user_measurements.exists():
                continue
            
            weight_data = [float(m.weight_kg) for m in user_measurements if m.weight_kg]
            systolic_data = [m.systolic for m in user_measurements if m.systolic]
            diastolic_data = [m.diastolic for m in user_measurements if m.diastolic]
            glucose_data = [float(m.blood_glucose) for m in user_measurements if m.blood_glucose]
            heart_rate_data = [m.heart_rate for m in user_measurements if m.heart_rate]
            
            scores = []
            
            if weight_data:
                avg_weight = sum(weight_data) / len(weight_data)
                profile = user.profile
                if profile.weight_baseline_kg:
                    target_weight = float(profile.weight_baseline_kg)
                    weight_score = max(0, 100 - abs(avg_weight - target_weight) / target_weight * 100)
                    scores.append(weight_score)
            
            if systolic_data and diastolic_data:
                avg_systolic = sum(systolic_data) / len(systolic_data)
                avg_diastolic = sum(diastolic_data) / len(diastolic_data)
                
                if avg_systolic < 120 and avg_diastolic < 80:
                    bp_score = 100
                elif avg_systolic < 140 and avg_diastolic < 90:
                    bp_score = 80
                else:
                    bp_score = 60
                scores.append(bp_score)
            
            if glucose_data:
                avg_glucose = sum(glucose_data) / len(glucose_data)
                if avg_glucose < 5.6:
                    glucose_score = 100
                elif avg_glucose < 7.0:
                    glucose_score = 80
                else:
                    glucose_score = 60
                scores.append(glucose_score)
            
            if heart_rate_data:
                avg_heart_rate = sum(heart_rate_data) / len(heart_rate_data)
                if 60 <= avg_heart_rate <= 100:
                    heart_rate_score = 100
                elif avg_heart_rate <= 110:
                    heart_rate_score = 80
                else:
                    heart_rate_score = 60
                scores.append(heart_rate_score)
            
            if scores:
                overall_score = sum(scores) / len(scores)
                print(f"\n用户: {user.username} - 健康评分: {overall_score:.1f}/100")
            else:
                print(f"\n用户: {user.username} - 无足够数据计算评分")

    def run_preprocessing(self):
        print("\n" + "=" * 80)
        print("数据预处理流程")
        print("=" * 80)
        print()
        
        self.analyze_data()
        self.normalize_data()
        self.detect_anomalies()
        self.calculate_health_scores()
        
        print("\n" + "=" * 80)
        print("数据预处理完成")
        print("=" * 80)


if __name__ == '__main__':
    preprocessor = DataPreprocessor()
    preprocessor.run_preprocessing()
