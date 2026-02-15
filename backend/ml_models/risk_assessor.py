"""
风险评估器

使用随机森林分类器评估健康风险等级
基于时间序列特征提取

风险等级:
- 低风险 (Low Risk): 0
- 中风险 (Medium Risk): 1
- 高风险 (High Risk): 2

作者: Health Management System Team
日期: 2026-02-15
"""

import os
import json
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import joblib

from sklearn.ensemble import RandomForestClassifier
from sklearn.preprocessing import StandardScaler
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix, accuracy_score

from ml_models.feature_extractor import FeatureExtractor


class RiskAssessor:
    """
    健康风险评估器
    
    使用随机森林分类器基于提取的特征评估风险等级
    """
    
    RISK_LEVELS = {
        0: '低风险',
        1: '中风险',
        2: '高风险'
    }
    
    # 健康指标的正常范围和风险阈值
    METRIC_THRESHOLDS = {
        'blood_glucose': {
            'normal_min': 3.9,
            'normal_max': 6.1,
            'high_risk_min': 7.0,  # 空腹血糖 >= 7.0 为糖尿病
            'high_risk_max': 3.0,  # < 3.0 为低血糖
        },
        'heart_rate': {
            'normal_min': 60,
            'normal_max': 100,
            'high_risk_min': 120,  # 心动过速
            'high_risk_max': 50,   # 心动过缓
        },
        'systolic': {
            'normal_min': 90,
            'normal_max': 120,
            'high_risk_min': 140,  # 高血压
            'high_risk_max': 80,   # 低血压
        },
        'diastolic': {
            'normal_min': 60,
            'normal_max': 80,
            'high_risk_min': 90,   # 高血压
            'high_risk_max': 50,   # 低血压
        },
        'weight_kg': {
            'bmi_normal_min': 18.5,
            'bmi_normal_max': 24.0,
            'bmi_high_risk_min': 28.0,  # 肥胖
            'bmi_high_risk_max': 17.0,  # 过轻
        }
    }
    
    def __init__(self, n_estimators: int = 100, max_depth: int = 10, 
                 random_state: int = 42):
        """
        初始化风险评估器
        
        Args:
            n_estimators: 随机森林树的数量
            max_depth: 树的最大深度
            random_state: 随机种子
        """
        self.n_estimators = n_estimators
        self.max_depth = max_depth
        self.random_state = random_state
        
        self.model = RandomForestClassifier(
            n_estimators=n_estimators,
            max_depth=max_depth,
            random_state=random_state,
            class_weight='balanced'  # 处理类别不平衡
        )
        
        self.scaler = StandardScaler()
        self.feature_names = None
        self.is_trained = False
    
    @staticmethod
    def generate_risk_labels(df: pd.DataFrame, metric: str, 
                            user_height_cm: float = 170.0) -> np.ndarray:
        """
        根据医学标准自动生成风险标签
        
        Args:
            df: 数据 DataFrame
            metric: 指标名称
            user_height_cm: 用户身高 (用于计算BMI)
            
        Returns:
            风险标签数组 (0: 低风险, 1: 中风险, 2: 高风险)
        """
        data = df[metric].values
        thresholds = RiskAssessor.METRIC_THRESHOLDS.get(metric)
        
        if thresholds is None:
            # 默认标签 (基于标准差)
            mean = np.mean(data)
            std = np.std(data)
            
            labels = np.zeros(len(data), dtype=int)
            labels[np.abs(data - mean) > 1.5 * std] = 1  # 中风险
            labels[np.abs(data - mean) > 2.5 * std] = 2  # 高风险
            
            return labels
        
        labels = np.zeros(len(data), dtype=int)  # 默认低风险
        
        if metric == 'weight_kg':
            # 特殊处理体重 (需要计算BMI)
            height_m = user_height_cm / 100
            bmi = data / (height_m ** 2)
            
            # 中风险: BMI 异常但不严重
            labels[(bmi < thresholds['bmi_normal_min']) | (bmi > thresholds['bmi_normal_max'])] = 1
            
            # 高风险: BMI 严重异常
            labels[(bmi < thresholds['bmi_high_risk_max']) | (bmi > thresholds['bmi_high_risk_min'])] = 2
        else:
            # 中风险: 超出正常范围
            labels[(data < thresholds['normal_min']) | (data > thresholds['normal_max'])] = 1
            
            # 高风险: 严重异常
            labels[(data < thresholds['high_risk_max']) | (data > thresholds['high_risk_min'])] = 2
        
        return labels
    
    def train(self, X: np.ndarray, y: np.ndarray, feature_names: List[str] = None,
             test_size: float = 0.2, verbose: bool = True) -> Dict:
        """
        训练风险评估模型
        
        Args:
            X: 特征矩阵
            y: 风险标签 (0, 1, 2)
            feature_names: 特征名称列表
            test_size: 测试集比例
            verbose: 是否打印详细信息
            
        Returns:
            训练结果字典
        """
        if verbose:
            print(f"\n{'='*60}")
            print("开始训练风险评估模型")
            print(f"样本数: {len(X)}, 特征数: {X.shape[1]}")
            print(f"{'='*60}\n")
        
        # 划分训练集和测试集
        X_train, X_test, y_train, y_test = train_test_split(
            X, y, test_size=test_size, random_state=self.random_state, stratify=y
        )
        
        # 特征标准化
        X_train_scaled = self.scaler.fit_transform(X_train)
        X_test_scaled = self.scaler.transform(X_test)
        
        # 训练模型
        self.model.fit(X_train_scaled, y_train)
        
        # 评估
        y_pred = self.model.predict(X_test_scaled)
        accuracy = accuracy_score(y_test, y_pred)
        
        if verbose:
            print(f"训练完成！")
            print(f"测试集准确率: {accuracy:.4f}\n")
            print("分类报告:")
            print(classification_report(
                y_test, y_pred, 
                target_names=['低风险', '中风险', '高风险']
            ))
            print("\n混淆矩阵:")
            print(confusion_matrix(y_test, y_pred))
        
        self.feature_names = feature_names
        self.is_trained = True
        
        return {
            'accuracy': float(accuracy),
            'train_samples': len(X_train),
            'test_samples': len(X_test),
        }
    
    def predict(self, X: np.ndarray, return_proba: bool = False) -> Dict:
        """
        预测风险等级
        
        Args:
            X: 特征矩阵 (单个样本或多个样本)
            return_proba: 是否返回概率
            
        Returns:
            预测结果字典
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 确保X是二维数组
        if X.ndim == 1:
            X = X.reshape(1, -1)
        
        # 标准化
        X_scaled = self.scaler.transform(X)
        
        # 预测
        predictions = self.model.predict(X_scaled)
        
        result = {
            'risk_level': int(predictions[0]),
            'risk_label': self.RISK_LEVELS[int(predictions[0])],
        }
        
        if return_proba:
            probabilities = self.model.predict_proba(X_scaled)[0]
            result['probabilities'] = {
                '低风险': float(probabilities[0]),
                '中风险': float(probabilities[1]),
                '高风险': float(probabilities[2]),
            }
            result['risk_score'] = float(probabilities[2])  # 高风险概率作为风险分数
        
        return result
    
    def get_feature_importance(self, top_n: int = 10) -> List[Tuple[str, float]]:
        """
        获取特征重要性排序
        
        Args:
            top_n: 返回前N个重要特征
            
        Returns:
            [(特征名, 重要性), ...] 列表
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        importances = self.model.feature_importances_
        
        if self.feature_names is not None:
            feature_importance = list(zip(self.feature_names, importances))
        else:
            feature_importance = [(f'feature_{i}', imp) for i, imp in enumerate(importances)]
        
        # 按重要性排序
        feature_importance.sort(key=lambda x: x[1], reverse=True)
        
        return feature_importance[:top_n]
    
    def analyze_risk_factors(self, X: np.ndarray, top_n: int = 5) -> Dict:
        """
        分析风险因素
        
        Args:
            X: 特征向量
            top_n: 返回前N个风险因素
            
        Returns:
            风险因素分析字典
        """
        prediction_result = self.predict(X, return_proba=True)
        
        # 获取特征重要性
        importance_list = self.get_feature_importance(top_n)
        
        # 提取关键风险因素
        key_factors = []
        for feature_name, importance in importance_list:
            # 简化特征名称并添加描述
            factor_desc = RiskAssessor._interpret_feature(feature_name)
            
            key_factors.append({
                'factor': feature_name,
                'importance': float(importance),
                'description': factor_desc
            })
        
        return {
            'risk_level': prediction_result['risk_label'],
            'risk_score': prediction_result['risk_score'],
            'probabilities': prediction_result['probabilities'],
            'key_factors': key_factors,
        }
    
    @staticmethod
    def _interpret_feature(feature_name: str) -> str:
        """
        解释特征名称
        
        Args:
            feature_name: 特征名称
            
        Returns:
            特征描述
        """
        interpretations = {
            'stat_mean': '平均值',
            'stat_std': '标准差（波动性）',
            'stat_max': '最大值',
            'stat_min': '最小值',
            'trend_linear_slope': '长期趋势',
            'trend_recent_trend': '近期趋势',
            'trend_change_rate': '变化率',
            'volatility_cv': '变异系数',
            'volatility_consecutive_rising': '连续上升天数',
            'volatility_consecutive_falling': '连续下降天数',
            'volatility_outlier_frequency': '异常值频率',
        }
        
        # 尝试匹配
        for key, desc in interpretations.items():
            if key in feature_name:
                # 提取指标名称
                metric = feature_name.split('_')[0] if '_' in feature_name else ''
                
                metric_names = {
                    'blood': '血糖',
                    'glucose': '血糖',
                    'heart': '心率',
                    'systolic': '收缩压',
                    'diastolic': '舒张压',
                    'weight': '体重',
                }
                
                metric_desc = ''
                for m_key, m_name in metric_names.items():
                    if m_key in metric.lower():
                        metric_desc = m_name
                        break
                
                if metric_desc:
                    return f'{metric_desc}{desc}'
                else:
                    return desc
        
        return feature_name
    
    def save_model(self, model_path: str, config_path: str = None):
        """
        保存模型
        
        Args:
            model_path: 模型文件路径
            config_path: 配置文件路径（可选）
        """
        if not self.is_trained:
            raise ValueError("模型尚未训练")
        
        # 保存模型
        joblib.dump({
            'model': self.model,
            'scaler': self.scaler,
            'feature_names': self.feature_names,
        }, model_path)
        
        print(f"模型已保存: {model_path}")
        
        # 保存配置
        if config_path:
            config = {
                'n_estimators': self.n_estimators,
                'max_depth': self.max_depth,
                'random_state': self.random_state,
                'feature_names': self.feature_names,
                'trained_at': datetime.now().isoformat(),
            }
            
            with open(config_path, 'w') as f:
                json.dump(config, f, indent=2)
            
            print(f"配置已保存: {config_path}")
    
    @classmethod
    def load_model(cls, model_path: str):
        """
        加载模型
        
        Args:
            model_path: 模型文件路径
            
        Returns:
            RiskAssessor 实例
        """
        if not os.path.exists(model_path):
            raise ValueError(f"模型文件不存在: {model_path}")
        
        data = joblib.load(model_path)
        
        assessor = cls()
        assessor.model = data['model']
        assessor.scaler = data['scaler']
        assessor.feature_names = data['feature_names']
        assessor.is_trained = True
        
        return assessor


if __name__ == '__main__':
    print("风险评估器测试")
    print("=" * 60)
    
    # 生成测试数据
    np.random.seed(42)
    n_samples = 300
    
    # 模拟特征
    X = np.random.randn(n_samples, 20)
    
    # 生成标签 (基于简单规则)
    y = np.zeros(n_samples, dtype=int)
    y[X[:, 0] > 1] = 1  # 中风险
    y[X[:, 0] > 2] = 2  # 高风险
    
    # 训练模型
    assessor = RiskAssessor()
    result = assessor.train(X, y, verbose=True)
    
    # 测试预测
    test_sample = X[0].reshape(1, -1)
    prediction = assessor.predict(test_sample, return_proba=True)
    
    print(f"\n{'='*60}")
    print("预测结果:")
    print(f"风险等级: {prediction['risk_label']}")
    print(f"风险分数: {prediction['risk_score']:.4f}")
    print(f"概率分布: {prediction['probabilities']}")
    
    # 特征重要性
    print(f"\n{'='*60}")
    print("特征重要性 (Top 5):")
    importance = assessor.get_feature_importance(top_n=5)
    for i, (feature, imp) in enumerate(importance, 1):
        print(f"{i}. {feature}: {imp:.4f}")
