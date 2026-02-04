"""
WebSocket consumers for real-time admin dashboard
替换本地内容：管理员实时数据流消费者
"""
import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta
from django.db.models import Count, Avg

User = get_user_model()


class AdminStreamConsumer(AsyncWebsocketConsumer):
    """
    管理员实时数据流消费者
    推送系统统计数据和健康警报
    """
    
    async def connect(self):
        """建立WebSocket连接"""
        # 检查用户是否为管理员
        user = self.scope['user']
        
        if not user.is_authenticated:
            await self.close()
            return
        
        # 检查管理员权限
        is_admin = await self.check_admin_permission(user)
        if not is_admin:
            await self.close()
            return
        
        # 加入admin组
        await self.channel_layer.group_add(
            'admin_dashboard',
            self.channel_name
        )
        
        await self.accept()
        
        # 开始发送实时数据
        self.should_send = True
        asyncio.create_task(self.send_periodic_updates())
    
    async def disconnect(self, close_code):
        """断开WebSocket连接"""
        self.should_send = False
        
        # 离开admin组
        await self.channel_layer.group_discard(
            'admin_dashboard',
            self.channel_name
        )
    
    async def receive(self, text_data):
        """接收客户端消息"""
        try:
            data = json.loads(text_data)
            command = data.get('command')
            
            if command == 'get_stats':
                await self.send_statistics()
            elif command == 'get_alerts':
                await self.send_alerts()
        except json.JSONDecodeError:
            pass
    
    async def send_periodic_updates(self):
        """定期发送更新数据"""
        while self.should_send:
            try:
                await self.send_statistics()
                await asyncio.sleep(5)  # 每5秒更新一次
            except Exception as e:
                print(f"Error sending periodic updates: {e}")
                break
    
    async def send_statistics(self):
        """发送统计数据"""
        stats = await self.get_system_statistics()
        
        await self.send(text_data=json.dumps({
            'type': 'statistics',
            'data': stats,
            'timestamp': datetime.now().isoformat()
        }))
    
    async def send_alerts(self):
        """发送警报数据"""
        alerts = await self.get_health_alerts()
        
        await self.send(text_data=json.dumps({
            'type': 'alerts',
            'data': alerts,
            'timestamp': datetime.now().isoformat()
        }))
    
    @database_sync_to_async
    def check_admin_permission(self, user):
        """检查管理员权限"""
        return user.is_superuser or user.role == 'admin'
    
    @database_sync_to_async
    def get_system_statistics(self):
        """获取系统统计数据"""
        from .models import Measurement, MedicationRecord, SleepLog, MoodLog
        
        # 活跃用户数（最近24小时有记录的用户）
        day_ago = datetime.now() - timedelta(days=1)
        active_users = Measurement.objects.filter(
            measured_at__gte=day_ago
        ).values('user').distinct().count()
        
        # 总用户数
        total_users = User.objects.filter(role='user').count()
        
        # 今日新增测量记录
        today = datetime.now().date()
        today_measurements = Measurement.objects.filter(
            measured_at__date=today
        ).count()
        
        # 平均健康评分（简化版本）
        recent_measurements = Measurement.objects.filter(
            measured_at__gte=day_ago
        )
        
        avg_systolic = recent_measurements.aggregate(Avg('systolic'))['systolic__avg'] or 0
        avg_heart_rate = recent_measurements.aggregate(Avg('heart_rate'))['heart_rate__avg'] or 0
        
        return {
            'active_users': active_users,
            'total_users': total_users,
            'today_measurements': today_measurements,
            'avg_systolic': round(avg_systolic, 1),
            'avg_heart_rate': round(avg_heart_rate, 1),
        }
    
    @database_sync_to_async
    def get_health_alerts(self):
        """获取健康警报"""
        from .models import Measurement
        
        # 查找最近的异常指标
        day_ago = datetime.now() - timedelta(days=1)
        measurements = Measurement.objects.filter(
            measured_at__gte=day_ago
        ).select_related('user')
        
        alerts = []
        
        for m in measurements:
            # 高血压警报
            if m.systolic and m.systolic > 140:
                alerts.append({
                    'type': 'high_blood_pressure',
                    'user': m.user.username,
                    'message': f'{m.user.username}血压偏高: {m.systolic}/{m.diastolic}',
                    'level': 'warning',
                    'time': m.measured_at.isoformat()
                })
            
            # 高血糖警报
            if m.blood_glucose and float(m.blood_glucose) > 7.0:
                alerts.append({
                    'type': 'high_glucose',
                    'user': m.user.username,
                    'message': f'{m.user.username}血糖偏高: {m.blood_glucose} mmol/L',
                    'level': 'warning',
                    'time': m.measured_at.isoformat()
                })
            
            # 心率异常警报
            if m.heart_rate and (m.heart_rate > 100 or m.heart_rate < 60):
                alerts.append({
                    'type': 'abnormal_heart_rate',
                    'user': m.user.username,
                    'message': f'{m.user.username}心率异常: {m.heart_rate} bpm',
                    'level': 'info',
                    'time': m.measured_at.isoformat()
                })
        
        # 限制警报数量
        return alerts[:20]
