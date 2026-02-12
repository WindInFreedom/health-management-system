# MySQL 数据库迁移指南

本文档说明如何将健康管理系统从 SQLite 迁移到 MySQL 数据库。

## 迁移优势

- **更好的并发性能**：MySQL 支持多用户并发访问
- **生产环境就绪**：MySQL 是生产环境的标准选择
- **更好的数据管理**：提供更强大的数据管理和备份功能
- **可扩展性**：支持更大的数据量和更复杂的查询

## 前置要求

1. 安装 MySQL Server 8.0 或更高版本
2. 安装 Python 依赖包

## 安装步骤

### 1. 安装 MySQL 驱动

```bash
cd backend
pip install pymysql==1.1.0
```

**注意**：本项目使用 PyMySQL（纯 Python 实现），在 Windows 上安装更简单，无需编译 C 扩展。

PyMySQL 已在 `settings.py` 中配置为 MySQL 客户端，无需额外配置。

### 2. 创建 MySQL 数据库

登录 MySQL：

```bash
mysql -u root -p
```

创建数据库：

```sql
CREATE DATABASE health_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

创建专用数据库用户（推荐）：

```sql
CREATE USER 'health_user'@'localhost' IDENTIFIED BY 'your_secure_password';
GRANT ALL PRIVILEGES ON health_management.* TO 'health_user'@'localhost';
FLUSH PRIVILEGES;
```

### 3. 配置环境变量

创建 `.env` 文件（如果还没有）：

```bash
DB_NAME=health_management
DB_USER=health_user
DB_PASSWORD=your_secure_password
DB_HOST=localhost
DB_PORT=3306
```

或者直接修改 `settings.py` 中的默认值。

### 4. 数据迁移

#### 方案A：全新安装（推荐用于开发环境）

```bash
cd backend

# 运行数据库迁移
python manage.py migrate

# 创建超级用户
python manage.py createsuperuser

# 加载演示数据（可选）
python manage.py loaddata fixtures/demo_users.json
python manage.py loaddata fixtures/demo_measurements.json
```

#### 方案B：从 SQLite 迁移现有数据

1. 安装数据迁移工具：

```bash
pip install django-dbbackup
```

2. 从 SQLite 导出数据：

```bash
python manage.py dumpdata > backup.json
```

3. 修改 `settings.py` 为 MySQL 配置

4. 在 MySQL 中创建数据库（见步骤2）

5. 运行迁移：

```bash
python manage.py migrate
```

6. 导入数据：

```bash
python manage.py loaddata backup.json
```

## 验证安装

启动开发服务器：

```bash
python manage.py runserver
```

访问 http://127.0.0.1:8000/admin 确认数据库连接正常。

## 常见问题

### 1. PyMySQL 安装失败

**问题**：安装 `pymysql` 时报错

**解决方案**：
```bash
# 升级 pip
python -m pip install --upgrade pip

# 使用国内镜像源安装
pip install pymysql==1.1.0 -i https://pypi.tuna.tsinghua.edu.cn/simple
```

### 2. 字符集问题

**问题**：中文数据乱码

**解决方案**：确保数据库使用 `utf8mb4` 字符集：

```sql
ALTER DATABASE health_management CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
```

### 3. 连接被拒绝

**问题**：`Can't connect to MySQL server`

**解决方案**：
- 检查 MySQL 服务是否运行
- 检查用户名和密码是否正确
- 检查防火墙设置

### 4. 权限问题

**问题**：`Access denied for user`

**解决方案**：
```sql
GRANT ALL PRIVILEGES ON health_management.* TO 'your_user'@'localhost';
FLUSH PRIVILEGES;
```

## 生产环境配置

在生产环境中，建议：

1. 使用环境变量存储敏感信息
2. 配置数据库连接池
3. 启用慢查询日志
4. 定期备份数据库

### 连接池配置（可选）

在 `requirements.txt` 中添加：

```
django-db-connection-pool==1.2.0
```

在 `settings.py` 中配置：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT'),
        'OPTIONS': {
            'charset': 'utf8mb4',
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
        'CONN_MAX_AGE': 600,
        'POOL': {
            'SIZE': 10,
            'MAX_OVERFLOW': 10,
            'RECYCLE': 300,
        }
    }
}
```

## 回滚到 SQLite

如果需要回滚到 SQLite，修改 `settings.py`：

```python
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}
```

然后运行迁移：

```bash
python manage.py migrate
```

## 参考资料

- [Django MySQL 文档](https://docs.djangoproject.com/en/4.2/ref/databases/#mysql-notes)
- [mysqlclient 文档](https://github.com/PyMySQL/mysqlclient)
- [MySQL 官方文档](https://dev.mysql.com/doc/)
