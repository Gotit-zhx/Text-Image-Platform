import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'
import { isAuthenticated } from './auth/session'

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
		path: '/:pathMatch(.*)*',
		redirect: '/'
	}
]

export const router = createRouter({
	history: createWebHistory(),
	routes
})

router.beforeEach((to) => {
	if (!to.meta.requiresAuth) return true
	if (isAuthenticated()) return true

	return {
		name: 'home',
		query: {
			redirect: to.fullPath
		}
	}
})
