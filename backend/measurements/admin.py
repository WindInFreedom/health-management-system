from django.contrib import admin
from .models import Measurement


@admin.register(Measurement)
class MeasurementAdmin(admin.ModelAdmin):
    list_display = ('user', 'measured_at', 'weight_kg', 'systolic', 'diastolic', 'blood_glucose', 'heart_rate')
    list_filter = ('user', 'measured_at')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'measured_at'
    ordering = ('-measured_at',)
    
    fieldsets = (
        ('基本信息', {
            'fields': ('user', 'measured_at')
        }),
        ('测量数据', {
            'fields': ('weight_kg', 'systolic', 'diastolic', 'blood_glucose', 'heart_rate')
        }),
        ('备注', {
            'fields': ('notes',)
        }),
    )
