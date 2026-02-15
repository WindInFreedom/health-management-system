import os
import json
import numpy as np
import torch
import torch.nn as nn
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.http import JsonResponse
import joblib
import warnings
import pandas as pd
from sklearn.preprocessing import MinMaxScaler
warnings.filterwarnings('ignore')


class GRUModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=1, output_size=1, bidirectional=False, dropout=0.2):
        super(GRUModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        self.gru = nn.GRU(input_size, hidden_size, num_layers, batch_first=True, bidirectional=bidirectional)
        
        fc_input_size = hidden_size * 2 if bidirectional else hidden_size
        self.fc = nn.Linear(fc_input_size, output_size)
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        batch_size = x.size(0)
        num_directions = 2 if self.bidirectional else 1
        h0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        out, _ = self.gru(x, h0)
        out = self.dropout(out[:, -1, :])
        out = self.fc(out)
        return out


def add_time_features(df):
    df = df.copy()
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['day'] = df.index.day
    df['dayofweek'] = df.index.dayofweek
    return df


def add_moving_avg_features(df, window=7):
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in ['year', 'month', 'day', 'dayofweek']:
            df[f'{col}_ma{window}'] = df[col].rolling(window=window).mean()
            df[f'{col}_ema'] = df[col].ewm(span=window).mean()
    return df


def add_lag_features(df, lag_days=[1, 7, 14]):
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in ['year', 'month', 'day', 'dayofweek'] and not col.endswith('_ma7') and not col.endswith('_ema'):
            for lag in lag_days:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df


def preprocess_data(df, feature_config):
    df = df.copy()
    
    if feature_config.get('use_time_features', False):
        df = add_time_features(df)
    
    if feature_config.get('use_moving_avg', False):
        df = add_moving_avg_features(df, feature_config.get('moving_avg_window', 7))
    
    if feature_config.get('use_lag_features', False):
        df = add_lag_features(df, feature_config.get('lag_days', [1, 7, 14]))
    
    df = df.dropna()
    return df


def clean_data(df):
    df = df.copy()
    
    for col in df.select_dtypes(include=[np.number]).columns:
        Q1 = df[col].quantile(0.25)
        Q3 = df[col].quantile(0.75)
        IQR = Q3 - Q1
        lower_bound = Q1 - 1.5 * IQR
        upper_bound = Q3 + 1.5 * IQR
        
        df[col] = df[col].clip(lower=lower_bound, upper=upper_bound)
    
    df = df.dropna()
    return df


def load_model(user_id, metric, model_dir='models'):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    model_file = os.path.join(model_dir, f'gru_model_user{user_id}_{metric}.pth')
    scaler_file = os.path.join(model_dir, f'scaler_user{user_id}_{metric}.pkl')
    original_scaler_file = os.path.join(model_dir, f'original_scaler_user{user_id}_{metric}.pkl')
    metrics_file = os.path.join(model_dir, f'metrics_gru_user{user_id}_{metric}.json')
    config_file = os.path.join(model_dir, f'config_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file):
        return None, None, None, None, None
    
    checkpoint = torch.load(model_file, map_location=device)
    
    bidirectional = checkpoint.get('bidirectional', False)
    dropout = checkpoint.get('dropout', 0.2)
    
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
    
    original_scaler = None
    if os.path.exists(original_scaler_file):
        original_scaler = joblib.load(original_scaler_file)
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    feature_config = None
    if os.path.exists(config_file):
        with open(config_file, 'r') as f:
            config_data = json.load(f)
            feature_config = config_data.get('feature_config')
    
    return model, scaler, metrics, original_scaler, feature_config


def predict_future(model, scaler, last_data, days=7, input_size=1, seq_length=14, 
                   df_processed=None, feature_config=None, metric_name=None, original_scaler=None):
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model.eval()
    
    predictions = []
    
    if df_processed is not None and feature_config is not None and metric_name is not None:
        for i in range(days):
            x = torch.FloatTensor(last_data[-seq_length:])
            
            if x.ndim == 1:
                x = x.unsqueeze(0).unsqueeze(-1)
            elif x.ndim == 2:
                x = x.unsqueeze(0)
            
            if x.shape[-1] != input_size:
                x = x[:, :, :input_size]
            
            y = model(x).detach().cpu().numpy()[0][0]
            predictions.append(y)
            
            if input_size == 1:
                last_data = np.append(last_data[1:], y)
            else:
                new_row = last_data[-1].copy()
                new_row[0] = y
                last_data = np.vstack([last_data[1:], new_row])
    else:
        for i in range(days):
            x = torch.FloatTensor(last_data[-seq_length:])
            
            if x.ndim == 1:
                x = x.unsqueeze(0).unsqueeze(-1)
            elif x.ndim == 2:
                x = x.unsqueeze(0)
            
            if x.shape[-1] != input_size:
                x = x[:, :, :input_size]
            
            y = model(x).detach().cpu().numpy()[0][0]
            predictions.append(y)
            
            if input_size == 1:
                last_data = np.append(last_data[1:], y)
            else:
                new_row = last_data[-1].copy()
                new_row[0] = y
                last_data = np.vstack([last_data[1:], new_row])
    
    predictions = np.array(predictions).reshape(-1, 1)
    
    if original_scaler is not None:
        predictions = predictions * original_scaler.scale_[0] + original_scaler.min_[0]
    else:
        predictions = predictions * scaler.scale_[0] + scaler.min_[0]
    
    return predictions.flatten()


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_gru_model(request):
    from measurements.models import Measurement, SleepLog, MoodLog
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metrics = request.data.get('metrics', ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose'])
    
    results = {}
    
    for metric in metrics:
        if metric in ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']:
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            data = list(measurements.values('measured_at', metric))
            
            if not data:
                results[metric] = {'error': '没有足够的测量数据用于训练'}
                continue
            
            import pandas as pd
            df = pd.DataFrame(data)
            df['measured_at'] = pd.to_datetime(df['measured_at'])
            df = df.sort_values('measured_at')
            df = df.set_index('measured_at')
            
            df_metric = df[[metric]].dropna()
            
            if len(df_metric) < 8:
                results[metric] = {'error': '数据不足，至少需要 8 条记录'}
                continue
            
            results[metric] = train_single_metric(df_metric, metric, user.id)
            
        elif metric == 'sleep_duration':
            sleep_logs = SleepLog.objects.filter(user=user).order_by('sleep_date')
            data = list(sleep_logs.values('sleep_date', 'duration_minutes'))
            
            if not data:
                results[metric] = {'error': '没有足够的睡眠数据用于训练'}
                continue
            
            import pandas as pd
            df = pd.DataFrame(data)
            df['sleep_date'] = pd.to_datetime(df['sleep_date'])
            df = df.sort_values('sleep_date')
            df = df.set_index('sleep_date')
            df['sleep_duration'] = df['duration_minutes'] / 60
            df_metric = df[['sleep_duration']].dropna()
            
            if len(df_metric) < 8:
                results[metric] = {'error': '数据不足，至少需要 8 条记录'}
                continue
            
            results[metric] = train_single_metric(df_metric, metric, user.id)
            
        elif metric == 'sleep_quality':
            sleep_logs = SleepLog.objects.filter(user=user).order_by('sleep_date')
            data = list(sleep_logs.values('sleep_date', 'quality_rating'))
            
            if not data:
                results[metric] = {'error': '没有足够的睡眠质量数据用于训练'}
                continue
            
            import pandas as pd
            df = pd.DataFrame(data)
            df['sleep_date'] = pd.to_datetime(df['sleep_date'])
            df = df.sort_values('sleep_date')
            df = df.set_index('sleep_date')
            df_metric = df[['quality_rating']].dropna()
            
            if len(df_metric) < 8:
                results[metric] = {'error': '数据不足，至少需要 8 条记录'}
                continue
            
            results[metric] = train_single_metric(df_metric, metric, user.id)
            
        elif metric == 'mood_rating':
            mood_logs = MoodLog.objects.filter(user=user).order_by('log_date')
            data = list(mood_logs.values('log_date', 'mood_rating'))
            
            if not data:
                results[metric] = {'error': '没有足够的心情数据用于训练'}
                continue
            
            import pandas as pd
            df = pd.DataFrame(data)
            df['log_date'] = pd.to_datetime(df['log_date'])
            df = df.sort_values('log_date')
            df = df.set_index('log_date')
            df_metric = df[['mood_rating']].dropna()
            
            if len(df_metric) < 8:
                results[metric] = {'error': '数据不足，至少需要 8 条记录'}
                continue
            
            results[metric] = train_single_metric(df_metric, metric, user.id)
    
    return Response({
        'message': '模型训练完成',
        'results': results
    })


def train_single_metric(df_metric, metric, user_id):
    from torch.utils.data import Dataset, DataLoader
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    
    class HealthDataset(Dataset):
        def __init__(self, data, seq_length=7):
            self.data = data
            self.seq_length = seq_length

        def __len__(self):
            return len(self.data) - self.seq_length

        def __getitem__(self, idx):
            x = self.data[idx:idx + self.seq_length]
            y = self.data[idx + self.seq_length, 0]
            return torch.FloatTensor(x), torch.FloatTensor([y])
    
    seq_length = 14
    train_size = int(len(df_metric) * 0.8)
    
    feature_config = {
        'use_time_features': False,
        'use_moving_avg': False,
        'moving_avg_window': 7,
        'use_lag_features': True,
        'lag_days': [1, 7, 14]
    }
    
    df_cleaned = clean_data(df_metric)
    df_processed = preprocess_data(df_cleaned, feature_config)
    
    original_scaler = MinMaxScaler()
    original_scaled = original_scaler.fit_transform(df_metric.values)
    
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df_processed.values)
    
    dataset = HealthDataset(scaled_data, seq_length)
    dataloader = DataLoader(dataset, batch_size=16, shuffle=False)
    
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    model = GRUModel(input_size=scaled_data.shape[1], hidden_size=128, num_layers=2, bidirectional=True, dropout=0.3).to(device)
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=0.0005)
    
    model.train()
    for epoch in range(100):
        total_loss = 0
        for batch_x, batch_y in dataloader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
    
    train_data = scaled_data[:train_size]
    test_data = scaled_data[train_size:]
    
    model.eval()
    predictions = []
    actuals = []
    
    with torch.no_grad():
        for i in range(len(test_data) - seq_length):
            x = torch.FloatTensor(test_data[i:i+seq_length]).unsqueeze(0).to(device)
            y = model(x).cpu().numpy()[0][0]
            predictions.append(y)
            actuals.append(test_data[i+seq_length, 0])
    
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    predictions = predictions * original_scaler.scale_[0] + original_scaler.min_[0]
    actuals = actuals * original_scaler.scale_[0] + original_scaler.min_[0]
    
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)
    mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
    
    metrics = {
        'MAE': float(mae),
        'RMSE': float(rmse),
        'R2': float(r2),
        'MAPE': float(mape)
    }
    
    os.makedirs('models', exist_ok=True)
    model_file = os.path.join('models', f'gru_model_user{user_id}_{metric}.pth')
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': scaled_data.shape[1],
        'hidden_size': model.hidden_size,
        'num_layers': model.num_layers,
        'output_size': 1,
        'bidirectional': model.bidirectional,
        'dropout': 0.3
    }, model_file)
    
    scaler_file = os.path.join('models', f'scaler_user{user_id}_{metric}.pkl')
    joblib.dump(scaler, scaler_file)
    
    original_scaler_file = os.path.join('models', f'original_scaler_user{user_id}_{metric}.pkl')
    joblib.dump(original_scaler, original_scaler_file)
    
    metrics_file = os.path.join('models', f'metrics_user{user_id}_{metric}.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    last_data = scaled_data[-7:]
    future_predictions = predict_future(model, scaler, last_data, days=7, input_size=scaled_data.shape[1])
    
    return {
        'metrics': metrics,
        'predictions': future_predictions.tolist()
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_model_metrics(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metric = request.GET.get('metric')
    
    if not metric:
        return Response({'error': '请指定指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    model, scaler, metrics, original_scaler, feature_config = load_model(user.id, metric)
    
    if model is None:
        return Response({'error': '模型不存在，请先训练模型'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'metric': metric,
        'metrics': metrics
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_with_model(request):
    from django.contrib.auth import get_user_model
    from measurements.models import SleepLog, MoodLog
    User = get_user_model()
    
    user = request.user
    metric = request.data.get('metric')
    days = request.data.get('days', 7)
    
    if not metric:
        return Response({'error': '请指定指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    feature_config = {
        'use_time_features': False,
        'use_moving_avg': False,
        'moving_avg_window': 7,
        'use_lag_features': True,
        'lag_days': [1, 7, 14]
    }
    
    import pandas as pd
    
    if metric in ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']:
        from measurements.models import Measurement
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        data = list(measurements.values('measured_at', metric))
        
        if len(data) < 7:
            return Response({'error': '数据不足，至少需要7条记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        df = df.set_index('measured_at')
        df_metric = df[[metric]].dropna()
        
        if len(df_metric) < 7:
            return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
        
    elif metric == 'sleep_duration':
        sleep_logs = SleepLog.objects.filter(user=user).order_by('sleep_date')
        data = list(sleep_logs.values('sleep_date', 'duration_minutes'))
        
        if len(data) < 7:
            return Response({'error': '数据不足，至少需要7条记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        df = pd.DataFrame(data)
        df['sleep_date'] = pd.to_datetime(df['sleep_date'])
        df = df.sort_values('sleep_date')
        df = df.set_index('sleep_date')
        df['sleep_duration'] = df['duration_minutes'] / 60
        df_metric = df[['sleep_duration']].dropna()
        
        if len(df_metric) < 7:
            return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
        
    elif metric == 'sleep_quality':
        sleep_logs = SleepLog.objects.filter(user=user).order_by('sleep_date')
        data = list(sleep_logs.values('sleep_date', 'quality_rating'))
        
        if len(data) < 7:
            return Response({'error': '数据不足，至少需要7条记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        df = pd.DataFrame(data)
        df['sleep_date'] = pd.to_datetime(df['sleep_date'])
        df = df.sort_values('sleep_date')
        df = df.set_index('sleep_date')
        df_metric = df[['quality_rating']].dropna()
        
        if len(df_metric) < 7:
            return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
        
    elif metric == 'mood_rating':
        mood_logs = MoodLog.objects.filter(user=user).order_by('log_date')
        data = list(mood_logs.values('log_date', 'mood_rating'))
        
        if len(data) < 7:
            return Response({'error': '数据不足，至少需要7条记录'}, status=status.HTTP_400_BAD_REQUEST)
        
        df = pd.DataFrame(data)
        df['log_date'] = pd.to_datetime(df['log_date'])
        df = df.sort_values('log_date')
        df = df.set_index('log_date')
        df_metric = df[['mood_rating']].dropna()
        
        if len(df_metric) < 7:
            return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
    
    model, scaler, metrics, original_scaler, feature_config = load_model(user.id, metric)
    
    if model is None:
        return Response({'error': '模型不存在，请先训练模型'}, status=status.HTTP_404_NOT_FOUND)
    
    checkpoint = torch.load(os.path.join('models', f'gru_model_user{user.id}_{metric}.pth'), map_location='cpu')
    input_size = checkpoint.get('input_size', 1)
    
    df_cleaned = clean_data(df_metric)
    
    if input_size == 1:
        df_processed = df_cleaned
    else:
        df_processed = preprocess_data(df_cleaned, feature_config)
    
    last_data = scaler.transform(df_processed.values)
    
    predictions = predict_future(model, scaler, last_data, days=days, input_size=input_size, seq_length=14, original_scaler=original_scaler)
    
    return Response({
        'metric': metric,
        'days': days,
        'predictions': predictions.tolist(),
        'metrics': metrics
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def predict_all_metrics(request):
    from django.contrib.auth import get_user_model
    from datetime import timedelta
    User = get_user_model()
    
    user = request.user
    days = int(request.GET.get('days', 7))
    
    metrics_to_predict = ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']
    predictions = {}
    
    for metric in metrics_to_predict:
        model, scaler, metrics, original_scaler, feature_config = load_model(user.id, metric)
        
        if model is None:
            continue
        
        config_file = os.path.join('models', f'config_user{user.id}_{metric}.json')
        seq_length = 14
        if os.path.exists(config_file):
            with open(config_file, 'r') as f:
                config_data = json.load(f)
                seq_length = config_data.get('training_config', {}).get('seq_length', 14)
        
        from measurements.models import Measurement
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        data = list(measurements.values('measured_at', metric))
        
        if len(data) < 7:
            continue
        
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        df = df.set_index('measured_at')
        df_metric = df[[metric]].dropna()
        
        if len(df_metric) < 7:
            continue
        
        checkpoint = torch.load(os.path.join('models', f'gru_model_user{user.id}_{metric}.pth'), map_location='cpu')
        input_size = checkpoint.get('input_size', 1)
        
        df_cleaned = clean_data(df_metric)
        
        if input_size == 1:
            df_processed = df_cleaned
        else:
            df_processed = preprocess_data(df_cleaned, feature_config)
        
        last_data = scaler.transform(df_processed.values)
        pred_values = predict_future(model, scaler, last_data, days=days, input_size=input_size, seq_length=seq_length, original_scaler=original_scaler)
        
        current_value = float(df_metric.iloc[-1].values[0])
        
        if metric == 'weight_kg':
            predictions['weight'] = {
                'current': current_value,
                'predicted': [round(v, 1) for v in pred_values],
                'trend': 'increasing' if pred_values[-1] > current_value else 'decreasing'
            }
        elif metric == 'systolic':
            if 'blood_pressure' not in predictions:
                predictions['blood_pressure'] = {
                    'current': {'systolic': int(current_value)},
                    'predicted': {'systolic': [int(round(v)) for v in pred_values]},
                    'trend': 'increasing' if pred_values[-1] > current_value else 'stable'
                }
            else:
                predictions['blood_pressure']['current']['systolic'] = int(current_value)
                predictions['blood_pressure']['predicted']['systolic'] = [int(round(v)) for v in pred_values]
        elif metric == 'diastolic':
            if 'blood_pressure' not in predictions:
                predictions['blood_pressure'] = {
                    'current': {'diastolic': int(current_value)},
                    'predicted': {'diastolic': [int(round(v)) for v in pred_values]},
                    'trend': 'increasing' if pred_values[-1] > current_value else 'stable'
                }
            else:
                predictions['blood_pressure']['current']['diastolic'] = int(current_value)
                predictions['blood_pressure']['predicted']['diastolic'] = [int(round(v)) for v in pred_values]
        elif metric == 'heart_rate':
            predictions['heart_rate'] = {
                'current': int(current_value),
                'predicted': [int(round(v)) for v in pred_values],
                'trend': 'increasing' if pred_values[-1] > current_value else 'stable'
            }
        elif metric == 'blood_glucose':
            predictions['blood_glucose'] = {
                'current': current_value,
                'predicted': [round(v, 1) for v in pred_values],
                'trend': 'increasing' if pred_values[-1] > current_value else 'stable'
            }
    
    if predictions:
        last_measurement = Measurement.objects.filter(user=user).order_by('-measured_at').first()
        if last_measurement:
            last_date = last_measurement.measured_at
            prediction_dates = [(last_date + timedelta(days=i)).strftime('%Y-%m-%d') for i in range(1, days + 1)]
            predictions['dates'] = prediction_dates
    
    return Response(predictions)
