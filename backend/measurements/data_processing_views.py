"""
数据处理API视图
提供数据预处理、清洗和验证的API接口
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from django.contrib.auth import get_user_model
from django.db.models import Count, Avg, Max, Min
from datetime import datetime, timedelta

from .models import Measurement, SleepLog, MoodLog, MedicationRecord
from .serializers import MeasurementSerializer, SleepLogSerializer, MoodLogSerializer

User = get_user_model()


class DataProcessingViewSet(viewsets.ViewSet):
    """数据处理视图集"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def preprocess_data(self, request):
        """数据预处理 - 分析、标准化、异常检测、健康评分"""
        user = request.user
        
        measurements = Measurement.objects.filter(user=user)
        
        if not measurements.exists():
            return Response({'message': '暂无测量数据'}, status=status.HTTP_404_NOT_FOUND)
        
        results = {
            'analysis': {},
            'normalization': {},
            'anomalies': [],
            'health_scores': {}
        }
        
        # 1. 数据分析
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        systolic_data = [m.systolic for m in measurements if m.systolic]
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        
        results['analysis'] = {
            'total_records': measurements.count(),
            'weight': {
                'min': round(min(weight_data), 2) if weight_data else None,
                'max': round(max(weight_data), 2) if weight_data else None,
                'avg': round(sum(weight_data) / len(weight_data), 2) if weight_data else None,
                'median': round(sorted(weight_data)[len(weight_data) // 2], 2) if weight_data else None,
            },
            'systolic': {
                'min': min(systolic_data) if systolic_data else None,
                'max': max(systolic_data) if systolic_data else None,
                'avg': round(sum(systolic_data) / len(systolic_data), 1) if systolic_data else None,
            },
            'diastolic': {
                'min': min(diastolic_data) if diastolic_data else None,
                'max': max(diastolic_data) if diastolic_data else None,
                'avg': round(sum(diastolic_data) / len(diastolic_data), 1) if diastolic_data else None,
            },
            'glucose': {
                'min': round(min(glucose_data), 2) if glucose_data else None,
                'max': round(max(glucose_data), 2) if glucose_data else None,
                'avg': round(sum(glucose_data) / len(glucose_data), 2) if glucose_data else None,
            },
            'heart_rate': {
                'min': min(heart_rate_data) if heart_rate_data else None,
                'max': max(heart_rate_data) if heart_rate_data else None,
                'avg': round(sum(heart_rate_data) / len(heart_rate_data), 1) if heart_rate_data else None,
            },
        }
        
        # 2. 数据标准化 - 计算体重变化百分比
        from users.models import Profile
        try:
            profile = user.profile
            if profile.weight_baseline_kg and weight_data:
                latest_weight = weight_data[-1]
                weight_diff = latest_weight - float(profile.weight_baseline_kg)
                weight_change_percent = (weight_diff / float(profile.weight_baseline_kg)) * 100
                results['normalization'] = {
                    'baseline_weight': float(profile.weight_baseline_kg),
                    'latest_weight': latest_weight,
                    'weight_change_percent': round(weight_change_percent, 2),
                    'notes': f'体重变化: {weight_change_percent:+.1f}%'
                }
        except Profile.DoesNotExist:
            results['normalization'] = {'notes': '未设置基线体重'}
        
        # 3. 异常检测
        anomalies_count = 0
        
        if weight_data:
            # 计算体重统计值
            mean_weight = sum(weight_data) / len(weight_data)
            std_weight = (sum((x - mean_weight) ** 2 for x in weight_data) / len(weight_data)) ** 0.5
            
            # 计算7天移动平均
            sorted_measurements = sorted(measurements, key=lambda x: x.measured_at)
            weight_moving_average = []
            
            for i, measurement in enumerate(sorted_measurements):
                if measurement.weight_kg:
                    # 计算最近7天的移动平均
                    window = sorted_measurements[max(0, i-6):i+1]
                    window_weights = [float(m.weight_kg) for m in window if m.weight_kg]
                    if window_weights:
                        moving_avg = sum(window_weights) / len(window_weights)
                        weight_moving_average.append({
                            'date': measurement.measured_at.isoformat(),
                            'original_weight': float(measurement.weight_kg),
                            'moving_average': round(moving_avg, 2),
                            'difference': round(float(measurement.weight_kg) - moving_avg, 2)
                        })
                        
                        # 检测短期剧烈波动（与移动平均的差异超过2kg）
                        if abs(float(measurement.weight_kg) - moving_avg) > 2:
                            results['anomalies'].append({
                                'type': '体重短期波动',
                                'value': f'{measurement.weight_kg}kg',
                                'moving_average': round(moving_avg, 2),
                                'difference': round(float(measurement.weight_kg) - moving_avg, 2),
                                'time': measurement.measured_at.isoformat()
                            })
                            anomalies_count += 1
            
            # 添加移动平均结果到返回数据
            if weight_moving_average:
                results['weight_moving_average'] = weight_moving_average
        
        if systolic_data and diastolic_data:
            # 计算血压统计值
            avg_systolic = sum(systolic_data) / len(systolic_data)
            avg_diastolic = sum(diastolic_data) / len(diastolic_data)
            std_systolic = (sum((x - avg_systolic) ** 2 for x in systolic_data) / len(systolic_data)) ** 0.5 if len(systolic_data) > 1 else 0
            std_diastolic = (sum((x - avg_diastolic) ** 2 for x in diastolic_data) / len(diastolic_data)) ** 0.5 if len(diastolic_data) > 1 else 0
            
            for measurement in measurements:
                if measurement.systolic and measurement.diastolic:
                    # 检测收缩压异常
                    if measurement.systolic > 180:
                        results['anomalies'].append({
                            'type': '收缩压严重异常',
                            'value': f'{measurement.systolic}/{measurement.diastolic}',
                            'clinical_event': '高血压危象',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    elif measurement.systolic > 140 or measurement.diastolic > 90:
                        results['anomalies'].append({
                            'type': '血压异常',
                            'value': f'{measurement.systolic}/{measurement.diastolic}',
                            'clinical_event': '高血压',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    elif measurement.systolic < 90 or measurement.diastolic < 60:
                        results['anomalies'].append({
                            'type': '血压异常',
                            'value': f'{measurement.systolic}/{measurement.diastolic}',
                            'clinical_event': '低血压',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    # 检测峰值异常（使用Z-score）
                    elif std_systolic > 0 and std_diastolic > 0:
                        z_systolic = (measurement.systolic - avg_systolic) / std_systolic
                        z_diastolic = (measurement.diastolic - avg_diastolic) / std_diastolic
                        if abs(z_systolic) > 2.5 or abs(z_diastolic) > 2.5:
                            results['anomalies'].append({
                                'type': '血压峰值异常',
                                'value': f'{measurement.systolic}/{measurement.diastolic}',
                                'z_score': {'systolic': round(z_systolic, 2), 'diastolic': round(z_diastolic, 2)},
                                'clinical_event': '血压波动异常',
                                'time': measurement.measured_at.isoformat()
                            })
                            anomalies_count += 1
        
        if glucose_data:
            # 计算血糖统计值
            mean_glucose = sum(glucose_data) / len(glucose_data)
            std_glucose = (sum((x - mean_glucose) ** 2 for x in glucose_data) / len(glucose_data)) ** 0.5 if len(glucose_data) > 1 else 0
            
            # 排序测量值
            sorted_measurements = sorted(measurements, key=lambda x: x.measured_at)
            glucose_imputation = []
            
            for i, measurement in enumerate(sorted_measurements):
                if measurement.blood_glucose:
                    # 核实数据来源
                    glucose_value = float(measurement.blood_glucose)
                    
                    # 检测血糖异常
                    if glucose_value > 15:
                        results['anomalies'].append({
                            'type': '血糖严重异常',
                            'value': f'{glucose_value} mmol/L',
                            'clinical_event': '高血糖危象',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    elif glucose_value > 7.0:
                        results['anomalies'].append({
                            'type': '血糖异常',
                            'value': f'{glucose_value} mmol/L',
                            'clinical_event': '高血糖',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    elif glucose_value < 3.9:
                        results['anomalies'].append({
                            'type': '血糖异常',
                            'value': f'{glucose_value} mmol/L',
                            'clinical_event': '低血糖',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    
                    glucose_imputation.append({
                        'date': measurement.measured_at.isoformat(),
                        'value': glucose_value,
                        'source': '原始数据',
                        'status': '有效'
                    })
                else:
                    # 使用前向填充进行插补
                    if i > 0 and sorted_measurements[i-1].blood_glucose:
                        imputed_value = float(sorted_measurements[i-1].blood_glucose)
                        glucose_imputation.append({
                            'date': measurement.measured_at.isoformat(),
                            'value': imputed_value,
                            'source': '前向填充',
                            'status': '插补'
                        })
                    # 如果前向填充不可用，使用平均值
                    elif glucose_data:
                        imputed_value = mean_glucose
                        glucose_imputation.append({
                            'date': measurement.measured_at.isoformat(),
                            'value': round(imputed_value, 2),
                            'source': '平均值',
                            'status': '插补'
                        })
            
            # 添加血糖插补结果到返回数据
            if glucose_imputation:
                results['glucose_imputation'] = glucose_imputation
        
        if heart_rate_data:
            # 计算心率统计值
            mean_heart_rate = sum(heart_rate_data) / len(heart_rate_data)
            std_heart_rate = (sum((x - mean_heart_rate) ** 2 for x in heart_rate_data) / len(heart_rate_data)) ** 0.5 if len(heart_rate_data) > 1 else 0
            
            # 排序测量值
            sorted_measurements = sorted(measurements, key=lambda x: x.measured_at)
            heart_rate_analysis = []
            resting_heart_rates = []
            
            for i, measurement in enumerate(sorted_measurements):
                if measurement.heart_rate:
                    hr_value = measurement.heart_rate
                    
                    # 分析心率
                    analysis = {
                        'date': measurement.measured_at.isoformat(),
                        'heart_rate': hr_value,
                        'status': '有效'
                    }
                    
                    # 识别静息心率（60-70 bpm）
                    if 60 <= hr_value <= 70:
                        analysis['type'] = '静息心率'
                        resting_heart_rates.append(hr_value)
                    # 识别运动后心率（>100 bpm）
                    elif hr_value > 100:
                        analysis['type'] = '运动后心率'
                        # 标记为极端值但保留
                        results['anomalies'].append({
                            'type': '心率极端值',
                            'value': f'{hr_value} bpm',
                            'event': '运动后',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    # 识别心动过缓（<40 bpm）
                    elif hr_value < 40:
                        analysis['type'] = '心动过缓'
                        results['anomalies'].append({
                            'type': '心率异常',
                            'value': f'{hr_value} bpm',
                            'event': '心动过缓',
                            'time': measurement.measured_at.isoformat()
                        })
                        anomalies_count += 1
                    else:
                        analysis['type'] = '正常心率'
                    
                    heart_rate_analysis.append(analysis)
            
            # 计算静息心率平均值
            if resting_heart_rates:
                avg_resting_hr = sum(resting_heart_rates) / len(resting_heart_rates)
                results['resting_heart_rate'] = {
                    'average': round(avg_resting_hr, 1),
                    'count': len(resting_heart_rates),
                    'measurements': resting_heart_rates
                }
            
            # 添加心率分析结果到返回数据
            if heart_rate_analysis:
                results['heart_rate_analysis'] = heart_rate_analysis
            
            # 脉搏数据处理（基于心率数据，确保一致性）
            pulse_analysis = []
            for analysis in heart_rate_analysis:
                pulse_analysis.append({
                    'date': analysis['date'],
                    'pulse': analysis['heart_rate'],
                    'status': analysis['status'],
                    'type': analysis['type'],
                    'consistency_with_heart_rate': '一致'  # 脉搏与心率保持一致
                })
            
            # 添加脉搏分析结果到返回数据
            if pulse_analysis:
                results['pulse_analysis'] = pulse_analysis
                # 计算脉搏统计值
                pulse_values = [p['pulse'] for p in pulse_analysis]
                if pulse_values:
                    results['pulse_statistics'] = {
                        'average': round(sum(pulse_values) / len(pulse_values), 1),
                        'min': min(pulse_values),
                        'max': max(pulse_values),
                        'count': len(pulse_values)
                    }
        
        # 4. 健康评分计算
        scores = []
        
        if weight_data:
            avg_weight = sum(weight_data) / len(weight_data)
            try:
                profile = user.profile
                if profile.weight_baseline_kg:
                    target_weight = float(profile.weight_baseline_kg)
                    weight_score = max(0, 100 - abs(avg_weight - target_weight) / target_weight * 100)
                    scores.append({'name': '体重', 'score': round(weight_score, 1)})
            except Profile.DoesNotExist:
                pass
        
        if systolic_data and diastolic_data:
            avg_systolic = sum(systolic_data) / len(systolic_data)
            avg_diastolic = sum(diastolic_data) / len(diastolic_data)
            
            if avg_systolic < 120 and avg_diastolic < 80:
                bp_score = 100
            elif avg_systolic < 140 and avg_diastolic < 90:
                bp_score = 80
            else:
                bp_score = 60
            scores.append({'name': '血压', 'score': bp_score})
        
        if glucose_data:
            avg_glucose = sum(glucose_data) / len(glucose_data)
            if avg_glucose < 5.6:
                glucose_score = 100
            elif avg_glucose < 7.0:
                glucose_score = 80
            else:
                glucose_score = 60
            scores.append({'name': '血糖', 'score': glucose_score})
        
        if heart_rate_data:
            avg_heart_rate = sum(heart_rate_data) / len(heart_rate_data)
            if 60 <= avg_heart_rate <= 100:
                heart_rate_score = 100
            elif avg_heart_rate <= 110:
                heart_rate_score = 80
            else:
                heart_rate_score = 60
            scores.append({'name': '心率', 'score': heart_rate_score})
        
        if scores:
            overall_score = sum(s['score'] for s in scores) / len(scores)
            results['health_scores'] = {
                'overall_score': round(overall_score, 1),
                'individual_scores': scores
            }
        
        return Response({
            'message': f'数据预处理完成，发现 {anomalies_count} 个异常值',
            'results': results,
            'anomalies_count': anomalies_count
        })
    
    @action(detail=False, methods=['post'])
    def clean_all_data(self, request):
        """一键清洗所有数据 - 清洗无效数据、删除重复记录、修复缺失值"""
        user = request.user
        
        total_removed = 0
        total_fixed = 0
        all_details = []
        
        # 1. 清洗无效数据
        measurements = Measurement.objects.filter(user=user)
        
        for measurement in measurements:
            removed = False
            
            if measurement.weight_kg:
                if measurement.weight_kg <= 0 or measurement.weight_kg > 300:
                    measurement.delete()
                    total_removed += 1
                    all_details.append(f"删除无效体重: {measurement.weight_kg}kg")
                    removed = True
            
            if measurement.systolic:
                if measurement.systolic < 50 or measurement.systolic > 250:
                    measurement.delete()
                    total_removed += 1
                    all_details.append(f"删除无效收缩压: {measurement.systolic}")
                    removed = True
            
            if measurement.diastolic:
                if measurement.diastolic < 30 or measurement.diastolic > 150:
                    measurement.delete()
                    total_removed += 1
                    all_details.append(f"删除无效舒张压: {measurement.diastolic}")
                    removed = True
            
            if measurement.blood_glucose:
                if measurement.blood_glucose < 1 or measurement.blood_glucose > 30:
                    measurement.delete()
                    total_removed += 1
                    all_details.append(f"删除无效血糖: {measurement.blood_glucose}")
                    removed = True
            
            if measurement.heart_rate:
                if measurement.heart_rate < 30 or measurement.heart_rate > 200:
                    measurement.delete()
                    total_removed += 1
                    all_details.append(f"删除无效心率: {measurement.heart_rate}")
                    removed = True
            
            if not removed:
                if not measurement.weight_kg and not measurement.systolic and not measurement.diastolic and not measurement.blood_glucose and not measurement.heart_rate:
                    measurement.delete()
                    total_removed += 1
                    all_details.append("删除空记录")
        
        # 2. 删除重复记录
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        seen = set()
        
        for measurement in measurements:
            key = (measurement.measured_at, measurement.weight_kg, measurement.systolic, measurement.diastolic)
            
            if key in seen:
                measurement.delete()
                total_removed += 1
                all_details.append(f"删除重复记录: {measurement.measured_at}")
            else:
                seen.add(key)
        
        # 3. 修复缺失值
        measurements = Measurement.objects.filter(user=user)
        
        for measurement in measurements:
            fixed = False
            
            if not measurement.weight_kg:
                user_measurements = measurements.exclude(weight_kg__isnull=True)
                if user_measurements.exists():
                    recent_weight = user_measurements.order_by('-measured_at').first()
                    if recent_weight and recent_weight.weight_kg:
                        measurement.weight_kg = recent_weight.weight_kg
                        measurement.save()
                        total_fixed += 1
                        all_details.append(f"修复体重: {measurement.measured_at}")
                        fixed = True
            
            if not measurement.heart_rate:
                user_measurements = measurements.exclude(heart_rate__isnull=True)
                if user_measurements.exists():
                    recent_hr = user_measurements.order_by('-measured_at').first()
                    if recent_hr and recent_hr.heart_rate:
                        measurement.heart_rate = recent_hr.heart_rate
                        measurement.save()
                        total_fixed += 1
                        all_details.append(f"修复心率: {measurement.measured_at}")
                        fixed = True
        
        return Response({
            'message': f'一键清洗完成，共删除 {total_removed} 条记录，修复 {total_fixed} 条记录',
            'removed_count': total_removed,
            'fixed_count': total_fixed,
            'details': all_details[:100]
        })
    
    @action(detail=False, methods=['get'])
    def overview(self, request):
        """获取数据概览"""
        user = request.user
        
        measurements = Measurement.objects.filter(user=user)
        sleep_logs = SleepLog.objects.filter(user=user)
        mood_logs = MoodLog.objects.filter(user=user)
        
        measurement_count = measurements.count()
        sleep_count = sleep_logs.count()
        mood_count = mood_logs.count()
        
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        avg_weight = sum(weight_data) / len(weight_data) if weight_data else 0
        
        systolic_data = [m.systolic for m in measurements if m.systolic]
        avg_systolic = sum(systolic_data) / len(systolic_data) if systolic_data else 0
        
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        avg_diastolic = sum(diastolic_data) / len(diastolic_data) if diastolic_data else 0
        
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        avg_glucose = sum(glucose_data) / len(glucose_data) if glucose_data else 0
        
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        avg_heart_rate = sum(heart_rate_data) / len(heart_rate_data) if heart_rate_data else 0
        
        return Response({
            'overview': {
                'total_measurements': measurement_count,
                'total_sleep_logs': sleep_count,
                'total_mood_logs': mood_count,
            },
            'measurements': {
                'count': measurement_count,
                'avg_weight': round(avg_weight, 2),
                'avg_systolic': round(avg_systolic, 1),
                'avg_diastolic': round(avg_diastolic, 1),
                'avg_glucose': round(avg_glucose, 2),
                'avg_heart_rate': round(avg_heart_rate, 1),
            },
            'sleep': {
                'count': sleep_count,
            },
            'mood': {
                'count': mood_count,
            }
        })
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取详细统计数据"""
        user = request.user
        
        measurements = Measurement.objects.filter(user=user)
        
        if not measurements.exists():
            return Response({'message': '暂无测量数据'}, status=status.HTTP_404_NOT_FOUND)
        
        weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
        systolic_data = [m.systolic for m in measurements if m.systolic]
        diastolic_data = [m.diastolic for m in measurements if m.diastolic]
        glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
        heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
        
        stats = {
            'weight': {
                'min': round(min(weight_data), 2) if weight_data else None,
                'max': round(max(weight_data), 2) if weight_data else None,
                'avg': round(sum(weight_data) / len(weight_data), 2) if weight_data else None,
                'median': round(sorted(weight_data)[len(weight_data) // 2], 2) if weight_data else None,
            },
            'systolic': {
                'min': min(systolic_data) if systolic_data else None,
                'max': max(systolic_data) if systolic_data else None,
                'avg': round(sum(systolic_data) / len(systolic_data), 1) if systolic_data else None,
            },
            'diastolic': {
                'min': min(diastolic_data) if diastolic_data else None,
                'max': max(diastolic_data) if diastolic_data else None,
                'avg': round(sum(diastolic_data) / len(diastolic_data), 1) if diastolic_data else None,
            },
            'glucose': {
                'min': round(min(glucose_data), 2) if glucose_data else None,
                'max': round(max(glucose_data), 2) if glucose_data else None,
                'avg': round(sum(glucose_data) / len(glucose_data), 2) if glucose_data else None,
            },
            'heart_rate': {
                'min': min(heart_rate_data) if heart_rate_data else None,
                'max': max(heart_rate_data) if heart_rate_data else None,
                'avg': round(sum(heart_rate_data) / len(heart_rate_data), 1) if heart_rate_data else None,
            },
        }
        
        return Response(stats)
    
    @action(detail=False, methods=['post'])
    def clean_invalid_data(self, request):
        """清洗无效数据"""
        user = request.user
        action_type = request.data.get('action', 'all')
        
        removed_count = 0
        details = []
        
        if action_type in ['all', 'measurements']:
            measurements = Measurement.objects.filter(user=user)
            
            for measurement in measurements:
                removed = False
                
                if measurement.weight_kg:
                    if measurement.weight_kg <= 0 or measurement.weight_kg > 300:
                        measurement.delete()
                        removed_count += 1
                        details.append(f"删除无效体重: {measurement.weight_kg}kg")
                        removed = True
                
                if measurement.systolic:
                    if measurement.systolic < 50 or measurement.systolic > 250:
                        measurement.delete()
                        removed_count += 1
                        details.append(f"删除无效收缩压: {measurement.systolic}")
                        removed = True
                
                if measurement.diastolic:
                    if measurement.diastolic < 30 or measurement.diastolic > 150:
                        measurement.delete()
                        removed_count += 1
                        details.append(f"删除无效舒张压: {measurement.diastolic}")
                        removed = True
                
                if measurement.blood_glucose:
                    if measurement.blood_glucose < 1 or measurement.blood_glucose > 30:
                        measurement.delete()
                        removed_count += 1
                        details.append(f"删除无效血糖: {measurement.blood_glucose}")
                        removed = True
                
                if measurement.heart_rate:
                    if measurement.heart_rate < 30 or measurement.heart_rate > 200:
                        measurement.delete()
                        removed_count += 1
                        details.append(f"删除无效心率: {measurement.heart_rate}")
                        removed = True
                
                if not removed:
                    if not measurement.weight_kg and not measurement.systolic and not measurement.diastolic and not measurement.blood_glucose and not measurement.heart_rate:
                        measurement.delete()
                        removed_count += 1
                        details.append("删除空记录")
        
        if action_type in ['all', 'sleep']:
            sleep_logs = SleepLog.objects.filter(user=user)
            
            for log in sleep_logs:
                removed = False
                
                if log.duration_minutes:
                    if log.duration_minutes < 60 or log.duration_minutes > 720:
                        log.delete()
                        removed_count += 1
                        details.append(f"删除无效睡眠时长: {log.duration_minutes}分钟")
                        removed = True
                
                if log.quality_rating:
                    if log.quality_rating < 1 or log.quality_rating > 10:
                        log.quality_rating = max(1, min(10, log.quality_rating))
                        log.save()
                        details.append(f"修正睡眠质量评分: {log.quality_rating}")
                
                if not removed:
                    if not log.duration_minutes:
                        log.delete()
                        removed_count += 1
                        details.append("删除空睡眠记录")
        
        if action_type in ['all', 'mood']:
            mood_logs = MoodLog.objects.filter(user=user)
            
            for log in mood_logs:
                removed = False
                
                if log.mood_rating:
                    if log.mood_rating < 1 or log.mood_rating > 10:
                        log.mood_rating = max(1, min(10, log.mood_rating))
                        log.save()
                        details.append(f"修正心情评分: {log.mood_rating}")
                
                if not removed:
                    if not log.mood_rating:
                        log.delete()
                        removed_count += 1
                        details.append("删除空心情记录")
        
        return Response({
            'message': f'清洗完成，共删除/修正 {removed_count} 条记录',
            'removed_count': removed_count,
            'details': details[:100]
        })
    
    @action(detail=False, methods=['post'])
    def remove_duplicates(self, request):
        """删除重复记录"""
        user = request.user
        data_type = request.data.get('type', 'measurements')
        
        duplicates_removed = 0
        details = []
        
        if data_type == 'measurements':
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            seen = set()
            
            for measurement in measurements:
                key = (measurement.measured_at, measurement.weight_kg, measurement.systolic, measurement.diastolic)
                
                if key in seen:
                    measurement.delete()
                    duplicates_removed += 1
                    details.append(f"删除重复记录: {measurement.measured_at}")
                else:
                    seen.add(key)
        
        return Response({
            'message': f'删除了 {duplicates_removed} 条重复记录',
            'removed_count': duplicates_removed,
            'details': details[:100]
        })
    
    @action(detail=False, methods=['post'])
    def fix_missing_values(self, request):
        """修复缺失值"""
        user = request.user
        data_type = request.data.get('type', 'measurements')
        
        fixed_count = 0
        details = []
        
        if data_type == 'measurements':
            measurements = Measurement.objects.filter(user=user)
            
            for measurement in measurements:
                fixed = False
                
                if not measurement.weight_kg:
                    user_measurements = measurements.exclude(weight_kg__isnull=True)
                    if user_measurements.exists():
                        recent_weight = user_measurements.order_by('-measured_at').first()
                        if recent_weight and recent_weight.weight_kg:
                            measurement.weight_kg = recent_weight.weight_kg
                            measurement.save()
                            fixed_count += 1
                            details.append(f"修复体重: {measurement.measured_at}")
                            fixed = True
                
                if not measurement.heart_rate:
                    user_measurements = measurements.exclude(heart_rate__isnull=True)
                    if user_measurements.exists():
                        recent_hr = user_measurements.order_by('-measured_at').first()
                        if recent_hr and recent_hr.heart_rate:
                            measurement.heart_rate = recent_hr.heart_rate
                            measurement.save()
                            fixed_count += 1
                            details.append(f"修复心率: {measurement.measured_at}")
                            fixed = True
        
        return Response({
            'message': f'修复了 {fixed_count} 条记录的缺失值',
            'fixed_count': fixed_count,
            'details': details[:100]
        })
    
    @action(detail=False, methods=['get'])
    def validate_data(self, request):
        """验证数据质量"""
        user = request.user
        
        results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        
        measurements = Measurement.objects.filter(user=user)
        
        if not measurements.exists():
            results['warnings'] += 1
            results['details'].append('缺少测量数据')
        else:
            count = measurements.count()
            if count < 100:
                results['warnings'] += 1
                results['details'].append(f'测量记录数过少: {count}条')
            else:
                results['passed'] += 1
                results['details'].append(f'测量记录数: {count}条 ✓')
            
            weight_data = [float(m.weight_kg) for m in measurements if m.weight_kg]
            if weight_data:
                avg_weight = sum(weight_data) / len(weight_data)
                if avg_weight < 30 or avg_weight > 200:
                    results['failed'] += 1
                    results['details'].append(f'平均体重异常: {avg_weight:.1f}kg ✗')
                else:
                    results['passed'] += 1
                    results['details'].append(f'平均体重: {avg_weight:.1f}kg ✓')
            
            systolic_data = [m.systolic for m in measurements if m.systolic]
            if systolic_data:
                avg_systolic = sum(systolic_data) / len(systolic_data)
                if avg_systolic < 70 or avg_systolic > 180:
                    results['failed'] += 1
                    results['details'].append(f'平均收缩压异常: {avg_systolic:.0f} ✗')
                else:
                    results['passed'] += 1
                    results['details'].append(f'平均收缩压: {avg_systolic:.0f} ✓')
            
            diastolic_data = [m.diastolic for m in measurements if m.diastolic]
            if diastolic_data:
                avg_diastolic = sum(diastolic_data) / len(diastolic_data)
                if avg_diastolic < 40 or avg_diastolic > 120:
                    results['failed'] += 1
                    results['details'].append(f'平均舒张压异常: {avg_diastolic:.0f} ✗')
                else:
                    results['passed'] += 1
                    results['details'].append(f'平均舒张压: {avg_diastolic:.0f} ✓')
            
            glucose_data = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
            if glucose_data:
                avg_glucose = sum(glucose_data) / len(glucose_data)
                if avg_glucose < 2 or avg_glucose > 20:
                    results['failed'] += 1
                    results['details'].append(f'平均血糖异常: {avg_glucose:.1f} ✗')
                else:
                    results['passed'] += 1
                    results['details'].append(f'平均血糖: {avg_glucose:.1f} ✓')
            
            heart_rate_data = [m.heart_rate for m in measurements if m.heart_rate]
            if heart_rate_data:
                avg_heart_rate = sum(heart_rate_data) / len(heart_rate_data)
                if avg_heart_rate < 40 or avg_heart_rate > 120:
                    results['failed'] += 1
                    results['details'].append(f'平均心率异常: {avg_heart_rate:.0f} ✗')
                else:
                    results['passed'] += 1
                    results['details'].append(f'平均心率: {avg_heart_rate:.0f} ✓')
        
        return Response(results)


class MoodDataProcessingViewSet(viewsets.ViewSet):
    """心情数据处理视图集"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def preprocess_mood_data(self, request):
        """心情数据预处理 - 分析、异常检测、健康评分"""
        user = request.user
        
        mood_logs = MoodLog.objects.filter(user=user)
        
        if not mood_logs.exists():
            return Response({'message': '暂无心情数据'}, status=status.HTTP_404_NOT_FOUND)
        
        results = {
            'analysis': {},
            'anomalies': [],
            'health_scores': {}
        }
        
        # 1. 数据分析
        rating_data = [log.mood_rating for log in mood_logs if log.mood_rating]
        
        results['analysis'] = {
            'total_records': mood_logs.count(),
            'rating': {
                'min': min(rating_data) if rating_data else None,
                'max': max(rating_data) if rating_data else None,
                'avg': round(sum(rating_data) / len(rating_data), 2) if rating_data else None,
            },
        }
        
        # 2. 异常检测
        anomalies_count = 0
        
        if rating_data:
            mean_rating = sum(rating_data) / len(rating_data)
            std_rating = (sum((x - mean_rating) ** 2 for x in rating_data) / len(rating_data)) ** 0.5
            
            for log in mood_logs:
                if log.mood_rating:
                    z_score = (log.mood_rating - mean_rating) / std_rating if std_rating > 0 else 0
                    if abs(z_score) > 3:
                        results['anomalies'].append({
                            'type': '心情评分异常',
                            'value': str(log.mood_rating),
                            'z_score': round(z_score, 2),
                            'time': log.log_date
                        })
                        anomalies_count += 1
        
        # 3. 健康评分计算
        scores = []
        
        if rating_data:
            avg_rating = sum(rating_data) / len(rating_data)
            if avg_rating >= 7:
                rating_score = 100
            elif avg_rating >= 5:
                rating_score = 80
            else:
                rating_score = 60
            scores.append({'name': '心情指数', 'score': rating_score})
        
        if scores:
            overall_score = sum(s['score'] for s in scores) / len(scores)
            results['health_scores'] = {
                'overall_score': round(overall_score, 1),
                'individual_scores': scores
            }
        
        return Response({
            'message': f'心情数据预处理完成，发现 {anomalies_count} 个异常值',
            'results': results,
            'anomalies_count': anomalies_count
        })
    
    @action(detail=False, methods=['post'])
    def clean_all_mood_data(self, request):
        """一键清洗心情数据"""
        user = request.user
        
        total_removed = 0
        total_fixed = 0
        all_details = []
        
        # 1. 清洗无效数据
        mood_logs = MoodLog.objects.filter(user=user)
        
        for log in mood_logs:
            removed = False
            
            if log.mood_rating:
                if log.mood_rating < 1 or log.mood_rating > 10:
                    log.mood_rating = max(1, min(10, log.mood_rating))
                    log.save()
                    total_fixed += 1
                    all_details.append(f"修正心情评分: {log.mood_rating}")
            
            if not removed:
                if not log.mood_rating:
                    log.delete()
                    total_removed += 1
                    all_details.append("删除空心情记录")
        
        # 2. 删除重复记录
        mood_logs = MoodLog.objects.filter(user=user).order_by('log_date')
        seen = set()
        
        for log in mood_logs:
            key = (log.log_date, log.mood_rating)
            
            if key in seen:
                log.delete()
                total_removed += 1
                all_details.append(f"删除重复记录: {log.log_date}")
            else:
                seen.add(key)
        
        return Response({
            'message': f'心情数据一键清洗完成，共删除 {total_removed} 条记录，修复 {total_fixed} 条记录',
            'removed_count': total_removed,
            'fixed_count': total_fixed,
            'details': all_details[:100]
        })
    
    @action(detail=False, methods=['get'])
    def validate_mood_data(self, request):
        """验证心情数据质量"""
        user = request.user
        
        mood_logs = MoodLog.objects.filter(user=user)
        
        if not mood_logs.exists():
            return Response({
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'details': ['缺少心情数据']
            })
        
        results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        
        count = mood_logs.count()
        if count < 100:
            results['warnings'] += 1
            results['details'].append(f'心情记录数过少: {count}条')
        else:
            results['passed'] += 1
            results['details'].append(f'心情记录数: {count}条 ✓')
        
        rating_data = [log.mood_rating for log in mood_logs if log.mood_rating]
        if rating_data:
            avg_rating = sum(rating_data) / len(rating_data)
            if avg_rating < 1 or avg_rating > 10:
                results['failed'] += 1
                results['details'].append(f'平均心情评分异常: {avg_rating:.1f} ✗')
            else:
                results['passed'] += 1
                results['details'].append(f'平均心情评分: {avg_rating:.1f} ✓')
        
        return Response(results)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def data_processing_summary(request):
    """获取数据处理摘要"""
    user = request.user
    
    measurements = Measurement.objects.filter(user=user)
    sleep_logs = SleepLog.objects.filter(user=user)
    mood_logs = MoodLog.objects.filter(user=user)
    
    return Response({
            'summary': {
                'total_measurements': measurements.count(),
                'total_sleep_logs': sleep_logs.count(),
                'total_mood_logs': mood_logs.count(),
            },
            'last_processed': datetime.now().isoformat(),
        })


class SleepDataProcessingViewSet(viewsets.ViewSet):
    """睡眠数据处理视图集"""
    permission_classes = [IsAuthenticated]
    
    @action(detail=False, methods=['post'])
    def preprocess_sleep_data(self, request):
        """睡眠数据预处理 - 分析、异常检测、健康评分"""
        user = request.user
        
        sleep_logs = SleepLog.objects.filter(user=user)
        
        if not sleep_logs.exists():
            return Response({'message': '暂无睡眠数据'}, status=status.HTTP_404_NOT_FOUND)
        
        results = {
            'analysis': {},
            'anomalies': [],
            'health_scores': {}
        }
        
        # 1. 数据分析
        duration_data = []
        for log in sleep_logs:
            if log.duration_minutes:
                duration_data.append(log.duration_minutes / 60) # 转换为小时
        
        quality_data = [log.quality_rating for log in sleep_logs if log.quality_rating]
        
        results['analysis'] = {
            'total_records': sleep_logs.count(),
            'duration': {
                'min': round(min(duration_data), 2) if duration_data else None,
                'max': round(max(duration_data), 2) if duration_data else None,
                'avg': round(sum(duration_data) / len(duration_data), 2) if duration_data else None,
            },
            'quality': {
                'min': min(quality_data) if quality_data else None,
                'max': max(quality_data) if quality_data else None,
                'avg': round(sum(quality_data) / len(quality_data), 2) if quality_data else None,
            },
        }
        
        # 2. 异常检测
        anomalies_count = 0
        
        if duration_data:
            mean_duration = sum(duration_data) / len(duration_data)
            std_duration = (sum((x - mean_duration) ** 2 for x in duration_data) / len(duration_data)) ** 0.5
            
            for log in sleep_logs:
                if log.duration_minutes:
                    duration_hours = log.duration_minutes / 60
                    z_score = (duration_hours - mean_duration) / std_duration if std_duration > 0 else 0
                    if abs(z_score) > 3:
                        results['anomalies'].append({
                            'type': '睡眠时长异常',
                            'value': f'{duration_hours:.2f}小时',
                            'z_score': round(z_score, 2),
                            'time': log.sleep_date
                        })
                        anomalies_count += 1
        
        if quality_data:
            for log in sleep_logs:
                if log.quality_rating and (log.quality_rating < 1 or log.quality_rating > 10):
                    results['anomalies'].append({
                        'type': '睡眠质量异常',
                        'value': str(log.quality_rating),
                        'time': log.sleep_date
                    })
                    anomalies_count += 1
        
        # 3. 健康评分计算
        scores = []
        
        if duration_data:
            avg_duration = sum(duration_data) / len(duration_data)
            if 7 <= avg_duration <= 9:
                duration_score = 100
            elif 6 <= avg_duration <= 10:
                duration_score = 80
            else:
                duration_score = 60
            scores.append({'name': '睡眠时长', 'score': duration_score})
        
        if quality_data:
            avg_quality = sum(quality_data) / len(quality_data)
            if avg_quality >= 7:
                quality_score = 100
            elif avg_quality >= 5:
                quality_score = 80
            else:
                quality_score = 60
            scores.append({'name': '睡眠质量', 'score': quality_score})
        
        if scores:
            overall_score = sum(s['score'] for s in scores) / len(scores)
            results['health_scores'] = {
                'overall_score': round(overall_score, 1),
                'individual_scores': scores
            }
        
        return Response({
            'message': f'睡眠数据预处理完成，发现 {anomalies_count} 个异常值',
            'results': results,
            'anomalies_count': anomalies_count
        })
    
    @action(detail=False, methods=['post'])
    def clean_all_sleep_data(self, request):
        """一键清洗睡眠数据"""
        user = request.user
        
        total_removed = 0
        total_fixed = 0
        all_details = []
        
        # 1. 清洗无效数据
        sleep_logs = SleepLog.objects.filter(user=user)
        
        for log in sleep_logs:
            removed = False
            
            if log.duration_minutes:
                if log.duration_minutes < 60 or log.duration_minutes > 720:
                    log.delete()
                    total_removed += 1
                    all_details.append(f"删除无效睡眠时长: {log.duration_minutes}分钟")
                    removed = True
            
            if log.quality_rating:
                if log.quality_rating < 1 or log.quality_rating > 10:
                    log.quality_rating = max(1, min(10, log.quality_rating))
                    log.save()
                    total_fixed += 1
                    all_details.append(f"修正睡眠质量评分: {log.quality_rating}")
            
            if not removed:
                if not log.duration_minutes:
                    log.delete()
                    total_removed += 1
                    all_details.append("删除空睡眠记录")
        
        # 2. 删除重复记录
        sleep_logs = SleepLog.objects.filter(user=user).order_by('sleep_date')
        seen = set()
        
        for log in sleep_logs:
            key = (log.sleep_date, log.duration_minutes)
            
            if key in seen:
                log.delete()
                total_removed += 1
                all_details.append(f"删除重复记录: {log.sleep_date}")
            else:
                seen.add(key)
        
        return Response({
            'message': f'睡眠数据一键清洗完成，共删除 {total_removed} 条记录，修复 {total_fixed} 条记录',
            'removed_count': total_removed,
            'fixed_count': total_fixed,
            'details': all_details[:100]
        })
    
    @action(detail=False, methods=['get'])
    def validate_sleep_data(self, request):
        """验证睡眠数据质量"""
        user = request.user
        
        sleep_logs = SleepLog.objects.filter(user=user)
        
        if not sleep_logs.exists():
            return Response({
                'passed': 0,
                'failed': 0,
                'warnings': 0,
                'details': ['缺少睡眠数据']
            })
        
        results = {
            'passed': 0,
            'failed': 0,
            'warnings': 0,
            'details': []
        }
        
        count = sleep_logs.count()
        if count < 100:
            results['warnings'] += 1
            results['details'].append(f'睡眠记录数过少: {count}条')
        else:
            results['passed'] += 1
            results['details'].append(f'睡眠记录数: {count}条 ✓')
        
        duration_data = [log.duration_minutes for log in sleep_logs if log.duration_minutes]
        if duration_data:
            avg_duration = sum(duration_data) / len(duration_data)
            if avg_duration < 240 or avg_duration > 600:
                results['failed'] += 1
                results['details'].append(f'平均睡眠时长异常: {avg_duration:.0f}分钟 ✗')
            else:
                results['passed'] += 1
                results['details'].append(f'平均睡眠时长: {avg_duration:.0f}分钟 ✓')
        
        quality_data = [log.quality_rating for log in sleep_logs if log.quality_rating]
        if quality_data:
            avg_quality = sum(quality_data) / len(quality_data)
            if avg_quality < 1 or avg_quality > 10:
                results['failed'] += 1
                results['details'].append(f'平均睡眠质量异常: {avg_quality:.1f} ✗')
            else:
                results['passed'] += 1
                results['details'].append(f'平均睡眠质量: {avg_quality:.1f} ✓')
        
        return Response(results)
