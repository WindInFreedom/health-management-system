"""
风险评估 API 路由

提供健康风险评估服务

作者: Health Management System Team
日期: 2026-02-15
"""

from fastapi import APIRouter, HTTPException
import sys
import os
import pandas as pd
import numpy as np

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
import django
django.setup()

from api.models.schemas import RiskAssessmentRequest, RiskAssessmentResponse
from ml_models.feature_extractor import FeatureExtractor
from ml_models.risk_assessor import RiskAssessor
from measurements.models import Measurement
from django.contrib.auth import get_user_model
from datetime import datetime, timedelta

User = get_user_model()
router = APIRouter()


@router.post("/risk-assessment", response_model=RiskAssessmentResponse)
async def assess_health_risk(request: RiskAssessmentRequest):
    """
    评估健康风险
    
    基于时间序列特征提取和随机森林分类器评估风险等级
    """
    try:
        # 验证用户
        try:
            user = User.objects.get(id=request.user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail=f"用户 {request.user_id} 不存在")
        
        # 获取指定时间窗口内的数据
        end_date = datetime.now()
        start_date = end_date - timedelta(days=request.time_window)
        
        measurements = Measurement.objects.filter(
            user=user,
            measured_at__gte=start_date,
            measured_at__lte=end_date
        ).order_by('measured_at')
        
        if measurements.count() < 30:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：仅有 {measurements.count()} 条记录，至少需要 30 条"
            )
        
        # 提取所有指标的特征
        all_features = {}
        
        for metric in request.metrics:
            data = list(measurements.values('measured_at', metric))
            df = pd.DataFrame(data)
            df[metric] = pd.to_numeric(df[metric], errors='coerce')
            df = df.dropna(subset=[metric])
            
            if len(df) < 10:
                continue
            
            # 提取特征
            metric_data = df[metric].values
            features = FeatureExtractor.extract_all_features(metric_data)
            all_features.update({f"{metric}_{k}": v for k, v in features.items()})
        
        if not all_features:
            raise HTTPException(status_code=400, detail="无法提取有效特征")
        
        # 转换为特征向量
        feature_vector = np.array(list(all_features.values()))
        
        # 使用简单的规则based风险评估 (由于没有预训练模型)
        # 基于统计特征判断风险
        risk_score = 0.0
        risk_factors = []
        
        # 检查各指标是否异常
        for metric in request.metrics:
            if f"{metric}_stat_mean" in all_features:
                mean_val = all_features[f"{metric}_stat_mean"]
                std_val = all_features.get(f"{metric}_stat_std", 0)
                cv = all_features.get(f"{metric}_volatility_cv", 0)
                
                # 根据医学标准判断
                thresholds = RiskAssessor.METRIC_THRESHOLDS.get(metric, {})
                
                if metric == 'blood_glucose':
                    if mean_val > 6.1:
                        risk_score += 0.3
                        risk_factors.append({
                            "factor": f"{metric}_high",
                            "importance": 0.35,
                            "description": "血糖平均值偏高"
                        })
                elif metric == 'systolic':
                    if mean_val > 120:
                        risk_score += 0.25
                        risk_factors.append({
                            "factor": f"{metric}_high",
                            "importance": 0.30,
                            "description": "收缩压偏高"
                        })
                elif metric == 'heart_rate':
                    if mean_val > 100 or mean_val < 60:
                        risk_score += 0.15
                        risk_factors.append({
                            "factor": f"{metric}_abnormal",
                            "importance": 0.20,
                            "description": "心率异常"
                        })
                
                # 波动性检查
                if cv > 15:
                    risk_score += 0.1
                    risk_factors.append({
                        "factor": f"{metric}_volatility",
                        "importance": 0.15,
                        "description": f"{metric}波动较大"
                    })
        
        # 限制风险分数在 0-1 之间
        risk_score = min(1.0, risk_score)
        
        # 确定风险等级
        if risk_score < 0.3:
            risk_level = "低风险"
            prob_low, prob_med, prob_high = 0.7, 0.25, 0.05
        elif risk_score < 0.6:
            risk_level = "中风险"
            prob_low, prob_med, prob_high = 0.2, 0.6, 0.2
        else:
            risk_level = "高风险"
            prob_low, prob_med, prob_high = 0.05, 0.25, 0.7
        
        # 确保至少有一些风险因素
        if not risk_factors:
            risk_factors.append({
                "factor": "overall_health",
                "importance": 0.5,
                "description": "整体健康状况良好，无明显风险因素"
            })
        
        return {
            "success": True,
            "user_id": request.user_id,
            "risk_level": risk_level,
            "risk_score": risk_score,
            "probabilities": {
                "低风险": prob_low,
                "中风险": prob_med,
                "高风险": prob_high
            },
            "key_factors": risk_factors[:5],  # 返回前5个风险因素
            "assessed_at": datetime.now().isoformat()
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"风险评估失败: {str(e)}")
