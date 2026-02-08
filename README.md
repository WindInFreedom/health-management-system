# 健康管理系统

一个基于 Vue.js（前端）和 Django REST Framework（后端)构建的综合性 Web 健康管理系统。该系统为用户提供健康指标追踪、趋势可视化、个性化健康报告评分以及未来健康指标预测等功能。

## 🌟 功能特性

### 用户功能
- **个人仪表板**：显示关键指标的健康状况概览
- **健康记录管理**：追踪体重、血压、心率、血糖等指标
- **预测分析**：使用时间序列分析预测健康指标趋势
- **综合健康报告**：
  - 多维度健康评分（0-100 分制）
  - 6 个关键健康维度的雷达图可视化
  - 基于评分的个性化建议
- **扩展追踪功能**：
  - 用药记录（剂量、频率、日期）
  - 睡眠追踪（时长、质量评分、趋势）
  - 情绪指数（每日评分及趋势分析）
- **个人档案**：年龄、性别、血型、身高、体重基准
- **头像与账户管理**：上传头像、修改密码

### 管理员/医生功能
- 用户管理
- 健康统计概览
- 访问所有用户健康数据
- 健康预警和警报

### 技术特性
- 基于 JWT 的身份认证
- RESTful API 架构
- 响应式设计（支持移动端和桌面端）
- 使用 ECharts 实现实时数据可视化
- 时间序列预测（ARIMA/ETS）
- 可配置的健康评分系统，基于临床范围

## 🏗️ 系统架构

### 前端
- **框架**：Vue 3（Composition API）
- **UI 库**：Element Plus
- **图表库**：ECharts 5.6
- **状态管理**：Pinia
- **路由**：Vue Router 4
- **构建工具**：Vite 4

### 后端
- **框架**：Django 4.2 + Django REST Framework
- **身份认证**：JWT（Simple JWT）
- **数据库**：SQLite（开发环境）/ PostgreSQL（生产环境就绪）
- **数据分析**：statsmodels, pandas, numpy, scipy
- **图像处理**：Pillow

## 📦 安装指南

### 前置要求
- Python 3.10+
- Node.js 18+ 和 npm
- Git

### 后端设置

1. 克隆仓库：
```bash
git clone https://github.com/WindInFreedom/health-management-system.git
cd health-management-system/backend
```

2. 创建并激活虚拟环境：
```bash
python -m venv venv
source venv/bin/activate  # Windows 系统: venv\Scripts\activate
```

3. 安装依赖：
```bash
pip install -r requirements.txt
```

4. 运行数据库迁移：
```bash
python manage.py migrate
```

5. 创建超级用户（可选）：
```bash
python manage.py createsuperuser
```

6. 启动开发服务器：
```bash
python manage.py runserver
```

后端 API 将运行在 `http://localhost:8000/api/`

### 前端设置

1. 进入前端目录：
```bash
cd ../frontend
```

2. 安装依赖：
```bash
npm install
```

3. 创建环境配置文件：
```bash
cp .env.example .env.local
```

4. 编辑 `.env.local` 并设置后端地址：
```env
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

5. 启动开发服务器：
```bash
npm run dev
```

前端将运行在 `http://localhost:5173/`

## 🔑 环境变量

### 后端（可选）
在 `backend/` 目录下创建 `.env` 文件：
```env
SECRET_KEY=你的密钥
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 前端
在 `frontend/` 目录下创建 `.env.local` 文件：
```env
# API 配置
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

## 📚 API 文档

### 身份认证
- `POST /api/auth/login/` - 用户登录
- `POST /api/auth/register/` - 用户注册
- `POST /api/auth/change-password/` - 修改密码

### 用户管理
- `GET /api/users/me/` - 获取当前用户信息
- `GET /api/profile/me/` - 获取/更新用户档案

### 健康记录
- `GET /api/measurements/` - 列出测量记录
- `POST /api/measurements/` - 创建测量记录
- `PUT /api/measurements/{id}/` - 更新测量记录
- `DELETE /api/measurements/{id}/` - 删除测量记录

### 健康报告与分析
- `GET /api/health-report/?days=30` - 生成包含评分的综合健康报告
- `GET /api/forecast/?metric=systolic&horizon=30` - 预测健康指标

### 扩展追踪
- `GET /api/medications/` - 列出用药记录
- `POST /api/medications/` - 创建用药记录
- `GET /api/sleep-logs/` - 列出睡眠日志
- `POST /api/sleep-logs/` - 创建睡眠日志
- `GET /api/mood-logs/` - 列出情绪日志
- `POST /api/mood-logs/` - 创建情绪日志

### 健康评分维度
健康报告评估 6 个关键维度：
1. **BMI 指数**（权重 20%）
2. **血压**（权重 25%）
3. **心率**（权重 15%）
4. **血糖**（权重 20%）
5. **睡眠质量**（权重 10%）
6. **情绪指数**（权重 10%）

每个维度根据临床范围和最佳值进行 0-100 分评分。

## 🧪 测试

### 后端测试
```bash
cd backend
pytest
```

### 前端构建测试
```bash
cd frontend
npm run build
```

## 🚀 部署

### 生产环境构建

#### 后端
```bash
cd backend
# 更新生产环境设置
python manage.py collectstatic
gunicorn health_management_system.wsgi:application
```

#### 前端
```bash
cd frontend
npm run build
# 将 dist/ 文件夹部署到 Web 服务器
```

## 🛠️ 技术栈

| 组件 | 技术 |
|------|------|
| 前端框架 | Vue 3 |
| UI 组件 | Element Plus |
| 图表 | ECharts |
| 状态管理 | Pinia |
| HTTP 客户端 | Axios |
| 后端框架 | Django 4.2 |
| API 框架 | Django REST Framework |
| 身份认证 | JWT (djangorestframework-simplejwt) |
| 数据库 | SQLite / PostgreSQL |
| 时间序列分析 | statsmodels |
| 数据处理 | pandas, numpy |

## 📖 使用指南

### 快速开始
1. 注册新账户或登录
2. 完善个人档案（年龄、性别、血型、身高、体重）
3. 开始记录健康测量数据
4. 在积累数据后查看健康报告（建议至少 5-10 次测量）

### 理解健康报告
- **评分**：80-100 分（优秀）、60-79 分（良好）、<60 分（需要关注）
- **雷达图**：可视化展示 6 个维度的健康状况
- **建议**：基于评分的个性化健康建议

### 使用预测功能
- 选择一个健康指标（如血压）
- 启用"显示预测"开关
- 选择预测时间范围（7、14 或 30 天）
- 查看带有置信区间的预测趋势

## 🤝 贡献

欢迎贡献！请随时提交 Pull Request。

## 📄 许可证

本项目采用 MIT 许可证。

## 👥 作者

- WindInFreedom - 初始工作

## 🙏 致谢

- Element Plus 提供 UI 组件
- ECharts 提供可视化功能
- Django REST Framework 提供 API 框架
- statsmodels 提供预测能力

## 📞 支持

如有问题或疑问，请在 GitHub 上提交 issue。
