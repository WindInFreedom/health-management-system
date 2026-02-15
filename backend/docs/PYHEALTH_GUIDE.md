# PyHealth 数据生成使用指南

## 概述

本模块使用 PyHealth 2.0 风格生成高质量医疗时间序列数据，支持生成符合医学标准的健康指标数据。

## 功能特性

- 生成10个用户 × 1000条记录的时间序列数据
- 包含完整的个人信息（姓名、年龄、性别、血型、身高等）
- 支持的健康指标：
  - 血糖 (blood_glucose): 3.9-6.1 mmol/L
  - 心率 (heart_rate): 60-100 bpm
  - 收缩压 (systolic): 90-120 mmHg
  - 舒张压 (diastolic): 60-80 mmHg
  - 体重 (weight_kg): 基于BMI计算
- 包含合理的异常值和疾病模拟（高血压、糖尿病）
- 自动导入MySQL数据库

## 使用方法

### 方法1: Django 管理命令（推荐）

```bash
# 使用默认参数生成数据
python manage.py generate_pyhealth_data

# 自定义参数
python manage.py generate_pyhealth_data --users 20 --records 500

# 只生成CSV，不导入数据库
python manage.py generate_pyhealth_data --no-import

# 指定输出目录
python manage.py generate_pyhealth_data --output-dir data/health_records

# 设置随机种子（用于可复现）
python manage.py generate_pyhealth_data --seed 123
```

### 方法2: 直接运行生成脚本

```bash
cd backend
python data_generation/pyhealth_generator.py
```

生成的CSV文件位于 `data_generation/output/`

### 方法3: 手动导入CSV到数据库

```bash
python data_generation/import_to_mysql.py [users_csv] [measurements_csv]
```

## 生成的数据结构

### 用户信息 (users.csv)

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户ID |
| username | str | 用户名 (user01-user10) |
| full_name | str | 中文姓名 |
| gender | str | 性别 (M/F) |
| age | int | 年龄 (18-80) |
| height_cm | float | 身高 (cm) |
| blood_type | str | 血型 (A/B/O/AB) |
| has_hypertension | bool | 是否高血压 |
| has_diabetes | bool | 是否糖尿病 |

### 测量数据 (measurements.csv)

| 字段 | 类型 | 说明 |
|------|------|------|
| user_id | int | 用户ID |
| username | str | 用户名 |
| measured_at | datetime | 测量时间 |
| blood_glucose | float | 血糖 (mmol/L) |
| heart_rate | int | 心率 (bpm) |
| systolic | int | 收缩压 (mmHg) |
| diastolic | int | 舒张压 (mmHg) |
| weight_kg | float | 体重 (kg) |

## 数据特点

### 真实性模拟

1. **年龄相关变化**: 年龄越大，血压和血糖基础值越高
2. **疾病模拟**: 
   - 高血压患者血压值整体偏高
   - 糖尿病患者血糖值整体偏高
3. **日常波动**: 
   - 血糖：餐前餐后差异
   - 血压：早晚差异
   - 心率：活动影响
4. **长期趋势**: 体重可能增加、减少或稳定

### 数据质量

- 符合医学正常范围
- 包含合理的异常值（约5-10%）
- 时间序列连续性好
- 适合训练机器学习模型

## 示例代码

### Python 脚本中使用

```python
from data_generation.pyhealth_generator import PyHealthDataGenerator

# 创建生成器
generator = PyHealthDataGenerator(
    num_users=10,
    records_per_user=1000,
    random_seed=42
)

# 生成数据
df_users, df_measurements = generator.generate_all_data()

# 保存到CSV
generator.save_to_csv(df_users, df_measurements, 'output')

# 使用生成的数据
print(f"生成了 {len(df_users)} 个用户")
print(f"生成了 {len(df_measurements)} 条记录")
print(df_measurements.head())
```

### 导入到数据库

```python
from data_generation.import_to_mysql import DataImporter

# 创建导入器
importer = DataImporter(
    users_csv='data_generation/output/users.csv',
    measurements_csv='data_generation/output/measurements.csv'
)

# 执行导入
importer.run()
```

## 常见问题

### Q: 数据生成需要多长时间？

A: 默认配置（10用户×1000记录）约需要10-30秒，主要取决于CPU性能。

### Q: 可以生成更多数据吗？

A: 可以，但建议单次不超过50用户×2000记录，否则可能内存不足。

### Q: 如何确保数据可复现？

A: 使用 `--seed` 参数设置相同的随机种子。

### Q: 导入数据库时会删除旧数据吗？

A: 是的，导入前会删除同用户名的旧记录。如需保留，请先备份。

### Q: 生成的数据可以用于生产环境吗？

A: 这是测试数据，仅用于开发和演示。生产环境请使用真实数据。

## 技术细节

### 数据生成算法

1. **用户生成**: 随机生成个人信息和基础生理指标
2. **时间序列生成**: 使用正态分布 + 时间因素 + 长期趋势
3. **异常值注入**: 基于医学阈值自动判断异常
4. **疾病模拟**: 调整基础值模拟慢性疾病影响

### 性能优化

- 使用 NumPy 向量化操作
- 批量数据库插入（batch_size=1000）
- DataFrame 优化的数据处理

## 扩展开发

### 添加新指标

编辑 `pyhealth_generator.py`，在 `generate_time_series_for_user` 方法中添加：

```python
# 5. 新指标 (例如: BMI)
bmi = weight_kg / (height_m ** 2)
record['bmi'] = round(bmi, 1)
```

### 自定义疾病模拟

修改 `generate_user_profile` 方法中的疾病概率：

```python
# 自定义高血压概率
has_hypertension = random.random() < (age_factor * 0.5)  # 增加概率
```

## 相关文档

- [模型训练文档](MODEL_TRAINING.md)
- [API 文档](../api/README.md)
- [数据库迁移指南](../MYSQL_MIGRATION.md)
