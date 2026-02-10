from rest_framework import permissions


class IsAdminUser(permissions.BasePermission):
    """
    只允许管理员用户访问
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_admin_user


class IsDoctorUser(permissions.BasePermission):
    """
    只允许医生用户访问
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated and request.user.is_doctor_user


class IsAdminOrDoctorUser(permissions.BasePermission):
    """
    允许管理员或医生用户访问
    """
    def has_permission(self, request, view):
        return (request.user and request.user.is_authenticated and 
                (request.user.is_admin_user or request.user.is_doctor_user))


class IsOwnerOrAdminOrDoctor(permissions.BasePermission):
    """
    允许资源所有者、管理员或医生访问
    """
    def has_object_permission(self, request, view, obj):
        # 管理员和医生可以访问所有对象
        if request.user.is_admin_user or request.user.is_doctor_user:
            return True
        
        # 普通用户只能访问自己的对象
        return obj.user == request.user


class IsOwnerOrReadOnly(permissions.BasePermission):
    """
    允许所有用户读取，但只有所有者可以写入
    """
    def has_object_permission(self, request, view, obj):
        # 读取权限对所有认证用户开放
        if request.method in permissions.SAFE_METHODS:
            return True
        
        # 写入权限只对所有者开放
        return obj.user == request.user
