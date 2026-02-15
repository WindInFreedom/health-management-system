import sys
print(f"Python版本: {sys.version}")

try:
    import tensorflow as tf
    print(f"TensorFlow版本: {tf.__version__}")
    print(f"TensorFlow路径: {tf.__file__}")
    
    from tensorflow import keras
    print(f"Keras版本: {keras.__version__}")
    
    from tensorflow.keras.models import load_model
    print("所有导入成功！")
    
    # 测试一个简单的操作
    a = tf.constant(1.0)
    b = tf.constant(2.0)
    c = a + b
    print(f"测试操作: 1.0 + 2.0 = {c.numpy()}")
    print("TensorFlow运行正常！")
except Exception as e:
    print(f"导入错误: {e}")
    import traceback
    traceback.print_exc()