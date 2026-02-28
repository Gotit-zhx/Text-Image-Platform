import type { LoginUser } from '../types'
import { apiRequest } from './client'
import type { ProfileEditPayload } from '../types'

const USE_MOCK_API = (import.meta.env.VITE_USE_MOCK_API || 'false') === 'true'

type AuthStats = {
	fans: number
	follows: number
}

const buildUser = (nameOrEmail: string, stats: AuthStats): LoginUser => {
	const name = nameOrEmail.includes('@') ? nameOrEmail.split('@')[0] : nameOrEmail
	const finalName = name || '测试用户'
	return {
		id: Date.now(),
		name: finalName,
		email: nameOrEmail,
		avatarText: finalName.slice(0, 1),
		fans: stats.fans,
		follows: stats.follows
	}
}

export const loginApi = async (
	account: string,
	password: string,
	stats: AuthStats
): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		return buildUser(account, stats)
	}

	return apiRequest<LoginUser>('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ account, password })
	})
}

export const registerApi = async (
	email: string,
	password: string,
	stats: AuthStats
): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		return buildUser(email, stats)
	}

	return apiRequest<LoginUser>('/auth/register', {
		method: 'POST',
		body: JSON.stringify({ email, password })
	})
}

export const meApi = async (): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		throw new Error('mock mode: me api disabled')
	}

	return apiRequest<LoginUser>('/users/me')
}

export const logoutApi = async (): Promise<{ success: boolean }> => {
	if (USE_MOCK_API) {
		return { success: true }
	}

	return apiRequest<{ success: boolean }>('/auth/logout', {
		method: 'POST'
	})
}

export const updateProfileApi = async (payload: ProfileEditPayload): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		return {
			id: Date.now(),
			name: payload.name,
			email: `${payload.name}@example.com`,
			avatarText: payload.name.slice(0, 1),
			avatarUrl: payload.avatarUrl,
			gender: payload.gender,
			fans: 0,
			follows: 0
		}
	}

	return apiRequest<LoginUser>('/users/me/profile', {
		method: 'PUT',
		body: JSON.stringify(payload)
	})
}
