"""
模型加载工具

提供统一的模型加载和预测接口

作者: Health Management System Team
日期: 2026-02-15
"""

import os
import json
import pandas as pd
from typing import Dict, Optional, Tuple, List
from datetime import datetime, timedelta


class ModelLoader:
    """
    模型加载器
    
    提供统一的模型加载和预测接口
    """
    
    SUPPORTED_MODELS = ['lstm', 'transformer']
    SUPPORTED_METRICS = ['blood_glucose', 'heart_rate', 'systolic', 'diastolic', 'weight_kg']
    
    @staticmethod
    def load_model(user_id: int, metric: str, model_type: str = 'lstm', 
                  model_dir: str = 'models'):
        """
        加载已训练的模型
        
        Args:
            user_id: 用户ID
            metric: 指标名称
            model_type: 模型类型
            model_dir: 模型目录
            
        Returns:
            (trainer, metrics) 或 (None, None)
        """
        if model_type not in ModelLoader.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型类型: {model_type}")
        
        if model_type == 'lstm':
            from ml_models.lstm_predictor import LSTMTrainer
            return LSTMTrainer.load_model(user_id, metric, model_dir)
        else:  # transformer
            from ml_models.transformer_predictor import TransformerTrainer
            return TransformerTrainer.load_model(user_id, metric, model_dir)
    
    @staticmethod
    def predict(df: pd.DataFrame, user_id: int, metric: str, days: int = 7,
               model_type: str = 'lstm', confidence_level: float = 0.95,
               model_dir: str = 'models') -> Dict:
        """
        使用已训练的模型进行预测
        
        Args:
            df: 历史数据 DataFrame
            user_id: 用户ID
            metric: 指标名称
            days: 预测天数
            model_type: 模型类型
            confidence_level: 置信水平
            model_dir: 模型目录
            
        Returns:
            预测结果字典
        """
        # 加载模型
        trainer, metrics = ModelLoader.load_model(user_id, metric, model_type, model_dir)
        
        if trainer is None:
            raise ValueError(f"找不到模型: user{user_id}_{metric}_{model_type}")
        
        # 预测未来值
        prediction_result = trainer.predict_future(df, metric, days, confidence_level)
        
        # 生成未来日期
        last_date = df.index[-1] if isinstance(df.index, pd.DatetimeIndex) else df['measured_at'].max()
        future_dates = [last_date + timedelta(days=i+1) for i in range(days)]
        
        # 构建回测数据（用于展示模型在历史数据上的表现）
        historical_backtest = ModelLoader._generate_backtest(trainer, df, metric)
        
        return {
            'success': True,
            'model_type': model_type,
            'metric': metric,
            'user_id': user_id,
            'predictions': prediction_result['predictions'],
            'confidence_interval': prediction_result['confidence_interval'],
            'future_dates': [d.strftime('%Y-%m-%d') for d in future_dates],
            'historical_backtest': historical_backtest,
            'metrics': metrics,
            'last_update': datetime.now().isoformat(),
        }
    
    @staticmethod
    def _generate_backtest(trainer, df: pd.DataFrame, metric: str, 
                          n_points: int = 50) -> Dict:
        """
        生成历史回测数据
        
        Args:
            trainer: 训练好的模型
            df: 历史数据
            metric: 指标名称
            n_points: 回测点数
            
        Returns:
            回测数据字典
        """
        import torch
        import numpy as np
        
        # 取最后 n_points 个数据点进行回测
        data = df[[metric]].values[-n_points*2:]  # 多取一些以确保有足够数据
        data = pd.DataFrame(data).fillna(method='ffill').fillna(method='bfill').values
        
        if len(data) < trainer.seq_length + n_points:
            n_points = len(data) - trainer.seq_length
        
        data_scaled = trainer.scaler_X.transform(data)
        
        actual_values = []
        predicted_values = []
        
        trainer.model.eval()
        
        for i in range(n_points):
            # 取序列
            seq = data_scaled[i:i+trainer.seq_length]
            actual = data[i+trainer.seq_length][0]
            
            # 预测
            input_tensor = torch.FloatTensor(seq).unsqueeze(0).to(trainer.device)
            with torch.no_grad():
                pred_scaled = trainer.model(input_tensor).cpu().numpy()[0]
            
            pred = trainer.scaler_y.inverse_transform(pred_scaled.reshape(-1, 1))[0][0]
            
            actual_values.append(float(actual))
            predicted_values.append(float(pred))
        
        return {
            'actual': actual_values,
            'predicted': predicted_values,
        }
    
    @staticmethod
    def get_available_models(user_id: int, model_dir: str = 'models') -> Dict[str, List[str]]:
        """
        获取用户可用的所有模型
        
        Args:
            user_id: 用户ID
            model_dir: 模型目录
            
        Returns:
            {model_type: [metric1, metric2, ...]}
        """
        available = {'lstm': [], 'transformer': []}
        
        if not os.path.exists(model_dir):
            return available
        
        for model_type in ModelLoader.SUPPORTED_MODELS:
            for metric in ModelLoader.SUPPORTED_METRICS:
                if model_type == 'lstm':
                    model_file = f'lstm_user{user_id}_{metric}.pth'
                else:
                    model_file = f'transformer_user{user_id}_{metric}.pth'
                
                model_path = os.path.join(model_dir, model_file)
                if os.path.exists(model_path):
                    available[model_type].append(metric)
        
        return available
    
    @staticmethod
    def get_model_info(user_id: int, metric: str, model_type: str = 'lstm',
                      model_dir: str = 'models') -> Optional[Dict]:
        """
        获取模型信息
        
        Args:
            user_id: 用户ID
            metric: 指标名称
            model_type: 模型类型
            model_dir: 模型目录
            
        Returns:
            模型信息字典 或 None
        """
        config_file = f'config_{model_type}_user{user_id}_{metric}.json'
        config_path = os.path.join(model_dir, config_file)
        
        if not os.path.exists(config_path):
            return None
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        return {
            'user_id': user_id,
            'metric': metric,
            'model_type': model_type,
            'trained_at': config.get('trained_at'),
            'metrics': config.get('metrics'),
            'seq_length': config.get('seq_length'),
        }
    
    @staticmethod
    def compare_models(df: pd.DataFrame, user_id: int, metric: str, 
                      days: int = 7, model_dir: str = 'models') -> Dict:
        """
        对比两种模型的预测结果
        
        Args:
            df: 历史数据
            user_id: 用户ID
            metric: 指标名称
            days: 预测天数
            model_dir: 模型目录
            
        Returns:
            对比结果字典
        """
        results = {}
        
        for model_type in ['lstm', 'transformer']:
            try:
                result = ModelLoader.predict(
                    df, user_id, metric, days, model_type, model_dir=model_dir
                )
                results[model_type] = result
            except Exception as e:
                print(f"{model_type.upper()} 预测失败: {str(e)}")
                results[model_type] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results


if __name__ == '__main__':
    print("模型加载工具")
    print(f"支持的模型: {ModelLoader.SUPPORTED_MODELS}")
    print(f"支持的指标: {ModelLoader.SUPPORTED_METRICS}")
