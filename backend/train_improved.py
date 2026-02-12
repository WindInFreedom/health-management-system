import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'health_management_system.settings')

import django
django.setup()

import json
import numpy as np
import torch
import torch.nn as nn
from sklearn.preprocessing import MinMaxScaler
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from torch.utils.data import Dataset, DataLoader
import joblib
import warnings
import pandas as pd
warnings.filterwarnings('ignore')

from measurements.models import Measurement
from django.contrib.auth import get_user_model
User = get_user_model()

# ==================== 配置区域 ====================
# 在这里修改配置来启用不同的改进方案

# 1. 模型架构配置
MODEL_CONFIG = {
    # 隐藏层大小：控制模型容量，越大越复杂但训练越慢
    # 可选值：32（默认）, 64, 128, 256
    'hidden_size': 128,  # 从64改为128，增加模型容量
    
    # GRU层数：控制模型深度，层数越多越复杂但训练越慢
    # 可选值：1（默认）, 2, 3
    'num_layers': 2,  # 保持2
    
    # 是否使用双向GRU：双向可以同时看到过去和未来信息
    # 可选值：False（默认）, True
    'bidirectional': True,  # 从False改为True，启用双向GRU
    
    # Dropout率：防止过拟合，值越大丢弃的神经元越多
    # 可选值：0.0（不丢弃）, 0.1, 0.2（默认）, 0.3, 0.5
    'dropout': 0.3,  # 从0.2改为0.3，增强正则化
}

# 2. 训练参数配置
TRAINING_CONFIG = {
    # 训练轮数（epochs）：训练多少轮
    # 可选值：50（默认）, 100, 200, 500
    'epochs': 200,  # 从100改为200，增加训练轮数
    
    # 学习率（learning rate）：控制参数更新的步长
    # 可选值：0.01（较大）, 0.001（默认）, 0.0001（较小）
    'learning_rate': 0.0005,  # 从0.001改为0.0005，降低学习率
    
    # 批次大小（batch size）：一次训练多少个样本
    # 可选值：16, 32（默认）, 64, 128
    'batch_size': 16,  # 从32改为16，更稳定的梯度更新
    
    # 序列长度（sequence length）：用过去多少天的数据预测下一天
    # 可选值：7（默认，一周）, 14（两周）, 30（一个月）
    'seq_length': 14,  # 从7改为14，使用更长历史
}

# 3. 特征工程配置
FEATURE_CONFIG = {
    # 是否添加时间特征（年、月、日、星期）
    # 可选值：False（默认）, True
    'use_time_features': False,  # 禁用时间特征
    
    # 是否添加移动平均特征
    # 可选值：False（默认）, True
    'use_moving_avg': False,  # 禁用移动平均
    
    # 移动平均窗口大小
    # 可选值：3, 7（默认）, 14
    'moving_avg_window': 7,  # 保持7
    
    # 是否添加滞后特征（过去N天的数据）
    # 可选值：False（默认）, True
    'use_lag_features': True,  # 只启用滞后特征
    
    # 滞后天数
    # 可选值：[1, 2, 3], [1, 7, 14]（默认）, [1, 3, 7, 14]
    'lag_days': [1, 7, 14]  # 保持多滞后特征
}

# ==================== 模型定义 ====================

class GRUModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=1, output_size=1, bidirectional=False, dropout=0.2):
        super(GRUModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        # GRU层
        self.gru = nn.GRU(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True,
            bidirectional=bidirectional  # 双向GRU
        )
        
        # 计算全连接层的输入维度
        # 如果是双向GRU，输出维度是hidden_size的2倍
        fc_input_size = hidden_size * 2 if bidirectional else hidden_size
        
        # 全连接层
        self.fc = nn.Linear(fc_input_size, output_size)
        
        # Dropout层
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # 初始化隐藏状态
        batch_size = x.size(0)
        num_directions = 2 if self.bidirectional else 1
        h0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        
        # 前向传播
        out, _ = self.gru(x, h0)
        
        # 取最后一个时间步的输出
        out = out[:, -1, :]
        
        # Dropout
        out = self.dropout(out)
        
        # 全连接层
        out = self.fc(out)
        return out

class LSTMModel(nn.Module):
    def __init__(self, input_size=1, hidden_size=32, num_layers=1, output_size=1, bidirectional=False, dropout=0.2):
        super(LSTMModel, self).__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        
        # LSTM层
        self.lstm = nn.LSTM(
            input_size, 
            hidden_size, 
            num_layers, 
            batch_first=True,
            bidirectional=bidirectional  # 双向LSTM
        )
        
        # 计算全连接层的输入维度
        fc_input_size = hidden_size * 2 if bidirectional else hidden_size
        
        # 全连接层
        self.fc = nn.Linear(fc_input_size, output_size)
        
        # Dropout层
        self.dropout = nn.Dropout(dropout)

    def forward(self, x):
        # 初始化隐藏状态和细胞状态
        batch_size = x.size(0)
        num_directions = 2 if self.bidirectional else 1
        h0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        c0 = torch.zeros(self.num_layers * num_directions, batch_size, self.hidden_size).to(x.device)
        
        # 前向传播
        out, _ = self.lstm(x, (h0, c0))
        
        # 取最后一个时间步的输出
        out = out[:, -1, :]
        
        # Dropout
        out = self.dropout(out)
        
        # 全连接层
        out = self.fc(out)
        return out

# ==================== 数据集定义 ====================

class HealthDataset(Dataset):
    def __init__(self, data, seq_length=7):
        self.data = data
        self.seq_length = seq_length

    def __len__(self):
        return len(self.data) - self.seq_length

    def __getitem__(self, idx):
        x = self.data[idx:idx + self.seq_length]
        y = self.data[idx + self.seq_length, 0]  # 只取第一列（原始指标）作为标签
        return torch.FloatTensor(x), torch.FloatTensor([y])

# ==================== 特征工程函数 ====================

def add_time_features(df):
    """
    添加时间特征
    - 年、月、日、星期几
    """
    df = df.copy()
    df['year'] = df.index.year
    df['month'] = df.index.month
    df['day'] = df.index.day
    df['dayofweek'] = df.index.dayofweek
    return df

def add_moving_avg_features(df, window=7):
    """
    添加移动平均特征
    - 简单移动平均
    - 指数移动平均
    """
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in ['year', 'month', 'day', 'dayofweek']:
            df[f'{col}_ma{window}'] = df[col].rolling(window=window).mean()
            df[f'{col}_ema'] = df[col].ewm(span=window).mean()
    return df

def add_lag_features(df, lag_days=[1, 7, 14]):
    """
    添加滞后特征
    - 过去N天的值
    """
    df = df.copy()
    for col in df.select_dtypes(include=[np.number]).columns:
        if col not in ['year', 'month', 'day', 'dayofweek'] and not col.endswith('_ma7') and not col.endswith('_ema'):
            for lag in lag_days:
                df[f'{col}_lag{lag}'] = df[col].shift(lag)
    return df

def preprocess_data(df, feature_config):
    """
    数据预处理和特征工程
    """
    df = df.copy()
    
    # 1. 添加时间特征
    if feature_config['use_time_features']:
        df = add_time_features(df)
    
    # 2. 添加移动平均特征
    if feature_config['use_moving_avg']:
        df = add_moving_avg_features(df, feature_config['moving_avg_window'])
    
    # 3. 添加滞后特征
    if feature_config['use_lag_features']:
        df = add_lag_features(df, feature_config['lag_days'])
    
    # 删除包含NaN的行
    df = df.dropna()
    
    return df

# ==================== 训练函数 ====================

def train_single_metric(df_metric, metric, user_id, model_config, training_config, feature_config, model_type='gru'):
    """
    训练单个指标的模型
    """
    seq_length = training_config['seq_length']
    
    # 数据预处理和特征工程
    df_processed = preprocess_data(df_metric, feature_config)
    
    # 保存特征工程后的索引，用于后续匹配原始数据
    processed_index = df_processed.index
    
    # 为原始指标单独创建 scaler（用于反归一化预测值）
    original_scaler = MinMaxScaler()
    original_scaled = original_scaler.fit_transform(df_metric.values)
    
    # 归一化特征工程后的数据
    scaler = MinMaxScaler()
    scaled_data = scaler.fit_transform(df_processed.values)
    
    # 数据集划分：8:1:1 (训练集:验证集:测试集)
    train_size = int(len(scaled_data) * 0.8)
    val_size = int(len(scaled_data) * 0.1)
    
    train_data = scaled_data[:train_size]
    val_data = scaled_data[train_size:train_size + val_size]
    test_data = scaled_data[train_size + val_size:]
    
    # 获取测试集对应的原始数据索引
    test_index = processed_index[train_size + val_size:]
    test_actual_values = df_metric.loc[test_index].values
    
    print(f'    数据集划分: 训练集={len(train_data)}, 验证集={len(val_data)}, 测试集={len(test_data)}')
    
    # 创建数据集
    train_dataset = HealthDataset(train_data, seq_length)
    val_dataset = HealthDataset(val_data, seq_length)
    
    train_dataloader = DataLoader(train_dataset, batch_size=training_config['batch_size'], shuffle=False)
    val_dataloader = DataLoader(val_dataset, batch_size=training_config['batch_size'], shuffle=False)
    
    # 计算输入维度
    input_size = df_processed.shape[1]
    
    # 创建模型
    device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
    
    if model_type == 'gru':
        model = GRUModel(
            input_size=input_size,
            hidden_size=model_config['hidden_size'],
            num_layers=model_config['num_layers'],
            output_size=1,
            bidirectional=model_config['bidirectional'],
            dropout=model_config['dropout']
        ).to(device)
    elif model_type == 'lstm':
        model = LSTMModel(
            input_size=input_size,
            hidden_size=model_config['hidden_size'],
            num_layers=model_config['num_layers'],
            output_size=1,
            bidirectional=model_config['bidirectional'],
            dropout=model_config['dropout']
        ).to(device)
    
    # 损失函数和优化器
    criterion = nn.MSELoss()
    optimizer = torch.optim.Adam(model.parameters(), lr=training_config['learning_rate'])
    
    # 学习率调度器
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='min', factor=0.5, patience=15)
    
    # 早停机制配置
    early_stopping_patience = 15
    early_stopping_counter = 0
    best_val_loss = float('inf')
    best_model_state = None
    
    # 训练
    model.train()
    for epoch in range(training_config['epochs']):
        total_loss = 0
        for batch_x, batch_y in train_dataloader:
            batch_x, batch_y = batch_x.to(device), batch_y.to(device)
            
            outputs = model(batch_x)
            loss = criterion(outputs, batch_y)
            
            optimizer.zero_grad()
            loss.backward()
            optimizer.step()
            
            total_loss += loss.item()
        
        avg_train_loss = total_loss / len(train_dataloader)
        
        # 验证集评估
        model.eval()
        val_loss = 0
        with torch.no_grad():
            for batch_x, batch_y in val_dataloader:
                batch_x, batch_y = batch_x.to(device), batch_y.to(device)
                outputs = model(batch_x)
                loss = criterion(outputs, batch_y)
                val_loss += loss.item()
        
        avg_val_loss = val_loss / len(val_dataloader)
        
        # 学习率调度
        scheduler.step(avg_val_loss)
        
        # 早停检查
        if avg_val_loss < best_val_loss:
            best_val_loss = avg_val_loss
            early_stopping_counter = 0
            best_model_state = model.state_dict().copy()
        else:
            early_stopping_counter += 1
        
        if (epoch + 1) % 20 == 0:
            print(f'    Epoch [{epoch+1}/{training_config["epochs"]}], Train Loss: {avg_train_loss:.4f}, Val Loss: {avg_val_loss:.4f}')
        
        # 早停触发
        if early_stopping_counter >= early_stopping_patience:
            print(f'    早停触发于 Epoch {epoch+1} (验证集loss {early_stopping_patience} 轮未改善)')
            break
        
        model.train()
    
    # 加载最佳模型
    if best_model_state is not None:
        model.load_state_dict(best_model_state)
        print(f'    已加载最佳模型 (验证集loss: {best_val_loss:.4f})')
    
    # 测试集评估
    model.eval()
    predictions = []
    actuals = []
    
    with torch.no_grad():
        for i in range(len(test_data) - seq_length):
            x = torch.FloatTensor(test_data[i:i+seq_length]).unsqueeze(0).to(device)
            y = model(x).cpu().numpy()[0][0]
            predictions.append(y)
            # 使用对应的原始数据作为实际值
            actuals.append(test_actual_values[i + seq_length, 0])
    
    # 反归一化预测值
    predictions = np.array(predictions)
    actuals = np.array(actuals)
    
    # 调试信息
    print(f'    调试: 预测值范围 [{predictions.min():.4f}, {predictions.max():.4f}], 实际值范围 [{actuals.min():.4f}, {actuals.max():.4f}]')
    print(f'    调试: original_scaler.scale_[0]={original_scaler.scale_[0]:.6f}, original_scaler.min_[0]={original_scaler.min_[0]:.6f}')
    
    # 使用 original_scaler 反归一化预测值
    predictions_reshaped = predictions.reshape(-1, 1)
    predictions_denorm = original_scaler.inverse_transform(predictions_reshaped)
    predictions = predictions_denorm.flatten()
    
    print(f'    调试: 反归一化后预测值范围 [{predictions.min():.4f}, {predictions.max():.4f}]')
    
    # 计算评估指标
    mae = mean_absolute_error(actuals, predictions)
    rmse = np.sqrt(mean_squared_error(actuals, predictions))
    r2 = r2_score(actuals, predictions)
    mape = np.mean(np.abs((actuals - predictions) / actuals)) * 100
    
    metrics = {
        'MAE': float(mae),
        'RMSE': float(rmse),
        'R2': float(r2),
        'MAPE': float(mape),
        'best_val_loss': float(best_val_loss)
    }
    
    # 保存模型
    os.makedirs('models', exist_ok=True)
    model_file = os.path.join('models', f'{model_type}_model_user{user_id}_{metric}.pth')
    torch.save({
        'model_state_dict': model.state_dict(),
        'input_size': input_size,
        'hidden_size': model_config['hidden_size'],
        'num_layers': model_config['num_layers'],
        'output_size': 1,
        'bidirectional': model_config['bidirectional'],
        'dropout': model_config['dropout']
    }, model_file)
    
    # 保存归一化器
    scaler_file = os.path.join('models', f'scaler_user{user_id}_{metric}.pkl')
    joblib.dump(scaler, scaler_file)
    
    # 保存评估指标
    metrics_file = os.path.join('models', f'metrics_{model_type}_user{user_id}_{metric}.json')
    with open(metrics_file, 'w') as f:
        json.dump(metrics, f, indent=2)
    
    return metrics

# ==================== 主程序 ====================

if __name__ == '__main__':
    user = User.objects.get(id=1)
    
    print('='*60)
    print('开始为用户 user001 训练改进版GRU模型')
    print('='*60)
    print(f'模型配置: {MODEL_CONFIG}')
    print(f'训练配置: {TRAINING_CONFIG}')
    print(f'特征配置: {FEATURE_CONFIG}')
    print('='*60)
    
    metrics_to_train = ['weight_kg', 'systolic', 'diastolic', 'heart_rate', 'blood_glucose']
    
    # 选择模型类型：'gru' 或 'lstm'
    model_type = 'gru'  # 修改这里：从'gru'改为'lstm'使用LSTM模型
    
    for metric in metrics_to_train:
        print(f'\n训练指标: {metric}')
        measurements = Measurement.objects.filter(user=user).order_by('measured_at')
        data = list(measurements.values('measured_at', metric))
        
        if not data:
            print(f'  跳过: 没有数据')
            continue
        
        df = pd.DataFrame(data)
        df['measured_at'] = pd.to_datetime(df['measured_at'])
        df = df.sort_values('measured_at')
        df = df.set_index('measured_at')
        
        # 将 Decimal 类型转换为 float
        df[metric] = df[metric].astype(float)
        
        df_metric = df[[metric]].dropna()
        
        if len(df_metric) < 8:
            print(f'  跳过: 数据不足 (需要至少8条记录，当前有{len(df_metric)}条)')
            continue
        
        print(f'  数据量: {len(df_metric)} 条记录')
        
        try:
            metrics = train_single_metric(
                df_metric, 
                metric, 
                user.id, 
                MODEL_CONFIG, 
                TRAINING_CONFIG, 
                FEATURE_CONFIG,
                model_type
            )
            print(f'  MAE: {metrics["MAE"]:.4f}')
            print(f'  RMSE: {metrics["RMSE"]:.4f}')
            print(f'  R2: {metrics["R2"]:.4f}')
            print(f'  MAPE: {metrics["MAPE"]:.2f}%')
        except Exception as e:
            print(f'  训练失败: {e}')
            import traceback
            traceback.print_exc()
    
    print('\n' + '='*60)
    print('训练完成！')
    print('='*60)
