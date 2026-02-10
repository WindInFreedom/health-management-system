# 健康管理系统 - 前端

## 开发环境设置

### 1. 安装依赖

```bash
npm install
```

### 2. 配置环境变量

复制 `.env.example` 到 `.env.local` 并根据你的后端地址进行配置：

```bash
cp .env.example .env.local
```

编辑 `.env.local`：

```env
# 开发环境推荐使用 Vite 代理
VITE_API_BASE_URL=/api

# 后端地址（仅在开发环境使用代理时需要）
VITE_BACKEND_URL=http://localhost:8000
```

**注意：**
- 开发环境下，建议使用 Vite 代理，设置 `VITE_API_BASE_URL=/api`
- 生产环境或不使用代理时，设置 `VITE_API_BASE_URL` 为完整后端地址，例如：`http://your-backend-server.com/api`

### 3. 启动开发服务器

```bash
npm run dev
```

前端将在 `http://localhost:5173` 启动，所有 `/api` 请求将被代理到后端服务器。

### 4. 构建生产版本

```bash
npm run build
```

构建产物将输出到 `dist` 目录。

## API 配置说明

### 统一的 API 实例

所有 API 请求应通过 `src/utils/axios.js` 导出的统一 axios 实例进行：

```javascript
import api from '@/utils/axios.js'

// 示例：获取数据
const { data } = await api.get('/users/me/')

// 示例：提交数据
const { data } = await api.post('/auth/login/', {
  username: 'user',
  password: 'pass'
})
```

### 环境变量

- `VITE_API_BASE_URL`: API 基础地址，默认为 `/api`
- `VITE_BACKEND_URL`: 后端服务器地址，仅在开发环境代理时使用，默认为 `http://localhost:8000`

### Vite 代理配置

开发环境下，Vite 会自动将 `/api/*` 的请求代理到后端服务器，配置在 `vite.config.js` 中：

```javascript
proxy: {
  '/api': {
    target: env.VITE_BACKEND_URL || 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

## 工具函数

### 日期格式化

使用统一的日期格式化工具 `src/utils/date.js`：

```javascript
import { formatDate } from '@/utils/date.js'

const formattedDate = formatDate(new Date()) // 默认中文格式
const customDate = formatDate(new Date(), { year: 'numeric', month: 'long' })
```

## 项目结构

```
frontend/
├── src/
│   ├── components/      # 可复用组件
│   ├── stores/          # Pinia 状态管理
│   │   └── auth.js      # 认证状态
│   ├── utils/           # 工具函数
│   │   ├── axios.js     # 统一 API 实例
│   │   └── date.js      # 日期格式化
│   ├── views/           # 页面组件
│   │   └── _dev/        # 开发测试页面（生产环境不包含）
│   ├── router/          # 路由配置
│   ├── App.vue          # 根组件
│   └── main.js          # 入口文件
├── .env.example         # 环境变量示例
├── vite.config.js       # Vite 配置
└── package.json         # 依赖配置
```

## 常见问题

### 1. API 请求失败 CORS 错误

确保：
- 开发环境使用了 Vite 代理（`VITE_API_BASE_URL=/api`）
- 后端地址正确配置在 `.env.local` 的 `VITE_BACKEND_URL` 中
- 后端服务器已启动且可访问

### 2. 登录后 Token 未生效

检查：
- `stores/auth.js` 中的 token 是否正确保存到 localStorage
- axios 拦截器是否正确添加 Authorization header
- 后端是否正确验证 JWT token

### 3. 生产环境 API 请求失败

生产环境需要在 `.env.production` 或构建时设置正确的后端地址：

```env
VITE_API_BASE_URL=https://your-production-api.com/api
```

## 开发规范

1. **API 调用**：统一使用 `src/utils/axios.js` 导出的实例
2. **路径规范**：API 路径使用相对路径，不包含 `/api` 前缀（由 baseURL 自动添加）
3. **日期格式**：使用 `src/utils/date.js` 的 `formatDate` 函数
4. **测试文件**：开发测试页面放在 `src/views/_dev/` 目录下

## 更新日志

### 2024 最新版本
- ✅ 统一 API 配置，使用 `VITE_API_BASE_URL` 环境变量
- ✅ 删除重复的 `api.js` 文件，统一使用 `axios.js`
- ✅ 配置 Vite 代理，解决开发环境 CORS 问题
- ✅ 修复登录页硬编码 URL，统一使用 axios 实例
- ✅ 新增统一日期格式化工具 `date.js`
- ✅ 测试文件移至 `_dev` 目录
