"""
Pydantic 数据模型

定义 API 请求和响应的数据结构

作者: Health Management System Team
日期: 2026-02-15
"""

from pydantic import BaseModel, Field
from typing import List, Dict, Optional
from datetime import datetime


# ==================== 预测相关模型 ====================

class PredictionRequest(BaseModel):
    """预测请求模型"""
    user_id: int = Field(..., description="用户ID")
    metric: str = Field(..., description="健康指标", 
                       pattern="^(blood_glucose|heart_rate|systolic|diastolic|weight_kg)$")
    days: int = Field(7, description="预测天数", ge=1, le=30)
    model_type: str = Field("lstm", description="模型类型", pattern="^(lstm|transformer)$")
    confidence_level: float = Field(0.95, description="置信水平", ge=0.8, le=0.99)


class ConfidenceInterval(BaseModel):
    """置信区间模型"""
    lower: List[float]
    upper: List[float]
    level: float


class HistoricalBacktest(BaseModel):
    """历史回测数据模型"""
    actual: List[float]
    predicted: List[float]


class ModelMetrics(BaseModel):
    """模型评估指标"""
    MAE: float = Field(..., description="平均绝对误差")
    RMSE: float = Field(..., description="均方根误差")
    R2: float = Field(..., description="决定系数")
    MAPE: float = Field(..., description="平均绝对百分比误差")


class PredictionResponse(BaseModel):
    """预测响应模型"""
    success: bool
    model_type: str
    metric: str
    user_id: int
    predictions: List[float]
    confidence_interval: ConfidenceInterval
    future_dates: List[str]
    historical_backtest: HistoricalBacktest
    metrics: ModelMetrics
    last_update: str


# ==================== 风险评估相关模型 ====================

class RiskAssessmentRequest(BaseModel):
    """风险评估请求模型"""
    user_id: int = Field(..., description="用户ID")
    metrics: List[str] = Field(
        default=["blood_glucose", "heart_rate", "systolic", "diastolic", "weight_kg"],
        description="要评估的指标列表"
    )
    time_window: int = Field(30, description="评估时间窗口（天）", ge=7, le=90)


class RiskFactor(BaseModel):
    """风险因素模型"""
    factor: str = Field(..., description="风险因素名称")
    importance: float = Field(..., description="重要性得分")
    description: str = Field(..., description="因素描述")


class RiskAssessmentResponse(BaseModel):
    """风险评估响应模型"""
    success: bool
    user_id: int
    risk_level: str = Field(..., description="风险等级：低风险/中风险/高风险")
    risk_score: float = Field(..., description="风险分数 0-1")
    probabilities: Dict[str, float] = Field(..., description="各风险等级概率")
    key_factors: List[RiskFactor] = Field(..., description="关键风险因素")
    assessed_at: str


# ==================== AI 建议相关模型 ====================

class UserProfile(BaseModel):
    """用户个人信息模型"""
    age: int = Field(..., description="年龄", ge=0, le=150)
    gender: str = Field(..., description="性别", pattern="^(M|F)$")
    height_cm: float = Field(..., description="身高(cm)", ge=50, le=250)
    weight_kg: float = Field(..., description="体重(kg)", ge=20, le=300)
    conditions: List[str] = Field(default=[], description="既往病史")


class RecentHealthData(BaseModel):
    """最近健康数据模型"""
    blood_glucose: Optional[List[float]] = None
    heart_rate: Optional[List[int]] = None
    systolic: Optional[List[int]] = None
    diastolic: Optional[List[int]] = None
    weight_kg: Optional[List[float]] = None


class AIAdviceRequest(BaseModel):
    """AI 建议请求模型"""
    user_id: int = Field(..., description="用户ID")
    user_profile: UserProfile
    recent_data: RecentHealthData
    risk_assessment: Optional[Dict] = Field(None, description="风险评估结果（可选）")


class LifestylePlan(BaseModel):
    """生活方式计划模型"""
    diet: str = Field(..., description="饮食建议")
    exercise: str = Field(..., description="运动建议")
    sleep: str = Field(..., description="作息建议")


class AIAdviceResponse(BaseModel):
    """AI 建议响应模型"""
    success: bool
    source: str = Field(..., description="来源: api/mock")
    analysis: str = Field(..., description="健康状况分析")
    recommendations: List[str] = Field(..., description="具体建议列表")
    lifestyle_plan: LifestylePlan
    medical_advice: str = Field(..., description="就医建议")
    generated_at: str


# ==================== 模型训练相关模型 ====================

class TrainModelRequest(BaseModel):
    """模型训练请求"""
    user_id: int = Field(..., description="用户ID")
    metric: str = Field(..., description="健康指标")
    model_type: str = Field("lstm", description="模型类型")
    epochs: int = Field(100, description="训练轮数", ge=10, le=500)
    batch_size: int = Field(32, description="批量大小", ge=8, le=128)
    seq_length: int = Field(14, description="序列长度", ge=7, le=60)


class TrainModelResponse(BaseModel):
    """模型训练响应"""
    success: bool
    model_type: str
    metric: str
    user_id: int
    metrics: ModelMetrics
    message: str


# ==================== 通用响应模型 ====================

class ErrorResponse(BaseModel):
    """错误响应模型"""
    success: bool = False
    error: str
    detail: Optional[str] = None


class HealthCheckResponse(BaseModel):
    """健康检查响应"""
    status: str
    timestamp: str
    version: str
