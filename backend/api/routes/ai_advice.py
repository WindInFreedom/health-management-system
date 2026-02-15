"""
AI 建议 API 路由

提供智能健康建议服务

作者: Health Management System Team
日期: 2026-02-15
"""

from fastapi import APIRouter, HTTPException
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from api.models.schemas import AIAdviceRequest, AIAdviceResponse
from ai_services.deepseek_advisor import DeepSeekAdvisor

router = APIRouter()

# 创建 DeepSeek 顾问实例 (默认使用 mock 模式)
advisor = DeepSeekAdvisor(mock_mode=True, use_cache=True)


@router.post("/ai-advice", response_model=AIAdviceResponse)
async def get_ai_health_advice(request: AIAdviceRequest):
    """
    获取AI健康建议
    
    基于用户信息、健康数据和风险评估结果生成个性化建议
    """
    try:
        # 构建用户配置
        user_profile = {
            'age': request.user_profile.age,
            'gender': request.user_profile.gender,
            'height_cm': request.user_profile.height_cm,
            'weight_kg': request.user_profile.weight_kg,
            'conditions': request.user_profile.conditions
        }
        
        # 构建最近数据
        recent_data = {}
        if request.recent_data.blood_glucose:
            recent_data['blood_glucose'] = request.recent_data.blood_glucose
        if request.recent_data.heart_rate:
            recent_data['heart_rate'] = request.recent_data.heart_rate
        if request.recent_data.systolic:
            recent_data['systolic'] = request.recent_data.systolic
        if request.recent_data.diastolic:
            recent_data['diastolic'] = request.recent_data.diastolic
        if request.recent_data.weight_kg:
            recent_data['weight_kg'] = request.recent_data.weight_kg
        
        # 构建风险评估（如果提供）
        risk_assessment = request.risk_assessment or {
            'level': '未评估',
            'key_factors': []
        }
        
        # 调用 AI 顾问
        advice = advisor.get_health_advice(user_profile, recent_data, risk_assessment)
        
        if not advice.get('success'):
            raise HTTPException(status_code=500, detail="生成建议失败")
        
        return advice
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取AI建议失败: {str(e)}")


@router.post("/ai-advice/simple")
async def get_simple_advice(metric: str, value: float, risk_level: str = "中风险"):
    """
    获取简单的单指标建议
    
    Args:
        metric: 指标名称
        value: 指标值
        risk_level: 风险等级
    """
    try:
        advice = advisor.get_simple_advice(metric, value, risk_level)
        return advice
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取简单建议失败: {str(e)}")


@router.post("/ai-advice/trend")
async def analyze_metric_trend(metric: str, trend_data: list):
    """
    分析指标趋势
    
    Args:
        metric: 指标名称
        trend_data: 趋势数据列表
    """
    try:
        analysis = advisor.analyze_trend(metric, trend_data)
        return analysis
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"趋势分析失败: {str(e)}")
