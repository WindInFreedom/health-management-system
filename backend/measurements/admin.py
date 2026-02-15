from django.contrib import admin
from .models import Measurement, MedicationRecord, SleepLog, MoodLog


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


@admin.register(MedicationRecord)
class MedicationRecordAdmin(admin.ModelAdmin):
    list_display = ('user', 'name', 'dosage', 'frequency', 'start_date', 'end_date')
    list_filter = ('user', 'start_date')
    search_fields = ('user__username', 'name', 'notes')
    date_hierarchy = 'start_date'
    ordering = ('-start_date',)


@admin.register(SleepLog)
class SleepLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'sleep_date', 'duration_minutes', 'quality_rating')
    list_filter = ('user', 'sleep_date')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'sleep_date'
    ordering = ('-sleep_date',)


@admin.register(MoodLog)
class MoodLogAdmin(admin.ModelAdmin):
    list_display = ('user', 'log_date', 'mood_rating')
    list_filter = ('user', 'log_date')
    search_fields = ('user__username', 'notes')
    date_hierarchy = 'log_date'
    ordering = ('-log_date',)
