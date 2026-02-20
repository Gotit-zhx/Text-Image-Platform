import type { LoginUser } from '../types'
import { apiRequest } from './client'

const USE_MOCK_API = (import.meta.env.VITE_USE_MOCK_API || 'true') === 'true'

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

export const loginApi = async (account: string, stats: AuthStats): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		return buildUser(account, stats)
	}

	return apiRequest<LoginUser>('/auth/login', {
		method: 'POST',
		body: JSON.stringify({ account })
	})
}

export const registerApi = async (email: string, stats: AuthStats): Promise<LoginUser> => {
	if (USE_MOCK_API) {
		return buildUser(email, stats)
	}

	return apiRequest<LoginUser>('/auth/register', {
		method: 'POST',
		body: JSON.stringify({ email })
	})
}
