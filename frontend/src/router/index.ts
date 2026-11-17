import { createRouter, createWebHistory, RouteRecordRaw, NavigationGuardNext, RouteLocationNormalized } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

// Layout imports
import AdminLayout from '@/layouts/AdminLayout.vue'
import EmployeeLayout from '@/layouts/EmployeeLayout.vue'

// Page imports
import LoginPage from '@/features/auth/pages/LoginPage.vue'
import NotFoundPage from '@/features/auth/pages/NotFoundPage.vue'
import AdminDashboard from '@/features/dashboard/pages/AdminDashboard.vue'
import EmployeeDashboard from '@/features/dashboard/pages/EmployeeDashboard.vue'
import EmployeeList from '@/features/employees/pages/EmployeeList.vue'
import EmployeeForm from '@/features/employees/pages/EmployeeForm.vue'
import AttendanceAdmin from '@/features/attendance/pages/AttendanceAdmin.vue'
import AttendanceEmployee from '@/features/attendance/pages/AttendanceEmployee.vue'
import LeaveRequestsAdmin from '@/features/leave/pages/LeaveRequestsAdmin.vue'
import LeaveRequestsEmployee from '@/features/leave/pages/LeaveRequestsEmployee.vue'
import ReportsPage from '@/features/reports/pages/ReportsPage.vue'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    component: LoginPage,
    meta: { requiresAuth: false },
  },
  {
    path: '/',
    component: AdminLayout,
    meta: { requiresAuth: true, requiresAdmin: true },
    children: [
      {
        path: '',
        component: AdminDashboard,
      },
      {
        path: 'employees',
        component: EmployeeList,
      },
      {
        path: 'employees/new',
        component: EmployeeForm,
      },
      {
        path: 'employees/:id/edit',
        component: EmployeeForm,
      },
      {
        path: 'attendance',
        component: AttendanceAdmin,
      },
      {
        path: 'leave',
        component: LeaveRequestsAdmin,
      },
      {
        path: 'reports',
        component: ReportsPage,
      },
    ],
  },
  {
    path: '/my',
    component: EmployeeLayout,
    meta: { requiresAuth: true, requiresEmployee: true },
    children: [
      {
        path: '',
        component: EmployeeDashboard,
      },
      {
        path: 'attendance',
        component: AttendanceEmployee,
      },
      {
        path: 'leave',
        component: LeaveRequestsEmployee,
      },
    ],
  },
  {
    path: '/:pathMatch(.*)*',
    component: NotFoundPage,
  },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

router.beforeEach(
  async (
    to: RouteLocationNormalized,
    from: RouteLocationNormalized,
    next: NavigationGuardNext
  ) => {
    const authStore = useAuthStore()

    // Check if already authenticated
    if (!authStore.isAuthenticated) {
      const isAuthenticated = await authStore.checkAuth()
      if (!isAuthenticated && to.path !== '/login') {
        return next('/login')
      }
    }

    const requiresAuth = to.meta.requiresAuth !== false
    const requiresAdmin = to.meta.requiresAdmin === true
    const requiresEmployee = to.meta.requiresEmployee === true

    // Redirect to login if not authenticated
    if (requiresAuth && !authStore.isAuthenticated) {
      return next('/login')
    }

    // Redirect authenticated users away from login
    if (to.path === '/login' && authStore.isAuthenticated) {
      return next(authStore.isAdmin ? '/' : '/my')
    }

    // Check role restrictions
    if (requiresAdmin && !authStore.isAdmin) {
      return next('/my')
    }

    if (requiresEmployee && !authStore.isEmployee) {
      return next('/')
    }

    next()
  }
)

export default router
