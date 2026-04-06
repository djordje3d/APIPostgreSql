import { createRouter, createWebHistory } from 'vue-router'
import type { RouteLocationNormalized } from 'vue-router'
import { isAuthenticated } from '../api/auth-storage'

/** Dashboard with no garage segment — default landing after login. */
function isDashboardAllGarages(to: RouteLocationNormalized): boolean {
  return (
    to.name === 'dashboard' &&
    (to.params.garageId == null ||
      to.params.garageId === '' ||
      (Array.isArray(to.params.garageId) && to.params.garageId.length === 0))
  )
}

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: 'Login', public: true },
    },
    { path: '/', redirect: '/dashboard' },
    {
      path: '/dashboard/:garageId?',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: 'Dashboard' },
    },
    {
      path: '/garage/:id',
      name: 'garage-detail',
      component: () => import('../views/GarageDetailView.vue'),
      meta: { title: 'Garage' },
    },
    // Redirect so /index.html or /Index.html shows the dashboard
    { path: '/index.html', redirect: '/dashboard' },
    { path: '/Index.html', redirect: '/dashboard' },
  ],
})

router.beforeEach((to) => {
  const publicRoute = to.meta.public === true
  if (publicRoute) {
    if (to.name === 'login' && isAuthenticated()) {
      return { path: '/dashboard', replace: true }
    }
    return true
  }
  if (!isAuthenticated()) {
    return {
      path: '/login',
      query: isDashboardAllGarages(to) ? undefined : { redirect: to.fullPath },
      replace: true,
    }
  }
  return true
})

export default router
