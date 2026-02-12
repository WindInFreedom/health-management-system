# 数据处理流程文档

本文档说明健康管理系统的数据预处理、清洗和验证流程。

## 概述

数据处理流程包括以下三个主要步骤：
1. **数据预处理** - 分析、标准化、异常检测、健康评分
2. **数据清洗** - 删除无效数据、修复缺失值、去重
3. **数据验证** - 完整性、一致性、合理性检查

## 工具脚本

### 1. 主入口脚本

**[data_pipeline.py](data_pipeline.py)** - 数据处理主入口

提供交互式菜单，可以执行所有数据处理操作：
- 数据预处理
- 数据清洗
- 数据验证
- 查看数据概览
- 修改数据
- 生成扩展数据

使用方法：
```bash
python data_pipeline.py
```

### 2. 数据预处理脚本

**[data_preprocessing.py](data_preprocessing.py)** - 数据预处理

功能：
- **数据分析**
  - 用户级别统计（体重、血压、血糖、心率）
  - 全局统计（最小值、最大值、平均值、中位数）

- **数据标准化**
  - 计算体重相对于基准值的变化百分比
  - 自动标记体重变化记录

- **异常检测**
  - 使用Z-score检测异常值（3倍标准差）
  - 检测超出正常范围的血压、血糖、心率
  - 自动标记异常记录

- **健康评分**
  - 体重评分（基于基准体重）
  - 血压评分（基于正常范围）
  - 血糖评分（基于正常范围）
  - 心率评分（基于正常范围）
  - 综合健康评分（0-100分）

使用方法：
```bash
python data_preprocessing.py
```

### 3. 数据清洗脚本

**[data_cleaning.py](data_cleaning.py)** - 数据清洗

功能：
- **清洗健康测量数据**
  - 删除无效体重（<=0 或 >300kg）
  - 删除无效收缩压（<50 或 >250）
  - 删除无效舒张压（<30 或 >150）
  - 删除无效血糖（<1 或 >30）
  - 删除无效心率（<30 或 >200）
  - 删除完全空的记录

- **清洗睡眠记录**
  - 删除无效睡眠时长（<60 或 >720分钟）
  - 修正睡眠质量评分（范围1-10）
  - 删除空记录

- **清洗心情记录**
  - 修正心情评分（范围1-10）
  - 删除空记录

- **删除重复记录**
  - 检测并删除完全重复的测量记录
  - 基于测量时间和数值判断重复

- **修复缺失值**
  - 使用最近的非空值填充缺失的体重
  - 使用最近的非空值填充缺失的心率
  - 保持数据连续性

- **验证数据一致性**
  - 检查时间顺序是否正确
  - 检测时间倒序异常

使用方法：
```bash
python data_cleaning.py
```

### 4. 数据验证脚本

**[data_validation.py](data_validation.py)** - 数据验证

功能：
- **验证健康测量数据**
  - 检查测量记录数量（至少100条）
  - 验证平均体重范围（30-200kg）
  - 验证平均收缩压范围（70-180）
  - 验证平均舒张压范围（40-120）
  - 验证平均血糖范围（2-20）
  - 验证平均心率范围（40-120）

- **验证睡眠记录**
  - 检查睡眠记录数量（至少100条）
  - 验证平均睡眠时长（4-10小时）
  - 验证睡眠质量评分（1-10）

- **验证心情记录**
  - 检查心情记录数量（至少100条）
  - 验证心情评分范围（1-10）

- **验证数据完整性**
  - 检查每个用户是否有测量数据
  - 检查每个用户是否有睡眠记录
  - 检查每个用户是否有心情记录
  - 标记数据不完整的用户

- **验证时间一致性**
  - 检查测量时间顺序是否正确
  - 检测时间倒序异常

使用方法：
```bash
python data_validation.py
```

## 数据处理流程

### 推荐的处理顺序

1. **数据验证** - 首先验证数据质量
   ```bash
   python data_validation.py
   ```

2. **数据清洗** - 清理无效和重复数据
   ```bash
   python data_cleaning.py
   ```

3. **数据预处理** - 分析和标准化数据
   ```bash
   python data_preprocessing.py
   ```

4. **查看结果** - 确认处理效果
   ```bash
   python show_data.py
   ```

### 一键执行所有流程

使用主脚本自动执行完整流程：
```bash
python data_pipeline.py
```

## 数据质量标准

### 健康测量数据

| 指标 | 正常范围 | 说明 |
|------|---------|------|
| 体重 | 30-200 kg | 成人正常体重范围 |
| 收缩压 | 70-180 mmHg | 正常血压范围 |
| 舒张压 | 40-120 mmHg | 正常血压范围 |
| 血糖 | 2-20 mmol/L | 正常血糖范围 |
| 心率 | 40-120 bpm | 正常心率范围 |

### 睡眠记录

| 指标 | 正常范围 | 说明 |
|------|---------|------|
| 睡眠时长 | 240-600 分钟 | 4-10小时 |
| 睡眠质量 | 1-10 | 评分范围 |

### 心情记录

| 指标 | 正常范围 | 说明 |
|------|---------|------|
| 心情评分 | 1-10 | 1=很差，10=很好 |

## 异常检测算法

### Z-score方法

用于检测异常值：
- 计算数据的平均值和标准差
- 计算每个数据点的Z-score
- Z-score = (值 - 平均值) / 标准差
- 当 |Z-score| > 3 时，标记为异常

### 基于规则的检测

使用医学标准检测异常：
- 血压：收缩压 > 180 或 < 70
- 血糖：> 15 或 < 3.5
- 心率：> 120 或 < 40

## 健康评分算法

### 体重评分
- 与基准体重比较
- 差异百分比 = |当前体重 - 基准体重| / 基准体重 × 100
- 评分 = max(0, 100 - 差异百分比)

### 血压评分
- 正常（<120/80）：100分
- 轻度升高（<140/90）：80分
- 明显升高（≥140/90）：60分

### 血糖评分
- 正常（<5.6）：100分
- 轻度升高（<7.0）：80分
- 明显升高（≥7.0）：60分

### 心率评分
- 正常（60-100）：100分
- 轻度异常（≤110）：80分
- 明显异常（>110）：60分

## 常见问题

### Q1: 数据预处理后数据变少了？

**A**: 这是正常的。数据预处理不会删除数据，只是分析和标记。如果数据减少，请检查数据清洗步骤。

### Q2: 如何恢复被删除的数据？

**A**: 数据清洗会删除无效数据，建议在清洗前备份数据库：
```bash
mysqldump -u root -p health_management > backup.sql
```

### Q3: 异常检测的阈值可以调整吗？

**A**: 可以。在 `data_preprocessing.py` 中修改 Z-score 阈值：
```python
if abs(z_score) > 3:  # 修改这个值
```

### Q4: 如何添加新的数据验证规则？

**A**: 在 `data_validation.py` 中添加新的验证逻辑：
```python
if avg_value < min_threshold or avg_value > max_threshold:
    print(f"  ✗ 错误: 平均值异常")
    self.validation_results['failed'] += 1
```

## 数据备份建议

### 定期备份

建议在执行数据清洗前备份数据：
```bash
# 备份整个数据库
mysqldump -u root -p123456 health_management > backup_$(date +%Y%m%d).sql

# 或使用Django的dumpdata命令
python manage.py dumpdata > backup.json
```

### 恢复数据

如果需要恢复数据：
```bash
# 从SQL恢复
mysql -u root -p123456 health_management < backup.sql

# 或使用Django的loaddata命令
python manage.py loaddata backup.json
```

## 性能优化建议

### 大数据量处理

如果数据量很大（>100万条），建议：
1. 使用批量操作
2. 添加数据库索引
3. 使用分页查询
4. 考虑使用异步任务

### 数据库优化

```sql
-- 添加索引
CREATE INDEX idx_user_measured_at ON measurements(user_id, measured_at);
CREATE INDEX idx_sleep_date ON sleep_logs(user_id, sleep_date);
CREATE INDEX idx_log_date ON mood_logs(user_id, log_date);
```

## 扩展功能

### 添加新的数据类型

如果需要添加新的数据类型（如运动记录、饮食记录）：
1. 在 `models.py` 中定义模型
2. 运行 `python manage.py makemigrations`
3. 运行 `python manage.py migrate`
4. 在数据处理脚本中添加相应的处理逻辑

### 自定义清洗规则

在 `data_cleaning.py` 中添加自定义规则：
```python
def clean_custom_field(self):
    for measurement in measurements:
        if measurement.custom_field:
            if not self._is_valid(measurement.custom_field):
                measurement.delete()
```

## 参考资料

- [Django 数据验证](https://docs.djangoproject.com/en/4.2/ref/validators/)
- [Python 数据清洗最佳实践](https://towardsdatascience.com/data-cleaning-in-python)
- [健康数据标准](https://www.who.int/guidelines/)

## 联系方式

如有问题或建议，请联系开发团队。
