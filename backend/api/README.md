# FastAPI 微服务 API 文档

## 概述

健康管理系统 AI 微服务提供以下功能:
- **预测服务**: LSTM/Transformer 深度学习模型预测健康指标
- **风险评估**: 基于特征提取和机器学习的健康风险评估
- **AI 建议**: DeepSeek API 集成的智能健康建议

## 快速开始

### 1. 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env` 并配置:

```bash
cp .env.example .env
```

编辑 `.env` 文件，设置 DeepSeek API Key (可选):
```
DEEPSEEK_API_KEY=your_api_key_here
```

### 3. 启动服务

```bash
# 从 backend 目录运行
python api/main.py
```

或使用 uvicorn:
```bash
uvicorn api.main:app --host 0.0.0.0 --port 8001 --reload
```

### 4. 访问 API 文档

- Swagger UI: http://localhost:8001/api/v2/docs
- ReDoc: http://localhost:8001/api/v2/redoc
- OpenAPI JSON: http://localhost:8001/api/v2/openapi.json

## API 端点

### 健康检查

**GET** `/api/v2/health`

返回服务健康状态。

响应:
```json
{
  "status": "healthy",
  "timestamp": "2026-02-15T12:00:00",
  "version": "2.0.0"
}
```

---

### 预测服务

#### 1. 预测健康指标

**POST** `/api/v2/predict`

使用训练好的模型预测未来健康指标值。

请求体:
```json
{
  "user_id": 1,
  "metric": "blood_glucose",
  "days": 7,
  "model_type": "lstm",
  "confidence_level": 0.95
}
```

响应:
```json
{
  "success": true,
  "model_type": "lstm",
  "metric": "blood_glucose",
  "user_id": 1,
  "predictions": [5.6, 5.7, 5.8, ...],
  "confidence_interval": {
    "lower": [5.1, 5.2, ...],
    "upper": [6.1, 6.2, ...],
    "level": 0.95
  },
  "future_dates": ["2026-02-16", "2026-02-17", ...],
  "historical_backtest": {
    "actual": [...],
    "predicted": [...]
  },
  "metrics": {
    "MAE": 0.34,
    "RMSE": 0.45,
    "R2": 0.78,
    "MAPE": 6.2
  },
  "last_update": "2026-02-15T12:00:00"
}
```

#### 2. 训练模型

**POST** `/api/v2/train`

训练新的预测模型。

请求体:
```json
{
  "user_id": 1,
  "metric": "blood_glucose",
  "model_type": "lstm",
  "epochs": 100,
  "batch_size": 32,
  "seq_length": 14
}
```

响应:
```json
{
  "success": true,
  "model_type": "lstm",
  "metric": "blood_glucose",
  "user_id": 1,
  "metrics": {
    "MAE": 0.34,
    "RMSE": 0.45,
    "R2": 0.78,
    "MAPE": 6.2
  },
  "message": "模型训练成功！MAE: 0.3400, R²: 0.7800"
}
```

#### 3. 列出可用模型

**GET** `/api/v2/models/{user_id}`

获取用户所有可用的训练模型。

响应:
```json
{
  "success": true,
  "user_id": 1,
  "models": {
    "lstm": ["blood_glucose", "heart_rate", "systolic"],
    "transformer": ["blood_glucose"]
  }
}
```

#### 4. 获取模型信息

**GET** `/api/v2/model-info/{user_id}/{metric}?model_type=lstm`

获取特定模型的详细信息。

响应:
```json
{
  "success": true,
  "user_id": 1,
  "metric": "blood_glucose",
  "model_type": "lstm",
  "trained_at": "2026-02-15T10:00:00",
  "metrics": {
    "MAE": 0.34,
    "RMSE": 0.45,
    "R2": 0.78,
    "MAPE": 6.2
  },
  "seq_length": 14
}
```

---

### 风险评估

**POST** `/api/v2/risk-assessment`

评估用户健康风险等级。

请求体:
```json
{
  "user_id": 1,
  "metrics": ["blood_glucose", "heart_rate", "systolic", "diastolic", "weight_kg"],
  "time_window": 30
}
```

响应:
```json
{
  "success": true,
  "user_id": 1,
  "risk_level": "中风险",
  "risk_score": 0.65,
  "probabilities": {
    "低风险": 0.2,
    "中风险": 0.6,
    "高风险": 0.2
  },
  "key_factors": [
    {
      "factor": "systolic_high",
      "importance": 0.35,
      "description": "收缩压偏高"
    },
    {
      "factor": "blood_glucose_volatility",
      "importance": 0.25,
      "description": "blood_glucose波动较大"
    }
  ],
  "assessed_at": "2026-02-15T12:00:00"
}
```

---

### AI 建议

#### 1. 获取完整健康建议

**POST** `/api/v2/ai-advice`

基于用户信息和健康数据生成个性化建议。

请求体:
```json
{
  "user_id": 1,
  "user_profile": {
    "age": 35,
    "gender": "M",
    "height_cm": 175,
    "weight_kg": 78,
    "conditions": ["高血压"]
  },
  "recent_data": {
    "blood_glucose": [5.6, 5.8, 6.1, 5.9],
    "heart_rate": [72, 75, 78, 76],
    "systolic": [135, 138, 140, 136],
    "diastolic": [85, 87, 90, 86]
  },
  "risk_assessment": {
    "level": "中风险",
    "key_factors": ["血压偏高", "体重超标"]
  }
}
```

响应:
```json
{
  "success": true,
  "source": "mock",
  "analysis": "根据您最近的健康数据，整体状况良好...",
  "recommendations": [
    "监测血压变化，建议每天早晚各测量一次血压",
    "保持规律的作息时间，每天保证7-8小时睡眠",
    "适度运动，每周进行3-5次有氧运动，每次30分钟以上"
  ],
  "lifestyle_plan": {
    "diet": "建议低盐低脂饮食...",
    "exercise": "建议每周进行3-5次有氧运动...",
    "sleep": "保持规律作息..."
  },
  "medical_advice": "建议2周后复查血压...",
  "generated_at": "2026-02-15T12:00:00"
}
```

#### 2. 获取简单建议

**POST** `/api/v2/ai-advice/simple?metric=blood_glucose&value=6.5&risk_level=中风险`

获取单指标的简单建议。

#### 3. 分析趋势

**POST** `/api/v2/ai-advice/trend`

分析指标变化趋势。

请求体:
```json
{
  "metric": "blood_glucose",
  "trend_data": [5.6, 5.8, 6.1, 5.9, 6.0, 5.7, 5.8]
}
```

---

## 支持的指标

- `blood_glucose`: 血糖 (mmol/L)
- `heart_rate`: 心率 (bpm)
- `systolic`: 收缩压 (mmHg)
- `diastolic`: 舒张压 (mmHg)
- `weight_kg`: 体重 (kg)

## 支持的模型类型

- `lstm`: LSTM 深度学习模型
- `transformer`: Transformer 注意力机制模型

## 错误处理

所有错误响应格式:
```json
{
  "success": false,
  "error": "错误类型",
  "detail": "详细错误信息"
}
```

常见错误码:
- `400`: 请求参数错误
- `404`: 资源不存在（用户或模型）
- `500`: 服务器内部错误

## 注意事项

1. **数据要求**: 预测和风险评估至少需要 100 条历史数据
2. **模型训练**: 首次使用前需先训练模型
3. **API Key**: DeepSeek API 需要有效的 API Key，否则使用 Mock 模式
4. **缓存**: AI 建议默认启用缓存，缓存有效期 1 小时

## 开发建议

### 本地测试

使用 curl 测试 API:

```bash
# 健康检查
curl http://localhost:8001/api/v2/health

# 预测
curl -X POST http://localhost:8001/api/v2/predict \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "metric": "blood_glucose", "days": 7}'

# 风险评估
curl -X POST http://localhost:8001/api/v2/risk-assessment \
  -H "Content-Type: application/json" \
  -d '{"user_id": 1, "metrics": ["blood_glucose", "heart_rate"]}'
```

### 集成到前端

```javascript
// 预测示例
const predictHealthMetric = async (userId, metric, days) => {
  const response = await fetch('http://localhost:8001/api/v2/predict', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      user_id: userId,
      metric: metric,
      days: days,
      model_type: 'lstm'
    })
  });
  return await response.json();
};
```

## 性能优化

1. **模型缓存**: 模型加载后缓存在内存中
2. **结果缓存**: AI 建议结果缓存 1 小时
3. **批量处理**: 支持批量特征提取
4. **异步处理**: 所有端点都是异步的

## 安全建议

1. 生产环境使用 HTTPS
2. 添加身份验证（JWT）
3. 限流保护
4. 输入验证
5. 日志审计

---

**版本**: 2.0.0  
**更新日期**: 2026-02-15
