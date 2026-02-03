"""
协同过滤算法实现
用于健康预警和风险评估
"""

import numpy as np
from django.contrib.auth import get_user_model
from django.db.models import Avg, StdDev
from .models import Measurement
from datetime import datetime, timedelta

User = get_user_model()


class HealthCollaborativeFiltering:
    def __init__(self):
        self.user_similarity_matrix = None
        self.health_profiles = {}
        
    def build_user_profiles(self):
        """构建用户健康档案"""
        users = User.objects.all()
        
        for user in users:
            measurements = Measurement.objects.filter(user=user).order_by('-measured_at')[:30]  # 最近30次测量
            
            if measurements.count() >= 10:  # 至少10次测量
                profile = {
                    'user_id': user.id,
                    'username': user.username,
                    'age': self.calculate_age(user),
                    'gender': getattr(user.profile, 'gender', 'unknown') if hasattr(user, 'profile') else 'unknown',
                    'health_metrics': self.calculate_health_metrics(measurements),
                    'risk_factors': self.identify_risk_factors(measurements),
                    'lifestyle_score': self.calculate_lifestyle_score(measurements)
                }
                self.health_profiles[user.id] = profile
    
    def calculate_age(self, user):
        """计算用户年龄"""
        if hasattr(user, 'profile') and user.profile.birth_date:
            today = datetime.now().date()
            birth_date = user.profile.birth_date
            return today.year - birth_date.year - ((today.month, today.day) < (birth_date.month, birth_date.day))
        return 35  # 默认年龄
    
    def calculate_health_metrics(self, measurements):
        """计算健康指标"""
        if not measurements:
            return {}
        
        weights = [m.weight_kg for m in measurements]
        systolic = [m.systolic for m in measurements]
        diastolic = [m.diastolic for m in measurements]
        heart_rates = [m.heart_rate for m in measurements]
        glucose = [m.blood_glucose for m in measurements]
        
        return {
            'avg_weight': np.mean(weights),
            'std_weight': np.std(weights),
            'avg_systolic': np.mean(systolic),
            'std_systolic': np.std(systolic),
            'avg_diastolic': np.mean(diastolic),
            'std_diastolic': np.std(diastolic),
            'avg_heart_rate': np.mean(heart_rates),
            'std_heart_rate': np.std(heart_rates),
            'avg_glucose': np.mean(glucose),
            'std_glucose': np.std(glucose),
            'latest_weight': weights[0] if weights else 0,
            'latest_systolic': systolic[0] if systolic else 0,
            'latest_diastolic': diastolic[0] if diastolic else 0,
            'latest_heart_rate': heart_rates[0] if heart_rates else 0,
            'latest_glucose': glucose[0] if glucose else 0,
        }
    
    def identify_risk_factors(self, measurements):
        """识别风险因素"""
        risk_factors = []
        
        if not measurements:
            return risk_factors
        
        latest = measurements.first()
        
        # 血压风险
        if latest.systolic > 140 or latest.diastolic > 90:
            risk_factors.append('high_blood_pressure')
        elif latest.systolic > 130 or latest.diastolic > 85:
            risk_factors.append('elevated_blood_pressure')
        
        # 血糖风险
        if latest.blood_glucose > 7.0:
            risk_factors.append('high_blood_glucose')
        elif latest.blood_glucose > 6.1:
            risk_factors.append('elevated_blood_glucose')
        
        # 心率风险
        if latest.heart_rate > 100:
            risk_factors.append('high_heart_rate')
        elif latest.heart_rate < 60:
            risk_factors.append('low_heart_rate')
        
        # 体重风险
        if latest.weight_kg > 90:
            risk_factors.append('overweight')
        elif latest.weight_kg < 50:
            risk_factors.append('underweight')
        
        return risk_factors
    
    def calculate_lifestyle_score(self, measurements):
        """计算生活方式评分（0-100）"""
        if not measurements:
            return 50
        
        score = 100
        
        latest = measurements.first()
        
        # 基于健康指标扣分
        if latest.systolic > 140 or latest.diastolic > 90:
            score -= 20
        elif latest.systolic > 130 or latest.diastolic > 85:
            score -= 10
        
        if latest.blood_glucose > 7.0:
            score -= 20
        elif latest.blood_glucose > 6.1:
            score -= 10
        
        if latest.heart_rate > 100 or latest.heart_rate < 60:
            score -= 10
        
        # 基于数据一致性扣分（规律性）
        if len(measurements) >= 10:
            weight_std = np.std([m.weight_kg for m in measurements])
            if weight_std > 5:  # 体重波动大
                score -= 15
        
        return max(0, score)
    
    def calculate_user_similarity(self, user1_id, user2_id):
        """计算用户相似度"""
        if user1_id not in self.health_profiles or user2_id not in self.health_profiles:
            return 0
        
        profile1 = self.health_profiles[user1_id]
        profile2 = self.health_profiles[user2_id]
        
        # 年龄相似度
        age_diff = abs(profile1['age'] - profile2['age'])
        age_similarity = max(0, 1 - age_diff / 50)  # 年龄差50岁为0相似度
        
        # 健康指标相似度
        metrics1 = profile1['health_metrics']
        metrics2 = profile2['health_metrics']
        
        # 计算欧氏距离
        distance = 0
        count = 0
        
        for metric in ['avg_weight', 'avg_systolic', 'avg_diastolic', 'avg_heart_rate', 'avg_glucose']:
            if metric in metrics1 and metric in metrics2:
                # 归一化处理
                val1 = float(metrics1[metric])
                val2 = float(metrics2[metric])
                
                # 使用相对差异
                if val1 > 0 and val2 > 0:
                    relative_diff = abs(val1 - val2) / max(val1, val2)
                    distance += relative_diff
                    count += 1
        
        if count > 0:
            metrics_similarity = max(0, 1 - distance / count)
        else:
            metrics_similarity = 0
        
        # 风险因素相似度
        risks1 = set(profile1['risk_factors'])
        risks2 = set(profile2['risk_factors'])
        
        if risks1 or risks2:
            intersection = len(risks1.intersection(risks2))
            union = len(risks1.union(risks2))
            risk_similarity = intersection / union if union > 0 else 1
        else:
            risk_similarity = 1
        
        # 综合相似度（权重：年龄0.2，健康指标0.5，风险因素0.3）
        overall_similarity = (
            0.2 * age_similarity +
            0.5 * metrics_similarity +
            0.3 * risk_similarity
        )
        
        return overall_similarity
    
    def find_similar_users(self, target_user_id, top_k=10):
        """找到相似用户"""
        if target_user_id not in self.health_profiles:
            return []
        
        similarities = []
        for user_id in self.health_profiles:
            if user_id != target_user_id:
                similarity = self.calculate_user_similarity(target_user_id, user_id)
                similarities.append((user_id, similarity))
        
        # 按相似度排序
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]
    
    def predict_health_risk(self, user_id):
        """预测健康风险"""
        if user_id not in self.health_profiles:
            return {}
        
        similar_users = self.find_similar_users(user_id, top_k=5)
        if not similar_users:
            return {}
        
        # 收集相似用户的风险因素
        risk_factors_count = {}
        total_similarity = 0
        
        for similar_user_id, similarity in similar_users:
            if similar_user_id in self.health_profiles:
                profile = self.health_profiles[similar_user_id]
                for risk_factor in profile['risk_factors']:
                    if risk_factor not in risk_factors_count:
                        risk_factors_count[risk_factor] = 0
                    risk_factors_count[risk_factor] += similarity
                total_similarity += similarity
        
        # 计算风险概率
        risk_predictions = {}
        if total_similarity > 0:
            for risk_factor, count in risk_factors_count.items():
                risk_predictions[risk_factor] = count / total_similarity
        
        return risk_predictions
    
    def generate_health_recommendations(self, user_id):
        """生成健康建议"""
        if user_id not in self.health_profiles:
            return []
        
        profile = self.health_profiles[user_id]
        recommendations = []
        
        # 基于当前风险因素的建议
        if 'high_blood_pressure' in profile['risk_factors']:
            recommendations.extend([
                '减少钠盐摄入，每日不超过6克',
                '增加有氧运动，每周至少150分钟',
                '限制酒精消费',
                '保持健康体重'
            ])
        
        if 'high_blood_glucose' in profile['risk_factors']:
            recommendations.extend([
                '控制碳水化合物摄入',
                '选择低GI食物',
                '规律进餐，避免暴饮暴食',
                '增加膳食纤维摄入'
            ])
        
        if 'high_heart_rate' in profile['risk_factors']:
            recommendations.extend([
                '减少咖啡因摄入',
                '进行放松训练，如冥想、瑜伽',
                '保证充足睡眠',
                '避免过度劳累'
            ])
        
        if 'overweight' in profile['risk_factors']:
            recommendations.extend([
                '控制总热量摄入',
                '增加蔬菜水果比例',
                '规律运动，每周至少3次',
                '避免高脂肪食物'
            ])
        
        # 基于相似用户的成功经验
        similar_users = self.find_similar_users(user_id, top_k=3)
        for similar_user_id, similarity in similar_users:
            if similar_user_id in self.health_profiles:
                similar_profile = self.health_profiles[similar_user_id]
                if similar_profile['lifestyle_score'] > 80:
                    recommendations.append(
                        f"与您健康状况相似的用户 {similar_profile['username']} 通过健康的生活方式获得了良好的健康指标"
                    )
        
        return list(set(recommendations))  # 去重
    
    def get_early_warning_alerts(self, user_id):
        """获取早期预警提醒"""
        if user_id not in self.health_profiles:
            return []
        
        profile = self.health_profiles[user_id]
        alerts = []
        
        # 基于趋势的预警
        metrics = profile['health_metrics']
        
        # 体重趋势预警
        if metrics.get('std_weight', 0) > 3:
            alerts.append({
                'type': 'weight_fluctuation',
                'message': '您的体重波动较大，建议保持稳定的饮食和运动习惯',
                'severity': 'medium'
            })
        
        # 血压趋势预警
        if metrics.get('latest_systolic', 0) > 130:
            alerts.append({
                'type': 'blood_pressure_trend',
                'message': '您的血压呈上升趋势，建议定期监测并咨询医生',
                'severity': 'high' if metrics.get('latest_systolic', 0) > 140 else 'medium'
            })
        
        # 血糖趋势预警
        if metrics.get('latest_glucose', 0) > 6.1:
            alerts.append({
                'type': 'blood_glucose_trend',
                'message': '您的血糖水平偏高，建议控制糖分摄入并增加运动',
                'severity': 'high' if metrics.get('latest_glucose', 0) > 7.0 else 'medium'
            })
        
        # 基于相似用户的预警
        risk_predictions = self.predict_health_risk(user_id)
        for risk_factor, probability in risk_predictions.items():
            if probability > 0.6:  # 高风险阈值
                risk_messages = {
                    'high_blood_pressure': '根据相似用户的数据，您有较高的高血压风险',
                    'high_blood_glucose': '根据相似用户的数据，您有较高的高血糖风险',
                    'high_heart_rate': '根据相似用户的数据，您有较高的心率异常风险',
                    'overweight': '根据相似用户的数据，您有较高的体重超标风险'
                }
                
                if risk_factor in risk_messages:
                    alerts.append({
                        'type': f'collaborative_{risk_factor}',
                        'message': risk_messages[risk_factor],
                        'severity': 'high',
                        'probability': probability
                    })
        
        return alerts


def get_collaborative_filtering_recommendations(user_id):
    """获取协同过滤推荐"""
    cf = HealthCollaborativeFiltering()
    cf.build_user_profiles()
    
    return {
        'similar_users': cf.find_similar_users(user_id, top_k=5),
        'risk_predictions': cf.predict_health_risk(user_id),
        'recommendations': cf.generate_health_recommendations(user_id),
        'early_warnings': cf.get_early_warning_alerts(user_id)
    }
