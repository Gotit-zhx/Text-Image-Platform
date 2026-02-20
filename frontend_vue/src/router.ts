import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

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
		component: RoutePlaceholder
	},
	{
		path: '/edit/:id(\\d+)',
		name: 'edit',
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
