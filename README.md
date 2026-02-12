# 健康管理系统 / Health Management System

一个基于 Vue.js（前端）和 Django REST Framework（后端）构建的综合性 Web 健康管理系统。该系统为用户提供健康指标追踪、趋势可视化、个性化健康报告评分以及未来健康指标预测等功能。

A comprehensive web-based health management system built with Vue.js (frontend) and Django REST Framework (backend). This system provides users with tools to track health metrics, visualize trends, receive personalized health reports with scoring, and forecast future health indicators.

## 🌟 功能特性 / Features

### 用户功能 / User Features
- **个人仪表板 / Personal Dashboard**：显示关键指标的健康状况概览 / Overview of health status with key metrics
- **健康记录管理 / Health Records Management**：追踪体重、血压、心率、血糖等指标 / Track weight, blood pressure, heart rate, blood glucose
- **预测分析 / Predictive Analytics**：使用时间序列分析预测健康指标趋势 / Forecast health metrics using time series analysis
- **综合健康报告 / Comprehensive Health Report**：
  - 多维度健康评分（0-100 分制）/ Multi-dimensional health scoring (0-100 scale)
  - 6 个关键健康维度的雷达图可视化 / Radar chart visualization of 6 key health dimensions
  - 基于评分的个性化建议 / Personalized suggestions based on scores
- **扩展追踪功能 / Extended Tracking**：
  - 用药记录（剂量、频率、日期）/ Medication logs (dosage, frequency, dates)
  - 睡眠追踪（时长、质量评分、趋势）/ Sleep tracking (duration, quality rating, trends)
  - 情绪指数（每日评分及趋势分析）/ Mood index (daily ratings with trend analysis)
- **个人档案 / Personal Profile**：年龄、性别、血型、身高、体重基准 / Age, gender, blood type, height, weight baseline
- **头像与账户管理 / Avatar & Account Management**：上传头像、修改密码 / Upload avatar, change password

### 管理员/医生功能 / Admin/Doctor Features
- 用户管理 / User management
- 健康统计概览 / Health statistics overview
- 访问所有用户健康数据 / Access to all user health data
- 健康预警和警报 / Health alerts and warnings

### 技术特性 / Technical Features
- 基于 JWT 的身份认证 / JWT-based authentication
- RESTful API 架构 / RESTful API architecture
- 响应式设计（支持移动端和桌面端）/ Responsive design (mobile & desktop)
- 使用 ECharts 实现实时数据可视化 / Real-time data visualization with ECharts
- 时间序列预测（ARIMA/ETS）/ Time series forecasting (ARIMA/ETS)
- 可配置的健康评分系统，基于临床范围 / Configurable health scoring with clinical ranges

## 🏗️ 系统架构 / Architecture

### 前端 / Frontend
- **框架 / Framework**：Vue 3（Composition API）
- **UI 库 / UI Library**：Element Plus
- **图表库 / Charts**：ECharts 5.6
- **状态管理 / State Management**：Pinia
- **路由 / Routing**：Vue Router 4
- **构建工具 / Build Tool**：Vite 4

### 后端 / Backend
- **框架 / Framework**：Django 4.2 + Django REST Framework
- **身份认证 / Authentication**：JWT（Simple JWT）
- **数据库 / Database**：SQLite（开发环境 / development）/ PostgreSQL（生产环境就绪 / production-ready）
- **数据分析 / Analytics**：statsmodels, pandas, numpy, scipy
- **图像处理 / Image Processing**：Pillow

## 📦 安装指南 / Installation

### 前置要求 / Prerequisites
- Python 3.10+
- Node.js 18+ 和 npm / and npm
- Git

### 后端设置 / Backend Setup

1. 克隆仓库 / Clone the repository：
```bash
git clone https://github.com/WindInFreedom/health-management-system.git
cd health-management-system/backend
```

2. 创建并激活虚拟环境 / Create and activate virtual environment：
```bash
python -m venv venv
source venv/bin/activate  # Windows 系统 / On Windows: venv\Scripts\activate
```

3. 安装依赖 / Install dependencies：
```bash
pip install -r requirements.txt
```

4. 运行数据库迁移 / Run migrations：
```bash
python manage.py migrate
```

5. 创建超级用户（可选）/ Create superuser (optional)：
```bash
python manage.py createsuperuser
```

6. 启动开发服务器 / Start development server：
```bash
python manage.py runserver
```

后端 API 将运行在 `http://localhost:8000/api/`

The backend API will be available at `http://localhost:8000/api/`

### 前端设置 / Frontend Setup

1. 进入前端目录 / Navigate to frontend directory：
```bash
cd ../frontend
```

2. 安装依赖 / Install dependencies：
```bash
npm install
```

3. 创建环境配置文件 / Create environment configuration：
```bash
cp .env.example .env.local
```

4. 编辑 `.env.local` 并设置后端地址 / Edit `.env.local` and set your backend URL：
```env
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

5. 启动开发服务器 / Start development server：
```bash
npm run dev
```

前端将运行在 `http://localhost:5173/`

The frontend will be available at `http://localhost:5173/`

## 🔑 环境变量 / Environment Variables

### 后端（可选）/ Backend (Optional)
在 `backend/` 目录下创建 `.env` 文件 / Create a `.env` file in `backend/` directory：
```env
SECRET_KEY=你的密钥 / your-secret-key-here
DEBUG=True
ALLOWED_HOSTS=localhost,127.0.0.1
CORS_ALLOWED_ORIGINS=http://localhost:5173,http://localhost:3000
```

### 前端 / Frontend
在 `frontend/` 目录下创建 `.env.local` 文件 / Create a `.env.local` file in `frontend/` directory：
```env
# API 配置 / API configuration
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

## 📚 API 文档 / API Documentation

### 身份认证 / Authentication
- `POST /api/auth/login/` - 用户登录 / User login
- `POST /api/auth/register/` - 用户注册 / User registration
- `POST /api/auth/change-password/` - 修改密码 / Change password

### 用户管理 / User Management
- `GET /api/users/me/` - 获取当前用户信息 / Get current user info
- `GET /api/profile/me/` - 获取/更新用户档案 / Get/update user profile

### 健康记录 / Health Records
- `GET /api/measurements/` - 列出测量记录 / List measurements
- `POST /api/measurements/` - 创建测量记录 / Create measurement
- `PUT /api/measurements/{id}/` - 更新测量记录 / Update measurement
- `DELETE /api/measurements/{id}/` - 删除测量记录 / Delete measurement

### 健康报告与分析 / Health Reporting & Analytics
- `GET /api/health-report/?days=30` - 生成包含评分的综合健康报告 / Generate comprehensive health report with scoring
- `GET /api/forecast/?metric=systolic&horizon=30` - 预测健康指标 / Forecast health metric

### 扩展追踪 / Extended Tracking
- `GET /api/medications/` - 列出用药记录 / List medication records
- `POST /api/medications/` - 创建用药记录 / Create medication record
- `GET /api/sleep-logs/` - 列出睡眠日志 / List sleep logs
- `POST /api/sleep-logs/` - 创建睡眠日志 / Create sleep log
- `GET /api/mood-logs/` - 列出情绪日志 / List mood logs
- `POST /api/mood-logs/` - 创建情绪日志 / Create mood log

### 健康评分维度 / Health Scoring Dimensions
健康报告评估 6 个关键维度 / The health report evaluates 6 key dimensions：
1. **BMI 指数 / BMI Index**（权重 / weight 20%）
2. **血压 / Blood Pressure**（权重 / weight 25%）
3. **心率 / Heart Rate**（权重 / weight 15%）
4. **血糖 / Blood Glucose**（权重 / weight 20%）
5. **睡眠质量 / Sleep Quality**（权重 / weight 10%）
6. **情绪指数 / Mood Index**（权重 / weight 10%）

每个维度根据临床范围和最佳值进行 0-100 分评分。

Each dimension is scored 0-100 based on clinical ranges and optimal values.

## 🧪 测试 / Testing

### 后端测试 / Backend Tests
```bash
cd backend
pytest
```

### 前端构建测试 / Frontend Build Test
```bash
cd frontend
npm run build
```

## 🚀 部署 / Deployment

### 生产环境构建 / Production Build

#### 后端 / Backend
```bash
cd backend
# 更新生产环境设置 / Update settings for production
python manage.py collectstatic
gunicorn health_management_system.wsgi:application
```

#### 前端 / Frontend
```bash
cd frontend
npm run build
# 将 dist/ 文件夹部署到 Web 服务器 / Deploy dist/ folder to web server
```

## 🛠️ 技术栈 / Technology Stack

| 组件 / Component | 技术 / Technology |
|------|------|
| 前端框架 / Frontend Framework | Vue 3 |
| UI 组件 / UI Components | Element Plus |
| 图表 / Charts | ECharts |
| 状态管理 / State Management | Pinia |
| HTTP 客户端 / HTTP Client | Axios |
| 后端框架 / Backend Framework | Django 4.2 |
| API 框架 / API Framework | Django REST Framework |
| 身份认证 / Authentication | JWT (djangorestframework-simplejwt) |
| 数据库 / Database | SQLite / PostgreSQL |
| 时间序列分析 / Time Series Analysis | statsmodels |
| 数据处理 / Data Processing | pandas, numpy |

## 📖 使用指南 / User Guide

### 快速开始 / Getting Started
1. 注册新账户或登录 / Register a new account or login
2. 完善个人档案（年龄、性别、血型、身高、体重）/ Complete your personal profile (age, gender, blood type, height, weight)
3. 开始记录健康测量数据 / Start recording health measurements
4. 在积累数据后查看健康报告（建议至少 5-10 次测量）/ View your health report after accumulating data (recommended: at least 5-10 measurements)

### 理解健康报告 / Understanding Your Health Report
- **评分 / Scores**：80-100 分（优秀 / Excellent）、60-79 分（良好 / Good）、<60 分（需要关注 / Needs Attention）
- **雷达图 / Radar Chart**：可视化展示 6 个维度的健康状况 / Visualizes your health across 6 dimensions
- **建议 / Suggestions**：基于评分的个性化健康建议 / Personalized recommendations based on your scores

### 使用预测功能 / Using Predictions
- 选择一个健康指标（如血压）/ Select a health metric (e.g., blood pressure)
- 启用"显示预测"开关 / Enable "Show Prediction" toggle
- 选择预测时间范围（7、14 或 30 天）/ Choose forecast horizon (7, 14, or 30 days)
- 查看带有置信区间的预测趋势 / View predicted trends with confidence intervals

## 🤝 贡献 / Contributing

欢迎贡献！请随时提交 Pull Request。

Contributions are welcome! Please feel free to submit a Pull Request.

## 📄 许可证 / License

本项目采用 MIT 许可证。

This project is licensed under the MIT License.

## 👥 作者 / Authors

- WindInFreedom - 初始工作 / Initial work

## 🙏 致谢 / Acknowledgments

- Element Plus 提供 UI 组件 / for the UI components
- ECharts 提供可视化功能 / for visualization
- Django REST Framework 提供 API 框架 / for the API
- statsmodels 提供预测能力 / for forecasting capabilities

## 📞 支持 / Support

如有问题或疑问，请在 GitHub 上提交 issue。

For issues and questions, please open an issue on GitHub.
