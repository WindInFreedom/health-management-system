from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .models import Profile, MedicationRecord, SleepLog, MoodLog
from .serializers import (
    UserSerializer, ProfileSerializer, RegistrationSerializer,
    MedicationRecordSerializer, SleepLogSerializer, MoodLogSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class UserListCreateView(generics.ListCreateAPIView):
    """
    列出所有用户 / 创建用户（注意：通常管理员操作可以放在管理接口）
    当前权限设置为认证用户；如需仅允许管理员创建/查看，请将 permission_classes 改为 IsAdminUser
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class UserDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    详情 / 更新 / 删除 用户
    注意：如果希望普通用户只能更新自己的信息，可在前端与后端做进一步限制（或改写 get_queryset）
    """
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfileListCreateView(generics.ListCreateAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


class ProfileDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Profile.objects.all()
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated]


@api_view(['POST'])
@permission_classes([])
def login_view(request):
    username = request.data.get('username')
    password = request.data.get('password')

    if not username or not password:
        return Response({
            'detail': '用户名和密码都是必需的'
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = authenticate(username=username, password=password)
        if user:
            refresh = RefreshToken.for_user(user)
            return Response({
                'access': str(refresh.access_token),
                'refresh': str(refresh),
                'user': UserSerializer(user).data
            })
        else:
            return Response({
                'detail': '用户名或密码错误'
            }, status=status.HTTP_401_UNAUTHORIZED)
    except Exception as e:
        return Response({
            'detail': f'登录错误: {str(e)}'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET', 'PATCH'])  # ⭐ 修改：添加 PATCH 支持
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    """
    获取或更新当前用户信息
    GET /api/users/me/ - 获取当前用户信息
    PATCH /api/users/me/ - 更新当前用户信息（部分更新）
    """
    if request.method == 'GET':
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    elif request.method == 'PATCH':
        serializer = UserSerializer(
            request.user,
            data=request.data,
            partial=True  # 允许部分更新
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    用户注册（开放）:
    POST /api/auth/register/
    body: { username, email, first_name?, last_name?, password, password2, department? }
    注意：后端会强制将自注册用户的 role 设置为 'user'（请在 RegistrationSerializer.create 中实现）
    """
    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# ==================== New Views for Enhanced Features ====================

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password(request):
    """
    Change user password.
    POST /api/auth/change-password/
    body: { old_password, new_password, confirm_password }
    """
    serializer = ChangePasswordSerializer(data=request.data)
    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    user = request.user

    # Check old password
    if not user.check_password(serializer.validated_data['old_password']):
        return Response({
            'old_password': ['当前密码错误']
        }, status=status.HTTP_400_BAD_REQUEST)

    # Set new password
    user.set_password(serializer.validated_data['new_password'])
    user.save()

    return Response({
        'message': '密码修改成功'
    }, status=status.HTTP_200_OK)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def my_profile(request):
    """
    Get or update current user's profile.
    GET/PUT/PATCH /api/profile/me/
    """
    # Get or create profile
    profile, created = Profile.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = ProfileSerializer(profile, context={'request': request})
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        partial = request.method == 'PATCH'
        serializer = ProfileSerializer(profile, data=request.data, partial=partial, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class MedicationRecordViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing medication records.
    Endpoints:
    - GET /api/medications/ - List user's medications
    - POST /api/medications/ - Create medication record
    - GET /api/medications/{id}/ - Get medication detail
    - PUT/PATCH /api/medications/{id}/ - Update medication
    - DELETE /api/medications/{id}/ - Delete medication
    """
    serializer_class = MedicationRecordSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        # Users can only see their own records
        return MedicationRecord.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class SleepLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing sleep logs.
    Endpoints:
    - GET /api/sleep-logs/ - List user's sleep logs
    - POST /api/sleep-logs/ - Create sleep log
    - GET /api/sleep-logs/{id}/ - Get sleep log detail
    - PUT/PATCH /api/sleep-logs/{id}/ - Update sleep log
    - DELETE /api/sleep-logs/{id}/ - Delete sleep log
    """
    serializer_class = SleepLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return SleepLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)


class MoodLogViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing mood logs.
    Endpoints:
    - GET /api/mood-logs/ - List user's mood logs
    - POST /api/mood-logs/ - Create mood log
    - GET /api/mood-logs/{id}/ - Get mood log detail
    - PUT/PATCH /api/mood-logs/{id}/ - Update mood log
    - DELETE /api/mood-logs/{id}/ - Delete mood log
    """
    serializer_class = MoodLogSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return MoodLog.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)