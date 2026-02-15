"""
预测 API 路由

提供健康指标预测服务

作者: Health Management System Team
日期: 2026-02-15
"""

from fastapi import APIRouter, HTTPException
import sys
import os
import pandas as pd

# 添加路径
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# 设置 Django 环境
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
import django
django.setup()

from api.models.schemas import (
    PredictionRequest, PredictionResponse,
    TrainModelRequest, TrainModelResponse,
    ErrorResponse
)
from ml_models.model_loader import ModelLoader
from ml_models.model_trainer import ModelTrainer
from measurements.models import Measurement
from django.contrib.auth import get_user_model

User = get_user_model()

router = APIRouter()


@router.post("/predict", response_model=PredictionResponse)
async def predict_health_metric(request: PredictionRequest):
    """
    预测健康指标
    
    Args:
        request: 预测请求
        
    Returns:
        预测结果（包含置信区间和历史回测）
    """
    try:
        # 验证用户
        try:
            user = User.objects.get(id=request.user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail=f"用户 {request.user_id} 不存在")
        
        # 获取历史数据
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        
        if measurements.count() < 100:
            raise HTTPException(
                status_code=400, 
                detail=f"数据不足：仅有 {measurements.count()} 条记录，至少需要 100 条"
            )
        
        # 转换为 DataFrame
        data = list(measurements.values('measured_at', request.metric))
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        df = df.set_index('measured_at')
        
        # 使用模型预测
        result = ModelLoader.predict(
            df=df,
            user_id=request.user_id,
            metric=request.metric,
            days=request.days,
            model_type=request.model_type,
            confidence_level=request.confidence_level
        )
        
        if not result.get('success'):
            raise HTTPException(status_code=404, detail="模型不存在，请先训练模型")
        
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"预测失败: {str(e)}")


@router.post("/train", response_model=TrainModelResponse)
async def train_model(request: TrainModelRequest):
    """
    训练预测模型
    
    Args:
        request: 训练请求
        
    Returns:
        训练结果
    """
    try:
        # 验证用户
        try:
            user = User.objects.get(id=request.user_id)
        except User.DoesNotExist:
            raise HTTPException(status_code=404, detail=f"用户 {request.user_id} 不存在")
        
        # 获取历史数据
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        
        if measurements.count() < 100:
            raise HTTPException(
                status_code=400,
                detail=f"数据不足：仅有 {measurements.count()} 条记录，至少需要 100 条"
            )
        
        # 转换为 DataFrame
        data = list(measurements.values('measured_at', request.metric))
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        df = df.set_index('measured_at')
        
        # 训练模型
        result = ModelTrainer.train_model(
            df=df,
            user_id=request.user_id,
            metric=request.metric,
            model_type=request.model_type,
            epochs=request.epochs,
            batch_size=request.batch_size,
            seq_length=request.seq_length,
            verbose=False  # API 模式不打印详细信息
        )
        
        return {
            "success": result['success'],
            "model_type": result['model_type'],
            "metric": result['metric'],
            "user_id": result['user_id'],
            "metrics": result['metrics'],
            "message": f"模型训练成功！MAE: {result['metrics']['MAE']:.4f}, R²: {result['metrics']['R2']:.4f}"
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"训练失败: {str(e)}")


@router.get("/models/{user_id}")
async def list_available_models(user_id: int):
    """
    列出用户可用的模型
    
    Args:
        user_id: 用户ID
        
    Returns:
        可用模型列表
    """
    try:
        available_models = ModelLoader.get_available_models(user_id)
        
        return {
            "success": True,
            "user_id": user_id,
            "models": available_models
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型列表失败: {str(e)}")


@router.get("/model-info/{user_id}/{metric}")
async def get_model_info(user_id: int, metric: str, model_type: str = "lstm"):
    """
    获取模型详细信息
    
    Args:
        user_id: 用户ID
        metric: 指标名称
        model_type: 模型类型
        
    Returns:
        模型信息
    """
    try:
        model_info = ModelLoader.get_model_info(user_id, metric, model_type)
        
        if model_info is None:
            raise HTTPException(
                status_code=404, 
                detail=f"模型不存在: user{user_id}_{metric}_{model_type}"
            )
        
        return {
            "success": True,
            **model_info
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"获取模型信息失败: {str(e)}")
