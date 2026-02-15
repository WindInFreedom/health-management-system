"""
统一模型训练接口

提供统一的模型训练、评估、预测接口
支持 LSTM 和 Transformer 模型

作者: Health Management System Team
日期: 2026-02-15
"""

import pandas as pd
from typing import Dict, Optional, Tuple
import numpy as np


class ModelTrainer:
    """
    统一模型训练器
    
    封装 LSTM 和 Transformer 模型的训练流程
    """
    
    SUPPORTED_MODELS = ['lstm', 'transformer']
    SUPPORTED_METRICS = ['blood_glucose', 'heart_rate', 'systolic', 'diastolic', 'weight_kg']
    
    @staticmethod
    def train_model(df: pd.DataFrame, user_id: int, metric: str, 
                   model_type: str = 'lstm', **kwargs) -> Dict:
        """
        训练模型
        
        Args:
            df: 包含时间序列数据的 DataFrame
            user_id: 用户ID
            metric: 要预测的指标
            model_type: 模型类型 ('lstm' 或 'transformer')
            **kwargs: 其他训练参数
            
        Returns:
            训练结果字典
        """
        if model_type not in ModelTrainer.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型类型: {model_type}. "
                           f"支持的类型: {ModelTrainer.SUPPORTED_MODELS}")
        
        if metric not in ModelTrainer.SUPPORTED_METRICS:
            raise ValueError(f"不支持的指标: {metric}. "
                           f"支持的指标: {ModelTrainer.SUPPORTED_METRICS}")
        
        # 检查数据量
        if len(df) < 100:
            raise ValueError(f"数据量不足: {len(df)}条，至少需要100条数据用于训练")
        
        print(f"\n{'='*60}")
        print(f"开始训练 {model_type.upper()} 模型")
        print(f"用户ID: {user_id}, 指标: {metric}")
        print(f"数据量: {len(df)}条")
        print(f"{'='*60}\n")
        
        # 根据模型类型选择训练器
        if model_type == 'lstm':
            from ml_models.lstm_predictor import LSTMTrainer
            trainer = LSTMTrainer(
                seq_length=kwargs.get('seq_length', 14),
                train_split=kwargs.get('train_split', 0.8),
                val_split=kwargs.get('val_split', 0.1),
                random_seed=kwargs.get('random_seed', 42)
            )
        else:  # transformer
            from ml_models.transformer_predictor import TransformerTrainer
            trainer = TransformerTrainer(
                seq_length=kwargs.get('seq_length', 14),
                train_split=kwargs.get('train_split', 0.8),
                val_split=kwargs.get('val_split', 0.1),
                random_seed=kwargs.get('random_seed', 42)
            )
        
        # 准备数据
        X_train, y_train, X_val, y_val, X_test, y_test = trainer.prepare_data(df, metric)
        
        # 训练模型
        history = trainer.train(
            X_train, y_train, X_val, y_val,
            epochs=kwargs.get('epochs', 100),
            batch_size=kwargs.get('batch_size', 32),
            learning_rate=kwargs.get('learning_rate', 0.001),
            patience=kwargs.get('patience', 15),
            verbose=kwargs.get('verbose', True)
        )
        
        # 评估模型
        metrics = trainer.evaluate(X_test, y_test)
        
        print(f"\n{'='*60}")
        print("训练完成！评估指标:")
        print(f"  MAE:  {metrics['MAE']:.4f}")
        print(f"  RMSE: {metrics['RMSE']:.4f}")
        print(f"  R²:   {metrics['R2']:.4f}")
        print(f"  MAPE: {metrics['MAPE']:.2f}%")
        print(f"{'='*60}\n")
        
        # 保存模型
        trainer.save_model(user_id, metric, metrics, model_dir='models')
        
        return {
            'success': True,
            'model_type': model_type,
            'metric': metric,
            'user_id': user_id,
            'metrics': metrics,
            'history': history,
            'data_info': {
                'total_samples': len(df),
                'train_samples': len(X_train),
                'val_samples': len(X_val),
                'test_samples': len(X_test),
            }
        }
    
    @staticmethod
    def train_all_metrics(df_dict: Dict[str, pd.DataFrame], user_id: int, 
                         model_type: str = 'lstm', **kwargs) -> Dict:
        """
        训练所有指标的模型
        
        Args:
            df_dict: 指标名称 -> DataFrame 的字典
            user_id: 用户ID
            model_type: 模型类型
            **kwargs: 其他训练参数
            
        Returns:
            所有指标的训练结果
        """
        results = {}
        
        for metric, df in df_dict.items():
            if metric not in ModelTrainer.SUPPORTED_METRICS:
                print(f"跳过不支持的指标: {metric}")
                continue
            
            try:
                result = ModelTrainer.train_model(
                    df, user_id, metric, model_type, **kwargs
                )
                results[metric] = result
            except Exception as e:
                print(f"训练 {metric} 失败: {str(e)}")
                results[metric] = {
                    'success': False,
                    'error': str(e)
                }
        
        return results
    
    @staticmethod
    def get_model_comparison(df: pd.DataFrame, user_id: int, metric: str) -> Dict:
        """
        对比 LSTM 和 Transformer 模型性能
        
        Args:
            df: 数据 DataFrame
            user_id: 用户ID
            metric: 指标名称
            
        Returns:
            对比结果字典
        """
        print(f"\n{'='*60}")
        print(f"模型对比: LSTM vs Transformer")
        print(f"用户ID: {user_id}, 指标: {metric}")
        print(f"{'='*60}\n")
        
        results = {}
        
        # 训练 LSTM
        try:
            lstm_result = ModelTrainer.train_model(
                df, user_id, metric, model_type='lstm', verbose=False
            )
            results['lstm'] = lstm_result
        except Exception as e:
            print(f"LSTM 训练失败: {str(e)}")
            results['lstm'] = {'success': False, 'error': str(e)}
        
        # 训练 Transformer
        try:
            transformer_result = ModelTrainer.train_model(
                df, user_id, metric, model_type='transformer', verbose=False
            )
            results['transformer'] = transformer_result
        except Exception as e:
            print(f"Transformer 训练失败: {str(e)}")
            results['transformer'] = {'success': False, 'error': str(e)}
        
        # 对比结果
        if results['lstm']['success'] and results['transformer']['success']:
            lstm_metrics = results['lstm']['metrics']
            transformer_metrics = results['transformer']['metrics']
            
            print(f"\n{'='*60}")
            print("模型对比结果:")
            print(f"{'指标':<10} {'LSTM':<15} {'Transformer':<15} {'更好':<10}")
            print(f"{'-'*60}")
            
            for key in ['MAE', 'RMSE', 'R2', 'MAPE']:
                lstm_val = lstm_metrics[key]
                transformer_val = transformer_metrics[key]
                
                # R² 越大越好，其他指标越小越好
                if key == 'R2':
                    better = 'LSTM' if lstm_val > transformer_val else 'Transformer'
                else:
                    better = 'LSTM' if lstm_val < transformer_val else 'Transformer'
                
                if key == 'MAPE':
                    print(f"{key:<10} {lstm_val:>10.2f}%     {transformer_val:>10.2f}%     {better:<10}")
                else:
                    print(f"{key:<10} {lstm_val:>10.4f}     {transformer_val:>10.4f}     {better:<10}")
            
            print(f"{'='*60}\n")
        
        return results


if __name__ == '__main__':
    print("统一模型训练接口")
    print(f"支持的模型: {ModelTrainer.SUPPORTED_MODELS}")
    print(f"支持的指标: {ModelTrainer.SUPPORTED_METRICS}")
