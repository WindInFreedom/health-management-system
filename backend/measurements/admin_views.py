from rest_framework.decorators import api_view, permission_classes
from rest_framework import permissions
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q, Count, Avg, Max, Min, StdDev
from .models import Measurement
from datetime import datetime, timedelta

User = get_user_model()


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def all_measurements(request):
    """
    获取所有用户的测量数据（医生和管理员专用）
    """
    user = request.user
    
    # 检查权限
    if not (user.is_admin_user or user.is_doctor_user):
        return Response({'error': '权限不足'}, status=403)
    
    # 获取查询参数
    user_id = request.query_params.get('user_id', None)
    metric_type = request.query_params.get('metric_type', None)
    start_date = request.query_params.get('start_date', None)
    end_date = request.query_params.get('end_date', None)
    
    # 构建查询
    measurements = Measurement.objects.all()
    
    if user_id:
        measurements = measurements.filter(user_id=user_id)
    
    if start_date:
        measurements = measurements.filter(measured_at__gte=start_date)
    
    if end_date:
        measurements = measurements.filter(measured_at__lte=end_date)
    
    # 按用户和时间排序
    measurements = measurements.order_by('user_id', '-measured_at')
    
    # 序列化数据
    data = []
    for measurement in measurements:
        data.append({
            'id': measurement.id,
            'user_id': measurement.user_id,
            'username': measurement.user.username,
            'user_role': measurement.user.role,
            'measured_at': measurement.measured_at,
            'weight_kg': float(measurement.weight_kg),
            'systolic': measurement.systolic,
            'diastolic': measurement.diastolic,
            'heart_rate': measurement.heart_rate,
            'blood_glucose': float(measurement.blood_glucose),
        })
    
    return Response({
        'count': len(data),
        'results': data
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_statistics_all(request):
    """
    获取所有用户的健康统计数据（医生和管理员专用）
    """
    user = request.user
    
    # 检查权限
    if not (user.is_admin_user or user.is_doctor_user):
        return Response({'error': '权限不足'}, status=403)
    
    # 获取所有用户的统计数据
    users_stats = []
    
    for user_obj in User.objects.all():
        measurements = Measurement.objects.filter(user=user_obj)
        
        if measurements.exists():
            stats = {
                'user_id': user_obj.id,
                'username': user_obj.username,
                'user_role': user_obj.role,
                'total_measurements': measurements.count(),
                'latest_measurement': measurements.latest('measured_at').measured_at,
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
                }
            }
            
            # 添加健康状态评估
            stats['health_status'] = assess_health_status(stats)
            
            users_stats.append(stats)
    
    return Response({
        'total_users': len(users_stats),
        'users_stats': users_stats
    })


def assess_health_status(stats):
    """评估健康状态"""
    issues = []
    
    # 检查血压
    if stats['blood_pressure']['latest_systolic'] > 140 or stats['blood_pressure']['latest_diastolic'] > 90:
        issues.append('高血压')
    elif stats['blood_pressure']['latest_systolic'] > 130 or stats['blood_pressure']['latest_diastolic'] > 85:
        issues.append('血压偏高')
    
    # 检查血糖
    if stats['blood_glucose']['latest'] > 7.0:
        issues.append('高血糖')
    elif stats['blood_glucose']['latest'] > 6.1:
        issues.append('血糖偏高')
    
    # 检查心率
    if stats['heart_rate']['latest'] > 100:
        issues.append('心率过快')
    elif stats['heart_rate']['latest'] < 60:
        issues.append('心率过慢')
    
    # 检查体重
    if stats['weight']['latest'] > 90:
        issues.append('超重')
    elif stats['weight']['latest'] < 50:
        issues.append('体重过轻')
    
    if not issues:
        return '健康'
    elif len(issues) <= 1:
        return '需关注'
    elif len(issues) <= 2:
        return '需改善'
    else:
        return '需就医'


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_alerts_all(request):
    """
    获取所有用户的健康预警（医生和管理员专用）
    """
    user = request.user
    
    # 检查权限
    if not (user.is_admin_user or user.is_doctor_user):
        return Response({'error': '权限不足'}, status=403)
    
    alerts = []
    
    # 获取所有用户的最新测量数据
    users = User.objects.all()
    for user_obj in users:
        latest_measurement = Measurement.objects.filter(user=user_obj).order_by('-measured_at').first()
        
        if latest_measurement:
            user_alerts = []
            
            # 血压预警
            if latest_measurement.systolic > 140 or latest_measurement.diastolic > 90:
                user_alerts.append({
                    'type': 'high_blood_pressure',
                    'message': f'血压偏高: {latest_measurement.systolic}/{latest_measurement.diastolic} mmHg',
                    'severity': 'high'
                })
            elif latest_measurement.systolic > 130 or latest_measurement.diastolic > 85:
                user_alerts.append({
                    'type': 'elevated_blood_pressure',
                    'message': f'血压略高: {latest_measurement.systolic}/{latest_measurement.diastolic} mmHg',
                    'severity': 'medium'
                })
            
            # 血糖预警
            if latest_measurement.blood_glucose > 7.0:
                user_alerts.append({
                    'type': 'high_blood_glucose',
                    'message': f'血糖偏高: {latest_measurement.blood_glucose} mmol/L',
                    'severity': 'high'
                })
            elif latest_measurement.blood_glucose > 6.1:
                user_alerts.append({
                    'type': 'elevated_blood_glucose',
                    'message': f'血糖略高: {latest_measurement.blood_glucose} mmol/L',
                    'severity': 'medium'
                })
            
            # 心率预警
            if latest_measurement.heart_rate > 100:
                user_alerts.append({
                    'type': 'high_heart_rate',
                    'message': f'心率偏快: {latest_measurement.heart_rate} bpm',
                    'severity': 'medium'
                })
            elif latest_measurement.heart_rate < 60:
                user_alerts.append({
                    'type': 'low_heart_rate',
                    'message': f'心率偏慢: {latest_measurement.heart_rate} bpm',
                    'severity': 'medium'
                })
            
            # 体重预警
            if latest_measurement.weight_kg > 90:
                user_alerts.append({
                    'type': 'overweight',
                    'message': f'体重超标: {latest_measurement.weight_kg} kg',
                    'severity': 'medium'
                })
            
            if user_alerts:
                alerts.append({
                    'user': {
                        'id': user_obj.id,
                        'username': user_obj.username,
                        'email': user_obj.email,
                        'role': user_obj.role
                    },
                    'alerts': user_alerts,
                    'measurement_date': latest_measurement.measured_at
                })
    
    # 按严重程度排序
    alerts.sort(key=lambda x: max(alert['severity'] for alert in x['alerts']), reverse=True)
    
    return Response({
        'total_alerts': len(alerts),
        'high_priority_alerts': len([a for a in alerts if any(alert['severity'] == 'high' for alert in a['alerts'])]),
        'medium_priority_alerts': len([a for a in alerts if any(alert['severity'] == 'medium' for alert in a['alerts'])]),
        'alerts': alerts
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def health_trends_analysis(request):
    """
    健康趋势分析（医生和管理员专用）
    """
    user = request.user
    
    # 检查权限
    if not (user.is_admin_user or user.is_doctor_user):
        return Response({'error': '权限不足'}, status=403)
    
    # 获取时间范围
    days = int(request.query_params.get('days', 30))
    start_date = datetime.now() - timedelta(days=days)
    
    # 获取所有用户的趋势数据
    trends_data = {}
    
    for metric in ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']:
        measurements = Measurement.objects.filter(
            measured_at__gte=start_date
        ).values('user__username', metric).order_by('measured_at')
        
        # 按用户分组
        user_data = {}
        for measurement in measurements:
            username = measurement['user__username']
            if username not in user_data:
                user_data[username] = []
            user_data[username].append(float(measurement[metric]))
        
        # 计算趋势
        trends_data[metric] = {}
        for username, values in user_data.items():
            if len(values) >= 2:
                # 简单线性趋势
                trend = (values[-1] - values[0]) / len(values)
                trends_data[metric][username] = {
                    'trend': trend,
                    'latest': values[-1],
                    'average': sum(values) / len(values),
                    'count': len(values)
                }
    
    return Response(trends_data)


@api_view(['POST', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def measurement_management(request, measurement_id=None):
    """
    测量数据管理（增删改查）
    """
    user = request.user
    
    # 检查权限
    if not (user.is_admin_user or user.is_doctor_user):
        return Response({'error': '权限不足'}, status=403)
    
    if request.method == 'POST':
        # 创建新测量数据
        data = request.data
        try:
            user_obj = User.objects.get(id=data['user_id'])
            measurement = Measurement.objects.create(
                user=user_obj,
                weight_kg=data['weight_kg'],
                systolic=data['systolic'],
                diastolic=data['diastolic'],
                heart_rate=data['heart_rate'],
                blood_glucose=data['blood_glucose'],
                measured_at=data.get('measured_at', datetime.now())
            )
            return Response({'id': measurement.id, 'message': '创建成功'})
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    elif request.method == 'PUT':
        # 更新测量数据
        try:
            measurement = Measurement.objects.get(id=measurement_id)
            data = request.data
            
            measurement.weight_kg = data.get('weight_kg', measurement.weight_kg)
            measurement.systolic = data.get('systolic', measurement.systolic)
            measurement.diastolic = data.get('diastolic', measurement.diastolic)
            measurement.heart_rate = data.get('heart_rate', measurement.heart_rate)
            measurement.blood_glucose = data.get('blood_glucose', measurement.blood_glucose)
            measurement.measured_at = data.get('measured_at', measurement.measured_at)
            
            measurement.save()
            return Response({'message': '更新成功'})
        except Measurement.DoesNotExist:
            return Response({'error': '测量数据不存在'}, status=404)
        except Exception as e:
            return Response({'error': str(e)}, status=400)
    
    elif request.method == 'DELETE':
        # 删除测量数据
        try:
            measurement = Measurement.objects.get(id=measurement_id)
            measurement.delete()
            return Response({'message': '删除成功'})
        except Measurement.DoesNotExist:
            return Response({'error': '测量数据不存在'}, status=404)
