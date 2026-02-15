import sys
print(f"Python版本: {sys.version}")
print(f"Python路径: {sys.path}")

try:
    import tensorflow as tf
    print(f"TensorFlow版本: {tf.__version__}")
    print(f"TensorFlow路径: {tf.__file__}")
    
    from tensorflow import keras
    print(f"Keras版本: {keras.__version__}")
    
    from tensorflow.keras.models import load_model
    print("所有导入成功！")
except ImportError as e:
    print(f"导入错误: {e}")
except Exception as e:
    print(f"其他错误: {e}")