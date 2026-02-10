"""
健康评分服务
替换本地内容：多维度健康评分算法，基于临床标准范围的归一化和加权计算
"""
from typing import Dict, List, Optional, Tuple
from django.conf import settings
from decimal import Decimal
import numpy as np


class HealthScoringService:
    """
    健康评分服务类
    计算多维度健康评分并生成建议
    """
    
    def __init__(self):
        # 从settings获取权重配置，如果没有则使用默认值
        self.weights = getattr(settings, 'HEALTH_SCORING_WEIGHTS', {
            'bmi': 0.15,
            'blood_pressure': 0.25,
            'heart_rate': 0.15,
            'blood_glucose': 0.20,
            'cholesterol': 0.10,
            'activity': 0.05,
            'sleep_quality': 0.05,
            'mood': 0.05,
        })
        
        # 健康指标的正常范围
        self.normal_ranges = getattr(settings, 'HEALTH_NORMAL_RANGES', {
            'bmi': {'min': 18.5, 'max': 24.9},
            'systolic_bp': {'min': 90, 'max': 120},
            'diastolic_bp': {'min': 60, 'max': 80},
            'heart_rate': {'min': 60, 'max': 100},
            'blood_glucose': {'min': 3.9, 'max': 6.1},
            'cholesterol': {'min': 3.1, 'max': 5.2},
            'sleep_hours': {'min': 7, 'max': 9},
            'mood_rating': {'min': 7, 'max': 10},
        })
    
    def calculate_bmi(self, weight_kg: float, height_cm: float) -> float:
        """计算BMI指数"""
        if not weight_kg or not height_cm or height_cm == 0:
            return 0
        height_m = height_cm / 100
        return weight_kg / (height_m ** 2)
    
    def normalize_to_score(self, value: float, min_normal: float, max_normal: float, 
                          min_limit: float = 0, max_limit: float = 200) -> float:
        """
        将指标值归一化为0-100分数
        
        Args:
            value: 实际测量值
            min_normal: 正常范围最小值
            max_normal: 正常范围最大值
            min_limit: 绝对最小限制
            max_limit: 绝对最大限制
        
        Returns:
            0-100的分数
        """
        if value is None:
            return 0
        
        # 在正常范围内，得分100
        if min_normal <= value <= max_normal:
            return 100.0
        
        # 低于正常范围
        if value < min_normal:
            if value <= min_limit:
                return 0.0
            # 线性映射到0-100
            return 100.0 * (value - min_limit) / (min_normal - min_limit)
        
        # 高于正常范围
        if value > max_normal:
            if value >= max_limit:
                return 0.0
            # 线性映射到0-100
            return 100.0 * (max_limit - value) / (max_limit - max_normal)
        
        return 0.0
    
    def score_bmi(self, bmi: float) -> Tuple[float, str]:
        """
        评分BMI并生成建议
        Returns: (score, advice)
        """
        if not bmi:
            return 0, "缺少身高或体重数据"
        
        ranges = self.normal_ranges['bmi']
        score = self.normalize_to_score(bmi, ranges['min'], ranges['max'], 10, 40)
        
        if bmi < 18.5:
            advice = "体重偏轻，建议增加营养摄入，适当增重"
        elif 18.5 <= bmi < 24.9:
            advice = "体重正常，请保持健康的生活方式"
        elif 24.9 <= bmi < 28:
            advice = "体重偏重，建议控制饮食，增加运动"
        elif 28 <= bmi < 30:
            advice = "超重，建议咨询营养师，制定减重计划"
        else:
            advice = "肥胖，建议及时就医，进行专业的体重管理"
        
        return score, advice
    
    def score_blood_pressure(self, systolic: int, diastolic: int) -> Tuple[float, str]:
        """
        评分血压并生成建议
        Returns: (score, advice)
        """
        if not systolic or not diastolic:
            return 0, "缺少血压数据"
        
        # 分别计算收缩压和舒张压的分数
        systolic_score = self.normalize_to_score(
            systolic, 
            self.normal_ranges['systolic_bp']['min'],
            self.normal_ranges['systolic_bp']['max'],
            60, 200
        )
        diastolic_score = self.normalize_to_score(
            diastolic,
            self.normal_ranges['diastolic_bp']['min'],
            self.normal_ranges['diastolic_bp']['max'],
            40, 130
        )
        
        # 取平均分
        score = (systolic_score + diastolic_score) / 2
        
        # 生成建议
        if systolic >= 180 or diastolic >= 120:
            advice = "血压危险性高血压，请立即就医"
        elif systolic >= 160 or diastolic >= 100:
            advice = "2级高血压，建议尽快就医，可能需要药物治疗"
        elif systolic >= 140 or diastolic >= 90:
            advice = "1级高血压，建议就医检查，改善生活方式"
        elif systolic >= 130 or diastolic >= 85:
            advice = "血压偏高，建议控制盐分摄入，增加运动，定期监测"
        elif systolic < 90 or diastolic < 60:
            advice = "血压偏低，如有头晕等不适请就医检查"
        else:
            advice = "血压正常，请继续保持健康的生活方式"
        
        return score, advice
    
    def score_heart_rate(self, heart_rate: int) -> Tuple[float, str]:
        """
        评分心率并生成建议
        Returns: (score, advice)
        """
        if not heart_rate:
            return 0, "缺少心率数据"
        
        ranges = self.normal_ranges['heart_rate']
        score = self.normalize_to_score(heart_rate, ranges['min'], ranges['max'], 40, 150)
        
        if heart_rate < 50:
            advice = "心率过慢，如有不适请就医检查"
        elif 50 <= heart_rate < 60:
            advice = "心率偏慢，通常见于运动员，如无不适可继续监测"
        elif 60 <= heart_rate <= 100:
            advice = "心率正常，请保持规律作息"
        elif 100 < heart_rate <= 110:
            advice = "心率偏快，建议减少咖啡因摄入，注意休息"
        else:
            advice = "心率过快，建议就医检查，排除心脏问题"
        
        return score, advice
    
    def score_blood_glucose(self, glucose: float) -> Tuple[float, str]:
        """
        评分血糖并生成建议
        Returns: (score, advice)
        """
        if not glucose:
            return 0, "缺少血糖数据"
        
        ranges = self.normal_ranges['blood_glucose']
        score = self.normalize_to_score(glucose, ranges['min'], ranges['max'], 2.0, 15.0)
        
        if glucose < 3.9:
            advice = "血糖偏低，注意及时补充能量，避免低血糖"
        elif 3.9 <= glucose <= 6.1:
            advice = "空腹血糖正常，请保持健康饮食"
        elif 6.1 < glucose <= 7.0:
            advice = "血糖偏高，建议控制糖分摄入，增加运动"
        elif 7.0 < glucose <= 11.1:
            advice = "血糖明显升高，建议尽快就医检查，可能为糖尿病前期"
        else:
            advice = "血糖严重升高，请立即就医，可能需要药物治疗"
        
        return score, advice
    
    def score_sleep_quality(self, duration_hours: float, quality_rating: int = None) -> Tuple[float, str]:
        """
        评分睡眠质量并生成建议
        Returns: (score, advice)
        """
        if not duration_hours:
            return 0, "缺少睡眠数据"
        
        # 基于时长的评分
        ranges = self.normal_ranges['sleep_hours']
        duration_score = self.normalize_to_score(duration_hours, ranges['min'], ranges['max'], 4, 12)
        
        # 如果有质量评分，综合计算
        if quality_rating:
            quality_score = (quality_rating / 10) * 100
            score = (duration_score * 0.6 + quality_score * 0.4)
        else:
            score = duration_score
        
        if duration_hours < 6:
            advice = "睡眠严重不足，会影响健康，建议调整作息"
        elif 6 <= duration_hours < 7:
            advice = "睡眠不足，建议增加睡眠时间"
        elif 7 <= duration_hours <= 9:
            advice = "睡眠时间充足，请保持规律的作息"
        else:
            advice = "睡眠时间过长，建议适当减少，保持规律"
        
        return score, advice
    
    def score_mood(self, mood_rating: int) -> Tuple[float, str]:
        """
        评分情绪指标并生成建议
        Returns: (score, advice)
        """
        if not mood_rating:
            return 0, "缺少情绪数据"
        
        score = (mood_rating / 10) * 100
        
        if mood_rating >= 8:
            advice = "情绪状态良好，请保持积极心态"
        elif 6 <= mood_rating < 8:
            advice = "情绪平稳，可以通过运动、社交等方式提升"
        elif 4 <= mood_rating < 6:
            advice = "情绪一般，建议关注心理健康，适当放松"
        else:
            advice = "情绪低落，建议与亲友交流或寻求专业心理咨询"
        
        return score, advice
    
    def calculate_overall_score(self, dimension_scores: Dict[str, float]) -> Tuple[float, str]:
        """
        计算总体健康评分
        
        Args:
            dimension_scores: 各维度分数字典
        
        Returns:
            (overall_score, overall_advice)
        """
        total_score = 0
        total_weight = 0
        
        for dimension, score in dimension_scores.items():
            if score > 0 and dimension in self.weights:
                total_score += score * self.weights[dimension]
                total_weight += self.weights[dimension]
        
        if total_weight == 0:
            return 0, "缺少足够的健康数据"
        
        overall_score = total_score / total_weight
        
        # 生成总体建议
        if overall_score >= 85:
            advice = "整体健康状况优秀，请继续保持健康的生活方式"
        elif overall_score >= 70:
            advice = "整体健康状况良好，注意个别指标的改善"
        elif overall_score >= 60:
            advice = "整体健康状况一般，建议针对性改善各项指标"
        else:
            advice = "整体健康状况需要关注，建议及时就医并调整生活方式"

        return {
            'overall_score': round(overall_score, 1) if overall_score else 0,
            'overall_status': overall_status,
            'overall_message': overall_message,
            'overall_suggestions': overall_suggestions,
            'dimensions': dimensions,
            'evaluation_period_days': self.days,
            'evaluated_at': timezone.now().isoformat()  # 修改这里
        }
    
    def generate_health_report(self, user_data: Dict) -> Dict:
        """
        生成完整的健康报告
        
        Args:
            user_data: 用户健康数据，包括：
                - weight_kg: 体重
                - height_cm: 身高
                - systolic: 收缩压
                - diastolic: 舒张压
                - heart_rate: 心率
                - blood_glucose: 血糖
                - sleep_hours: 睡眠时长
                - sleep_quality: 睡眠质量评分
                - mood_rating: 情绪评分
        
        Returns:
            完整的健康报告字典
        """
        dimensions = []
        dimension_scores = {}
        
        # 计算BMI评分
        if user_data.get('weight_kg') and user_data.get('height_cm'):
            bmi = self.calculate_bmi(user_data['weight_kg'], user_data['height_cm'])
            score, advice = self.score_bmi(bmi)
            dimensions.append({
                'name': 'BMI指数',
                'value': round(bmi, 2),
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['bmi'] = score
        
        # 计算血压评分
        if user_data.get('systolic') and user_data.get('diastolic'):
            score, advice = self.score_blood_pressure(
                user_data['systolic'],
                user_data['diastolic']
            )
            dimensions.append({
                'name': '血压',
                'value': f"{user_data['systolic']}/{user_data['diastolic']} mmHg",
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['blood_pressure'] = score
        
        # 计算心率评分
        if user_data.get('heart_rate'):
            score, advice = self.score_heart_rate(user_data['heart_rate'])
            dimensions.append({
                'name': '心率',
                'value': f"{user_data['heart_rate']} bpm",
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['heart_rate'] = score
        
        # 计算血糖评分
        if user_data.get('blood_glucose'):
            score, advice = self.score_blood_glucose(float(user_data['blood_glucose']))
            dimensions.append({
                'name': '血糖',
                'value': f"{user_data['blood_glucose']} mmol/L",
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['blood_glucose'] = score
        
        # 计算睡眠评分
        if user_data.get('sleep_hours'):
            score, advice = self.score_sleep_quality(
                user_data['sleep_hours'],
                user_data.get('sleep_quality')
            )
            dimensions.append({
                'name': '睡眠质量',
                'value': f"{user_data['sleep_hours']} 小时",
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['sleep_quality'] = score
        
        # 计算情绪评分
        if user_data.get('mood_rating'):
            score, advice = self.score_mood(user_data['mood_rating'])
            dimensions.append({
                'name': '情绪指数',
                'value': f"{user_data['mood_rating']}/10",
                'score': round(score, 2),
                'advice': advice
            })
            dimension_scores['mood'] = score
        
        # 计算总体评分
        overall_score, overall_advice = self.calculate_overall_score(dimension_scores)
        
        return {
            'dimensions': dimensions,
            'overall_score': round(overall_score, 2),
            'overall_advice': overall_advice,
            'dimension_scores': dimension_scores
        }
