from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserListCreateView, UserDetailView, 
    ProfileListCreateView, ProfileDetailView,
    current_user, login_view, register_view,
    change_password, my_profile,
    MedicationRecordViewSet, SleepLogViewSet, MoodLogViewSet,
)
from . import management_views, profile_views

# 创建路由器
router = DefaultRouter()
router.register(r'profiles-extended', profile_views.ProfileViewSet, basename='profile-extended')

# Create router for ViewSets
router = DefaultRouter()
router.register(r'medications', MedicationRecordViewSet, basename='medication')
router.register(r'sleep-logs', SleepLogViewSet, basename='sleep-log')
router.register(r'mood-logs', MoodLogViewSet, basename='mood-log')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='auth-login'),
    path('auth/register/', register_view, name='auth-register'),
    path('auth/change-password/', change_password, name='change-password'),
    
    # User endpoints
    path('users/', UserListCreateView.as_view(), name='user-list-create'),
    path('users/<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('users/me/', current_user, name='current-user'),
    
    # Profile endpoints
    path('profiles/', ProfileListCreateView.as_view(), name='profile-list-create'),
    path('profiles/<int:pk>/', ProfileDetailView.as_view(), name='profile-detail'),
    path('profile/me/', my_profile, name='my-profile'),
    
    # Legacy endpoints (keeping for compatibility)
    path('login/', login_view, name='login'),
    path('me/', current_user, name='current-user-alt'),
    
    # User management endpoints (admin/doctor)
    path('management/users/', management_views.UserManagementListView.as_view(), name='user-management-list'),
    path('management/users/<int:pk>/', management_views.UserManagementDetailView.as_view(), name='user-management-detail'),
    path('management/statistics/', management_views.user_statistics, name='user-statistics'),
    path('management/alerts/', management_views.health_alerts, name='health-alerts'),
    path('management/create-doctor/', management_views.create_doctor_user, name='create-doctor'),
    path('management/user/<int:user_id>/health-summary/', management_views.get_user_health_summary, name='user-health-summary'),
    
    # Include router URLs for tracking features
    path('', include(router.urls)),
]
