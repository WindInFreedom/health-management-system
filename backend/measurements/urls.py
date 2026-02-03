from django.urls import path
from .views import (
    MeasurementListCreateView,
    MeasurementDetailView,
    my_measurements,
    health_statistics,
    predict_health_trends,
    health_recommendations,
    # 新增导入：
    my_report,
    report_for_user,
)
from . import collaborative_views
from . import admin_views

from rest_framework.routers import DefaultRouter
from .views import MeasurementViewSet

# 使用 DefaultRouter 注册 viewset（如果你想使用 viewset 的自动路由）
router = DefaultRouter()
router.register(r'measurements', MeasurementViewSet, basename='measurement')

urlpatterns = [
    # 传统的基于视图的路由（保留现有实现以兼容前端）
    path('measurements/', MeasurementListCreateView.as_view(), name='measurement-list-create'),
    path('measurements/<int:pk>/', MeasurementDetailView.as_view(), name='measurement-detail'),
    path('measurements/my-measurements/', my_measurements, name='my-measurements'),
    path('measurements/statistics/', health_statistics, name='health-statistics'),
    path('measurements/predict/', predict_health_trends, name='predict-health-trends'),
    path('measurements/recommendations/', health_recommendations, name='health-recommendations'),

    path('measurements/report/my/', my_report, name='my-report'),
    path('measurements/report/<int:user_id>/', report_for_user, name='report-for-user'),

    # 协同过滤功能
    path('collaborative/recommendations/', collaborative_views.collaborative_recommendations, name='collaborative-recommendations'),
    path('collaborative/risk-prediction/', collaborative_views.health_risk_prediction, name='health-risk-prediction'),
    path('collaborative/personalized-recommendations/', collaborative_views.personalized_recommendations, name='personalized-recommendations'),
    path('collaborative/early-warnings/', collaborative_views.early_warning_alerts, name='early-warning-alerts'),
    path('collaborative/similar-users/', collaborative_views.similar_users_health_data, name='similar-users-health-data'),

    # 管理员/医生专用API
    path('admin/all-measurements/', admin_views.all_measurements, name='all-measurements'),
    path('admin/statistics-all/', admin_views.health_statistics_all, name='health-statistics-all'),
    path('admin/alerts-all/', admin_views.health_alerts_all, name='health-alerts-all'),
    path('admin/trends-analysis/', admin_views.health_trends_analysis, name='health-trends-analysis'),
    path('admin/measurements/<int:measurement_id>/', admin_views.measurement_management, name='measurement-management'),
    path('admin/measurements/', admin_views.measurement_management, name='measurement-management-create'),
]

# 将 router 的自动路由追加到 urlpatterns（不会包含 'api/' 前缀）
# 项目级 urls.py 已负责把 measurements.urls 以 path('api/', include(...)) 挂载
urlpatterns += router.urls