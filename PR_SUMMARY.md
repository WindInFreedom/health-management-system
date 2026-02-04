# PR Summary: 统一前端 API 配置与调用方式

## 🎯 目标

统一前端 API 配置与调用方式，修复硬编码后端 URL，完善开发环境代理与环境变量，提升可维护性与本地化体验。

## 📋 问题背景

1. **重复的 API 封装**: `frontend/src/utils/axios.js` 与 `frontend/src/utils/api.js` 共存，环境变量命名不一致（`VITE_API_BASE` vs `VITE_API_BASE_URL`）
2. **硬编码后端 URL**: 登录页使用 `fetch` 直接调用 `http://127.0.0.1:8000/api/...`，绕过 axios 拦截器
3. **缺少开发代理**: 开发环境没有配置代理，容易遇到 CORS 问题
4. **重复代码**: 多个组件各自实现 `formatDate` 函数
5. **测试文件混乱**: 测试页面与正式代码混在一起

## ✅ 主要变更

### 1. 统一 API 配置 (`src/utils/axios.js`)
- ✅ 删除重复的 `api.js` 文件
- ✅ 使用统一环境变量 `VITE_API_BASE_URL`，默认值 `/api`
- ✅ 保留完整的 token 刷新逻辑
- ✅ 更新所有组件使用统一的 axios 实例

**变更前:**
```javascript
// 两个文件，环境变量不一致
import.meta.env.VITE_API_BASE  // axios.js
import.meta.env.VITE_API_BASE_URL  // api.js
```

**变更后:**
```javascript
// 统一使用一个实例
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'
```

### 2. 配置 Vite 开发代理 (`vite.config.js`)
- ✅ 添加 `/api` 代理配置
- ✅ 支持通过 `VITE_BACKEND_URL` 环境变量配置后端地址
- ✅ 解决开发环境 CORS 问题

```javascript
proxy: {
  '/api': {
    target: env.VITE_BACKEND_URL || 'http://localhost:8000',
    changeOrigin: true,
  }
}
```

### 3. 修复硬编码 URL
- ✅ `LoginSimple.vue`: 从 `fetch('http://127.0.0.1:8000/...')` 改为 `api.post('/auth/login/')`
- ✅ `Login.vue`: 同样改用 axios 实例
- ✅ `TestDashboard.vue`: 更新为使用 axios 实例
- ✅ `MeasurementsList.vue`: 更新导入和 API 路径

**变更前:**
```javascript
// 硬编码，绕过拦截器
fetch('http://127.0.0.1:8000/api/auth/login/', {...})
```

**变更后:**
```javascript
// 统一通过 axios 实例
const { data } = await api.post('/auth/login/', {...})
```

### 4. 创建统一工具函数
- ✅ `src/utils/date.js`: 统一日期格式化
- ✅ 支持可配置的 locale 参数

```javascript
export function formatDate(date, options = {}, locale = 'zh-CN') {
  // 统一的日期格式化逻辑
}
```

### 5. 测试文件管理
- ✅ 创建 `src/views/_dev/` 目录
- ✅ 移动测试文件到专用目录
  - `test.vue` → `views/_dev/test.vue`
  - `TestDashboard.vue` → `views/_dev/TestDashboard.vue`

### 6. 完善文档和配置
- ✅ 创建 `frontend/README.md` - 详细的开发指南
- ✅ 创建 `.env.example` - 环境变量配置示例
- ✅ 创建 `.gitignore` - 排除本地环境文件
- ✅ 删除不规范的 `frontend.env.development`

## 📁 文件变更统计

```
添加文件:
+ frontend/.env.example (环境变量示例)
+ frontend/.gitignore (Git 忽略规则)
+ frontend/README.md (开发文档)
+ frontend/src/utils/date.js (统一日期工具)
+ frontend/src/views/_dev/test.vue (测试页面)
+ frontend/src/views/_dev/TestDashboard.vue (测试仪表盘)

删除文件:
- frontend/frontend.env.development (命名不规范)
- frontend/src/utils/api.js (重复文件)
- frontend/src/test.vue (已移动)
- frontend/src/views/TestDashboard.vue (已移动)

修改文件:
~ frontend/vite.config.js (添加代理配置)
~ frontend/src/utils/axios.js (统一环境变量)
~ frontend/src/views/Login.vue (使用 axios)
~ frontend/src/views/LoginSimple.vue (使用 axios)
~ frontend/src/views/MeasurementsList.vue (更新导入)
```

## 🧪 验证结果

✅ **构建测试**: 通过
```bash
npm run build
✓ 2050 modules transformed.
✓ built in 11.00s
```

✅ **代码审查**: 通过并修复反馈
- 改进注释使其更具指导性
- 使 locale 参数可配置
- 移除不必要的 TODO

✅ **安全检查**: 通过
```
CodeQL Analysis: 0 alerts found
```

## 📚 使用指南

### 开发环境配置

1. 复制环境变量示例:
```bash
cp .env.example .env.local
```

2. 编辑 `.env.local`:
```env
VITE_API_BASE_URL=/api
VITE_BACKEND_URL=http://localhost:8000
```

3. 启动开发服务器:
```bash
npm run dev
```

### API 调用示例

```javascript
import api from '@/utils/axios.js'

// GET 请求
const { data } = await api.get('/users/me/')

// POST 请求
const { data } = await api.post('/auth/login/', {
  username: 'user',
  password: 'pass'
})
```

### 日期格式化

```javascript
import { formatDate } from '@/utils/date.js'

// 默认中文格式
formatDate(new Date())

// 自定义格式
formatDate(new Date(), { year: 'numeric', month: 'long' }, 'en-US')
```

## 🎉 验收标准

- ✅ 所有 API 调用均通过统一的 axios 实例
- ✅ 前端不再硬编码 `http://127.0.0.1:8000` 或 `http://localhost:8000`
- ✅ 开发环境可通过 Vite 代理正常访问后端（前端统一用 `/api` 前缀）
- ✅ 登录流程使用 axios 实例，支持统一的错误处理与令牌刷新逻辑
- ✅ 仓库新增 `.env.example`，开发者能按注释替换为本地实际后端地址
- ✅ 日期格式化统一为 `utils/date.js`
- ✅ 测试页面移至 `_dev` 目录

## 🔄 迁移指南

如果你正在使用旧版本的代码，需要进行以下更新：

1. **更新环境变量**: 将 `VITE_API_BASE` 改为 `VITE_API_BASE_URL`
2. **更新导入**: 将 `from '../utils/api'` 改为 `from '../utils/axios.js'`
3. **创建本地配置**: 根据 `.env.example` 创建 `.env.local`
4. **更新 API 路径**: 移除路径中的 `/api` 前缀（baseURL 会自动添加）

## 📝 注意事项

1. **环境变量文件**: `.env.local` 已在 `.gitignore` 中，不会被提交到版本控制
2. **代理配置**: 仅在开发环境（`npm run dev`）有效，生产环境需要在 `.env.production` 中配置完整后端地址
3. **登录跳转**: axios 拦截器中使用 `window.location.href` 是为了完全清除应用状态
4. **测试文件**: `_dev` 目录下的文件仅供开发测试，可以通过构建配置在生产环境排除

## 🚀 后续优化建议

1. 考虑添加 API 响应的类型定义（TypeScript）
2. 实现更细粒度的错误处理和用户提示
3. 添加 API 请求/响应的日志记录（开发环境）
4. 考虑使用 Pinia 插件持久化 token
5. 为生产环境添加构建时排除 `_dev` 目录的配置
