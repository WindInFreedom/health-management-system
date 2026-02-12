# GRU模型训练与预测功能说明

## 概述

本系统集成了基于PyTorch的GRU（门控循环单元）模型，用于预测健康指标的未来趋势。该功能支持对基本指标、睡眠记录和心情记录进行时间序列预测。

## 功能特性

- **轻量级模型**: 使用GRU模型，参数量少，训练速度快
- **多指标支持**: 支持体重、血压、心率、血糖、睡眠时长、睡眠质量、心情评分等指标
- **准确度评估**: 提供MAE、RMSE、R²、MAPE四种评估指标
- **可视化展示**: 在前端图表中展示预测结果
- **模型持久化**: 训练好的模型自动保存，可重复使用

## 技术栈

- **深度学习框架**: PyTorch 2.10.0
- **数据处理**: Pandas, NumPy
- **数据归一化**: MinMaxScaler (scikit-learn)
- **评估指标**: scikit-learn

## 模型架构

```
GRUModel(
  input_size=1,      # 单变量时间序列
  hidden_size=32,    # 隐藏层大小
  num_layers=1,      # GRU层数
  output_size=1      # 单步预测
)
```

### 模型结构
- 输入层: 接收过去7天的数据
- GRU层: 1层，32个隐藏单元
- Dropout层: 0.2的dropout率
- 输出层: 全连接层，输出预测值

## 训练参数

- **序列长度**: 7天（使用过去7天的数据预测下一天）
- **训练集/测试集比例**: 80%/20%
- **批次大小**: 32
- **训练轮数**: 50
- **学习率**: 0.001
- **优化器**: Adam
- **损失函数**: MSE (均方误差)

## 支持的指标

### 基本指标
- `weight_kg`: 体重
- `systolic`: 收缩压
- `diastolic`: 舒张压
- `heart_rate`: 心率
- `blood_glucose`: 血糖

### 睡眠记录
- `sleep_duration`: 睡眠时长（小时）
- `sleep_quality`: 睡眠质量评分

### 心情记录
- `mood_rating`: 心情评分

## 使用方法

### 1. 训练模型

#### 通过API训练
```bash
POST /api/gru-model/train/
Content-Type: application/json
Authorization: Bearer <token>

{
  "metrics": ["weight_kg", "systolic", "diastolic", "heart_rate", "blood_glucose"]
}
```

#### 通过命令行训练
```bash
cd backend
python manage.py export_health_data --user-id 1
python train_gru_model.py --user-id 1 --metrics weight_kg systolic diastolic
```

### 2. 进行预测

#### 通过API预测
```bash
POST /api/gru-model/predict/
Content-Type: application/json
Authorization: Bearer <token>

{
  "metric": "weight_kg",
  "days": 7
}
```

#### 响应示例
```json
{
  "metric": "weight_kg",
  "days": 7,
  "predictions": [70.5, 70.3, 70.1, 69.9, 69.8, 69.7, 69.6],
  "metrics": {
    "MAE": 0.5234,
    "RMSE": 0.6876,
    "R2": 0.8234,
    "MAPE": 0.7423
  }
}
```

### 3. 获取模型准确度指标

```bash
GET /api/gru-model/metrics/?metric=weight_kg
Authorization: Bearer <token>
```

## 前端使用

### 基本指标页面
1. 进入"基本指标"页面
2. 点击"训练GRU模型"按钮训练模型
3. 勾选"显示预测"复选框
4. 调整预测天数（1-30天）
5. 查看预测结果和准确度指标

### 睡眠记录页面
1. 进入"睡眠记录"页面
2. 点击"训练GRU模型"按钮训练模型
3. 勾选"显示预测"复选框
4. 调整预测天数
5. 查看睡眠时长预测结果

### 心情记录页面
1. 进入"心情记录"页面
2. 点击"训练GRU模型"按钮训练模型
3. 勾选"显示预测"复选框
4. 调整预测天数
5. 查看心情评分预测结果

## 模型文件

训练后的模型文件保存在 `backend/models/` 目录下：

- `gru_model_user{user_id}_{metric}.pth`: PyTorch模型文件
- `scaler_user{user_id}_{metric}.pkl`: 数据归一化器
- `metrics_user{user_id}_{metric}.json`: 模型评估指标

## 评估指标说明

### MAE (Mean Absolute Error) - 平均绝对误差
- **含义**: 预测值与真实值之间绝对误差的平均值
- **范围**: [0, +∞)
- **越小越好**: 值越小表示预测越准确
- **单位**: 与原始数据单位相同

### RMSE (Root Mean Square Error) - 均方根误差
- **含义**: 预测值与真实值之间平方误差的平方根
- **范围**: [0, +∞)
- **越小越好**: 值越小表示预测越准确
- **特点**: 对异常值更敏感

### R² (R-squared) - 决定系数
- **含义**: 模型解释的方差占总方差的比例
- **范围**: (-∞, 1]
- **越大越好**: 值越接近1表示模型拟合越好
- **解释**:
  - R² = 1: 完美拟合
  - R² = 0: 模型效果等于简单平均值
  - R² < 0: 模型效果不如简单平均值

### MAPE (Mean Absolute Percentage Error) - 平均绝对百分比误差
- **含义**: 预测值与真实值之间绝对百分比误差的平均值
- **范围**: [0, +∞)
- **越小越好**: 值越小表示预测越准确
- **单位**: 百分比(%)
- **解释**:
  - MAPE < 10%: 预测非常准确
  - 10% ≤ MAPE < 20%: 预测良好
  - 20% ≤ MAPE < 50%: 预测合理
  - MAPE ≥ 50%: 预测不准确

## 数据要求

### 最小数据量
- 至少需要8条有效记录用于训练
- 至少需要7条有效记录用于预测

### 数据质量
- 数据应按时间顺序排列
- 缺失值会被自动过滤
- 异常值会影响模型性能

## 性能优化建议

1. **数据量**: 数据量越大，模型性能越好
2. **数据质量**: 清洗异常值可以提高预测准确度
3. **训练频率**: 定期重新训练模型以适应最新数据
4. **预测范围**: 短期预测（1-7天）比长期预测更准确

## 常见问题

### Q: 训练失败，提示"数据不足"
A: 确保该指标至少有8条有效记录。可以通过数据预处理和清洗功能提高数据质量。

### Q: 预测结果不准确
A: 可能的原因：
- 数据量不足
- 数据存在异常值
- 数据波动较大
- 建议先进行数据清洗，然后重新训练模型

### Q: 模型训练很慢
A: GRU模型已经很轻量级。如果仍然慢，可能的原因：
- 数据量很大
- 计算机性能有限
- 可以考虑减少训练轮数（修改代码中的epochs参数）

### Q: 如何重新训练模型？
A: 直接点击"训练GRU模型"按钮即可，新模型会覆盖旧模型。

## 扩展开发

### 添加新的预测指标
1. 在`gru_model_views.py`的`train_gru_model`函数中添加新的指标处理逻辑
2. 在`predict_with_model`函数中添加对应的预测逻辑
3. 在前端页面添加训练和预测按钮

### 调整模型参数
修改`gru_model_views.py`中的以下参数：
- `hidden_size`: 隐藏层大小
- `num_layers`: GRU层数
- `epochs`: 训练轮数
- `lr`: 学习率

### 改进模型性能
- 增加训练数据量
- 调整模型架构（增加隐藏层大小或层数）
- 使用更复杂的模型（如LSTM、Transformer）
- 添加特征工程

## 技术支持

如有问题或建议，请联系开发团队。
