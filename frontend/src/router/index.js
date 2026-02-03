import { createRouter, createWebHashHistory } from 'vue-router'
import LoginSimple from '../views/LoginSimple.vue'
import Register from '../views/Register.vue'
import AdvancedDashboard from '../views/AdvancedDashboard.vue'
import EnhancedDoctorDashboard from '../views/EnhancedDoctorDashboard.vue'
import EnhancedAdminDashboard from '../views/EnhancedAdminDashboard.vue'
import MeasurementsList from '../views/MeasurementsList.vue'
import SimpleHealthReport from '../views/SimpleHealthReport.vue'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  // 登录页
  { path: '/', name: 'login', component: LoginSimple },

  // 入口：根据角色重定向到具体仪表盘（保留以便直接访问 /dashboard）
  {
    path: '/dashboard',
    name: 'dashboard-entry',
    meta: { requiresAuth: true },
    beforeEnter: (to, from, next) => {
      const authStore = useAuthStore()
      const role = authStore.user?.role
      console.log('[router] /dashboard beforeEnter role =', role)
      if (role === 'admin') return next({ name: 'dashboard-admin' })
      if (role === 'doctor') return next({ name: 'dashboard-doctor' })
      return next({ name: 'dashboard-user' })
    }
  },
  { path: '/', component: LoginSimple },
  { path: '/register', component: Register },
  { path: '/dashboard', component: AdvancedDashboard, meta: { requiresAuth: true } },
  // 具体的仪表盘页面（命名路由）
  { path: '/dashboard-user', name: 'dashboard-user', component: AdvancedDashboard, meta: { requiresAuth: true } },
  { path: '/dashboard-doctor', name: 'dashboard-doctor', component: EnhancedDoctorDashboard, meta: { requiresAuth: true } },
  { path: '/dashboard-admin', name: 'dashboard-admin', component: EnhancedAdminDashboard, meta: { requiresAuth: true } },

  // 其他受保护页面
  { path: '/measurements', name: 'measurements', component: MeasurementsList, meta: { requiresAuth: true } },
  { path: '/health-report', name: 'health-report', component: SimpleHealthReport, meta: { requiresAuth: true } },

  // 捕获未匹配的路径，避免空白页
  { path: '/:pathMatch(.*)*', redirect: '/' }
]

const router = createRouter({
  history: createWebHashHistory(),
  routes
})

// 全局守卫：需要登录才能访问
router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  const hasToken = !!authStore.token
  console.log('[router] beforeEach from', from.fullPath, 'to', to.fullPath, 'hasToken =', hasToken)
  if (to.meta.requiresAuth && !hasToken) {
    next({ name: 'login' })
  } else {
    next()
  }
})

router.afterEach((to) => {
  console.log('[router] afterEach navigated to', to.fullPath)
})

export default router
