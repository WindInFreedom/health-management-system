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

from .models import Measurement
from users.models import SleepLog, MoodLog
from .serializers import MeasurementSerializer, SleepLogSerializer, MoodLogSerializer

User = get_user_model()


class DataProcessingViewSet(viewsets.ViewSet):
    """数据处理视图集"""
    permission_classes = [IsAuthenticated]
    
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
