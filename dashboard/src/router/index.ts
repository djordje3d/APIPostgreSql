import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
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
    { path: '/index.html', redirect: '/' },
    { path: '/Index.html', redirect: '/' },
  ],
})

export default router
