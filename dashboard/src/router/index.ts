import { createRouter, createWebHistory } from 'vue-router'
import { isAuthenticated } from '../api/auth-storage'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/LoginView.vue'),
      meta: { title: 'Login', public: true },
    },
    {
      path: '/',
      name: 'dashboard',
      component: () => import('../views/DashboardView.vue'),
      meta: { title: 'Dashboard' },
    },
    {
      path: '/by-garage',
      name: 'dashboard-by-garage',
      component: () => import('../views/GarageDashboardView.vue'),
      meta: { title: 'Dashboard by garage' },
    },
    {
      path: '/garage/:id',
      name: 'garage-detail',
      component: () => import('../views/GarageDetailView.vue'),
      meta: { title: 'Garage' },
    },
    // Redirect so /index.html or /Index.html shows the dashboard
    { path: '/index.html', redirect: '/' },
    { path: '/Index.html', redirect: '/' },
  ],
})

router.beforeEach((to) => {
  const publicRoute = to.meta.public === true
  if (publicRoute) {
    if (to.name === 'login' && isAuthenticated()) {
      return { path: '/', replace: true }
    }
    return true
  }
  if (!isAuthenticated()) {
    return { path: '/login', query: to.path !== '/' ? { redirect: to.fullPath } : undefined, replace: true }
  }
  return true
})

export default router
