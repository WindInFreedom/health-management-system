// 替换本地内容：扩展路由配置以支持新增页面
import { createRouter, createWebHashHistory } from 'vue-router'
import LoginSimple from '../views/LoginSimple.vue'
import Register from '../views/Register.vue'
import DashboardLayout from '../views/DashboardLayout.vue'
import AdvancedDashboard from '../views/AdvancedDashboard.vue'
import EnhancedDoctorDashboard from '../views/EnhancedDoctorDashboard.vue'
import EnhancedAdminDashboard from '../views/EnhancedAdminDashboard.vue'
import MeasurementsList from '../views/MeasurementsList.vue'
import MeasurementsEnhanced from '../views/MeasurementsEnhanced.vue'
import SimpleHealthReport from '../views/SimpleHealthReport.vue'
import HealthReportNew from '../views/HealthReportNew.vue'
import PersonalCenter from '../views/PersonalCenter.vue'
import PersonalProfile from '../views/PersonalProfile.vue'
import MedicationLogs from '../views/MedicationLogs.vue'
import SleepLogs from '../views/SleepLogs.vue'
import MoodLogs from '../views/MoodLogs.vue'
import { useAuthStore } from '../stores/auth.js'

const routes = [
  // 登录页
  { path: '/', name: 'login', component: LoginSimple },
  { path: '/register', name: 'register', component: Register },

  // Dashboard with layout and nested routes
  {
    path: '/',
    component: DashboardLayout,
    meta: { requiresAuth: true },
    children: [
      {
        path: 'dashboard',
        name: 'dashboard-entry',
        beforeEnter: (to, from, next) => {
          const authStore = useAuthStore()
          const role = authStore.user?.role
          console.log('[router] /dashboard beforeEnter role =', role)
          if (role === 'admin') return next({ name: 'dashboard-admin' })
          if (role === 'doctor') return next({ name: 'dashboard-doctor' })
          return next({ name: 'dashboard-user' })
        }
      },
      { path: 'dashboard-user', name: 'dashboard-user', component: AdvancedDashboard },
      { path: 'dashboard-doctor', name: 'dashboard-doctor', component: EnhancedDoctorDashboard },
      { path: 'dashboard-admin', name: 'dashboard-admin', component: EnhancedAdminDashboard },
      { path: 'personal-center', name: 'personal-center', component: PersonalCenter },
      { path: 'profile', name: 'profile', component: PersonalProfile },
      { path: 'measurements', name: 'measurements', component: MeasurementsEnhanced },
      { path: 'measurements-list', name: 'measurements-list', component: MeasurementsList },
      { path: 'health-report', name: 'health-report', component: HealthReportNew },
      { path: 'health-report-old', name: 'health-report-old', component: SimpleHealthReport },
      { path: 'medications', name: 'medications', component: MedicationLogs },
      { path: 'sleep-logs', name: 'sleep-logs', component: SleepLogs },
      { path: 'mood-logs', name: 'mood-logs', component: MoodLogs },
    ]
  },

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
