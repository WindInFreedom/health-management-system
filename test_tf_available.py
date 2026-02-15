import sys
import os

# 添加项目路径
sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))

try:
    from measurements.lgb_model_views import TF_AVAILABLE, tf, keras, load_model
    print(f"TF_AVAILABLE: {TF_AVAILABLE}")
    
    if TF_AVAILABLE:
        print(f"TensorFlow版本: {tf.__version__}")
        print(f"Keras版本: {keras.__version__}")
        print("load_model函数: 可用")
    else:
        print("TensorFlow不可用")
        print(f"tf变量: {tf}")
        print(f"keras变量: {keras}")
        print(f"load_model变量: {load_model}")
        
        # 尝试直接导入
        try:
            import tensorflow as tf
            print(f"直接导入TensorFlow版本: {tf.__version__}")
        except Exception as e:
            print(f"直接导入错误: {e}")
            
            # 检查具体的错误类型
            import traceback
            traceback.print_exc()
            
except Exception as e:
    print(f"导入模块错误: {e}")
    import traceback
    traceback.print_exc()