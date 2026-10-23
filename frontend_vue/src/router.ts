import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { ensureSession, isAdminAuthenticated, isAuthenticated } from './auth/session'

const RoutePlaceholder = { template: '<div />' }

const routes: RouteRecordRaw[] = [
  {path:'/settings/profile',name:'settings-profile',meta:{requiresAuth:true},component:RoutePlaceholder},
  { path: '/search', name: 'search', component: RoutePlaceholder },
  { path: '/reports', name: 'reports', meta: { requiresAuth: true }, component: RoutePlaceholder },
  {
    path: '/admin/reports',
    name: 'admin-reports',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/admin/appeals',
    name: 'admin-appeals',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  { path: '/u/:id(\\d+)', name: 'user', component: RoutePlaceholder },
  {
    path: '/bookmarks',
    name: 'bookmarks',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },
  {
    path: '/notifications',
    name: 'notifications',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },
  {
    path: '/settings/privacy',
    name: 'settings-privacy',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },

  { path: '/drafts', name: 'drafts', meta: { requiresAuth: true }, component: RoutePlaceholder },
  { path: '/following', name: 'following', component: RoutePlaceholder },
  { path: '/auth/:action(verify|reset)', name: 'auth-token', component: RoutePlaceholder },
  {
    path: '/settings/account',
    name: 'settings-account',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },
  {
    path: '/',
    name: 'home',
    component: RoutePlaceholder
  },
  {
    path: '/profile',
    name: 'profile',
    component: RoutePlaceholder
  },
  {
    path: '/publish',
    name: 'publish',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },
  {
    path: '/edit/:id(\\d+)',
    name: 'edit',
    meta: { requiresAuth: true },
    component: RoutePlaceholder
  },
  {
    path: '/detail/:id(\\d+)',
    name: 'detail',
    component: RoutePlaceholder
  },
  {
    path: '/admin/login',
    name: 'admin-login',
    component: RoutePlaceholder
  },
  {
    path: '/admin',
    name: 'admin-dashboard',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/admin/posts',
    name: 'admin-posts',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/admin/comments',
    name: 'admin-comments',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/admin/users',
    name: 'admin-users',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/admin/audit-logs',
    name: 'admin-audit-logs',
    meta: { requiresAdmin: true },
    component: RoutePlaceholder
  },
  {
    path: '/:pathMatch(.*)*',
    redirect: '/'
  }
]

export const router = createRouter({
  history: createWebHistory(),
  routes,
  scrollBehavior(to, from, saved) {
    if (to.name === 'detail' && window.history.state.background) return false
    if (from.name === 'detail' && window.history.state.forward) return false
    return saved || { top: 0 }
  }
})

router.beforeEach(async (to) => {
  if (to.name === 'profile') {
    const user = await ensureSession()
    const id = Number(to.query.userId || user?.id)
    if (!id) return { name: 'home', query: { redirect: '/profile' } }
    const menu = Number(to.query.menu || 0)
    if (menu === 5) return '/notifications'
    if (menu === 6) return { path: `/u/${id}`, query: { tab: 'posts' } }
    return {
      path: `/u/${id}`,
      query: { tab: ['posts', 'comments', 'bookmarks', 'followers', 'following'][menu] || 'posts' }
    }
  }

  if (to.meta.requiresAdmin) {
    await ensureSession('admin')
    if (isAdminAuthenticated()) return true
    return {
      name: 'admin-login',
      query: {
        redirect: to.fullPath
      }
    }
  }

  if (!to.meta.requiresAuth) return true
  await ensureSession()
  if (isAuthenticated()) return true

  return {
    name: 'home',
    query: {
      redirect: to.fullPath
    }
  }
})
