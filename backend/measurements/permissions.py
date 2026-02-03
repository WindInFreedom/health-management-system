from rest_framework import permissions

class IsOwnerOrAdminOrDoctor(permissions.BasePermission):
    """
    - 普通用户: 只能查看/操作自己的 Measurement 对象
    - 医生/管理员: 可以查看/操作任意用户的数据
    - 所有请求要求已认证
    """
    def has_permission(self, request, view):
        return request.user and request.user.is_authenticated

    def has_object_permission(self, request, view, obj):
        # obj 为 Measurement 实例，假定有 .user / .user_id 属性
        user = request.user
        if getattr(user, "is_admin_user", False) or getattr(user, "is_doctor_user", False):
            return True
        return obj.user_id == user.id