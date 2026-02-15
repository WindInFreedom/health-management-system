"""
DeepSeek AI 顾问

集成 DeepSeek API 提供智能健康建议
支持缓存、错误处理和Mock模式

作者: Health Management System Team
日期: 2026-02-15
"""

import os
import json
import time
import hashlib
from typing import Dict, Optional
from datetime import datetime, timedelta

try:
    import openai
    from openai import OpenAI
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False
    print("警告: openai 库未安装，DeepSeek API 不可用")

from ai_services.prompt_templates import PromptTemplates


class DeepSeekAdvisor:
    """
    DeepSeek AI 健康顾问
    
    使用 DeepSeek API 生成个性化健康建议
    """
    
    # DeepSeek API 配置
    DEEPSEEK_API_BASE = "https://api.deepseek.com"
    DEEPSEEK_MODEL = "deepseek-chat"
    
    def __init__(self, api_key: Optional[str] = None, use_cache: bool = True, 
                 cache_ttl: int = 3600, mock_mode: bool = False):
        """
        初始化 DeepSeek 顾问
        
        Args:
            api_key: DeepSeek API Key (从环境变量读取: DEEPSEEK_API_KEY)
            use_cache: 是否使用缓存
            cache_ttl: 缓存有效期 (秒)
            mock_mode: 是否使用 Mock 模式（用于测试）
        """
        self.mock_mode = mock_mode
        self.use_cache = use_cache
        self.cache_ttl = cache_ttl
        self.cache = {}  # 简单的内存缓存
        
        if not mock_mode:
            # 从环境变量或参数获取 API Key
            self.api_key = api_key or os.getenv('DEEPSEEK_API_KEY')
            
            if not self.api_key:
                print("警告: 未设置 DEEPSEEK_API_KEY，将使用 Mock 模式")
                self.mock_mode = True
            elif not OPENAI_AVAILABLE:
                print("警告: openai 库不可用，将使用 Mock 模式")
                self.mock_mode = True
            else:
                # 初始化 OpenAI 客户端 (DeepSeek 兼容 OpenAI API)
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.DEEPSEEK_API_BASE
                )
    
    def _get_cache_key(self, prompt: str) -> str:
        """
        生成缓存键
        
        Args:
            prompt: 提示词
            
        Returns:
            缓存键 (MD5 hash)
        """
        return hashlib.md5(prompt.encode()).hexdigest()
    
    def _get_from_cache(self, cache_key: str) -> Optional[Dict]:
        """
        从缓存获取结果
        
        Args:
            cache_key: 缓存键
            
        Returns:
            缓存的结果或None
        """
        if not self.use_cache:
            return None
        
        if cache_key in self.cache:
            cached_item = self.cache[cache_key]
            
            # 检查是否过期
            if time.time() - cached_item['timestamp'] < self.cache_ttl:
                return cached_item['data']
            else:
                # 过期，删除
                del self.cache[cache_key]
        
        return None
    
    def _save_to_cache(self, cache_key: str, data: Dict):
        """
        保存到缓存
        
        Args:
            cache_key: 缓存键
            data: 数据
        """
        if self.use_cache:
            self.cache[cache_key] = {
                'data': data,
                'timestamp': time.time()
            }
    
    def _call_api(self, prompt: str, max_retries: int = 3, 
                  timeout: int = 30) -> Dict:
        """
        调用 DeepSeek API
        
        Args:
            prompt: 提示词
            max_retries: 最大重试次数
            timeout: 超时时间（秒）
            
        Returns:
            API 响应字典
        """
        if self.mock_mode:
            return self._mock_response(prompt)
        
        # 检查缓存
        cache_key = self._get_cache_key(prompt)
        cached_result = self._get_from_cache(cache_key)
        
        if cached_result is not None:
            print("使用缓存结果")
            return cached_result
        
        # 调用 API
        for attempt in range(max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.DEEPSEEK_MODEL,
                    messages=[
                        {"role": "system", "content": "你是一位专业的健康顾问。"},
                        {"role": "user", "content": prompt}
                    ],
                    temperature=0.7,
                    max_tokens=2000,
                    timeout=timeout
                )
                
                # 解析响应
                content = response.choices[0].message.content
                
                # 尝试解析为 JSON
                try:
                    result = json.loads(content)
                except json.JSONDecodeError:
                    # 如果不是 JSON，包装成字典
                    result = {
                        'raw_response': content,
                        'success': True
                    }
                
                result['success'] = True
                result['source'] = 'api'
                
                # 保存到缓存
                self._save_to_cache(cache_key, result)
                
                return result
                
            except openai.APITimeoutError:
                print(f"API 超时 (尝试 {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': 'API 超时',
                        'fallback': self._mock_response(prompt)
                    }
                time.sleep(2 ** attempt)  # 指数退避
                
            except openai.RateLimitError:
                print(f"API 限流 (尝试 {attempt + 1}/{max_retries})")
                if attempt == max_retries - 1:
                    return {
                        'success': False,
                        'error': 'API 限流',
                        'fallback': self._mock_response(prompt)
                    }
                time.sleep(5 ** attempt)
                
            except Exception as e:
                print(f"API 错误: {str(e)}")
                return {
                    'success': False,
                    'error': str(e),
                    'fallback': self._mock_response(prompt)
                }
        
        return {
            'success': False,
            'error': '超过最大重试次数',
            'fallback': self._mock_response(prompt)
        }
    
    def _mock_response(self, prompt: str) -> Dict:
        """
        生成 Mock 响应（用于测试和 API 不可用时）
        
        Args:
            prompt: 提示词
            
        Returns:
            Mock 响应字典
        """
        # 简单的规则based响应
        response = {
            'success': True,
            'source': 'mock',
            'analysis': '根据您最近的健康数据，整体状况良好。部分指标略有波动，建议持续监测。',
            'recommendations': [
                '保持规律的作息时间，每天保证7-8小时睡眠',
                '适度运动，每周进行3-5次有氧运动，每次30分钟以上',
                '均衡饮食，控制盐分摄入，多吃新鲜蔬菜水果',
                '定期测量并记录健康数据，及时发现异常变化',
                '保持良好心态，避免过度焦虑和压力'
            ],
            'lifestyle_plan': {
                'diet': '建议低盐低脂饮食，每日盐分摄入不超过6克。多吃富含膳食纤维的食物如燕麦、全麦面包、豆类等。适量摄入优质蛋白，如鱼肉、鸡胸肉、豆腐等。',
                'exercise': '建议每周进行3-5次有氧运动，如快走、慢跑、游泳、骑车等，每次30-45分钟。另外可以配合一些力量训练，如哑铃、深蹲等，增强肌肉力量。',
                'sleep': '保持规律作息，建议晚上10-11点入睡，早上6-7点起床，保证每天7-8小时的睡眠时间。睡前避免使用电子设备，保持卧室安静舒适。'
            },
            'medical_advice': '目前数据无明显异常，建议每3个月进行一次常规体检。如出现持续不适症状，请及时就医。'
        }
        
        # 根据提示词内容调整响应
        if '高血压' in prompt or '血压' in prompt:
            response['recommendations'].insert(0, '监测血压变化，建议每天早晚各测量一次血压')
            response['medical_advice'] = '建议2周后复查血压。如血压持续偏高（≥140/90 mmHg），请到心血管科就诊。'
        
        if '糖尿病' in prompt or '血糖' in prompt:
            response['recommendations'].insert(0, '控制碳水化合物摄入，避免高糖食物')
            response['medical_advice'] = '建议定期检测空腹血糖和糖化血红蛋白。如血糖控制不佳，请到内分泌科就诊。'
        
        return response
    
    def get_health_advice(self, user_profile: Dict, recent_data: Dict, 
                         risk_assessment: Dict) -> Dict:
        """
        获取健康建议
        
        Args:
            user_profile: 用户个人信息
            recent_data: 最近健康数据
            risk_assessment: 风险评估结果
            
        Returns:
            健康建议字典
        """
        # 生成提示词
        prompt = PromptTemplates.get_health_advice_prompt(
            user_profile, recent_data, risk_assessment
        )
        
        # 调用 API
        result = self._call_api(prompt)
        
        # 如果 API 失败但有 fallback，使用 fallback
        if not result.get('success') and 'fallback' in result:
            result = result['fallback']
        
        # 添加时间戳
        result['generated_at'] = datetime.now().isoformat()
        
        return result
    
    def get_simple_advice(self, metric: str, value: float, risk_level: str) -> Dict:
        """
        获取简单的单指标建议
        
        Args:
            metric: 指标名称
            value: 指标值
            risk_level: 风险等级
            
        Returns:
            建议字典
        """
        prompt = PromptTemplates.get_simple_advice_prompt(metric, value, risk_level)
        result = self._call_api(prompt)
        
        if not result.get('success') and 'fallback' in result:
            result = result['fallback']
        
        result['generated_at'] = datetime.now().isoformat()
        
        return result
    
    def analyze_trend(self, metric: str, trend_data: list) -> Dict:
        """
        分析指标趋势
        
        Args:
            metric: 指标名称
            trend_data: 趋势数据列表
            
        Returns:
            分析结果字典
        """
        prompt = PromptTemplates.get_trend_analysis_prompt(metric, trend_data)
        result = self._call_api(prompt)
        
        if not result.get('success') and 'fallback' in result:
            result = result['fallback']
        
        result['generated_at'] = datetime.now().isoformat()
        
        return result


if __name__ == '__main__':
    print("DeepSeek AI 顾问测试")
    print("=" * 70)
    
    # 创建顾问实例 (Mock 模式)
    advisor = DeepSeekAdvisor(mock_mode=True)
    
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
    
    # 获取健康建议
    advice = advisor.get_health_advice(user_profile, recent_data, risk_assessment)
    
    print("\n健康建议:")
    print(json.dumps(advice, indent=2, ensure_ascii=False))
    print("\n" + "=" * 70)
