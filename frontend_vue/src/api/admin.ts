import type { LoginUser } from '../types'
import { apiRequest } from './client'

export type Pagination = {
	total: number
	page: number
	pageSize: number
}

export type AdminPostItem = {
	id: number
	title: string
	author: string
	authorId: number
	status: 'pending' | 'approved' | 'rejected' | 'offline'
	reviewReason: string
	likes: number
	comments: number
	createdAt: string
	reviewedAt?: string | null
	reviewedBy?: string
}

export type AdminCommentItem = {
	id: number
	content: string
	author: string
	authorId: number
	postId: number
	postTitle: string
	isHidden: boolean
	createdAt: string
}

export type AdminUserItem = {
	id: number
	name: string
	email: string
	isActive: boolean
	isAdmin: boolean
	roles: string[]
}

export type AdminAuditItem = {
	id: number
	actorId: number | null
	actorName: string
	action: string
	targetType: string
	targetId: number
	detail: Record<string, unknown>
	ip: string
	createdAt: string
}

export const adminLoginApi = (account: string, password: string) =>
	apiRequest<LoginUser>('/admin/auth/login', {
		method: 'POST',
		body: JSON.stringify({ account, password })
	})

export const adminLogoutApi = () =>
	apiRequest<{ success: boolean }>('/admin/auth/logout', {
		method: 'POST'
	})

export const adminMeApi = () => apiRequest<LoginUser>('/admin/auth/me')

export const getAdminOverviewApi = () =>
	apiRequest<{
		postPendingCount: number
		commentHiddenCount: number
		todayActiveUsers: number
		auditEvents24h: number
	}>('/admin/dashboard/overview')

export const getAdminPostsApi = (params: { page?: number; pageSize?: number; status?: string; keyword?: string }) => {
	const query = new URLSearchParams()
	if (params.page) query.set('page', String(params.page))
	if (params.pageSize) query.set('pageSize', String(params.pageSize))
	if (params.status) query.set('status', params.status)
	if (params.keyword) query.set('keyword', params.keyword)
	return apiRequest<{ items: AdminPostItem[]; pagination: Pagination }>(`/admin/moderation/posts?${query.toString()}`)
}

export const reviewAdminPostApi = (postId: number, action: string, reason = '') =>
	apiRequest<{ id: number; status: string }>(`/admin/moderation/posts/${postId}/review`, {
		method: 'POST',
		body: JSON.stringify({ action, reason })
	})

export const getAdminCommentsApi = (params: {
	page?: number
	pageSize?: number
	visibility?: string
	keyword?: string
}) => {
	const query = new URLSearchParams()
	if (params.page) query.set('page', String(params.page))
	if (params.pageSize) query.set('pageSize', String(params.pageSize))
	if (params.visibility) query.set('visibility', params.visibility)
	if (params.keyword) query.set('keyword', params.keyword)
	return apiRequest<{ items: AdminCommentItem[]; pagination: Pagination }>(`/admin/moderation/comments?${query.toString()}`)
}

export const hideAdminCommentApi = (commentId: number) =>
	apiRequest<{ id: number; isHidden: boolean }>(`/admin/moderation/comments/${commentId}/hide`, {
		method: 'POST',
		body: JSON.stringify({})
	})

export const restoreAdminCommentApi = (commentId: number) =>
	apiRequest<{ id: number; isHidden: boolean }>(`/admin/moderation/comments/${commentId}/restore`, {
		method: 'POST',
		body: JSON.stringify({})
	})

export const deleteAdminCommentApi = (commentId: number) =>
	apiRequest<{ id: number; deleted: boolean }>(`/admin/moderation/comments/${commentId}`, {
		method: 'DELETE'
	})

export const getAdminUsersApi = (params: { page?: number; pageSize?: number; keyword?: string }) => {
	const query = new URLSearchParams()
	if (params.page) query.set('page', String(params.page))
	if (params.pageSize) query.set('pageSize', String(params.pageSize))
	if (params.keyword) query.set('keyword', params.keyword)
	return apiRequest<{ items: AdminUserItem[]; pagination: Pagination }>(`/admin/users?${query.toString()}`)
}

export const updateAdminUserRolesApi = (userId: number, roles: string[]) =>
	apiRequest<{ id: number; roles: string[]; isAdmin: boolean }>(`/admin/users/${userId}/roles`, {
		method: 'PUT',
		body: JSON.stringify({ roles })
	})

export const getAdminAuditLogsApi = (params: { page?: number; pageSize?: number; action?: string; targetType?: string }) => {
	const query = new URLSearchParams()
	if (params.page) query.set('page', String(params.page))
	if (params.pageSize) query.set('pageSize', String(params.pageSize))
	if (params.action) query.set('action', params.action)
	if (params.targetType) query.set('targetType', params.targetType)
	return apiRequest<{ items: AdminAuditItem[]; pagination: Pagination }>(`/admin/audit/logs?${query.toString()}`)
}
