from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from django.contrib.auth import get_user_model
from .models import Profile
from .serializers import UserSerializer, ProfileSerializer

# 如果你已经在 serializers.py 中实现了 RegistrationSerializer，请确保导入它
try:
    from .serializers import RegistrationSerializer
except Exception:
    RegistrationSerializer = None

User = get_user_model()


class UserListCreateView(generics.ListCreateAPIView):
    """
    列出所有用户 / 创建用户（注意：通常管理员操作可以放在管��接口）
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


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def current_user(request):
    serializer = UserSerializer(request.user)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    """
    用户注册（开放）:
    POST /api/auth/register/
    body: { username, email, first_name?, last_name?, password, password2, department? }
    注意：后端会强制将自注册用户的 role 设置为 'user'（请在 RegistrationSerializer.create 中实现）
    """
    if RegistrationSerializer is None:
        return Response({'error': 'RegistrationSerializer 未实现，请在 users/serializers.py 中添加'},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    serializer = RegistrationSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.save()
        return Response(UserSerializer(user).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
