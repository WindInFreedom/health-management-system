from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from django.db.models import Q
from .models import Profile
from .serializers import UserSerializer, ProfileSerializer
from .permissions import IsAdminUser, IsDoctorUser, IsAdminOrDoctorUser

User = get_user_model()


class UserManagementListView(generics.ListCreateAPIView):
    """
    用户管理列表 - 管理员和医生可以查看所有用户
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrDoctorUser]
    
    def get_queryset(self):
        queryset = User.objects.all().order_by('-date_joined')
        
        # 搜索过滤
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(username__icontains=search) |
                Q(email__icontains=search) |
                Q(first_name__icontains=search) |
                Q(last_name__icontains=search)
            )
        
        # 角色过滤
        role = self.request.query_params.get('role', None)
        if role:
            queryset = queryset.filter(role=role)
        
        return queryset


class UserManagementDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    用户管理详情 - 管理员可以修改所有用户，医生只能查看
    """
    serializer_class = UserSerializer
    permission_classes = [IsAdminOrDoctorUser]
    queryset = User.objects.all()
    
    def update(self, request, *args, **kwargs):
        # 只有管理员可以修改用户
        if not request.user.is_admin_user:
            return Response(
                {'error': '只有管理员可以修改用户信息'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().update(request, *args, **kwargs)
    
    def destroy(self, request, *args, **kwargs):
        # 只有管理员可以删除用户
        if not request.user.is_admin_user:
            return Response(
                {'error': '只有管理员可以删除用户'}, 
                status=status.HTTP_403_FORBIDDEN
            )
        return super().destroy(request, *args, **kwargs)


@api_view(['GET'])
@permission_classes([IsAdminOrDoctorUser])
def user_statistics(request):
    """
    用户统计信息 - 管理员和医生可以查看
    """
    total_users = User.objects.count()
    admin_users = User.objects.filter(role='admin').count()
    doctor_users = User.objects.filter(role='doctor').count()
    regular_users = User.objects.filter(role='user').count()
    
    # 最近注册的用户
    recent_users = User.objects.order_by('-date_joined')[:5]
    recent_users_data = UserSerializer(recent_users, many=True).data
    
    # 活跃用户（有测量记录的用户）
    from measurements.models import Measurement
    active_users = Measurement.objects.values('user').distinct().count()
    
    return Response({
        'total_users': total_users,
        'admin_users': admin_users,
        'doctor_users': doctor_users,
        'regular_users': regular_users,
        'active_users': active_users,
        'recent_users': recent_users_data
    })


@api_view(['GET'])
@permission_classes([IsAdminOrDoctorUser])
def health_alerts(request):
    """
    健康预警信息 - 管理员和医生可以查看
    """
    from measurements.models import Measurement
    
    alerts = []
    
    # 获取所有用户的最新测量数据
    users = User.objects.all()
    for user in users:
        latest_measurement = Measurement.objects.filter(user=user).order_by('-measured_at').first()
        
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
                        'id': user.id,
                        'username': user.username,
                        'email': user.email,
                        'role': user.role
                    },
                    'alerts': user_alerts,
                    'measurement_date': latest_measurement.measured_at
                })
    
    # 按严重程度排序
    alerts.sort(key=lambda x: max(alert['severity'] for alert in x['alerts']), reverse=True)
    
    return Response({
        'total_alerts': len(alerts),
        'alerts': alerts[:20]  # 限制返回数量
    })


@api_view(['POST'])
@permission_classes([IsAdminUser])
def create_doctor_user(request):
    """
    创建医生用户 - 只有管理员可以创建
    """
    data = request.data
    
    # 设置角色为医生
    data['role'] = 'doctor'
    data['is_doctor'] = True
    
    serializer = UserSerializer(data=data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAdminOrDoctorUser])
def get_user_health_summary(request, user_id):
    """
    获取用户健康摘要 - 管理员和医生可以查看
    """
    try:
        user = User.objects.get(id=user_id)
        from measurements.models import Measurement
        
        measurements = Measurement.objects.filter(user=user).order_by('-measured_at')
        
        if not measurements.exists():
            return Response({'error': '该用户暂无健康数据'}, status=status.HTTP_404_NOT_FOUND)
        
        latest = measurements.first()
        
        # 计算平均值
        from django.db.models import Avg, Max, Min
        
        summary = {
            'user': UserSerializer(user).data,
            'latest_measurement': {
                'date': latest.measured_at,
                'weight': latest.weight_kg,
                'systolic': latest.systolic,
                'diastolic': latest.diastolic,
                'heart_rate': latest.heart_rate,
                'blood_glucose': latest.blood_glucose
            },
            'statistics': {
                'total_measurements': measurements.count(),
                'avg_weight': measurements.aggregate(Avg('weight_kg'))['weight_kg__avg'],
                'avg_systolic': measurements.aggregate(Avg('systolic'))['systolic__avg'],
                'avg_diastolic': measurements.aggregate(Avg('diastolic'))['diastolic__avg'],
                'avg_heart_rate': measurements.aggregate(Avg('heart_rate'))['heart_rate__avg'],
                'avg_blood_glucose': measurements.aggregate(Avg('blood_glucose'))['blood_glucose__avg'],
                'max_systolic': measurements.aggregate(Max('systolic'))['systolic__max'],
                'min_systolic': measurements.aggregate(Min('systolic'))['systolic__min'],
            },
            'health_status': 'normal'  # 这里可以添加健康状态评估逻辑
        }
        
        return Response(summary)
        
    except User.DoesNotExist:
        return Response({'error': '用户不存在'}, status=status.HTTP_404_NOT_FOUND)
