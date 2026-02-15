"""
扩展的健康数据视图
替换本地内容：药物、睡眠、情绪记录的CRUD API和健康报告生成
"""
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db.models import Avg, Count
from decimal import Decimal

from .models import MedicationRecord, Measurement
from users.models import SleepLog, MoodLog  # 从 users.models 导入
from .serializers import (
    MedicationRecordSerializer,
    SleepLogSerializer,
    MoodLogSerializer
)
from .services.scoring_service import HealthScoringService

User = get_user_model()


class MedicationRecordViewSet(viewsets.ModelViewSet):
    """药物记录视图集"""
    serializer_class = MedicationRecordSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MedicationRecord.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SleepLogViewSet(viewsets.ModelViewSet):
    """睡眠记录视图集"""
    serializer_class = SleepLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return SleepLog.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取情绪统计数据"""
        logs = self.get_queryset()
        
        if not logs.exists():
            return Response({'message': '暂无睡眠数据'}, status=status.HTTP_404_NOT_FOUND)
        
        avg_duration = logs.aggregate(Avg('duration_minutes'))['duration_minutes__avg']
        avg_quality = logs.exclude(quality_rating__isnull=True).aggregate(
            Avg('quality_rating')
        )['quality_rating__avg']
        
        return Response({
            'average_duration_hours': round(avg_duration / 60, 2) if avg_duration else 0,
            'average_quality_rating': round(avg_quality, 2) if avg_quality else None,
            'total_records': logs.count()
        })


class MoodLogViewSet(viewsets.ModelViewSet):
    """情绪记录视图集"""
    serializer_class = MoodLogSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return MoodLog.objects.filter(user=self.request.user)
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """获取情绪统计数据"""
        logs = self.get_queryset()
        
        if not logs.exists():
            return Response({'message': '暂无情绪数据'}, status=status.HTTP_404_NOT_FOUND)
        
        avg_rating = logs.aggregate(Avg('mood_rating'))['mood_rating__avg']
        
        # 最近7天的情绪趋势
        week_ago = datetime.now().date() - timedelta(days=7)
        recent_logs = logs.filter(log_date__gte=week_ago).order_by('log_date')
        
        trend_data = [
            {
                'date': log.log_date.isoformat(),
                'rating': log.mood_rating
            }
            for log in recent_logs
        ]
        
        return Response({
            'average_rating': round(avg_rating, 2) if avg_rating else 0,
            'total_records': logs.count(),
            'recent_trend': trend_data
        })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_report(request, user_id=None):
    """
    生成用户健康报告
    GET /api/health-report/ 或 GET /api/health-report/{user_id}
    """
    # 如果没有指定user_id或者不是管理员/医生，则只能查看自己的
    user = request.user
    if user_id:
        if not (user.is_admin_user or user.is_doctor_user):
            return Response(
                {'error': '权限不足'},
                status=status.HTTP_403_FORBIDDEN
            )
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': '用户不存在'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    # 获取用户最新的健康数据
    latest_measurement = Measurement.objects.filter(user=user).order_by('-measured_at').first()
    
    if not latest_measurement:
        return Response(
            {'error': '暂无健康数据'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # 获取用户档案
    profile = getattr(user, 'profile', None)
    
    # 获取睡眠数据
    recent_sleep = SleepLog.objects.filter(user=user).order_by('-start_time').first()
    avg_sleep = SleepLog.objects.filter(user=user).aggregate(Avg('duration_minutes'))['duration_minutes__avg']
    
    # 获取情绪数据
    recent_mood = MoodLog.objects.filter(user=user).order_by('-log_date').first()
    
    # 准备健康数据
    user_data = {
        'weight_kg': float(latest_measurement.weight_kg) if latest_measurement.weight_kg else None,
        'height_cm': float(profile.height) if profile and profile.height else None,
        'systolic': latest_measurement.systolic,
        'diastolic': latest_measurement.diastolic,
        'heart_rate': latest_measurement.heart_rate,
        'blood_glucose': float(latest_measurement.blood_glucose) if latest_measurement.blood_glucose else None,
        'sleep_hours': (avg_sleep / 60) if avg_sleep else None,
        'sleep_quality': recent_sleep.quality_rating if recent_sleep else None,
        'mood_rating': recent_mood.mood_rating if recent_mood else None,
    }
    
    # 生成健康报告
    scoring_service = HealthScoringService()
    report = scoring_service.generate_health_report(user_data)
    
    # 添加用户信息
    report['user_info'] = {
        'id': user.id,
        'username': user.username,
        'email': user.email
    }
    
    # 添加数据时间戳
    report['generated_at'] = datetime.now().isoformat()
    report['latest_measurement_at'] = latest_measurement.measured_at.isoformat()
    
    return Response(report)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def health_forecast(request, user_id=None):
    """
    健康指标预测
    GET /api/health-forecast/?metric=weight&horizon=7
    """
    # 简化版本：返回基于历史平均的预测
    # 完整版本需要实现时间序列预测模型
    
    user = request.user
    if user_id and (user.is_admin_user or user.is_doctor_user):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    
    metric = request.GET.get('metric', 'weight')
    horizon = int(request.GET.get('horizon', 7))
    
    # 获取历史数据
    measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:30]
    
    if not measurements.exists():
        return Response({'error': '数据不足，无法进行预测'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 简单的移动平均预测
    if metric == 'weight':
        values = [float(m.weight_kg) for m in measurements if m.weight_kg]
    elif metric == 'systolic':
        values = [m.systolic for m in measurements if m.systolic]
    elif metric == 'diastolic':
        values = [m.diastolic for m in measurements if m.diastolic]
    elif metric == 'heart_rate':
        values = [m.heart_rate for m in measurements if m.heart_rate]
    elif metric == 'blood_glucose':
        values = [float(m.blood_glucose) for m in measurements if m.blood_glucose]
    else:
        return Response({'error': '不支持的指标类型'}, status=status.HTTP_400_BAD_REQUEST)
    
    if not values:
        return Response({'error': f'{metric}数据不足'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 计算趋势
    avg = sum(values) / len(values)
    recent_avg = sum(values[:7]) / min(len(values), 7)
    trend = "stable"
    if recent_avg > avg * 1.05:
        trend = "increasing"
    elif recent_avg < avg * 0.95:
        trend = "decreasing"
    
    # 生成预测值（简单版本：使用最近的平均值）
    predictions = [round(recent_avg, 2) for _ in range(horizon)]
    
    # 计算置信区间（简单版本：使用标准差）
    import statistics
    std_dev = statistics.stdev(values) if len(values) > 1 else 0
    confidence_lower = [round(v - std_dev, 2) for v in predictions]
    confidence_upper = [round(v + std_dev, 2) for v in predictions]
    
    return Response({
        'metric': metric,
        'horizon_days': horizon,
        'current_value': values[0],
        'predicted_values': predictions,
        'confidence_interval': {
            'lower': confidence_lower,
            'upper': confidence_upper
        },
        'trend': trend,
        'historical_average': round(avg, 2),
        'recent_average': round(recent_avg, 2)
    })
