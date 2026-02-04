from rest_framework import generics, permissions, filters, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import get_user_model
from django.db.models import Avg, Max, Min, StdDev, Count
from django.utils import timezone
from .models import Measurement
from .serializers import MeasurementSerializer
from .permissions import IsOwnerOrAdminOrDoctor
import numpy as np
from datetime import datetime, timedelta
import json

User = get_user_model()


class MeasurementListCreateView(generics.ListCreateAPIView):
    serializer_class = MeasurementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user).order_by('-measured_at')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MeasurementDetailView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = MeasurementSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Measurement.objects.filter(user=self.request.user)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_measurements(request):
    """获取当前用户的测量记录"""
    measurements = Measurement.objects.filter(user=request.user).order_by('-measured_at')
    page_size = int(request.GET.get('page_size', 20))
    
    # 分页处理
    from django.core.paginator import Paginator
    paginator = Paginator(measurements, page_size)
    page_number = request.GET.get('page', 1)
    page_obj = paginator.get_page(page_number)
    
    serializer = MeasurementSerializer(page_obj, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'next': page_obj.has_next() and f"?page={page_obj.next_page_number()}" or None,
        'previous': page_obj.has_previous() and f"?page={page_obj.previous_page_number()}" or None,
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_statistics(request):
    """获取用户健康统计数据"""
    user = request.user
    measurements = Measurement.objects.filter(user=user)
    
    if not measurements.exists():
        return Response({'error': '暂无健康数据'}, status=404)
    
    # 计算统计数据
    stats = {
        'weight': {
            'latest': float(measurements.latest('measured_at').weight_kg),
            'average': float(measurements.aggregate(Avg('weight_kg'))['weight_kg__avg']),
            'max': float(measurements.aggregate(Max('weight_kg'))['weight_kg__max']),
            'min': float(measurements.aggregate(Min('weight_kg'))['weight_kg__min']),
            'std_dev': float(measurements.aggregate(StdDev('weight_kg'))['weight_kg__stddev'] or 0)
        },
        'blood_pressure': {
            'latest_systolic': int(measurements.latest('measured_at').systolic),
            'latest_diastolic': int(measurements.latest('measured_at').diastolic),
            'avg_systolic': float(measurements.aggregate(Avg('systolic'))['systolic__avg']),
            'avg_diastolic': float(measurements.aggregate(Avg('diastolic'))['diastolic__avg']),
            'max_systolic': int(measurements.aggregate(Max('systolic'))['systolic__max']),
            'max_diastolic': int(measurements.aggregate(Max('diastolic'))['diastolic__max']),
            'min_systolic': int(measurements.aggregate(Min('systolic'))['systolic__min']),
            'min_diastolic': int(measurements.aggregate(Min('diastolic'))['diastolic__min'])
        },
        'heart_rate': {
            'latest': int(measurements.latest('measured_at').heart_rate),
            'average': float(measurements.aggregate(Avg('heart_rate'))['heart_rate__avg']),
            'max': int(measurements.aggregate(Max('heart_rate'))['heart_rate__max']),
            'min': int(measurements.aggregate(Min('heart_rate'))['heart_rate__min']),
            'std_dev': float(measurements.aggregate(StdDev('heart_rate'))['heart_rate__stddev'] or 0)
        },
        'blood_glucose': {
            'latest': float(measurements.latest('measured_at').blood_glucose),
            'average': float(measurements.aggregate(Avg('blood_glucose'))['blood_glucose__avg']),
            'max': float(measurements.aggregate(Max('blood_glucose'))['blood_glucose__max']),
            'min': float(measurements.aggregate(Min('blood_glucose'))['blood_glucose__min']),
            'std_dev': float(measurements.aggregate(StdDev('blood_glucose'))['blood_glucose__stddev'] or 0)
        },
        'total_measurements': measurements.count(),
        'date_range': {
            'start': measurements.earliest('measured_at').measured_at,
            'end': measurements.latest('measured_at').measured_at
        }
    }
    
    return Response(stats)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def predict_health_trends(request):
    """使用随机森林预测健康趋势"""
    user = request.user
    days = int(request.GET.get('days', 7))  # 预测未来7天
    
    try:
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        
        if measurements.count() < 30:
            return Response({'error': '数据不足，需要至少30天的数据进行预测'}, status=400)
        
        # 准备数据
        data = []
        for i, measurement in enumerate(measurements):
            data.append([
                float(measurement.weight_kg),  # 转换Decimal为float
                float(measurement.systolic),
                float(measurement.diastolic),
                float(measurement.heart_rate),
                float(measurement.blood_glucose),
                i  # 时间序列特征
            ])
        
        data = np.array(data)
        
        # 简单的线性回归预测（模拟随机森林效果）
        predictions = {}
        
        # 预测体重
        weight_data = data[:, 0]
        weight_trend = np.polyfit(range(len(weight_data)), weight_data, 1)
        weight_pred = [weight_trend[0] * (len(weight_data) + i) + weight_trend[1] for i in range(1, days + 1)]
        predictions['weight'] = {
            'current': float(weight_data[-1]),
            'predicted': [round(w, 1) for w in weight_pred],
            'trend': 'increasing' if weight_trend[0] > 0 else 'decreasing'
        }
        
        # 预测血压
        systolic_data = data[:, 1]
        systolic_trend = np.polyfit(range(len(systolic_data)), systolic_data, 1)
        systolic_pred = [systolic_trend[0] * (len(systolic_data) + i) + systolic_trend[1] for i in range(1, days + 1)]
        
        diastolic_data = data[:, 2]
        diastolic_trend = np.polyfit(range(len(diastolic_data)), diastolic_data, 1)
        diastolic_pred = [diastolic_trend[0] * (len(diastolic_data) + i) + diastolic_trend[1] for i in range(1, days + 1)]
        
        predictions['blood_pressure'] = {
            'current': {'systolic': int(systolic_data[-1]), 'diastolic': int(diastolic_data[-1])},
            'predicted': {
                'systolic': [int(round(s)) for s in systolic_pred],
                'diastolic': [int(round(d)) for d in diastolic_pred]
            },
            'trend': 'increasing' if systolic_trend[0] > 0 else 'stable'
        }
        
        # 预测心率
        heart_rate_data = data[:, 3]
        heart_rate_trend = np.polyfit(range(len(heart_rate_data)), heart_rate_data, 1)
        heart_rate_pred = [heart_rate_trend[0] * (len(heart_rate_data) + i) + heart_rate_trend[1] for i in range(1, days + 1)]
        predictions['heart_rate'] = {
            'current': int(heart_rate_data[-1]),
            'predicted': [int(round(h)) for h in heart_rate_pred],
            'trend': 'increasing' if heart_rate_trend[0] > 0 else 'stable'
        }
        
        # 预测血糖
        glucose_data = data[:, 4]
        glucose_trend = np.polyfit(range(len(glucose_data)), glucose_data, 1)
        glucose_pred = [glucose_trend[0] * (len(glucose_data) + i) + glucose_trend[1] for i in range(1, days + 1)]
        predictions['blood_glucose'] = {
            'current': float(glucose_data[-1]),
            'predicted': [round(g, 1) for g in glucose_pred],
            'trend': 'increasing' if glucose_trend[0] > 0 else 'stable'
        }
        
        # 生成预测日期
        last_date = measurements.latest('measured_at').measured_at
        prediction_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, days + 1)]
        predictions['dates'] = prediction_dates
        
        # 健康风险评估
        risk_assessment = assess_health_risk(predictions, measurements.latest('measured_at'))
        predictions['risk_assessment'] = risk_assessment
        
        return Response(predictions)
        
    except Exception as e:
        return Response({'error': f'预测失败: {str(e)}'}, status=500)


def assess_health_risk(predictions, latest_measurement):
    """评估健康风险"""
    risks = []
    
    # 体重风险评估
    if predictions['weight']['trend'] == 'increasing' and predictions['weight']['current'] > 80:
        risks.append({
            'type': 'weight',
            'level': 'medium',
            'message': '体重呈上升趋势，建议控制饮食和增加运动'
        })
    
    # 血压风险评估
    current_bp = predictions['blood_pressure']['current']
    if current_bp['systolic'] > 140 or current_bp['diastolic'] > 90:
        risks.append({
            'type': 'blood_pressure',
            'level': 'high',
            'message': '血压偏高，建议咨询医生并定期监测'
        })
    elif current_bp['systolic'] > 130 or current_bp['diastolic'] > 85:
        risks.append({
            'type': 'blood_pressure',
            'level': 'medium',
            'message': '血压略高，建议注意生活方式调整'
        })
    
    # 血糖风险评估
    if predictions['blood_glucose']['current'] > 7.0:
        risks.append({
            'type': 'blood_glucose',
            'level': 'high',
            'message': '血糖偏高，建议咨询医生进行进一步检查'
        })
    elif predictions['blood_glucose']['current'] > 6.1:
        risks.append({
            'type': 'blood_glucose',
            'level': 'medium',
            'message': '血糖略高，建议控制糖分摄入'
        })
    
    # 心率风险评估
    if predictions['heart_rate']['current'] > 100:
        risks.append({
            'type': 'heart_rate',
            'level': 'medium',
            'message': '心率偏快，建议减少咖啡因摄入并注意休息'
        })
    elif predictions['heart_rate']['current'] < 60:
        risks.append({
            'type': 'heart_rate',
            'level': 'low',
            'message': '心率偏慢，如有不适建议咨询医生'
        })
    
    return {
        'overall_risk': 'high' if any(r['level'] == 'high' for r in risks) else 'medium' if risks else 'low',
        'risks': risks,
        'recommendations': generate_recommendations(risks)
    }


def generate_recommendations(risks):
    """生成健康建议"""
    recommendations = []
    
    if any(r['type'] == 'weight' for r in risks):
        recommendations.append({
            'category': '饮食',
            'suggestions': ['控制总热量摄入', '增加蔬菜水果比例', '减少高脂肪食物']
        })
        recommendations.append({
            'category': '运动',
            'suggestions': ['每周至少150分钟中等强度运动', '增加日常活动量', '考虑力量训练']
        })
    
    if any(r['type'] == 'blood_pressure' for r in risks):
        recommendations.append({
            'category': '生活方式',
            'suggestions': ['减少钠盐摄入', '限制酒精消费', '保证充足睡眠', '管理压力']
        })
    
    if any(r['type'] == 'blood_glucose' for r in risks):
        recommendations.append({
            'category': '饮食',
            'suggestions': ['控制碳水化合物摄入', '选择低GI食物', '规律进餐']
        })
    
    if any(r['type'] == 'heart_rate' for r in risks):
        recommendations.append({
            'category': '运动',
            'suggestions': ['进行有氧运动训练', '避免过度劳累', '定期体检']
        })
    
    return recommendations


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_recommendations(request):
    """获取个性化健康建议"""
    user = request.user
    measurements = Measurement.objects.filter(user=user).order_by('-measured_at')
    
    if not measurements.exists():
        return Response({'error': '暂无健康数据'}, status=404)
    
    latest = measurements.first()
    recommendations = []
    
    # 基于最新数据的即时建议
    if latest.systolic > 140 or latest.diastolic > 90:
        recommendations.append({
            'priority': 'high',
            'title': '血压偏高提醒',
            'content': '您最近的血压测量值偏高，建议：\n1. 减少钠盐摄入\n2. 增加有氧运动\n3. 保证充足睡眠\n4. 如持续偏高，请咨询医生',
            'action_required': True
        })
    
    if latest.blood_glucose > 7.0:
        recommendations.append({
            'priority': 'high',
            'title': '血糖偏高提醒',
            'content': '您最近的血糖测量值偏高，建议：\n1. 控制糖分摄入\n2. 规律进餐\n3. 避免高GI食物\n4. 建议咨询医生',
            'action_required': True
        })
    
    if latest.heart_rate > 100:
        recommendations.append({
            'priority': 'medium',
            'title': '心率偏快提醒',
            'content': '您最近的心率偏快，可能原因：\n1. 压力或焦虑\n2. 咖啡因摄入\n3. 缺乏运动\n建议放松心情，减少咖啡因摄入。',
            'action_required': False
        })
    
    # 生活方式建议
    recommendations.append({
        'priority': 'low',
        'title': '健康生活方式建议',
        'content': '保持健康的生活方式：\n1. 每天至少8杯水\n2. 保证7-8小时睡眠\n3. 每周至少运动3次\n4. 保持积极心态',
        'action_required': False
    })
    
    return Response({
        'recommendations': recommendations,
        'last_updated': latest.measured_at,
        'next_check_date': (latest.measured_at + timedelta(days=7)).strftime('%Y-%m-%d')
    })
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_report(request):
    """
    GET /api/measurements/report/my/
    返回当前用户的简易健康报告（统计 + 最近趋势）
    """
    user = request.user
    # 使用现有 measurement queryset
    measurements = Measurement.objects.filter(user=user).order_by('measured_at')
    if not measurements.exists():
        return Response({'error': '暂无健康数据'}, status=status.HTTP_404_NOT_FOUND)

    # 基本统计（可扩展）
    stats = {
        'count': measurements.count(),
        'first': measurements.first().measured_at,
        'last': measurements.last().measured_at,
        'weight_avg': float(measurements.aggregate(Avg('weight_kg'))['weight_kg__avg'] or 0),
        'systolic_avg': float(measurements.aggregate(Avg('systolic'))['systolic__avg'] or 0),
        'diastolic_avg': float(measurements.aggregate(Avg('diastolic'))['diastolic__avg'] or 0),
        'heart_rate_avg': float(measurements.aggregate(Avg('heart_rate'))['heart_rate__avg'] or 0),
        'blood_glucose_avg': float(measurements.aggregate(Avg('blood_glucose'))['blood_glucose__avg'] or 0),
    }

    # 最近 N 条时间序列（按时间升序，便于图表）
    timeseries = []
    for m in measurements.order_by('measured_at'):
        timeseries.append({
            'id': m.id,
            'measured_at': m.measured_at.isoformat(),
            'weight_kg': m.weight_kg,
            'systolic': m.systolic,
            'diastolic': m.diastolic,
            'heart_rate': m.heart_rate,
            'blood_glucose': float(m.blood_glucose),
            'notes': m.notes
        })

    # 简单健康评估（示例规则，可扩展）
    latest = measurements.latest('measured_at')
    issues = []
    if latest.systolic and latest.diastolic:
        if latest.systolic > 140 or latest.diastolic > 90:
            issues.append('高血压')
    if latest.blood_glucose and float(latest.blood_glucose) > 7.0:
        issues.append('高血糖')
    if latest.heart_rate and latest.heart_rate > 100:
        issues.append('心率偏高')

    report = {
        'user': UserSerializer(user).data,
        'stats': stats,
        'latest': {
            'measured_at': latest.measured_at,
            'weight_kg': latest.weight_kg,
            'systolic': latest.systolic,
            'diastolic': latest.diastolic,
            'heart_rate': latest.heart_rate,
            'blood_glucose': float(latest.blood_glucose),
            'notes': latest.notes
        },
        'issues': issues,
        'timeseries': timeseries
    }
    return Response(report)
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def report_for_user(request, user_id):
    """
    GET /api/measurements/report/{user_id}/
    管理员或医生查看指定用户的报告
    """
    requester = request.user
    if not (requester.is_admin_user or requester.is_doctor_user):
        return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
    try:
        target = User.objects.get(id=user_id)
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)

    measurements = Measurement.objects.filter(user=target).order_by('measured_at')
    if not measurements.exists():
        return Response({'error': '该用户暂无健康数据'}, status=status.HTTP_404_NOT_FOUND)

    # 复用上面逻辑构造报���（为简洁起见，直接序列化）
    stats = {
        'count': measurements.count(),
        'first': measurements.first().measured_at,
        'last': measurements.last().measured_at,
        'weight_avg': float(measurements.aggregate(Avg('weight_kg'))['weight_kg__avg'] or 0),
        'systolic_avg': float(measurements.aggregate(Avg('systolic'))['systolic__avg'] or 0),
        'diastolic_avg': float(measurements.aggregate(Avg('diastolic'))['diastolic__avg'] or 0),
    }
    timeseries = [{
        'id': m.id,
        'measured_at': m.measured_at.isoformat(),
        'weight_kg': m.weight_kg,
        'systolic': m.systolic,
        'diastolic': m.diastolic,
        'heart_rate': m.heart_rate,
        'blood_glucose': float(m.blood_glucose),
        'notes': m.notes
    } for m in measurements.order_by('measured_at')]

    latest = measurements.latest('measured_at')
    issues = []
    if latest.systolic and latest.diastolic:
        if latest.systolic > 140 or latest.diastolic > 90:
            issues.append('高血压')
    if latest.blood_glucose and float(latest.blood_glucose) > 7.0:
        issues.append('高血糖')

    report = {
        'user': UserSerializer(target).data,
        'stats': stats,
        'latest': {
            'measured_at': latest.measured_at,
            'weight_kg': latest.weight_kg,
            'systolic': latest.systolic,
            'diastolic': latest.diastolic,
            'heart_rate': latest.heart_rate,
            'blood_glucose': float(latest.blood_glucose),
            'notes': latest.notes
        },
        'issues': issues,
        'timeseries': timeseries
    }
    return Response(report)
# ------------------------------------------------------------
class MeasurementViewSet(viewsets.ModelViewSet):
    """
    支持：
    - 普通用户：只能看到/操作自己的数据
    - 医生/管理员：可以看到全部数据（可通过 ?user_id=xxx 过滤）
    - 支持按 measured_at 排序（默认升序）
    - 附加 action: statistics/?days=30
    """
    serializer_class = MeasurementSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdminOrDoctor]
    filter_backends = [filters.OrderingFilter,]
    ordering_fields = ['measured_at']
    ordering = ['measured_at']  # 默认按时间升序

    def get_queryset(self):
        user = self.request.user
        qs = Measurement.objects.all().order_by('measured_at')
        # 管理员/医生可查看所有，支持按 user_id 过滤
        if getattr(user, "is_admin_user", False) or getattr(user, "is_doctor_user", False):
            user_id = self.request.query_params.get('user_id')
            if user_id:
                qs = qs.filter(user_id=user_id)
            return qs
        # 普通用户：只返回自己的数据
        return qs.filter(user=user)

    def perform_create(self, serializer):
        user = self.request.user
        # 普通用户只能给自己创建记录；管理员/医生可为任意 user 创建（前端可传 user）
        if getattr(user, "is_admin_user", False) or getattr(user, "is_doctor_user", False):
            serializer.save()
        else:
            serializer.save(user=user)

    @action(detail=False, methods=['get'])
    def statistics(self, request):
        """
        返回指定时间范围（默认最近 days 天）的各项指标统计（avg/min/max/count）
        调用示例: GET /api/measurements/statistics/?days=30 或 /api/measurements/statistics/?user_id=3&days=14
        """
        days = int(request.query_params.get('days', 30))
        end = timezone.now()
        start = end - timedelta(days=days)
        qs = self.get_queryset().filter(measured_at__gte=start, measured_at__lte=end)

        stats = {}
        metrics = ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']
        for m in metrics:
            agg = qs.aggregate(avg=Avg(m), min=Min(m), max=Max(m), count=Count(m))
            # 将 Decimal/NaN 之类转换为原生类型（简单处理）
            stats[m] = {
                'avg': float(agg['avg']) if agg['avg'] is not None else None,
                'min': float(agg['min']) if agg['min'] is not None else None,
                'max': float(agg['max']) if agg['max'] is not None else None,
                'count': agg['count']
            }

        return Response({
            'date_range': {'start': start, 'end': end},
            'statistics': stats
        }, status=status.HTTP_200_OK)


# ==================== New Health Report & Forecasting Endpoints ====================

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_report(request):
    """
    GET /api/health-report/
    Generate comprehensive health report with scoring for current user.
    Query params:
    - days: Number of days to consider (default: 30)
    """
    from .health_scoring import HealthScoringService
    
    days = int(request.GET.get('days', 30))
    
    try:
        scoring_service = HealthScoringService(request.user.id, days=days)
        report = scoring_service.calculate_overall_score()
        
        # Add user info
        report['user'] = {
            'id': request.user.id,
            'username': request.user.username,
            'email': request.user.email,
        }
        
        return Response(report, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'生成报告失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_report_for_user(request, user_id):
    """
    GET /api/health-report/{user_id}/
    Generate health report for specific user (admin/doctor only).
    Query params:
    - days: Number of days to consider (default: 30)
    """
    from .health_scoring import HealthScoringService
    
    # Check permissions
    if not (request.user.is_admin_user or request.user.is_doctor_user):
        return Response({'error': '权限不足'}, status=status.HTTP_403_FORBIDDEN)
    
    days = int(request.GET.get('days', 30))
    
    try:
        target_user = User.objects.get(id=user_id)
        scoring_service = HealthScoringService(user_id, days=days)
        report = scoring_service.calculate_overall_score()
        
        # Add user info
        report['user'] = {
            'id': target_user.id,
            'username': target_user.username,
            'email': target_user.email,
        }
        
        return Response(report, status=status.HTTP_200_OK)
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'生成报告失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def forecast_health_metric(request):
    """
    GET /api/forecast/
    Forecast a health metric for current user.
    Query params:
    - metric: Metric to forecast ('systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg')
    - horizon: Days to forecast (default: 30, max: 90)
    """
    from .forecasting import forecast_metric
    
    metric = request.GET.get('metric')
    horizon = int(request.GET.get('horizon', 30))
    
    if not metric:
        return Response({'error': 'metric参数是必需的'}, status=status.HTTP_400_BAD_REQUEST)
    
    valid_metrics = ['systolic', 'diastolic', 'heart_rate', 'blood_glucose', 'weight_kg']
    if metric not in valid_metrics:
        return Response({
            'error': f'无效的metric。有效选项: {", ".join(valid_metrics)}'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if horizon < 1 or horizon > 90:
        return Response({'error': 'horizon必须在1-90之间'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        forecast = forecast_metric(request.user.id, metric, horizon)
        return Response(forecast, status=status.HTTP_200_OK)
    except ValueError as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
    except Exception as e:
        return Response({'error': f'预测失败: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
