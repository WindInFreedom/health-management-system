"""
特征提取器

从时间序列健康数据中提取统计、趋势和波动特征
用于风险评估和机器学习模型

作者: Health Management System Team
日期: 2026-02-15
"""

import numpy as np
import pandas as pd
from typing import Dict, List
from scipy import stats
from sklearn.linear_model import LinearRegression


class FeatureExtractor:
    """
    健康数据特征提取器
    
    提取统计特征、趋势特征和波动特征
    """
    
    @staticmethod
    def extract_statistical_features(data: np.ndarray) -> Dict[str, float]:
        """
        提取统计特征
        
        Args:
            data: 时间序列数据 (1D array)
            
        Returns:
            统计特征字典
        """
        if len(data) == 0:
            return {}
        
        features = {
            'mean': float(np.mean(data)),
            'median': float(np.median(data)),
            'std': float(np.std(data)),
            'min': float(np.min(data)),
            'max': float(np.max(data)),
            'range': float(np.max(data) - np.min(data)),
            'q1': float(np.percentile(data, 25)),
            'q2': float(np.percentile(data, 50)),
            'q3': float(np.percentile(data, 75)),
            'iqr': float(np.percentile(data, 75) - np.percentile(data, 25)),
        }
        
        return features
    
    @staticmethod
    def extract_trend_features(data: np.ndarray, window_short: int = 7, 
                               window_long: int = 30) -> Dict[str, float]:
        """
        提取趋势特征
        
        Args:
            data: 时间序列数据
            window_short: 短期窗口大小 (默认7天)
            window_long: 长期窗口大小 (默认30天)
            
        Returns:
            趋势特征字典
        """
        if len(data) == 0:
            return {}
        
        features = {}
        
        # 线性回归斜率 (整体趋势)
        if len(data) > 1:
            X = np.arange(len(data)).reshape(-1, 1)
            y = data.reshape(-1, 1)
            
            try:
                model = LinearRegression()
                model.fit(X, y)
                features['linear_slope'] = float(model.coef_[0][0])
                features['linear_intercept'] = float(model.intercept_[0])
            except:
                features['linear_slope'] = 0.0
                features['linear_intercept'] = float(np.mean(data))
        
        # 移动平均
        if len(data) >= window_short:
            ma_short = np.convolve(data, np.ones(window_short)/window_short, mode='valid')
            features['ma_short'] = float(np.mean(ma_short)) if len(ma_short) > 0 else float(np.mean(data))
            
            # 最近趋势 (最后几个移动平均值的趋势)
            if len(ma_short) > 1:
                recent_slope = (ma_short[-1] - ma_short[0]) / len(ma_short)
                features['recent_trend'] = float(recent_slope)
        else:
            features['ma_short'] = float(np.mean(data))
            features['recent_trend'] = 0.0
        
        if len(data) >= window_long:
            ma_long = np.convolve(data, np.ones(window_long)/window_long, mode='valid')
            features['ma_long'] = float(np.mean(ma_long)) if len(ma_long) > 0 else float(np.mean(data))
        else:
            features['ma_long'] = float(np.mean(data))
        
        # 变化率 (最近 vs 历史)
        if len(data) >= window_long:
            recent_mean = np.mean(data[-window_short:])
            long_term_mean = np.mean(data[-window_long:-window_short]) if len(data) > window_short else np.mean(data)
            
            if long_term_mean != 0:
                features['change_rate'] = float((recent_mean - long_term_mean) / long_term_mean * 100)
            else:
                features['change_rate'] = 0.0
        else:
            features['change_rate'] = 0.0
        
        return features
    
    @staticmethod
    def extract_volatility_features(data: np.ndarray) -> Dict[str, float]:
        """
        提取波动特征
        
        Args:
            data: 时间序列数据
            
        Returns:
            波动特征字典
        """
        if len(data) == 0:
            return {}
        
        features = {}
        
        # 变异系数 (Coefficient of Variation)
        mean = np.mean(data)
        std = np.std(data)
        features['cv'] = float(std / mean * 100) if mean != 0 else 0.0
        
        # 连续上升/下降天数
        if len(data) > 1:
            diffs = np.diff(data)
            
            # 当前连续上升天数
            current_rising = 0
            for i in range(len(diffs)-1, -1, -1):
                if diffs[i] > 0:
                    current_rising += 1
                else:
                    break
            
            # 当前连续下降天数
            current_falling = 0
            for i in range(len(diffs)-1, -1, -1):
                if diffs[i] < 0:
                    current_falling += 1
                else:
                    break
            
            features['consecutive_rising'] = int(current_rising)
            features['consecutive_falling'] = int(current_falling)
            
            # 最大连续上升/下降天数
            max_rising = 0
            max_falling = 0
            current_r = 0
            current_f = 0
            
            for diff in diffs:
                if diff > 0:
                    current_r += 1
                    current_f = 0
                    max_rising = max(max_rising, current_r)
                elif diff < 0:
                    current_f += 1
                    current_r = 0
                    max_falling = max(max_falling, current_f)
                else:
                    current_r = 0
                    current_f = 0
            
            features['max_consecutive_rising'] = int(max_rising)
            features['max_consecutive_falling'] = int(max_falling)
        else:
            features['consecutive_rising'] = 0
            features['consecutive_falling'] = 0
            features['max_consecutive_rising'] = 0
            features['max_consecutive_falling'] = 0
        
        # 异常值频率 (使用 IQR 方法)
        q1 = np.percentile(data, 25)
        q3 = np.percentile(data, 75)
        iqr = q3 - q1
        
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        
        outliers = np.sum((data < lower_bound) | (data > upper_bound))
        features['outlier_frequency'] = float(outliers / len(data) * 100)
        
        # 峰度和偏度
        if len(data) > 3:
            features['skewness'] = float(stats.skew(data))
            features['kurtosis'] = float(stats.kurtosis(data))
        else:
            features['skewness'] = 0.0
            features['kurtosis'] = 0.0
        
        return features
    
    @staticmethod
    def extract_all_features(data: np.ndarray, window_short: int = 7, 
                            window_long: int = 30) -> Dict[str, float]:
        """
        提取所有特征
        
        Args:
            data: 时间序列数据
            window_short: 短期窗口
            window_long: 长期窗口
            
        Returns:
            所有特征字典
        """
        all_features = {}
        
        # 统计特征
        stat_features = FeatureExtractor.extract_statistical_features(data)
        all_features.update({f'stat_{k}': v for k, v in stat_features.items()})
        
        # 趋势特征
        trend_features = FeatureExtractor.extract_trend_features(data, window_short, window_long)
        all_features.update({f'trend_{k}': v for k, v in trend_features.items()})
        
        # 波动特征
        volatility_features = FeatureExtractor.extract_volatility_features(data)
        all_features.update({f'volatility_{k}': v for k, v in volatility_features.items()})
        
        return all_features
    
    @staticmethod
    def extract_multi_metric_features(df: pd.DataFrame, 
                                     metrics: List[str] = None) -> Dict[str, float]:
        """
        从多个指标中提取特征
        
        Args:
            df: 包含多个指标的 DataFrame
            metrics: 指标列表 (默认为所有数值列)
            
        Returns:
            多指标特征字典
        """
        if metrics is None:
            metrics = df.select_dtypes(include=[np.number]).columns.tolist()
        
        all_features = {}
        
        for metric in metrics:
            if metric not in df.columns:
                continue
            
            data = df[metric].dropna().values
            
            if len(data) == 0:
                continue
            
            # 提取该指标的所有特征
            metric_features = FeatureExtractor.extract_all_features(data)
            
            # 添加指标前缀
            for key, value in metric_features.items():
                all_features[f'{metric}_{key}'] = value
        
        return all_features


if __name__ == '__main__':
    # 测试特征提取
    np.random.seed(42)
    test_data = np.random.randn(100) * 5 + 100
    
    print("特征提取器测试")
    print("=" * 60)
    
    # 统计特征
    stat_features = FeatureExtractor.extract_statistical_features(test_data)
    print("\n统计特征:")
    for key, value in stat_features.items():
        print(f"  {key}: {value:.4f}")
    
    # 趋势特征
    trend_features = FeatureExtractor.extract_trend_features(test_data)
    print("\n趋势特征:")
    for key, value in trend_features.items():
        print(f"  {key}: {value:.4f}")
    
    # 波动特征
    volatility_features = FeatureExtractor.extract_volatility_features(test_data)
    print("\n波动特征:")
    for key, value in volatility_features.items():
        print(f"  {key}: {value:.4f}")
    
    print("\n" + "=" * 60)
    print(f"总特征数: {len(stat_features) + len(trend_features) + len(volatility_features)}")
