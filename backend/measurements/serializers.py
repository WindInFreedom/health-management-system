from rest_framework import serializers
from .models import Measurement

class MeasurementSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(read_only=True)

    class Meta:
        model = Measurement
        fields = [
            'id', 'user', 'measured_at', 'weight_kg', 'systolic', 'diastolic',
            'blood_glucose', 'heart_rate'
        ]
        read_only_fields = ['id']

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
