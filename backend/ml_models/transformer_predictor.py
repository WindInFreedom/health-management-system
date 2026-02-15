"""
Transformer 预测模型

使用 Transformer 架构进行时间序列健康数据预测
支持:
- 多头注意力机制 (Multi-Head Attention)
- 位置编码 (Positional Encoding)
- 前馈神经网络 (Feed Forward Network)
- 层归一化 (Layer Normalization)

架构:
- Input Embedding
- Positional Encoding
- Multi-Head Attention (4 heads)
- Feed Forward Network
- Layer Normalization
- Output Linear Layer

作者: Health Management System Team
日期: 2026-02-15
"""

import os
import json
import math
import numpy as np
import pandas as pd
from typing import Dict, List, Tuple, Optional
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

try:
    import torch
    import torch.nn as nn
    import torch.optim as optim
    from torch.utils.data import Dataset, DataLoader
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False
    print("警告: PyTorch 未安装，Transformer 模型不可用")


class PositionalEncoding(nn.Module):
    """位置编码"""
    
    def __init__(self, d_model: int, max_len: int = 5000, dropout: float = 0.1):
        """
        初始化位置编码
        
        Args:
            d_model: 嵌入维度
            max_len: 最大序列长度
            dropout: Dropout 比率
        """
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)
        
        # 创建位置编码矩阵
        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        
        pe = pe.unsqueeze(0)  # [1, max_len, d_model]
        self.register_buffer('pe', pe)
    
    def forward(self, x):
        """
        Args:
            x: [batch_size, seq_len, d_model]
        """
        x = x + self.pe[:, :x.size(1), :]
        return self.dropout(x)


class TransformerPredictor(nn.Module):
    """
    Transformer 时间序列预测模型
    
    使用 Transformer 编码器进行序列编码，然后通过全连接层输出预测
    """
    
    def __init__(self, input_size: int = 1, d_model: int = 64, nhead: int = 4, 
                 num_encoder_layers: int = 2, dim_feedforward: int = 256, 
                 dropout: float = 0.1, output_size: int = 1):
        """
        初始化 Transformer 模型
        
        Args:
            input_size: 输入特征维度
            d_model: 嵌入维度
            nhead: 注意力头数
            num_encoder_layers: 编码器层数
            dim_feedforward: 前馈网络维度
            dropout: Dropout 比率
            output_size: 输出维度
        """
        super(TransformerPredictor, self).__init__()
        
        self.input_size = input_size
        self.d_model = d_model
        
        # 输入嵌入层
        self.input_embedding = nn.Linear(input_size, d_model)
        
        # 位置编码
        self.pos_encoder = PositionalEncoding(d_model, dropout=dropout)
        
        # Transformer 编码器
        encoder_layer = nn.TransformerEncoderLayer(
            d_model=d_model,
            nhead=nhead,
            dim_feedforward=dim_feedforward,
            dropout=dropout,
            batch_first=True
        )
        self.transformer_encoder = nn.TransformerEncoder(
            encoder_layer,
            num_layers=num_encoder_layers
        )
        
        # 输出层
        self.fc_out = nn.Linear(d_model, output_size)
        
        # 初始化权重
        self._init_weights()
    
    def _init_weights(self):
        """初始化模型权重"""
        for p in self.parameters():
            if p.dim() > 1:
                nn.init.xavier_uniform_(p)
    
    def forward(self, x, mask=None):
        """
        前向传播
        
        Args:
            x: 输入张量 [batch_size, seq_length, input_size]
            mask: 注意力掩码（可选）
            
        Returns:
            输出张量 [batch_size, output_size]
        """
        # 输入嵌入
        x = self.input_embedding(x)  # [batch_size, seq_length, d_model]
        x = x * math.sqrt(self.d_model)  # 缩放
        
        # 位置编码
        x = self.pos_encoder(x)
        
        # Transformer 编码
        x = self.transformer_encoder(x, mask=mask)
        
        # 取最后一个时间步的输出
        x = x[:, -1, :]  # [batch_size, d_model]
        
        # 输出层
        output = self.fc_out(x)  # [batch_size, output_size]
        
        return output


class TransformerTrainer:
    """
    Transformer 模型训练器
    
    提供完整的训练、验证、测试流程
    """
    
    def __init__(self, seq_length: int = 14, train_split: float = 0.8, 
                 val_split: float = 0.1, random_seed: int = 42):
        """
        初始化训练器
        
        Args:
            seq_length: 序列长度
            train_split: 训练集比例
            val_split: 验证集比例
            random_seed: 随机种子
        """
        self.seq_length = seq_length
        self.train_split = train_split
        self.val_split = val_split
        self.random_seed = random_seed
        
        # 设置随机种子
        torch.manual_seed(random_seed)
        np.random.seed(random_seed)
        
        # 设备
        self.device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
        
        # 模型和优化器
        self.model = None
        self.optimizer = None
        self.criterion = nn.MSELoss()
        
        # 数据缩放器
        self.scaler_X = None
        self.scaler_y = None
        
        # 训练历史
        self.history = {
            'train_loss': [],
            'val_loss': [],
        }
    
    def create_sequences(self, data: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
        """创建滑动窗口序列"""
        X, y = [], []
        
        for i in range(len(data) - self.seq_length):
            X.append(data[i:i + self.seq_length])
            y.append(data[i + self.seq_length])
        
        return np.array(X), np.array(y)
    
    def prepare_data(self, df: pd.DataFrame, metric: str) -> Tuple:
        """
        准备训练数据
        
        Args:
            df: 包含时间序列数据的 DataFrame
            metric: 要预测的指标名称
            
        Returns:
            (X_train, y_train, X_val, y_val, X_test, y_test)
        """
        # 提取数据并处理缺失值
        data = df[[metric]].values
        data = pd.DataFrame(data).fillna(method='ffill').fillna(method='bfill').values
        
        # 数据标准化
        from sklearn.preprocessing import StandardScaler
        
        self.scaler_X = StandardScaler()
        self.scaler_y = StandardScaler()
        
        data_scaled = self.scaler_X.fit_transform(data)
        
        # 创建序列
        X, y = self.create_sequences(data_scaled)
        
        # 划分数据集
        n_samples = len(X)
        train_size = int(n_samples * self.train_split)
        val_size = int(n_samples * self.val_split)
        
        X_train = X[:train_size]
        y_train = y[:train_size]
        
        X_val = X[train_size:train_size + val_size]
        y_val = y[train_size:train_size + val_size]
        
        X_test = X[train_size + val_size:]
        y_test = y[train_size + val_size:]
        
        return X_train, y_train, X_val, y_val, X_test, y_test
    
    def train(self, X_train, y_train, X_val, y_val, epochs: int = 100, 
              batch_size: int = 32, learning_rate: float = 0.001, 
              patience: int = 15, verbose: bool = True) -> Dict:
        """
        训练 Transformer 模型
        
        Args:
            X_train, y_train: 训练数据
            X_val, y_val: 验证数据
            epochs: 训练轮数
            batch_size: 批量大小
            learning_rate: 学习率
            patience: 早停耐心值
            verbose: 是否打印训练信息
            
        Returns:
            训练历史字典
        """
        from ml_models.lstm_predictor import TimeSeriesDataset
        
        # 创建数据加载器
        train_dataset = TimeSeriesDataset(X_train, y_train)
        val_dataset = TimeSeriesDataset(X_val, y_val)
        
        train_loader = DataLoader(train_dataset, batch_size=batch_size, shuffle=True)
        val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
        
        # 创建模型
        input_size = X_train.shape[2]
        self.model = TransformerPredictor(
            input_size=input_size,
            d_model=64,
            nhead=4,
            num_encoder_layers=2,
            dim_feedforward=256,
            dropout=0.1
        ).to(self.device)
        
        # 优化器
        self.optimizer = optim.Adam(self.model.parameters(), lr=learning_rate)
        
        # 学习率调度器
        scheduler = optim.lr_scheduler.ReduceLROnPlateau(
            self.optimizer, mode='min', factor=0.5, patience=5, verbose=verbose
        )
        
        # 早停
        best_val_loss = float('inf')
        patience_counter = 0
        best_model_state = None
        
        if verbose:
            print(f"开始训练 Transformer 模型...")
            print(f"设备: {self.device}")
            print(f"训练样本: {len(X_train)}, 验证样本: {len(X_val)}")
            print(f"输入维度: {input_size}, 序列长度: {self.seq_length}")
        
        for epoch in range(epochs):
            # 训练阶段
            self.model.train()
            train_loss = 0.0
            
            for batch_X, batch_y in train_loader:
                batch_X = batch_X.to(self.device)
                batch_y = batch_y.to(self.device)
                
                # 前向传播
                outputs = self.model(batch_X)
                loss = self.criterion(outputs, batch_y)
                
                # 反向传播
                self.optimizer.zero_grad()
                loss.backward()
                torch.nn.utils.clip_grad_norm_(self.model.parameters(), max_norm=1.0)
                self.optimizer.step()
                
                train_loss += loss.item()
            
            train_loss /= len(train_loader)
            
            # 验证阶段
            self.model.eval()
            val_loss = 0.0
            
            with torch.no_grad():
                for batch_X, batch_y in val_loader:
                    batch_X = batch_X.to(self.device)
                    batch_y = batch_y.to(self.device)
                    
                    outputs = self.model(batch_X)
                    loss = self.criterion(outputs, batch_y)
                    val_loss += loss.item()
            
            val_loss /= len(val_loader)
            
            # 记录历史
            self.history['train_loss'].append(train_loss)
            self.history['val_loss'].append(val_loss)
            
            # 学习率调度
            scheduler.step(val_loss)
            
            # 早停检查
            if val_loss < best_val_loss:
                best_val_loss = val_loss
                patience_counter = 0
                best_model_state = self.model.state_dict().copy()
            else:
                patience_counter += 1
            
            if verbose and (epoch + 1) % 10 == 0:
                print(f"Epoch [{epoch+1}/{epochs}] "
                      f"Train Loss: {train_loss:.6f}, Val Loss: {val_loss:.6f}")
            
            # 早停
            if patience_counter >= patience:
                if verbose:
                    print(f"早停触发于 Epoch {epoch+1}")
                break
        
        # 恢复最佳模型
        if best_model_state is not None:
            self.model.load_state_dict(best_model_state)
        
        if verbose:
            print(f"训练完成！最佳验证损失: {best_val_loss:.6f}")
        
        return self.history
    
    def evaluate(self, X_test, y_test) -> Dict[str, float]:
        """评估模型性能"""
        self.model.eval()
        
        X_test_tensor = torch.FloatTensor(X_test).to(self.device)
        
        with torch.no_grad():
            predictions = self.model(X_test_tensor).cpu().numpy()
        
        # 反标准化
        predictions = self.scaler_y.inverse_transform(predictions.reshape(-1, 1)).flatten()
        y_test_original = self.scaler_y.inverse_transform(y_test.reshape(-1, 1)).flatten()
        
        # 计算指标
        from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
        
        mae = mean_absolute_error(y_test_original, predictions)
        rmse = np.sqrt(mean_squared_error(y_test_original, predictions))
        r2 = r2_score(y_test_original, predictions)
        
        # MAPE
        mask = y_test_original != 0
        mape = np.mean(np.abs((y_test_original[mask] - predictions[mask]) / y_test_original[mask])) * 100
        
        metrics = {
            'MAE': float(mae),
            'RMSE': float(rmse),
            'R2': float(r2),
            'MAPE': float(mape)
        }
        
        return metrics
    
    def predict_future(self, df: pd.DataFrame, metric: str, days: int = 7, 
                       confidence_level: float = 0.95) -> Dict:
        """预测未来值（带置信区间）"""
        self.model.eval()
        
        # 准备最后一个序列
        data = df[[metric]].values
        data = pd.DataFrame(data).fillna(method='ffill').fillna(method='bfill').values
        data_scaled = self.scaler_X.transform(data)
        
        current_sequence = data_scaled[-self.seq_length:].copy()
        
        predictions = []
        lower_bounds = []
        upper_bounds = []
        
        # Monte Carlo Dropout 用于置信区间估计
        n_iterations = 100
        
        for _ in range(days):
            input_seq = torch.FloatTensor(current_sequence).unsqueeze(0).to(self.device)
            
            # 多次预测
            self.model.train()  # 启用 Dropout
            mc_predictions = []
            
            with torch.no_grad():
                for _ in range(n_iterations):
                    pred = self.model(input_seq).cpu().numpy()[0]
                    mc_predictions.append(pred)
            
            mc_predictions = np.array(mc_predictions)
            
            # 计算均值和置信区间
            mean_pred = mc_predictions.mean(axis=0)
            std_pred = mc_predictions.std(axis=0)
            
            z_score = 1.96  # 95% confidence
            
            predictions.append(mean_pred[0])
            lower_bounds.append(mean_pred[0] - z_score * std_pred[0])
            upper_bounds.append(mean_pred[0] + z_score * std_pred[0])
            
            # 更新序列
            current_sequence = np.vstack([current_sequence[1:], mean_pred.reshape(1, -1)])
        
        # 反标准化
        predictions = self.scaler_y.inverse_transform(np.array(predictions).reshape(-1, 1)).flatten()
        lower_bounds = self.scaler_y.inverse_transform(np.array(lower_bounds).reshape(-1, 1)).flatten()
        upper_bounds = self.scaler_y.inverse_transform(np.array(upper_bounds).reshape(-1, 1)).flatten()
        
        return {
            'predictions': predictions.tolist(),
            'confidence_interval': {
                'lower': lower_bounds.tolist(),
                'upper': upper_bounds.tolist(),
                'level': confidence_level
            }
        }
    
    def save_model(self, user_id: int, metric: str, metrics: Dict, 
                   model_dir: str = 'models'):
        """保存模型及配置"""
        os.makedirs(model_dir, exist_ok=True)
        
        model_path = os.path.join(model_dir, f'transformer_user{user_id}_{metric}.pth')
        torch.save({
            'model_state_dict': self.model.state_dict(),
            'scaler_X': self.scaler_X,
            'scaler_y': self.scaler_y,
            'seq_length': self.seq_length,
        }, model_path)
        
        config_path = os.path.join(model_dir, f'config_transformer_user{user_id}_{metric}.json')
        config = {
            'seq_length': self.seq_length,
            'train_split': self.train_split,
            'val_split': self.val_split,
            'metrics': metrics,
            'trained_at': datetime.now().isoformat(),
        }
        
        with open(config_path, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"模型已保存: {model_path}")
        print(f"配置已保存: {config_path}")
    
    @classmethod
    def load_model(cls, user_id: int, metric: str, model_dir: str = 'models'):
        """加载已保存的模型"""
        model_path = os.path.join(model_dir, f'transformer_user{user_id}_{metric}.pth')
        config_path = os.path.join(model_dir, f'config_transformer_user{user_id}_{metric}.json')
        
        if not os.path.exists(model_path) or not os.path.exists(config_path):
            return None, None
        
        with open(config_path, 'r') as f:
            config = json.load(f)
        
        trainer = cls(seq_length=config['seq_length'])
        
        checkpoint = torch.load(model_path, map_location=trainer.device)
        
        trainer.scaler_X = checkpoint['scaler_X']
        trainer.scaler_y = checkpoint['scaler_y']
        trainer.seq_length = checkpoint['seq_length']
        
        input_size = 1
        trainer.model = TransformerPredictor(input_size=input_size).to(trainer.device)
        trainer.model.load_state_dict(checkpoint['model_state_dict'])
        trainer.model.eval()
        
        return trainer, config['metrics']


if __name__ == '__main__':
    print("Transformer 预测模型模块")
    print(f"PyTorch 可用: {TORCH_AVAILABLE}")
    if TORCH_AVAILABLE:
        print(f"CUDA 可用: {torch.cuda.is_available()}")
