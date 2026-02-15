"""
Health Scoring Service
Implements a multi-dimensional health evaluation system with configurable metrics and weights.
Returns normalized scores (0-100) for various health indicators plus an overall score.
"""

import numpy as np
from typing import Dict, List, Tuple, Optional
from datetime import timedelta
from django.utils import timezone  # 使用 timezone 而不是 datetime
from django.contrib.auth import get_user_model
from measurements.models import Measurement, SleepLog, MoodLog

User = get_user_model()


class HealthScoringConfig:
    """
    Configuration for health metrics scoring.
    Defines normal ranges, weights, and scoring parameters for each health metric.
    """
    
    # Metric configurations: (optimal_min, optimal_max, weight, unit, label)
    METRICS = {
        'bmi': {
            'optimal_range': (18.5, 24.9),
            'acceptable_range': (17.0, 29.9),
            'weight': 0.20,
            'unit': 'kg/m²',
            'label': 'BMI指数',
            'higher_is_better': False  # Optimal is in range
        },
        'blood_pressure': {
            'systolic_optimal': (90, 120),
            'diastolic_optimal': (60, 80),
            'systolic_acceptable': (85, 139),
            'diastolic_acceptable': (55, 89),
            'weight': 0.25,
            'unit': 'mmHg',
            'label': '血压',
        },
        'heart_rate': {
            'optimal_range': (60, 80),
            'acceptable_range': (50, 100),
            'weight': 0.15,
            'unit': 'bpm',
            'label': '心率',
        },
        'blood_glucose': {
            'optimal_range': (3.9, 6.1),
            'acceptable_range': (3.5, 7.0),
            'weight': 0.20,
            'unit': 'mmol/L',
            'label': '血糖',
        },
        'sleep_quality': {
            'optimal_range': (7.0, 9.0),  # hours
            'acceptable_range': (6.0, 10.0),
            'weight': 0.10,
            'unit': '小时',
            'label': '睡眠质量',
        },
        'mood_index': {
            'optimal_range': (7, 10),
            'acceptable_range': (5, 10),
            'weight': 0.10,
            'unit': '分',
            'label': '心情指数',
        },
    }


class HealthScoringService:
    """
    Service for calculating health scores based on user measurements.
    """
    
    def __init__(self, user_id: int, days: int = 30):
        """
        Initialize scoring service for a user.
        
        Args:
            user_id: User ID to score
            days: Number of days to consider for scoring (default: 30)
        """
        self.user_id = user_id
        self.days = days
        self.user = User.objects.get(id=user_id)
        self.config = HealthScoringConfig()
        
    def calculate_bmi(self, weight_kg: float, height_cm: float) -> float:
        """Calculate BMI from weight and height."""
        if height_cm <= 0:
            return None
        height_m = height_cm / 100.0
        return weight_kg / (height_m ** 2)
    
    def score_metric_in_range(self, value: float, optimal_range: Tuple[float, float], 
                               acceptable_range: Tuple[float, float]) -> float:
        """
        Score a metric based on optimal and acceptable ranges.
        
        Returns:
            Score from 0-100
        """
        if value is None:
            return None
            
        opt_min, opt_max = optimal_range
        acc_min, acc_max = acceptable_range
        
        # Perfect score if in optimal range
        if opt_min <= value <= opt_max:
            return 100.0
        
        # Partial score if in acceptable range
        if acc_min <= value < opt_min:
            # Linear interpolation from 60 to 100
            ratio = (value - acc_min) / (opt_min - acc_min)
            return 60.0 + ratio * 40.0
        elif opt_max < value <= acc_max:
            # Linear interpolation from 100 to 60
            ratio = (value - opt_max) / (acc_max - opt_max)
            return 100.0 - ratio * 40.0
        
        # Below or above acceptable range - poor score
        if value < acc_min:
            distance = acc_min - value
            range_width = acc_min - (acc_min * 0.5)  # Allow 50% below
            ratio = min(distance / range_width, 1.0)
            return max(60.0 - ratio * 60.0, 0.0)
        else:  # value > acc_max
            distance = value - acc_max
            range_width = acc_max * 0.5  # Allow 50% above
            ratio = min(distance / range_width, 1.0)
            return max(60.0 - ratio * 60.0, 0.0)
    
    def get_recent_measurements(self) -> List[Measurement]:
        """Get recent measurements for the user."""
        start_date = timezone.now() - timedelta(days=self.days)
        return Measurement.objects.filter(
            user_id=self.user_id,
            measured_at__gte=start_date
        ).order_by('-measured_at')
    
    def score_bmi(self) -> Dict:
        """Score BMI based on recent measurements and profile."""
        measurements = self.get_recent_measurements()
        profile = getattr(self.user, 'profile', None)
        
        if not profile or not profile.height_cm:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '身高信息缺失，无法计算BMI',
                'suggestions': ['请在个人档案中填写身高信息']
            }
        
        # Get latest weight
        weight_measurement = measurements.filter(weight_kg__isnull=False).first()
        if not weight_measurement:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '体重数据缺失',
                'suggestions': ['请记录您的体重数据']
            }
        
        bmi = self.calculate_bmi(float(weight_measurement.weight_kg), float(profile.height_cm))
        config = self.config.METRICS['bmi']
        score = self.score_metric_in_range(bmi, config['optimal_range'], config['acceptable_range'])
        
        # Generate status and suggestions
        status, suggestions = self._get_status_and_suggestions('bmi', bmi, score)
        
        return {
            'score': round(score, 1) if score is not None else None,
            'value': round(bmi, 1) if bmi is not None else None,
            'status': status,
            'message': f'您的BMI为 {bmi:.1f}',
            'suggestions': suggestions
        }
    
    def score_blood_pressure(self) -> Dict:
        """Score blood pressure based on recent measurements."""
        measurements = self.get_recent_measurements()
        bp_measurements = measurements.filter(
            systolic__isnull=False, 
            diastolic__isnull=False
        )[:10]  # Last 10 measurements
        
        if not bp_measurements:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '血压数据缺失',
                'suggestions': ['请记录您的血压数据']
            }
        
        # Average recent blood pressure
        avg_systolic = np.mean([m.systolic for m in bp_measurements])
        avg_diastolic = np.mean([m.diastolic for m in bp_measurements])
        
        config = self.config.METRICS['blood_pressure']
        
        # Score both systolic and diastolic
        systolic_score = self.score_metric_in_range(
            avg_systolic, 
            config['systolic_optimal'], 
            config['systolic_acceptable']
        )
        diastolic_score = self.score_metric_in_range(
            avg_diastolic, 
            config['diastolic_optimal'], 
            config['diastolic_acceptable']
        )
        
        # Overall score is average of both
        score = (systolic_score + diastolic_score) / 2
        
        status, suggestions = self._get_status_and_suggestions('blood_pressure', (avg_systolic, avg_diastolic), score)
        
        return {
            'score': round(score, 1),
            'value': {'systolic': round(avg_systolic, 1), 'diastolic': round(avg_diastolic, 1)},
            'status': status,
            'message': f'平均血压: {avg_systolic:.0f}/{avg_diastolic:.0f} mmHg',
            'suggestions': suggestions
        }
    
    def score_heart_rate(self) -> Dict:
        """Score heart rate based on recent measurements."""
        measurements = self.get_recent_measurements()
        hr_measurements = measurements.filter(heart_rate__isnull=False)[:10]
        
        if not hr_measurements:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '心率数据缺失',
                'suggestions': ['请记录您的心率数据']
            }
        
        avg_hr = np.mean([m.heart_rate for m in hr_measurements])
        config = self.config.METRICS['heart_rate']
        score = self.score_metric_in_range(avg_hr, config['optimal_range'], config['acceptable_range'])
        
        status, suggestions = self._get_status_and_suggestions('heart_rate', avg_hr, score)
        
        return {
            'score': round(score, 1),
            'value': round(avg_hr, 1),
            'status': status,
            'message': f'平均心率: {avg_hr:.0f} bpm',
            'suggestions': suggestions
        }
    
    def score_blood_glucose(self) -> Dict:
        """Score blood glucose based on recent measurements."""
        measurements = self.get_recent_measurements()
        glucose_measurements = measurements.filter(blood_glucose__isnull=False)[:10]
        
        if not glucose_measurements:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '血糖数据缺失',
                'suggestions': ['请记录您的血糖数据']
            }
        
        avg_glucose = np.mean([float(m.blood_glucose) for m in glucose_measurements])
        config = self.config.METRICS['blood_glucose']
        score = self.score_metric_in_range(avg_glucose, config['optimal_range'], config['acceptable_range'])
        
        status, suggestions = self._get_status_and_suggestions('blood_glucose', avg_glucose, score)
        
        return {
            'score': round(score, 1),
            'value': round(avg_glucose, 1),
            'status': status,
            'message': f'平均血糖: {avg_glucose:.1f} mmol/L',
            'suggestions': suggestions
        }

    def score_sleep_quality(self) -> Dict:
        """Score sleep quality based on recent sleep logs."""
        # 将 datetime 转换为 date 类型
        start_date = (timezone.now() - timedelta(days=self.days)).date()
        sleep_logs = SleepLog.objects.filter(
            user_id=self.user_id,
            sleep_date__gte=start_date
        )[:14]  # Last 2 weeks

        if not sleep_logs:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '睡眠数据缺失',
                'suggestions': ['请记录您的睡眠数据']
            }

        # Average sleep duration in hours
        avg_sleep_hours = np.mean([log.duration_minutes / 60.0 for log in sleep_logs])
        config = self.config.METRICS['sleep_quality']
        score = self.score_metric_in_range(avg_sleep_hours, config['optimal_range'], config['acceptable_range'])

        status, suggestions = self._get_status_and_suggestions('sleep_quality', avg_sleep_hours, score)

        return {
            'score': round(score, 1),
            'value': round(avg_sleep_hours, 1),
            'status': status,
            'message': f'平均睡眠时长: {avg_sleep_hours:.1f} 小时',
            'suggestions': suggestions
        }

    def score_mood_index(self) -> Dict:
        """Score mood based on recent mood logs."""
        # 将 datetime 转换为 date 类型
        start_date = (timezone.now() - timedelta(days=self.days)).date()
        mood_logs = MoodLog.objects.filter(
            user_id=self.user_id,
            log_date__gte=start_date
        )[:14]  # Last 2 weeks

        if not mood_logs:
            return {
                'score': None,
                'value': None,
                'status': 'insufficient_data',
                'message': '心情数据缺失',
                'suggestions': ['请记录您的每日心情']
            }

        avg_mood = np.mean([log.mood_rating for log in mood_logs])
        config = self.config.METRICS['mood_index']
        score = self.score_metric_in_range(avg_mood, config['optimal_range'], config['acceptable_range'])

        status, suggestions = self._get_status_and_suggestions('mood_index', avg_mood, score)

        return {
            'score': round(score, 1),
            'value': round(avg_mood, 1),
            'status': status,
            'message': f'平均心情指数: {avg_mood:.1f}/10',
            'suggestions': suggestions
        }
    
    def _get_status_and_suggestions(self, metric: str, value, score: float) -> Tuple[str, List[str]]:
        """Generate status and suggestions based on score."""
        if score is None:
            return 'insufficient_data', ['数据不足，无法评估']
        
        suggestions = []
        
        if score >= 80:
            status = 'good'
            if metric == 'bmi':
                suggestions.append('保持良好的体重管理')
            elif metric == 'blood_pressure':
                suggestions.append('血压控制良好，继续保持')
            elif metric == 'heart_rate':
                suggestions.append('心率正常，保持规律运动')
            elif metric == 'blood_glucose':
                suggestions.append('血糖控制良好')
            elif metric == 'sleep_quality':
                suggestions.append('睡眠质量优秀，继续保持')
            elif metric == 'mood_index':
                suggestions.append('心情愉悦，保持积极心态')
        elif score >= 60:
            status = 'moderate'
            if metric == 'bmi':
                suggestions.extend(['注意饮食均衡', '适当增加运动量'])
            elif metric == 'blood_pressure':
                suggestions.extend(['注意减少盐分摄入', '保持心情放松', '定期监测血压'])
            elif metric == 'heart_rate':
                suggestions.extend(['注意休息', '适度运动'])
            elif metric == 'blood_glucose':
                suggestions.extend(['控制碳水化合物摄入', '增加膳食纤维', '定期监测血糖'])
            elif metric == 'sleep_quality':
                suggestions.extend(['建立规律作息', '睡前避免使用电子设备'])
            elif metric == 'mood_index':
                suggestions.extend(['多与亲友交流', '尝试放松活动'])
        else:
            status = 'warning'
            if metric == 'bmi':
                suggestions.extend(['建议咨询营养师', '制定个性化饮食计划', '增加运动'])
            elif metric == 'blood_pressure':
                suggestions.extend(['建议就医检查', '严格控制盐分摄入', '避免情绪激动'])
            elif metric == 'heart_rate':
                suggestions.extend(['建议就医检查', '避免剧烈运动', '保持充足休息'])
            elif metric == 'blood_glucose':
                suggestions.extend(['建议就医检查', '严格控制饮食', '定期监测血糖'])
            elif metric == 'sleep_quality':
                suggestions.extend(['建议咨询医生', '改善睡眠环境', '考虑心理咨询'])
            elif metric == 'mood_index':
                suggestions.extend(['建议寻求专业心理咨询', '与亲友多交流', '适当户外活动'])
        
        return status, suggestions
    
    def calculate_overall_score(self) -> Dict:
        """
        Calculate overall health score with per-dimension scores.
        
        Returns:
            Dict containing overall score and detailed dimension scores
        """
        dimensions = {
            'bmi': self.score_bmi(),
            'blood_pressure': self.score_blood_pressure(),
            'heart_rate': self.score_heart_rate(),
            'blood_glucose': self.score_blood_glucose(),
            'sleep_quality': self.score_sleep_quality(),
            'mood_index': self.score_mood_index(),
        }
        
        # Calculate weighted overall score
        total_weight = 0
        weighted_sum = 0
        
        for metric_name, result in dimensions.items():
            if result['score'] is not None:
                weight = self.config.METRICS[metric_name]['weight']
                weighted_sum += result['score'] * weight
                total_weight += weight
        
        overall_score = (weighted_sum / total_weight) if total_weight > 0 else None
        
        # Overall status and suggestions
        if overall_score is None:
            overall_status = 'insufficient_data'
            overall_message = '数据不足，无法生成完整报告'
            overall_suggestions = ['请补充更多健康数据以获得准确评估']
        elif overall_score >= 80:
            overall_status = 'excellent'
            overall_message = '您的整体健康状况优秀'
            overall_suggestions = ['继续保持良好的生活习惯', '定期体检']
        elif overall_score >= 60:
            overall_status = 'good'
            overall_message = '您的整体健康状况良好'
            overall_suggestions = ['注意改善评分较低的指标', '保持健康生活方式']
        else:
            overall_status = 'needs_attention'
            overall_message = '您的健康状况需要关注'
            overall_suggestions = ['建议尽快就医检查', '重点改善评分较低的指标', '定期监测健康数据']
        
        return {
            'overall_score': round(overall_score, 1) if overall_score is not None else None,
            'overall_status': overall_status,
            'overall_message': overall_message,
            'overall_suggestions': overall_suggestions,
            'dimensions': dimensions,
            'evaluation_period_days': self.days,
            'evaluated_at': timezone.now().isoformat()
        }
