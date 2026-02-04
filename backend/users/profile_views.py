"""
扩展的用户管理视图
替换本地内容：支持档案管理、密码修改和头像上传
"""
from rest_framework import status, viewsets
from rest_framework.decorators import api_view, permission_classes, action, parser_classes
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser
from django.contrib.auth import get_user_model
from django.conf import settings
import uuid
import os

from .models import Profile
from .serializers import (
    UserSerializer,
    ProfileSerializer,
    ChangePasswordSerializer
)

User = get_user_model()


class ProfileViewSet(viewsets.ModelViewSet):
    """用户档案ViewSet"""
    serializer_class = ProfileSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        # 普通用户只能查看自己的档案
        if self.request.user.is_admin_user or self.request.user.is_doctor_user:
            return Profile.objects.all()
        return Profile.objects.filter(user=self.request.user)
    
    def get_object(self):
        # 如果访问 /api/profiles/me/ 则返回当前用户的档案
        if self.kwargs.get('pk') == 'me':
            profile, created = Profile.objects.get_or_create(user=self.request.user)
            return profile
        return super().get_object()


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_profile(request, user_id=None):
    """
    获取或更新用户信息
    GET/PUT/PATCH /api/users/{user_id}/ 或 /api/users/me/
    """
    # 确定目标用户
    if user_id == 'me' or user_id is None:
        user = request.user
    else:
        # 只有管理员和医生可以访问其他用户
        if not (request.user.is_admin_user or request.user.is_doctor_user):
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
    
    if request.method == 'GET':
        serializer = UserSerializer(user)
        return Response(serializer.data)
    
    elif request.method in ['PUT', 'PATCH']:
        # 只能修改自己的信息
        if user != request.user:
            return Response(
                {'error': '只能修改自己的信息'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        partial = request.method == 'PATCH'
        serializer = UserSerializer(user, data=request.data, partial=partial)
        
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def change_password(request):
    """
    修改密码
    POST /api/auth/change-password/
    """
    serializer = ChangePasswordSerializer(
        data=request.data,
        context={'request': request}
    )
    
    if serializer.is_valid():
        # 设置新密码
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        
        return Response({
            'message': '密码修改成功'
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser])
def upload_avatar(request):
    """
    上传用户头像
    POST /api/users/upload-avatar/
    
    替换本地内容：支持本地存储和S3对象存储
    """
    if 'avatar' not in request.FILES:
        return Response(
            {'error': '请上传头像文件'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    avatar_file = request.FILES['avatar']
    
    # 验证文件类型
    allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp']
    if avatar_file.content_type not in allowed_types:
        return Response(
            {'error': '只支持 JPEG, PNG, GIF, WebP 格式的图片'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 验证文件大小 (最大5MB)
    if avatar_file.size > 5 * 1024 * 1024:
        return Response(
            {'error': '文件大小不能超过5MB'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # 生成唯一文件名
    ext = os.path.splitext(avatar_file.name)[1]
    filename = f"avatar_{request.user.id}_{uuid.uuid4().hex[:8]}{ext}"
    
    # 检查是否使用S3存储
    use_s3 = getattr(settings, 'USE_S3_STORAGE', False)
    
    if use_s3:
        try:
            import boto3
            from botocore.exceptions import ClientError
            
            # 配置S3客户端
            s3_client = boto3.client(
                's3',
                aws_access_key_id=settings.AWS_ACCESS_KEY_ID,
                aws_secret_access_key=settings.AWS_SECRET_ACCESS_KEY,
                endpoint_url=settings.AWS_S3_ENDPOINT_URL,
                region_name=settings.AWS_S3_REGION_NAME
            )
            
            # 上传到S3
            bucket_name = settings.AWS_STORAGE_BUCKET_NAME
            s3_key = f"avatars/{filename}"
            
            s3_client.upload_fileobj(
                avatar_file,
                bucket_name,
                s3_key,
                ExtraArgs={'ACL': 'public-read', 'ContentType': avatar_file.content_type}
            )
            
            # 生成公开URL
            if settings.AWS_S3_CUSTOM_DOMAIN:
                avatar_url = f"https://{settings.AWS_S3_CUSTOM_DOMAIN}/{s3_key}"
            else:
                avatar_url = f"{settings.AWS_S3_ENDPOINT_URL}/{bucket_name}/{s3_key}"
            
        except Exception as e:
            return Response(
                {'error': f'上传失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    else:
        # 本地存储
        try:
            # 确保media目录存在
            avatars_dir = os.path.join(settings.MEDIA_ROOT, 'avatars')
            os.makedirs(avatars_dir, exist_ok=True)
            
            # 保存文件
            file_path = os.path.join(avatars_dir, filename)
            with open(file_path, 'wb+') as destination:
                for chunk in avatar_file.chunks():
                    destination.write(chunk)
            
            # 生成URL
            avatar_url = f"{settings.MEDIA_URL}avatars/{filename}"
            
        except Exception as e:
            return Response(
                {'error': f'保存失败: {str(e)}'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    # 更新用户头像URL
    request.user.avatar_url = avatar_url
    request.user.save()
    
    return Response({
        'message': '头像上传成功',
        'avatar_url': avatar_url
    }, status=status.HTTP_200_OK)
