"""
WebSocket routing for Django Channels
替换本地内容：实时管理员仪表板的WebSocket路由配置
"""
from django.urls import re_path
from . import consumers

websocket_urlpatterns = [
    re_path(r'ws/admin/stream/$', consumers.AdminStreamConsumer.as_asgi()),
]
