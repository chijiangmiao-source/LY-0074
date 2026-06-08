import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const routes: RouteRecordRaw[] = [
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue'),
    meta: { requiresAuth: false, title: '登录' },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    meta: { requiresAuth: true },
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        name: 'Dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板', icon: 'mdi-view-dashboard' },
      },
      {
        path: 'stores',
        name: 'Stores',
        component: () => import('@/views/Stores.vue'),
        meta: { title: '门店管理', icon: 'mdi-store' },
      },
      {
        path: 'buckets',
        name: 'Buckets',
        component: () => import('@/views/Buckets.vue'),
        meta: { title: '花桶档案', icon: 'mdi-bucket' },
      },
      {
        path: 'categories',
        name: 'Categories',
        component: () => import('@/views/Categories.vue'),
        meta: { title: '花材分类', icon: 'mdi-tag-multiple' },
      },
      {
        path: 'flowers',
        name: 'Flowers',
        component: () => import('@/views/Flowers.vue'),
        meta: { title: '花材管理', icon: 'mdi-flower' },
      },
      {
        path: 'records',
        name: 'Records',
        component: () => import('@/views/Records.vue'),
        meta: { title: '业务记录', icon: 'mdi-clipboard-list' },
      },
      {
        path: 'trace',
        name: 'Trace',
        component: () => import('@/views/Trace.vue'),
        meta: { title: '操作轨迹', icon: 'mdi-history' },
      },
      {
        path: 'performance',
        name: 'Performance',
        component: () => import('@/views/Performance.vue'),
        meta: { title: '员工绩效与责任追踪', icon: 'mdi-account-tie' },
      },
      {
        path: 'responsibility-trace',
        name: 'ResponsibilityTrace',
        component: () => import('@/views/ResponsibilityTrace.vue'),
        meta: { title: '责任追踪详情', icon: 'mdi-account-clock-outline' },
      },
    ],
  },
  { path: '/:pathMatch(.*)*', redirect: '/dashboard' },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  auth.loadUserFromStorage()

  document.title = (to.meta.title ? `${to.meta.title} - ` : '') + '花店花桶周转管理系统'

  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    next({ path: '/login', query: { redirect: to.fullPath } })
  } else if (to.path === '/login' && auth.isLoggedIn) {
    next('/')
  } else {
    next()
  }
})

export default router
