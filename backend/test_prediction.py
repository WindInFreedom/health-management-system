import os
import sys
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')
django.setup()

import pandas as pd
import numpy as np
import torch
import joblib
from measurements.models import Measurement
from users.models import SleepLog, MoodLog
from django.contrib.auth import get_user_model

User = get_user_model()

def load_model(user_id, metric, model_dir='models'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model_file = os.path.join(model_dir, f'gru_model_user{user_id}_{metric}.pth')
    scaler_file = os.path.join(model_dir, f'scaler_user{user_id}_{metric}.pkl')
    metrics_file = os.path.join(model_dir, f'metrics_gru_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file):
        return None, None, None
    
    checkpoint = torch.load(model_file, map_location=device)
    
    bidirectional = checkpoint.get('bidirectional', False)
    dropout = checkpoint.get('dropout', 0.2)
    
    from measurements.gru_model_views import GRUModel
    model = GRUModel(
        checkpoint['input_size'],
        checkpoint['hidden_size'],
        checkpoint['num_layers'],
        checkpoint['output_size'],
        bidirectional=bidirectional,
        dropout=dropout
    ).to(device)
    model.load_state_dict(checkpoint['model_state_dict'])
    model.eval()
    
    scaler = joblib.load(scaler_file)
    
    import json
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return model, scaler, metrics

def test_prediction():
    user = User.objects.get(id=1)
    metric = 'heart_rate'
    
    measurements = Measurement.objects.filter(user=user).order_by('measured_at')
    data = list(measurements.values('measured_at', metric))
    
    df = pd.DataFrame(data)
    df['measured_at'] = pd.to_datetime(df['measured_at'])
    df = df.sort_values('measured_at')
    df = df.set_index('measured_at')
    df_metric = df[[metric]].dropna()
    
    print(f'原始数据量: {len(df_metric)} 条记录')
    print(f'原始数据范围: {df_metric[metric].min():.2f} - {df_metric[metric].max():.2f}')
    print(f'原始数据均值: {df_metric[metric].mean():.2f}')
    print(f'原始数据标准差: {df_metric[metric].std():.2f}')
    print()
    
    model, scaler, metrics = load_model(user.id, metric)
    
    if model is None:
        print('模型不存在')
        return
    
    print(f'模型指标: {metrics}')
    print()
    
    checkpoint = torch.load(os.path.join('models', f'gru_model_user{user.id}_{metric}.pth'), map_location='cpu')
    input_size = checkpoint.get('input_size', 1)
    print(f'模型输入大小: {input_size}')
    print()
    
    from measurements.gru_model_views import clean_data, preprocess_data
    
    feature_config = {
        'use_time_features': True,
        'use_moving_avg': True,
        'moving_avg_window': 7,
        'use_lag_features': True,
        'lag_days': [1, 7, 14]
    }
    
    df_cleaned = clean_data(df_metric)
    print(f'清洗后数据量: {len(df_cleaned)} 条记录')
    
    df_processed = preprocess_data(df_cleaned, feature_config)
    print(f'处理后数据量: {len(df_processed)} 条记录')
    print(f'处理后特征数量: {df_processed.shape[1]}')
    print(f'处理后特征列: {df_processed.columns.tolist()}')
    print()
    
    last_data = scaler.transform(df_processed.values)
    print(f'归一化后数据形状: {last_data.shape}')
    print(f'归一化后数据范围: {last_data.min():.4f} - {last_data.max():.4f}')
    print(f'归一化后数据均值: {last_data.mean():.4f}')
    print(f'归一化后数据标准差: {last_data.std():.4f}')
    print()
    
    print(f'scaler.scale_: {scaler.scale_}')
    print(f'scaler.min_: {scaler.min_}')
    print()
    
    from measurements.gru_model_views import predict_future
    
    predictions = predict_future(model, scaler, last_data, days=7, input_size=input_size, seq_length=14)
    print(f'预测值: {predictions}')
    print(f'预测值范围: {predictions.min():.2f} - {predictions.max():.2f}')
    print(f'预测值均值: {predictions.mean():.2f}')
    print(f'预测值标准差: {predictions.std():.2f}')
    print()
    
    print('对比:')
    print(f'原始数据最后7天: {df_metric[metric].tail(7).values}')
    print(f'预测值: {predictions}')

if __name__ == '__main__':
    test_prediction()