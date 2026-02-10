import pymysql

try:
    connection = pymysql.connect(
        host='localhost',
        port=3307,
        user='root',
        password='123456',
        charset='utf8mb4'
    )
    
    cursor = connection.cursor()
    
    cursor.execute("CREATE DATABASE IF NOT EXISTS health_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci")
    
    print("数据库 'health_management' 创建成功！")
    
    cursor.close()
    connection.close()
    
except Exception as e:
    print(f"创建数据库失败: {e}")
