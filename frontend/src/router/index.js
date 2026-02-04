// 替换本地内容：扩展路由配置以支持新增页面
import { createRouter, createWebHashHistory } from 'vue-router'
import LoginSimple from '../views/LoginSimple.vue'
import Register from '../views/Register.vue'
import AdvancedDashboard from '../views/AdvancedDashboard.vue'
import EnhancedDoctorDashboard from '../views/EnhancedDoctorDashboard.vue'
import EnhancedAdminDashboard from '../views/EnhancedAdminDashboard.vue'
import MeasurementsList from '../views/MeasurementsList.vue'
import SimpleHealthReport from '../views/SimpleHealthReport.vue'
import EnhancedHealthReport from '../views/EnhancedHealthReport.vue'
import PersonalCenter from '../views/PersonalCenter.vue'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  // 登录页
  { path: '/', name: 'login', component: LoginSimple },
  { path: '/register', component: Register },

  // 入口：根据角色重定向到具体仪表盘
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
  
  // 具体的仪表盘页面
  { path: '/dashboard-user', name: 'dashboard-user', component: AdvancedDashboard, meta: { requiresAuth: true } },
  { path: '/dashboard-doctor', name: 'dashboard-doctor', component: EnhancedDoctorDashboard, meta: { requiresAuth: true } },
  { path: '/dashboard-admin', name: 'dashboard-admin', component: EnhancedAdminDashboard, meta: { requiresAuth: true } },

  // 健康记录
  { path: '/measurements', name: 'measurements', component: MeasurementsList, meta: { requiresAuth: true } },
  
  // 健康报告
  { path: '/health-report', name: 'health-report', component: SimpleHealthReport, meta: { requiresAuth: true } },
  { path: '/health-report-enhanced', name: 'health-report-enhanced', component: EnhancedHealthReport, meta: { requiresAuth: true } },
  
  // 替换本地内容：新增个人中心和档案管理路由
  { path: '/personal-center', name: 'personal-center', component: PersonalCenter, meta: { requiresAuth: true } },
  
  // TODO: 待实现的页面路由
  // { path: '/profile', name: 'profile', component: Profile, meta: { requiresAuth: true } },
  // { path: '/medications', name: 'medications', component: MedicationLogs, meta: { requiresAuth: true } },
  // { path: '/sleep-logs', name: 'sleep-logs', component: SleepLogs, meta: { requiresAuth: true } },
  // { path: '/mood-logs', name: 'mood-logs', component: MoodLogs, meta: { requiresAuth: true } },
  // { path: '/visualizations', name: 'visualizations', component: Visualizations, meta: { requiresAuth: true } },

  // 捕获未匹配的路径
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
