import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { isAdminAuthenticated, isAuthenticated } from './auth/session'

const RoutePlaceholder = { template: '<div />' }

const routes: RouteRecordRaw[] = [
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
	routes
})

router.beforeEach((to) => {
	if (to.meta.requiresAdmin) {
		if (isAdminAuthenticated()) return true
		return {
			name: 'admin-login',
			query: {
				redirect: to.fullPath
			}
		}
	}

	if (!to.meta.requiresAuth) return true
	if (isAuthenticated()) return true

	return {
		name: 'home',
		query: {
			redirect: to.fullPath
		}
	}
})
