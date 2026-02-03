from django.urls import path
from .views import (
    UserListCreateView, UserDetailView, 
    ProfileListCreateView, ProfileDetailView,
    current_user, login_view,register_view,
)
from . import management_views

urlpatterns = [
    path('login/', login_view, name='login'),
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('profiles/', ProfileListCreateView.as_view(), name='profile-list-create'),
    path('profiles/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('me/', current_user, name='current-user'),

    path('auth/register/', register_view, name='auth-register'),
    path('auth/login/', login_view, name='auth-login'),
    path('users/me/', current_user, name='current-user'),
    # 用户管理功能
    path('management/users/', management_views.UserManagementListView.as_view(), name='user-management-list'),
    path('management/users/<int:pk>/', management_views.UserManagementDetailView.as_view(), name='user-management-detail'),
    path('management/statistics/', management_views.user_statistics, name='user-statistics'),
    path('management/alerts/', management_views.health_alerts, name='health-alerts'),
    path('management/create-doctor/', management_views.create_doctor_user, name='create-doctor'),
    path('management/user/<int:user_id>/health-summary/', management_views.get_user_health_summary, name='user-health-summary'),
]
