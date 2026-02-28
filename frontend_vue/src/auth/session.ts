import type { LoginUser } from '../types'

type SessionScope = 'community' | 'admin'

const SESSION_USER_KEYS: Record<SessionScope, string> = {
	community: 'frontend_vue_login_user',
	admin: 'frontend_vue_admin_user'
}

const canUseStorage = () => typeof window !== 'undefined' && !!window.localStorage

export const readSessionUser = (scope: SessionScope = 'community'): LoginUser | null => {
	if (!canUseStorage()) return null
	const raw = window.localStorage.getItem(SESSION_USER_KEYS[scope])
	if (!raw) return null

	try {
		return JSON.parse(raw) as LoginUser
	} catch {
		window.localStorage.removeItem(SESSION_USER_KEYS[scope])
		return null
	}
}

export const writeSessionUser = (user: LoginUser, scope: SessionScope = 'community') => {
	if (!canUseStorage()) return
	window.localStorage.setItem(SESSION_USER_KEYS[scope], JSON.stringify(user))
}

export const clearSessionUser = (scope: SessionScope = 'community') => {
	if (!canUseStorage()) return
	window.localStorage.removeItem(SESSION_USER_KEYS[scope])
}

export const isAuthenticated = () => Boolean(readSessionUser('community'))

export const isAdminAuthenticated = () => {
	const user = readSessionUser('admin')
	return Boolean(user && user.isAdmin)
}
