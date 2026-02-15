from rest_framework import serializers
from .models import Measurement, MedicationRecord
from users.models import SleepLog, MoodLog  # 从 users.models 导入


class MeasurementSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Measurement
        fields = [
            'id', 'user', 'measured_at', 'weight_kg', 'systolic', 'diastolic',
            'blood_glucose', 'heart_rate', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']

    def validate(self, data):
        # 至少需要一个测量值
        if not any([
            data.get('weight_kg'),
            data.get('systolic'),
            data.get('diastolic'),
            data.get('blood_glucose'),
            data.get('heart_rate')
        ]):
            raise serializers.ValidationError("至少需要提供一个测量值")
        
        # 验证血压值
        systolic = data.get('systolic')
        diastolic = data.get('diastolic')
        
        if systolic and diastolic:
            if systolic <= diastolic:
                raise serializers.ValidationError("收缩压必须大于舒张压")
        
        return data
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # 延迟导入 User queryset 避免循环 import（如果需要）
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['user'].queryset = User.objects.all()


# 替换本地内容：新增序列化器支持扩展的健康指标
class MedicationRecordSerializer(serializers.ModelSerializer):
    """药物记录序列化器"""
    class Meta:
        model = MedicationRecord
        fields = [
            'id', 'user', 'name', 'dosage', 'frequency',
            'start_date', 'end_date', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'created_at', 'updated_at']
    
    def validate(self, data):
        """验证开始日期和结束日期"""
        if data.get('end_date') and data.get('start_date'):
            if data['end_date'] < data['start_date']:
                raise serializers.ValidationError("结束日期不能早于开始日期")
        return data


class SleepLogSerializer(serializers.ModelSerializer):
    """睡眠记录序列化器"""
    duration_hours = serializers.SerializerMethodField()
    
    class Meta:
        model = SleepLog
        fields = [
            'id', 'user', 'start_time', 'end_time', 'duration_minutes',
            'duration_hours', 'quality_rating', 'notes', 'created_at', 'updated_at'
        ]
        read_only_fields = ['user', 'duration_minutes', 'created_at', 'updated_at']
    
    def get_duration_hours(self, obj):
        """返回睡眠时长（小时）"""
        return round(obj.duration_minutes / 60, 2) if obj.duration_minutes else 0
    
    def validate(self, data):
        """验证开始时间和结束时间"""
        if data.get('end_time') and data.get('start_time'):
            if data['end_time'] <= data['start_time']:
                raise serializers.ValidationError("结束时间必须晚于开始时间")
        return data


class MoodLogSerializer(serializers.ModelSerializer):
    """情绪记录序列化器"""
    mood_description = serializers.SerializerMethodField()
    
    class Meta:
        model = MoodLog
        fields = ['id', 'user', 'log_date', 'mood_rating', 'notes', 'created_at', 'updated_at']
    
    def get_mood_description(self, obj):
        """根据评分返回情绪描述"""
        if obj.mood_rating >= 9:
            return "非常愉悦"
        elif obj.mood_rating >= 7:
            return "心情不错"
        elif obj.mood_rating >= 5:
            return "情绪平稳"
        elif obj.mood_rating >= 3:
            return "有些低落"
        else:
            return "情绪低沉"
