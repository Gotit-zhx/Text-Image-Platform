import { ref } from 'vue'
import {
	adminLoginApi,
	adminLogoutApi,
	adminMeApi,
	deleteAdminCommentApi,
	getAdminAuditLogsApi,
	getAdminCommentsApi,
	getAdminOverviewApi,
	getAdminPostsApi,
	getAdminUsersApi,
	hideAdminCommentApi,
	restoreAdminCommentApi,
	reviewAdminPostApi,
	updateAdminUserRolesApi,
	type AdminAuditItem,
	type AdminCommentItem,
	type AdminPostItem,
	type AdminUserItem,
	type Pagination
} from '../api/admin'
import type { LoginUser } from '../types'
import { clearSessionUser, readSessionUser, writeSessionUser } from '../auth/session'

const defaultPagination: Pagination = { total: 0, page: 1, pageSize: 10 }

export const useAdminState = () => {
	const adminUser = ref<LoginUser | null>(readSessionUser())
	const loading = ref(false)
	const error = ref('')

	const overview = ref({
		postPendingCount: 0,
		commentHiddenCount: 0,
		todayActiveUsers: 0,
		auditEvents24h: 0
	})

	const posts = ref<AdminPostItem[]>([])
	const postsPagination = ref<Pagination>({ ...defaultPagination })

	const comments = ref<AdminCommentItem[]>([])
	const commentsPagination = ref<Pagination>({ ...defaultPagination })

	const users = ref<AdminUserItem[]>([])
	const usersPagination = ref<Pagination>({ ...defaultPagination })

	const logs = ref<AdminAuditItem[]>([])
	const logsPagination = ref<Pagination>({ ...defaultPagination })

	const adminLogin = async (account: string, password: string) => {
		let loggedUser: LoginUser | null = null
		await withLoading(async () => {
			const user = await adminLoginApi(account, password)
			adminUser.value = user
			writeSessionUser(user)
			loggedUser = user
		})
		return loggedUser
	}

	const loadAdminSession = async () => {
		try {
			const user = await adminMeApi()
			adminUser.value = user
			writeSessionUser(user)
			return user
		} catch {
			adminUser.value = null
			clearSessionUser()
			return null
		}
	}

	const adminLogout = async () => {
		try {
			await adminLogoutApi()
		} finally {
			adminUser.value = null
			clearSessionUser()
		}
	}

	const withLoading = async (runner: () => Promise<void>) => {
		loading.value = true
		error.value = ''
		try {
			await runner()
		} catch (e) {
			error.value = e instanceof Error ? e.message : '请求失败'
		} finally {
			loading.value = false
		}
	}

	const loadOverview = async () => {
		await withLoading(async () => {
			overview.value = await getAdminOverviewApi()
		})
	}

	const loadPosts = async (params: { page?: number; pageSize?: number; status?: string; keyword?: string } = {}) => {
		await withLoading(async () => {
			const result = await getAdminPostsApi(params)
			posts.value = result.items
			postsPagination.value = result.pagination
		})
	}

	const reviewPost = async (postId: number, action: string, reason = '') => {
		await withLoading(async () => {
			await reviewAdminPostApi(postId, action, reason)
		})
	}

	const loadComments = async (params: {
		page?: number
		pageSize?: number
		visibility?: string
		keyword?: string
	} = {}) => {
		await withLoading(async () => {
			const result = await getAdminCommentsApi(params)
			comments.value = result.items
			commentsPagination.value = result.pagination
		})
	}

	const hideComment = async (id: number) => {
		await withLoading(async () => {
			await hideAdminCommentApi(id)
		})
	}

	const restoreComment = async (id: number) => {
		await withLoading(async () => {
			await restoreAdminCommentApi(id)
		})
	}

	const deleteComment = async (id: number) => {
		await withLoading(async () => {
			await deleteAdminCommentApi(id)
		})
	}

	const loadUsers = async (params: { page?: number; pageSize?: number; keyword?: string } = {}) => {
		await withLoading(async () => {
			const result = await getAdminUsersApi(params)
			users.value = result.items
			usersPagination.value = result.pagination
		})
	}

	const updateUserRoles = async (id: number, roles: string[]) => {
		await withLoading(async () => {
			await updateAdminUserRolesApi(id, roles)
		})
	}

	const loadLogs = async (params: { page?: number; pageSize?: number; action?: string; targetType?: string } = {}) => {
		await withLoading(async () => {
			const result = await getAdminAuditLogsApi(params)
			logs.value = result.items
			logsPagination.value = result.pagination
		})
	}

	return {
		adminUser,
		loading,
		error,
		overview,
		posts,
		postsPagination,
		comments,
		commentsPagination,
		users,
		usersPagination,
		logs,
		logsPagination,
		adminLogin,
		loadAdminSession,
		adminLogout,
		loadOverview,
		loadPosts,
		reviewPost,
		loadComments,
		hideComment,
		restoreComment,
		deleteComment,
		loadUsers,
		updateUserRoles,
		loadLogs
	}
}
