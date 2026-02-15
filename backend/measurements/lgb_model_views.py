import os
import json
import numpy as np
import pandas as pd
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import warnings
warnings.filterwarnings('ignore')

try:
    import lightgbm as lgb
except ImportError:
    lgb = None

try:
    import xgboost as xgb
except ImportError:
    xgb = None

try:
    import torch
    import torch.nn as nn
    torch_device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
except (ImportError, OSError):
    torch = None
    torch_device = None

try:
    import joblib
except ImportError:
    joblib = None

try:
    import tensorflow as tf
    from tensorflow import keras
    from tensorflow.keras.models import load_model
    TF_AVAILABLE = True
except (ImportError, OSError):
    TF_AVAILABLE = False
    tf = None
    keras = None
    load_model = None

# ==================== 数据清洗与验证 ====================

def clean_and_validate_data(df, metric):
    df = df.copy()
    
    for col in df.columns:
        if col == metric:
            df[col] = pd.to_numeric(df[col], errors='coerce')
    
    # 基础范围过滤
    if metric == 'systolic':
        df = df[(df[metric] >= 80) & (df[metric] <= 200)]
    elif metric == 'diastolic':
        df = df[(df[metric] >= 50) & (df[metric] <= 120)]
    elif metric == 'heart_rate':
        df = df[(df[metric] >= 40) & (df[metric] <= 180)]
    elif metric == 'weight_kg':
        df = df[(df[metric] >= 30) & (df[metric] <= 200)]
    elif metric == 'blood_glucose':
        df = df[(df[metric] >= 3) & (df[metric] <= 20)]
    
    # 单日变化异常检测
    if len(df) > 1:
        df = df.sort_index()
        df['daily_change'] = df[metric].diff().abs()
        
        # 体重单日变化超过±5kg视为异常
        if metric == 'weight_kg':
            df = df[df['daily_change'] <= 5]
        # 血糖单日变化超过±10视为异常
        elif metric == 'blood_glucose':
            df = df[df['daily_change'] <= 10]
        # 血压单日变化超过±30视为异常
        elif metric in ['systolic', 'diastolic']:
            df = df[df['daily_change'] <= 30]
        # 心率单日变化超过±40视为异常
        elif metric == 'heart_rate':
            df = df[df['daily_change'] <= 40]
        
        df = df.drop(columns=['daily_change'])
    
    df = df.asfreq('D')
    df[metric] = df[metric].ffill().bfill()
    df = df.dropna()
    
    return df

# ==================== 特征工程函数 ====================

def add_time_features(df):
    df = df.copy()
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['day'] = df.index.day
    df['dayofweek'] = df.index.dayofweek
    df['dayofyear'] = df.index.dayofyear
    df['weekofyear'] = df.index.isocalendar().week
    
    # 周期性特征（使用sin/cos编码）
    df['dayofweek_sin'] = np.sin(2 * np.pi * df['dayofweek'] / 7)
    df['dayofweek_cos'] = np.cos(2 * np.pi * df['dayofweek'] / 7)
    df['month_sin'] = np.sin(2 * np.pi * df['month'] / 12)
    df['month_cos'] = np.cos(2 * np.pi * df['month'] / 12)
    df['dayofyear_sin'] = np.sin(2 * np.pi * df['dayofyear'] / 365)
    df['dayofyear_cos'] = np.cos(2 * np.pi * df['dayofyear'] / 365)
    
    # 是否周末
    df['is_weekend'] = (df['dayofweek'] >= 5).astype(int)
    
    # 是否月初/月中/月末
    df['is_month_start'] = (df['day'] <= 10).astype(int)
    df['is_month_mid'] = ((df['day'] > 10) & (df['day'] <= 20)).astype(int)
    df['is_month_end'] = (df['day'] > 20).astype(int)
    
    return df

def add_moving_avg_features(df, window=7):
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        skip_cols = ['year', 'month', 'day', 'dayofweek', 'dayofyear', 'weekofyear', 
                    'dayofweek_sin', 'dayofweek_cos', 'month_sin', 'month_cos',
                    'dayofyear_sin', 'dayofyear_cos', 'is_weekend', 'is_month_start', 
                    'is_month_mid', 'is_month_end']
        skip_suffixes = ['_ma', '_ema', '_lag', '_diff', '_std', '_min', '_max', '_median']
        if col not in skip_cols and not any(col.endswith(suffix) for suffix in skip_suffixes):
            # 多种滚动窗口
            for w in [3, 7, 14, 30]:
                df[f'{col}_ma{w}'] = df[col].rolling(window=w).mean()
                df[f'{col}_std{w}'] = df[col].rolling(window=w).std()
                df[f'{col}_min{w}'] = df[col].rolling(window=w).min()
                df[f'{col}_max{w}'] = df[col].rolling(window=w).max()
                df[f'{col}_median{w}'] = df[col].rolling(window=w).median()
            
            # 指数移动平均
            df[f'{col}_ema'] = df[col].ewm(span=window).mean()
    return df

def add_lag_features(df, lag_days=[1, 2, 3, 4, 5, 6, 7]):
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        skip_cols = ['year', 'month', 'day', 'dayofweek', 'dayofyear', 'weekofyear', 
                    'dayofweek_sin', 'dayofweek_cos', 'month_sin', 'month_cos',
                    'dayofyear_sin', 'dayofyear_cos', 'is_weekend', 'is_month_start', 
                    'is_month_mid', 'is_month_end']
        skip_suffixes = ['_ma', '_ema', '_lag', '_diff', '_std', '_min', '_max', '_median']
        if col not in skip_cols and not any(col.endswith(suffix) for suffix in skip_suffixes):
            for lag in lag_days:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df

def add_diff_features(df, target_col=None):
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        skip_cols = ['year', 'month', 'day', 'dayofweek', 'dayofyear', 'weekofyear', 
                    'dayofweek_sin', 'dayofweek_cos', 'month_sin', 'month_cos',
                    'dayofyear_sin', 'dayofyear_cos', 'is_weekend', 'is_month_start', 
                    'is_month_mid', 'is_month_end']
        skip_suffixes = ['_ma', '_ema', '_lag', '_diff', '_std', '_min', '_max', '_median']
        if col not in skip_cols and not any(col.endswith(suffix) for suffix in skip_suffixes):
            # 一阶差分
            df[f'{col}_diff'] = df[col].diff()
            # 二阶差分
            df[f'{col}_diff2'] = df[col].diff(2)
            # 百分比变化
            df[f'{col}_pct_change'] = df[col].pct_change()
    return df

def preprocess_data(df, feature_config, target_col):
    df = df.copy()
    
    if feature_config['use_time_features']:
        df = add_time_features(df)
    
    if feature_config['use_moving_avg']:
        df = add_moving_avg_features(df, feature_config['moving_avg_window'])
    
    if feature_config['use_lag_features']:
        df = add_lag_features(df, feature_config['lag_days'])
    
    if feature_config['use_diff_features']:
        df = add_diff_features(df, target_col)
    
    df = df.dropna()
    return df

# ==================== 加载模型 ====================

def load_lgb_model(user_id, metric, model_dir='models'):
    model_file = os.path.join(model_dir, f'lgb_model_user{user_id}_{metric}.txt')
    metrics_file = os.path.join(model_dir, f'metrics_lgb_user{user_id}_{metric}.json')
    config_file = os.path.join(model_dir, f'config_lgb_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file):
        return None, None, None, None
    
    model = lgb.Booster(model_file=model_file)
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
        feature_config = config_data.get('feature_config')
        feature_cols = config_data.get('feature_cols')
    
    return model, metrics, feature_config, feature_cols

def load_xgb_model(user_id, metric, model_dir='models'):
    model_file = os.path.join(model_dir, f'xgb_model_user{user_id}_{metric}.json')
    metrics_file = os.path.join(model_dir, f'metrics_xgb_user{user_id}_{metric}.json')
    config_file = os.path.join(model_dir, f'config_xgb_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file):
        return None, None, None, None
    
    model = xgb.Booster()
    model.load_model(model_file)
    
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    with open(config_file, 'r') as f:
        config_data = json.load(f)
        feature_config = config_data.get('feature_config')
        feature_cols = config_data.get('feature_cols')
    
    return model, metrics, feature_config, feature_cols

# ==================== 预测函数 ====================

def predict_future_lgb(model, df_original, metric, feature_config, feature_cols, days=7):
    predictions = []
    df = df_original.copy()
    
    for i in range(days):
        df_processed = preprocess_data(df, feature_config, metric)
        
        if len(df_processed) < 1:
            break
        
        last_row = df_processed.iloc[-1:][feature_cols]
        pred = model.predict(last_row)[0]
        predictions.append(pred)
        
        new_date = df.index[-1] + pd.Timedelta(days=1)
        new_row = pd.DataFrame({metric: [pred]}, index=[new_date])
        df = pd.concat([df, new_row])
    
    return np.array(predictions)

def smooth_predictions(predictions, window=3):
    smoothed = []
    for i in range(len(predictions)):
        start = max(0, i - window + 1)
        end = min(len(predictions), i + window)
        smoothed.append(np.mean(predictions[start:end]))
    return np.array(smoothed)

# ==================== TensorFlow LSTM 模型支持 ====================

def create_sequences(data, seq_length=7):
    X, y = [], []
    for i in range(len(data) - seq_length):
        X.append(data[i:i + seq_length])
        y.append(data[i + seq_length])
    return np.array(X), np.array(y)

def build_lstm_model(input_shape, units=50, dropout_rate=0.2):
    from tensorflow.keras.models import Sequential
    from tensorflow.keras.layers import LSTM, Dense, Dropout
    from tensorflow import keras
    
    model = Sequential([
        LSTM(units=units, return_sequences=True, input_shape=input_shape),
        Dropout(dropout_rate),
        LSTM(units=units, return_sequences=False),
        Dropout(dropout_rate),
        Dense(units=1)
    ])
    
    model.compile(
        optimizer=keras.optimizers.Adam(learning_rate=0.001),
        loss='mse',
        metrics=['mae']
    )
    
    return model

def train_lstm_model(user_id, metric, seq_length=7, epochs=100, batch_size=16):
    if not TF_AVAILABLE:
        return None, {'error': 'TensorFlow not available'}
    
    if joblib is None:
        return None, {'error': 'joblib not available'}
    
    from measurements.models import Measurement
    from sklearn.preprocessing import MinMaxScaler
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau
    
    measurements = Measurement.objects.filter(user_id=user_id).order_by('measured_at')
    data = list(measurements.values('measured_at', metric))
    
    print(f"LSTM训练 - 用户ID: {user_id}, 指标: {metric}, 数据量: {len(data)}")
    
    if len(data) < 50:
        return None, {'error': '数据不足，至少需要50条数据'}
    
    df = pd.DataFrame(data)
    df['measured_at'] = pd.to_datetime(df['measured_at'])
    df = df.sort_values('measured_at')
    df = df.set_index('measured_at')
    
    df[metric] = df[metric].astype(float)
    df_clean = df[[metric]].dropna()
    
    print(f"LSTM训练 - 清洗后数据量: {len(df_clean)}")
    
    if len(df_clean) < 50:
        return None, {'error': '有效数据不足，至少需要50条数据'}
    
    values = df_clean[metric].values.reshape(-1, 1)
    
    scaler = MinMaxScaler(feature_range=(0, 1))
    scaled_values = scaler.fit_transform(values)
    
    X, y = create_sequences(scaled_values, seq_length)
    
    print(f"LSTM训练 - 序列数据量: {len(X)}, X形状: {X.shape}, y形状: {y.shape}")
    
    if len(X) < 30:
        return None, {'error': '序列数据不足'}
    
    train_size = int(len(X) * 0.8)
    val_size = int(len(X) * 0.1)
    
    print(f"LSTM训练 - 训练集: {train_size}, 验证集: {val_size}, 测试集: {len(X) - train_size - val_size}")
    
    X_train = X[:train_size]
    y_train = y[:train_size]
    X_val = X[train_size:train_size + val_size]
    y_val = y[train_size:train_size + val_size]
    X_test = X[train_size + val_size:]
    y_test = y[train_size + val_size:]
    
    input_shape = (X_train.shape[1], X_train.shape[2])
    
    print(f"LSTM训练 - 输入形状: {input_shape}")
    
    model = build_lstm_model(input_shape, units=50, dropout_rate=0.2)
    
    early_stopping = EarlyStopping(
        monitor='val_loss',
        patience=10,
        restore_best_weights=True
    )
    
    reduce_lr = ReduceLROnPlateau(
        monitor='val_loss',
        factor=0.5,
        patience=5,
        min_lr=0.00001
    )
    
    history = model.fit(
        X_train, y_train,
        epochs=epochs,
        batch_size=batch_size,
        validation_data=(X_val, y_val),
        callbacks=[early_stopping, reduce_lr],
        verbose=0
    )
    
    print(f"LSTM训练 - 训练完成，实际训练轮数: {len(history.history['loss'])}")
    
    y_pred_test = model.predict(X_test, verbose=0)
    y_pred_test_rescaled = scaler.inverse_transform(y_pred_test)
    y_test_rescaled = scaler.inverse_transform(y_test)
    
    print(f"LSTM训练 - 测试集预测完成，预测形状: {y_pred_test.shape}")
    
    mae = mean_absolute_error(y_test_rescaled, y_pred_test_rescaled)
    rmse = np.sqrt(mean_squared_error(y_test_rescaled, y_pred_test_rescaled))
    r2 = r2_score(y_test_rescaled, y_pred_test_rescaled)
    mape = np.mean(np.abs((y_test_rescaled - y_pred_test_rescaled) / y_test_rescaled)) * 100
    
    print(f"LSTM训练 - MAE: {mae:.4f}, RMSE: {rmse:.4f}, R2: {r2:.4f}, MAPE: {mape:.2f}%")
    
    metrics = {
        'mae': float(mae),
        'rmse': float(rmse),
        'r2': float(r2),
        'mape': float(mape)
    }
    
    os.makedirs('models', exist_ok=True)
    
    model_file = os.path.join('models', f'lstm_model_user{user_id}_{metric}.keras')
    model.save(model_file)
    
    scaler_file = os.path.join('models', f'scaler_lstm_user{user_id}_{metric}.pkl')
    joblib.dump(scaler, scaler_file)
    
    config_file = os.path.join('models', f'config_lstm_user{user_id}_{metric}.json')
    with open(config_file, 'w') as f:
        json.dump({
            'model_type': 'lstm',
            'seq_length': seq_length,
            'units': 50,
            'dropout_rate': 0.2,
            'epochs': epochs,
            'batch_size': batch_size
        }, f, indent=2)
    
    metrics_file = os.path.join('models', f'metrics_lstm_user{user_id}_{metric}.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return model, metrics

def predict_lstm(user_id, metric, df_cleaned, days=7):
    if not TF_AVAILABLE:
        return None, None, None, None
    
    if joblib is None:
        return None, None, None, None
    
    model_file = os.path.join('models', f'lstm_model_user{user_id}_{metric}.keras')
    scaler_file = os.path.join('models', f'scaler_lstm_user{user_id}_{metric}.pkl')
    config_file = os.path.join('models', f'config_lstm_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file):
        return None, None, None, None
    
    model = load_model(model_file)
    scaler = joblib.load(scaler_file)
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    seq_length = config['seq_length']
    
    values = df_cleaned[metric].values.reshape(-1, 1)
    scaled_values = scaler.transform(values)
    
    last_sequence = scaled_values[-seq_length:].reshape(1, seq_length, 1)
    
    predictions = []
    lower_bounds = []
    upper_bounds = []
    
    for i in range(days):
        pred_scaled = model.predict(last_sequence, verbose=0)
        pred = scaler.inverse_transform(pred_scaled)[0][0]
        predictions.append(pred)
        
        # 计算置信区间，随预测时间变远而逐渐增宽
        # 基于预测步数的不确定性增加
        uncertainty_factor = 1 + (i * 0.1)  # 每步增加10%的不确定性
        
        # 使用最近预测值的标准差作为基础
        if len(predictions) >= 3:
            std = np.std(predictions[-3:]) * uncertainty_factor
        else:
            # 使用历史数据的标准差
            std = np.std(values) * uncertainty_factor
        
        # 95%置信区间
        lower_bounds.append(pred - 1.96 * std)
        upper_bounds.append(pred + 1.96 * std)
        
        last_sequence = np.roll(last_sequence, -1, axis=1)
        last_sequence[0, -1, 0] = pred_scaled[0][0]
    
    metrics_file = os.path.join('models', f'metrics_lstm_user{user_id}_{metric}.json')
    if os.path.exists(metrics_file):
        with open(metrics_file, 'r') as f:
            metrics = json.load(f)
    else:
        metrics = None
    
    return np.array(predictions), metrics, np.array(lower_bounds), np.array(upper_bounds)

# ==================== PyTorch 模型支持 ====================

if torch is not None:
    class LSTMModel(nn.Module):
        def __init__(self, input_size=1, hidden_size=64, num_layers=2, dropout=0.2):
            super(LSTMModel, self).__init__()
            self.hidden_size = hidden_size
            self.num_layers = num_layers
            
            self.lstm = nn.LSTM(
                input_size=input_size,
                hidden_size=hidden_size,
                num_layers=num_layers,
                batch_first=True,
                dropout=dropout
            )
            self.fc = nn.Linear(hidden_size, 1)
            
        def forward(self, x):
            lstm_out, _ = self.lstm(x)
            lstm_out = lstm_out[:, -1, :]
            output = self.fc(lstm_out)
            return output

    class TCNModel(nn.Module):
        def __init__(self, input_size=1, num_channels=[64, 64, 64, 64], kernel_size=3, dropout=0.2):
            super(TCNModel, self).__init__()
            
            layers = []
            num_levels = len(num_channels)
            for i in range(num_levels):
                dilation_size = 2 ** i
                in_channels = input_size if i == 0 else num_channels[i-1]
                out_channels = num_channels[i]
                
                padding = (kernel_size - 1) * dilation_size // 2
                
                layers += [
                    nn.Conv1d(
                        in_channels=in_channels,
                        out_channels=out_channels,
                        kernel_size=kernel_size,
                        padding=padding,
                        dilation=dilation_size
                    ),
                    nn.ReLU(),
                    nn.Dropout(dropout)
                ]
            
            self.network = nn.Sequential(*layers)
            self.fc = nn.Linear(num_channels[-1], 1)
            
        def forward(self, x):
            x = x.transpose(1, 2)
            x = self.network(x)
            x = x[:, :, -1]
            output = self.fc(x)
            return output
else:
    LSTMModel = None
    TCNModel = None

def load_pytorch_model(user_id, metric):
    if torch is None:
        return None, None, None
    
    model_dir = 'models'
    model_file = os.path.join(model_dir, f'pytorch_model_user{user_id}_{metric}.pth')
    config_file = os.path.join(model_dir, f'config_pytorch_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file) or not os.path.exists(config_file):
        return None, None, None
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    model_type = config['model_type']
    sequence_length = config['sequence_length']
    
    if model_type == 'lstm':
        model = LSTMModel(input_size=1, hidden_size=64, num_layers=2, dropout=0.3)
    elif model_type == 'tcn':
        model = TCNModel(input_size=1, num_channels=[64, 64, 64, 64], kernel_size=3, dropout=0.3)
    else:
        return None, None, None
    
    model.load_state_dict(torch.load(model_file, map_location=torch_device))
    model.to(torch_device)
    model.eval()
    
    scaler_mean = config['scaler_mean']
    scaler_scale = config['scaler_scale']
    
    return model, sequence_length, (scaler_mean, scaler_scale)

def predict_pytorch(user_id, metric, df_cleaned, days=7):
    model, sequence_length, scaler_params = load_pytorch_model(user_id, metric)
    
    if model is None:
        return None, None
    
    data_values = df_cleaned[metric].values.reshape(-1, 1)
    
    scaler_mean, scaler_scale = scaler_params
    data_scaled = (data_values - scaler_mean) / scaler_scale
    
    model.eval()
    predictions = []
    
    current_sequence = data_scaled[-sequence_length:].copy()
    
    for _ in range(days):
        sequence_tensor = torch.FloatTensor(current_sequence[-sequence_length:]).unsqueeze(0).to(torch_device)
        with torch.no_grad():
            pred = model(sequence_tensor)
        
        predictions.append(pred.item())
        current_sequence = np.append(current_sequence[1:], pred)
    
    predictions = np.array(predictions)
    predictions = predictions * scaler_scale + scaler_mean
    
    metrics_file = os.path.join('models', f'metrics_pytorch_user{user_id}_{metric}.json')
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return predictions, metrics

def load_advanced_model(user_id, metric):
    if joblib is None:
        return None, None, None
    
    model_dir = 'models'
    model_file = os.path.join(model_dir, f'advanced_model_user{user_id}_{metric}.pkl')
    config_file = os.path.join(model_dir, f'config_advanced_user{user_id}_{metric}.json')
    
    if not os.path.exists(model_file) or not os.path.exists(config_file):
        return None, None, None
    
    with open(config_file, 'r') as f:
        config = json.load(f)
    
    model_type = config['model_type']
    
    model = joblib.load(model_file)
    
    return model, model_type, config

def predict_advanced(user_id, metric, df_cleaned, days=7, confidence_level=0.95):
    model, model_type, config = load_advanced_model(user_id, metric)
    
    if model is None:
        return None, None, None, None
    
    df_lag = add_lag_features(df_cleaned, lag_days=[1, 2, 3, 4, 5, 6, 7])
    df_lag = add_diff_features(df_lag)
    df_lag = df_lag.dropna()
    
    if len(df_lag) < 1:
        return None, None, None, None
    
    feature_cols = [col for col in df_lag.columns if col != metric]
    
    # 使用Bootstrap方法计算置信区间
    n_bootstrap = 100
    bootstrap_predictions = []
    
    for b in range(n_bootstrap):
        predictions = []
        for i in range(days):
            # Bootstrap采样
            sample_idx = np.random.choice(len(df_lag), size=len(df_lag), replace=True)
            df_sample = df_lag.iloc[sample_idx].copy()
            # 保存原始索引
            original_index = df_sample.index.copy()
            # 重置索引以避免重复标签
            df_sample = df_sample.reset_index(drop=True)
            
            last_row = df_sample.iloc[-1:][feature_cols]
            
            if last_row.isnull().any().any():
                predictions.append(np.nan)
                continue
            
            if model_type == 'svr':
                from sklearn.preprocessing import MinMaxScaler
                scaler = MinMaxScaler()
                last_row_scaled = scaler.fit_transform(last_row)
                pred = model.predict(last_row_scaled)[0]
            else:
                pred = model.predict(last_row)[0]
            
            predictions.append(pred)
            
            # 使用原始索引的最后一个时间戳
            last_timestamp = original_index[-1]
            new_date = last_timestamp + pd.Timedelta(days=1)
            new_row = pd.DataFrame({metric: [pred]}, index=[new_date])
            df_sample = pd.concat([df_sample, new_row])
            # 更新原始索引
            original_index = df_sample.index.copy()
            
            last_idx = len(df_sample) - 1
            prev_idx = len(df_sample) - 2
            
            for lag in [1, 2, 3, 4, 5, 6, 7]:
                lag_col = f'{metric}_lag{lag}'
                if lag == 1:
                    df_sample.loc[last_idx, lag_col] = df_sample.loc[prev_idx, metric]
                else:
                    prev_lag_idx = last_idx - lag
                    df_sample.loc[last_idx, lag_col] = df_sample.loc[prev_lag_idx, lag_col]
            
            diff_col = f'{metric}_diff'
            df_sample.loc[last_idx, diff_col] = df_sample.loc[last_idx, metric] - df_sample.loc[prev_idx, metric]
        
        bootstrap_predictions.append(predictions)
    
    bootstrap_predictions = np.array(bootstrap_predictions)
    
    # 计算置信区间
    alpha = 1 - confidence_level
    lower_percentile = (alpha / 2) * 100
    upper_percentile = (1 - alpha / 2) * 100
    
    predictions = np.median(bootstrap_predictions, axis=0)
    lower_bound = np.percentile(bootstrap_predictions, lower_percentile, axis=0)
    upper_bound = np.percentile(bootstrap_predictions, upper_percentile, axis=0)
    
    metrics_file = os.path.join('models', f'metrics_advanced_user{user_id}_{metric}.json')
    with open(metrics_file, 'r') as f:
        metrics = json.load(f)
    
    return predictions, metrics, lower_bound, upper_bound

def predict_future_ensemble(df_cleaned, metric, feature_config, feature_cols, lgb_model=None, xgb_model=None, days=7, lgb_weight=0.6, xgb_weight=0.4):
    predictions = []
    df = df_cleaned.copy()
    
    for i in range(days):
        df_processed = preprocess_data(df, feature_config, metric)
        
        if len(df_processed) < 1:
            break
        
        last_row = df_processed.iloc[-1:][feature_cols]
        
        pred = 0
        if lgb_model is not None:
            pred += lgb_model.predict(last_row)[0] * lgb_weight
        if xgb_model is not None:
            dtest = xgb.DMatrix(last_row)
            pred += xgb_model.predict(dtest)[0] * xgb_weight
        
        predictions.append(pred)
        
        new_date = df.index[-1] + pd.Timedelta(days=1)
        new_row = pd.DataFrame({metric: [pred]}, index=[new_date])
        df = pd.concat([df, new_row])
    
    predictions = np.array(predictions)
    
    predictions = smooth_predictions(predictions)
    
    return predictions

# ==================== API端点 ====================

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_model_metrics(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metric = request.GET.get('metric')
    
    if not metric:
        return Response({'error': '请指定指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    model, metrics, feature_config, feature_cols = load_lgb_model(user.id, metric)
    
    if model is None:
        return Response({'error': '模型不存在，请先训练模型'}, status=status.HTTP_404_NOT_FOUND)
    
    return Response({
        'metric': metric,
        'metrics': metrics
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_lgb_model(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metrics_to_train = request.data.get('metrics', [])
    
    if not metrics_to_train:
        return Response({'error': '请指定要训练的指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    results = {}
    
    for metric in metrics_to_train:
        try:
            from measurements.models import Measurement
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            data = list(measurements.values('measured_at', metric))
            
            if not data:
                results[metric] = {'error': '没有数据'}
                continue
            
            df = pd.DataFrame(data)
            df['measured_at'] = pd.to_datetime(df['measured_at'])
            df = df.sort_values('measured_at')
            df = df.set_index('measured_at')
            
            df[metric] = df[metric].astype(float)
            df_metric = df[[metric]].dropna()
            
            if len(df_metric) < 20:
                results[metric] = {'error': '数据不足'}
                continue
            
            df_cleaned = clean_and_validate_data(df_metric, metric)
            df_processed = preprocess_data(df_cleaned, {
                'use_time_features': False,
                'use_moving_avg': False,
                'use_lag_features': True,
                'use_diff_features': True,
                'moving_avg_window': 7,
                'lag_days': [1, 2, 3, 4, 5, 6, 7]
            })
            
            target_col = metric
            feature_cols = [col for col in df_processed.columns if col != target_col]
            
            X = df_processed[feature_cols]
            y = df_processed[target_col]
            
            train_size = int(len(X) * 0.8)
            val_size = int(len(X) * 0.1)
            
            X_train = X[:train_size]
            y_train = y[:train_size]
            X_val = X[train_size:train_size + val_size]
            y_val = y[train_size:train_size + val_size]
            X_test = X[train_size + val_size:]
            y_test = y[train_size + val_size:]
            
            train_data = lgb.Dataset(X_train, label=y_train)
            val_data = lgb.Dataset(X_val, label=y_val, reference=train_data)
            
            params = {
                'objective': 'regression',
                'metric': 'rmse',
                'boosting_type': 'gbdt',
                'num_leaves': 31,
                'learning_rate': 0.05,
                'feature_fraction': 0.9,
                'bagging_fraction': 0.8,
                'bagging_freq': 5,
                'verbose': -1
            }
            
            model = lgb.train(
                params,
                train_data,
                valid_sets=[train_data, val_data],
                num_boost_round=1000,
                callbacks=[lgb.early_stopping(stopping_rounds=50), lgb.log_evaluation(period=100)]
            )
            
            y_pred = model.predict(X_test, num_iteration=model.best_iteration)
            
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            mae = mean_absolute_error(y_test, y_pred)
            rmse = np.sqrt(mean_squared_error(y_test, y_pred))
            r2 = r2_score(y_test, y_pred)
            mape = np.mean(np.abs((y_test - y_pred) / y_test)) * 100
            
            metrics = {
                'MAE': float(mae),
                'RMSE': float(rmse),
                'R2': float(r2),
                'MAPE': float(mape)
            }
            
            os.makedirs('models', exist_ok=True)
            
            model_file = os.path.join('models', f'lgb_model_user{user.id}_{metric}.txt')
            model.save_model(model_file)
            
            metrics_file = os.path.join('models', f'metrics_lgb_user{user.id}_{metric}.json')
            with open(metrics_file, 'w') as f:
                json.dump(metrics, f, indent=2)
            
            config_file = os.path.join('models', f'config_lgb_user{user.id}_{metric}.json')
            with open(config_file, 'w') as f:
                json.dump({
                    'feature_config': {
                        'use_time_features': False,
                        'use_moving_avg': False,
                        'use_lag_features': True,
                        'use_diff_features': True,
                        'moving_avg_window': 7,
                        'lag_days': [1, 2, 3, 4, 5, 6, 7]
                    },
                    'feature_cols': feature_cols
                }, f, indent=2)
            
            results[metric] = metrics
            
        except Exception as e:
            results[metric] = {'error': str(e)}
    
    return Response(results)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_pytorch_model(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metrics_to_train = request.data.get('metrics', [])
    
    if not metrics_to_train:
        return Response({'error': '请指定要训练的指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    if torch is None:
        return Response({'error': 'PyTorch未安装'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    results = {}
    
    for metric in metrics_to_train:
        try:
            from measurements.models import Measurement
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            data = list(measurements.values('measured_at', metric))
            
            if not data:
                results[metric] = {'error': '没有数据'}
                continue
            
            df = pd.DataFrame(data)
            df['measured_at'] = pd.to_datetime(df['measured_at'])
            df = df.sort_values('measured_at')
            df = df.set_index('measured_at')
            
            df[metric] = df[metric].astype(float)
            df_metric = df[[metric]].dropna()
            
            if len(df_metric) < 50:
                results[metric] = {'error': '数据不足，至少需要50条数据'}
                continue
            
            df_cleaned = clean_and_validate_data(df_metric, metric)
            
            data_values = df_cleaned[metric].values.reshape(-1, 1)
            
            from sklearn.preprocessing import MinMaxScaler
            scaler = MinMaxScaler()
            data_scaled = scaler.fit_transform(data_values)
            
            sequence_length = 30
            train_size = int(len(data_scaled) * 0.8)
            val_size = int(len(data_scaled) * 0.1)
            
            train_data = data_scaled[:train_size]
            val_data = data_scaled[train_size:train_size + val_size]
            test_data = data_scaled[train_size + val_size:]
            
            class TimeSeriesDataset(torch.utils.data.Dataset):
                def __init__(self, data, sequence_length=30):
                    self.data = data
                    self.sequence_length = sequence_length
                    
                def __len__(self):
                    return len(self.data) - self.sequence_length
                    
                def __getitem__(self, idx):
                    return (
                        torch.FloatTensor(self.data[idx:idx + self.sequence_length]),
                        torch.FloatTensor(self.data[idx + self.sequence_length])
                    )
            
            train_dataset = TimeSeriesDataset(train_data, sequence_length)
            val_dataset = TimeSeriesDataset(val_data, sequence_length)
            
            batch_size = 32
            train_loader = torch.utils.data.DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
            val_loader = torch.utils.data.DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
            
            models_to_train = {
                'lstm': LSTMModel(input_size=1, hidden_size=64, num_layers=2, dropout=0.3),
                'tcn': TCNModel(input_size=1, num_channels=[64, 64, 64, 64], kernel_size=3, dropout=0.3)
            }
            
            model_results = {}
            
            for model_name, model in models_to_train.items():
                model.to(torch_device)
                
                criterion = nn.MSELoss()
                optimizer = optim.Adam(model.parameters(), lr=0.001)
                scheduler = optim.lr_scheduler.ReduceLROnPlateau(
                    optimizer, mode='min', factor=0.5, patience=10, verbose=False
                )
                
                best_val_loss = float('inf')
                best_model_state = None
                patience_counter = 0
                
                for epoch in range(150):
                    model.train()
                    train_loss = 0
                    for batch_x, batch_y in train_loader:
                        batch_x, batch_y = batch_x.to(torch_device), batch_y.to(torch_device)
                        
                        optimizer.zero_grad()
                        outputs = model(batch_x)
                        loss = criterion(outputs.squeeze(), batch_y)
                        loss.backward()
                        optimizer.step()
                        train_loss += loss.item()
                    
                    model.eval()
                    val_loss = 0
                    with torch.no_grad():
                        for batch_x, batch_y in val_loader:
                            batch_x, batch_y = batch_x.to(torch_device), batch_y.to(torch_device)
                            outputs = model(batch_x)
                            loss = criterion(outputs.squeeze(), batch_y)
                            val_loss += loss.item()
                    
                    val_loss /= len(val_loader)
                    
                    scheduler.step(val_loss)
                    
                    if val_loss < best_val_loss:
                        best_val_loss = val_loss
                        best_model_state = model.state_dict()
                        patience_counter = 0
                    else:
                        patience_counter += 1
                    
                    if patience_counter >= 20:
                        break
                
                if best_model_state is not None:
                    model.load_state_dict(best_model_state)
                
                model.eval()
                predictions = []
                
                with torch.no_grad():
                    for i in range(len(test_data) - sequence_length):
                        sequence = torch.FloatTensor(test_data[i:i + sequence_length]).unsqueeze(0).to(torch_device)
                        pred = model(sequence)
                        predictions.append(pred.item())
                
                predictions = np.array(predictions)
                actual = test_data[sequence_length:]
                
                from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
                mae = mean_absolute_error(actual, predictions)
                rmse = np.sqrt(mean_squared_error(actual, predictions))
                r2 = r2_score(actual, predictions)
                mape = np.mean(np.abs((actual - predictions) / actual)) * 100
                
                model_results[model_name] = {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'r2': float(r2),
                    'mape': float(mape),
                    'val_loss': float(best_val_loss)
                }
            
            best_model_name = min(model_results.keys(), key=lambda k: model_results[k]['mae'])
            best_model = models_to_train[best_model_name]
            best_metrics = model_results[best_model_name]
            
            os.makedirs('models', exist_ok=True)
            
            model_file = os.path.join('models', f'pytorch_model_user{user.id}_{metric}.pth')
            torch.save(best_model.state_dict(), model_file)
            
            metrics_file = os.path.join('models', f'metrics_pytorch_user{user.id}_{metric}.json')
            with open(metrics_file, 'w') as f:
                json.dump(best_metrics, f, indent=2)
            
            config_file = os.path.join('models', f'config_pytorch_user{user.id}_{metric}.json')
            with open(config_file, 'w') as f:
                json.dump({
                    'model_type': best_model_name,
                    'sequence_length': sequence_length,
                    'scaler_mean': float(scaler.data_min_[0]),
                    'scaler_scale': float(scaler.data_range_[0]),
                    'all_models': model_results
                }, f, indent=2)
            
            results[metric] = {
                'model_type': best_model_name,
                'mae': best_metrics['mae'],
                'rmse': best_metrics['rmse'],
                'r2': best_metrics['r2'],
                'mape': best_metrics['mape']
            }
            
        except Exception as e:
            results[metric] = {'error': str(e)}
            import traceback
            traceback.print_exc()
    
    return Response(results)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_advanced_model(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metrics_to_train = request.data.get('metrics', [])
    
    if not metrics_to_train:
        return Response({'error': '请指定要训练的指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    if joblib is None:
        return Response({'error': 'joblib未安装'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    results = {}
    
    for metric in metrics_to_train:
        try:
            from measurements.models import Measurement
            measurements = Measurement.objects.filter(user=user).order_by('measured_at')
            data = list(measurements.values('measured_at', metric))
            
            if not data:
                results[metric] = {'error': '没有数据'}
                continue
            
            df = pd.DataFrame(data)
            df['measured_at'] = pd.to_datetime(df['measured_at'])
            df = df.sort_values('measured_at')
            df = df.set_index('measured_at')
            
            df[metric] = df[metric].astype(float)
            df_metric = df[[metric]].dropna()
            
            if len(df_metric) < 50:
                results[metric] = {'error': '数据不足，至少需要50条数据'}
                continue
            
            df_cleaned = clean_and_validate_data(df_metric, metric)
            
            df_lag = add_lag_features(df_cleaned, lag_days=[1, 2, 3, 4, 5, 6, 7])
            df_lag = add_diff_features(df_lag)
            df_processed = df_lag.dropna()
            
            if len(df_processed) < 30:
                results[metric] = {'error': '处理后数据不足'}
                continue
            
            target_col = metric
            feature_cols = [col for col in df_processed.columns if col != target_col]
            
            X = df_processed[feature_cols]
            y = df_processed[target_col]
            
            train_size = int(len(X) * 0.8)
            val_size = int(len(X) * 0.1)
            
            X_train = X[:train_size]
            y_train = y[:train_size]
            X_val = X[train_size:train_size + val_size]
            y_val = y[train_size:train_size + val_size]
            X_test = X[train_size + val_size:]
            y_test = y[train_size + val_size:]
            
            from sklearn.ensemble import RandomForestRegressor, GradientBoostingRegressor
            from sklearn.svm import SVR
            from sklearn.preprocessing import MinMaxScaler
            from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
            
            models_to_train = {
                'random_forest': RandomForestRegressor(
                    n_estimators=100,
                    max_depth=10,
                    min_samples_split=10,
                    min_samples_leaf=4,
                    random_state=42,
                    n_jobs=-1
                ),
                'gradient_boosting': GradientBoostingRegressor(
                    n_estimators=100,
                    learning_rate=0.1,
                    max_depth=3,
                    min_samples_split=10,
                    min_samples_leaf=4,
                    random_state=42
                )
            }
            
            model_results = {}
            
            for model_name, model in models_to_train.items():
                model.fit(X_train, y_train)
                y_pred_val = model.predict(X_val)
                val_mae = mean_absolute_error(y_val, y_pred_val)
                
                y_pred_test = model.predict(X_test)
                mae = mean_absolute_error(y_test, y_pred_test)
                rmse = np.sqrt(mean_squared_error(y_test, y_pred_test))
                r2 = r2_score(y_test, y_pred_test)
                mape = np.mean(np.abs((y_test - y_pred_test) / y_test)) * 100
                
                model_results[model_name] = {
                    'mae': float(mae),
                    'rmse': float(rmse),
                    'r2': float(r2),
                    'mape': float(mape),
                    'val_mae': float(val_mae)
                }
            
            best_model_name = min(model_results.keys(), key=lambda k: model_results[k]['mae'])
            best_model = models_to_train[best_model_name]
            best_metrics = model_results[best_model_name]
            
            os.makedirs('models', exist_ok=True)
            
            model_file = os.path.join('models', f'advanced_model_user{user.id}_{metric}.pkl')
            joblib.dump(best_model, model_file)
            
            metrics_file = os.path.join('models', f'metrics_advanced_user{user.id}_{metric}.json')
            with open(metrics_file, 'w') as f:
                json.dump(best_metrics, f, indent=2)
            
            config_file = os.path.join('models', f'config_advanced_user{user.id}_{metric}.json')
            with open(config_file, 'w') as f:
                json.dump({
                    'model_type': best_model_name,
                    'all_models': model_results
                }, f, indent=2)
            
            results[metric] = {
                'model_type': best_model_name,
                'mae': best_metrics['mae'],
                'rmse': best_metrics['rmse'],
                'r2': best_metrics['r2'],
                'mape': best_metrics['mape']
            }
            
        except Exception as e:
            results[metric] = {'error': str(e)}
            import traceback
            traceback.print_exc()
    
    return Response(results)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def train_lstm_model_api(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metrics_to_train = request.data.get('metrics', [])
    
    if not metrics_to_train:
        return Response({'error': '请指定要训练的指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 重新检查TensorFlow可用性
    try:
        import tensorflow as tf
        from tensorflow import keras
        from tensorflow.keras.models import load_model
        tf_available = True
        tf_version = tf.__version__
        print(f"TensorFlow检查成功: {tf_version}")
    except (ImportError, OSError) as e:
        tf_available = False
        print(f"TensorFlow检查失败: {e}")
        import traceback
        traceback.print_exc()
    
    if not tf_available:
        return Response({'error': 'TensorFlow未安装，无法训练LSTM模型'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    results = {}
    
    for metric in metrics_to_train:
        try:
            model, metrics = train_lstm_model(user.id, metric, seq_length=7, epochs=100, batch_size=16)
            
            if model is None:
                results[metric] = metrics
            else:
                results[metric] = {
                    'model_type': 'lstm',
                    'mae': metrics['mae'],
                    'rmse': metrics['rmse'],
                    'r2': metrics['r2'],
                    'mape': metrics['mape']
                }
            
        except Exception as e:
            results[metric] = {'error': str(e)}
            import traceback
            traceback.print_exc()
    
    return Response(results)


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
        lgb_model, lgb_metrics, lgb_feature_config, lgb_feature_cols = load_lgb_model(user.id, metric)
        
        if lgb_model is None:
            continue
        
        xgb_model = None
        xgb_model_file = os.path.join('models', f'xgb_model_user{user.id}_{metric}.json')
        if os.path.exists(xgb_model_file):
            xgb_model = xgb.Booster()
            xgb_model.load_model(xgb_model_file)
        
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
        
        df_cleaned = clean_and_validate_data(df_metric, metric)
        
        if len(df_cleaned) < 1:
            continue
        
        pred_values = predict_future_ensemble(df_cleaned, metric, lgb_feature_config, lgb_feature_cols, lgb_model, xgb_model, days=days)
        
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


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def predict_with_model(request):
    from django.contrib.auth import get_user_model
    User = get_user_model()
    
    user = request.user
    metric = request.data.get('metric')
    days = int(request.data.get('days', 7))
    
    if not metric:
        return Response({'error': '请指定指标'}, status=status.HTTP_400_BAD_REQUEST)
    
    from measurements.models import Measurement
    measurements = Measurement.objects.filter(user=user).order_by('measured_at')
    data = list(measurements.values('measured_at', metric))
    
    if len(data) < 7:
        return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
    
    df = pd.DataFrame(data)
    df['measured_at'] = pd.to_datetime(df['measured_at'])
    df = df.sort_values('measured_at')
    df = df.set_index('measured_at')
    df_metric = df[[metric]].dropna()
    
    if len(df_metric) < 7:
        return Response({'error': '有效数据不足'}, status=status.HTTP_400_BAD_REQUEST)
    
    df_cleaned = clean_and_validate_data(df_metric, metric)
    
    if len(df_cleaned) < 8:
        return Response({'error': '有效数据不足，至少需要8条数据'}, status=status.HTTP_400_BAD_REQUEST)
    
    # 计算历史预测值（用于对比）
    historical_predictions = []
    historical_dates = []
    historical_actuals = []
    
    if len(df_cleaned) >= 14:
        # 使用最后7天作为测试集
        test_size = min(7, len(df_cleaned) // 2)
        train_data = df_cleaned.iloc[:-test_size]
        test_data = df_cleaned.iloc[-test_size:]
        
        for i in range(len(test_data)):
            current_data = pd.concat([train_data, test_data.iloc[:i]])
            if len(current_data) < 8:
                continue
            
            # 优先使用LSTM模型计算历史预测
            pred, _, _, _ = predict_lstm(user.id, metric, current_data, days=1)
            if pred is None:
                # 如果LSTM失败，尝试高级模型
                pred, _, _, _ = predict_advanced(user.id, metric, current_data, days=1)
            
            if pred is not None and len(pred) > 0:
                historical_dates.append(test_data.index[i].strftime('%Y-%m-%d'))
                historical_actuals.append(test_data.iloc[i][metric])
                historical_predictions.append(pred[0])
    
    # 尝试使用LSTM模型
    lstm_predictions, lstm_metrics, lstm_lower_bound, lstm_upper_bound = predict_lstm(user.id, metric, df_cleaned, days=days)
    
    if lstm_predictions is not None:
        return Response({
            'metric': metric,
            'days': days,
            'predictions': lstm_predictions.tolist(),
            'lower_bound': lstm_lower_bound.tolist() if lstm_lower_bound is not None else None,
            'upper_bound': lstm_upper_bound.tolist() if lstm_upper_bound is not None else None,
            'metrics': lstm_metrics,
            'model_type': 'lstm',
            'historical': {
                'dates': historical_dates,
                'actuals': historical_actuals,
                'predictions': historical_predictions
            } if historical_dates else None
        })
    
    advanced_predictions, advanced_metrics, lower_bound, upper_bound = predict_advanced(user.id, metric, df_cleaned, days=days)
    
    if advanced_predictions is not None:
        return Response({
            'metric': metric,
            'days': days,
            'predictions': advanced_predictions.tolist(),
            'lower_bound': lower_bound.tolist() if lower_bound is not None else None,
            'upper_bound': upper_bound.tolist() if upper_bound is not None else None,
            'metrics': advanced_metrics,
            'model_type': 'advanced',
            'historical': {
                'dates': historical_dates,
                'actuals': historical_actuals,
                'predictions': historical_predictions
            } if historical_dates else None
        })
    
    pytorch_predictions, pytorch_metrics = predict_pytorch(user.id, metric, df_cleaned, days=days)
    
    if pytorch_predictions is not None:
        return Response({
            'metric': metric,
            'days': days,
            'predictions': pytorch_predictions.tolist(),
            'metrics': pytorch_metrics,
            'model_type': 'pytorch',
            'historical': {
                'dates': historical_dates,
                'actuals': historical_actuals,
                'predictions': historical_predictions
            } if historical_dates else None
        })
    
    lgb_model, lgb_metrics, lgb_feature_config, lgb_feature_cols = load_lgb_model(user.id, metric)
    
    if lgb_model is None:
        return Response({'error': '模型不存在，请先训练模型'}, status=status.HTTP_404_NOT_FOUND)
    
    xgb_model, xgb_metrics, xgb_feature_config, xgb_feature_cols = load_xgb_model(user.id, metric)
    
    if xgb_model is not None:
        if set(lgb_feature_cols) != set(xgb_feature_cols):
            xgb_model = None
    
    pred_values = predict_future_ensemble(df_cleaned, metric, lgb_feature_config, lgb_feature_cols, lgb_model, xgb_model, days=days)
    
    return Response({
        'metric': metric,
        'days': days,
        'predictions': pred_values.tolist(),
        'metrics': lgb_metrics,
        'model_type': 'ensemble',
        'historical': {
            'dates': historical_dates,
            'actuals': historical_actuals,
            'predictions': historical_predictions
        } if historical_dates else None
    })
