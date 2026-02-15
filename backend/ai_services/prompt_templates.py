"""
健康建议提示词模板

为 DeepSeek API 提供专业的健康咨询提示词

作者: Health Management System Team
日期: 2026-02-15
"""

from typing import Dict, List


class PromptTemplates:
    """健康建议提示词模板"""
    
    @staticmethod
    def get_health_advice_prompt(user_profile: Dict, recent_data: Dict, 
                                 risk_assessment: Dict) -> str:
        """
        生成健康建议提示词
        
        Args:
            user_profile: 用户个人信息
            recent_data: 最近健康数据
            risk_assessment: 风险评估结果
            
        Returns:
            提示词字符串
        """
        # 构建用户基本信息
        age = user_profile.get('age', '未知')
        gender = '男性' if user_profile.get('gender') == 'M' else '女性'
        height = user_profile.get('height_cm', '未知')
        weight = user_profile.get('weight_kg', '未知')
        conditions = user_profile.get('conditions', [])
        
        conditions_str = '、'.join(conditions) if conditions else '无已知疾病'
        
        # 构建健康数据摘要
        data_summary = []
        if 'blood_glucose' in recent_data:
            values = recent_data['blood_glucose']
            avg = sum(values) / len(values) if values else 0
            data_summary.append(f"血糖: 平均 {avg:.1f} mmol/L")
        
        if 'heart_rate' in recent_data:
            values = recent_data['heart_rate']
            avg = sum(values) / len(values) if values else 0
            data_summary.append(f"心率: 平均 {avg:.0f} bpm")
        
        if 'systolic' in recent_data and 'diastolic' in recent_data:
            sys_values = recent_data['systolic']
            dia_values = recent_data['diastolic']
            sys_avg = sum(sys_values) / len(sys_values) if sys_values else 0
            dia_avg = sum(dia_values) / len(dia_values) if dia_values else 0
            data_summary.append(f"血压: 平均 {sys_avg:.0f}/{dia_avg:.0f} mmHg")
        
        data_summary_str = '，'.join(data_summary)
        
        # 构建风险评估信息
        risk_level = risk_assessment.get('level', '未知')
        key_factors = risk_assessment.get('key_factors', [])
        factors_str = '、'.join(key_factors) if key_factors else '无明显风险因素'
        
        # 构建提示词
        prompt = f"""你是一位专业的健康顾问，拥有丰富的医学知识和临床经验。请根据以下用户的健康数据和风险评估结果，提供个性化的健康建议。

【用户基本信息】
- 年龄: {age}岁
- 性别: {gender}
- 身高: {height} cm
- 体重: {weight} kg
- 既往病史: {conditions_str}

【最近健康数据（近7天）】
{data_summary_str}

【风险评估结果】
- 风险等级: {risk_level}
- 主要风险因素: {factors_str}

【请提供以下内容】

1. 当前健康状况分析（2-3句话）
   - 客观分析用户当前的健康状态
   - 指出需要关注的重点指标

2. 针对高风险因素的具体建议（3-5条）
   - 每条建议要具体、可执行
   - 包含明确的数量或时间要求
   - 避免泛泛而谈

3. 生活方式改善计划
   - 饮食建议: 具体的饮食原则和推荐食物
   - 运动建议: 运动类型、频率、时长
   - 作息建议: 睡眠时间、休息安排

4. 就医建议（如有必要）
   - 是否需要就医
   - 建议复查的时间
   - 需要咨询的专科

【重要要求】
- 语言通俗易懂，避免过多医学术语
- 建议具体可执行，避免泛泛而谈  
- 语气温和鼓励，避免引起焦虑
- 如果数据正常，也要给予肯定并提供预防性建议
- 不要包含任何XML标签或特殊格式符号，使用纯文本

请以JSON格式返回，包含以下字段:
{{
  "analysis": "当前健康状况分析",
  "recommendations": ["具体建议1", "具体建议2", ...],
  "lifestyle_plan": {{
    "diet": "饮食建议",
    "exercise": "运动建议",
    "sleep": "作息建议"
  }},
  "medical_advice": "就医建议（如无需就医则说明无需就医）"
}}
"""
        
        return prompt
    
    @staticmethod
    def get_simple_advice_prompt(metric: str, value: float, risk_level: str) -> str:
        """
        生成简单的单指标建议提示词
        
        Args:
            metric: 指标名称
            value: 指标值
            risk_level: 风险等级
            
        Returns:
            提示词字符串
        """
        metric_names = {
            'blood_glucose': '血糖',
            'heart_rate': '心率',
            'systolic': '收缩压',
            'diastolic': '舒张压',
            'weight_kg': '体重'
        }
        
        metric_cn = metric_names.get(metric, metric)
        
        prompt = f"""作为一位健康顾问，请针对用户的{metric_cn}指标提供简短的建议。

【指标信息】
- 指标: {metric_cn}
- 当前值: {value}
- 风险等级: {risk_level}

请提供：
1. 简短评价（1句话）
2. 2-3条具体建议

要求：通俗易懂，具体可行，温和鼓励。

请以JSON格式返回:
{{
  "comment": "简短评价",
  "tips": ["建议1", "建议2", "建议3"]
}}
"""
        
        return prompt
    
    @staticmethod
    def get_trend_analysis_prompt(metric: str, trend_data: List[float]) -> str:
        """
        生成趋势分析提示词
        
        Args:
            metric: 指标名称
            trend_data: 趋势数据列表
            
        Returns:
            提示词字符串
        """
        metric_names = {
            'blood_glucose': '血糖',
            'heart_rate': '心率',
            'systolic': '收缩压',
            'diastolic': '舒张压',
            'weight_kg': '体重'
        }
        
        metric_cn = metric_names.get(metric, metric)
        
        # 计算趋势统计
        avg = sum(trend_data) / len(trend_data) if trend_data else 0
        max_val = max(trend_data) if trend_data else 0
        min_val = min(trend_data) if trend_data else 0
        
        prompt = f"""请分析用户最近的{metric_cn}变化趋势。

【趋势数据（最近{len(trend_data)}天）】
- 平均值: {avg:.2f}
- 最高值: {max_val:.2f}
- 最低值: {min_val:.2f}
- 数据序列: {', '.join([f'{v:.1f}' for v in trend_data[:10]])}...

请提供：
1. 趋势判断（上升/下降/稳定）
2. 趋势评价（是否健康）
3. 调整建议（2-3条）

请以JSON格式返回:
{{
  "trend": "趋势判断",
  "evaluation": "趋势评价",
  "suggestions": ["建议1", "建议2"]
}}
"""
        
        return prompt


if __name__ == '__main__':
    # 测试提示词生成
    print("健康建议提示词模板测试")
    print("=" * 70)
    
    # 测试数据
    user_profile = {
        'age': 35,
        'gender': 'M',
        'height_cm': 175,
        'weight_kg': 78,
        'conditions': ['高血压']
    }
    
    recent_data = {
        'blood_glucose': [5.6, 5.8, 6.1, 5.9, 6.0, 5.7, 5.8],
        'heart_rate': [72, 75, 78, 76, 74, 73, 75],
        'systolic': [135, 138, 140, 136, 137, 139, 138],
        'diastolic': [85, 87, 90, 86, 88, 89, 87]
    }
    
    risk_assessment = {
        'level': '中风险',
        'key_factors': ['血压偏高', '体重超标']
    }
    
    # 生成提示词
    prompt = PromptTemplates.get_health_advice_prompt(
        user_profile, recent_data, risk_assessment
    )
    
    print(prompt)
    print("\n" + "=" * 70)
