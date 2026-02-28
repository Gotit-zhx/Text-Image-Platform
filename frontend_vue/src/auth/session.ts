import type { LoginUser } from '../types'

const SESSION_USER_KEY = 'frontend_vue_login_user'

const canUseStorage = () => typeof window !== 'undefined' && !!window.localStorage

export const readSessionUser = (): LoginUser | null => {
	if (!canUseStorage()) return null
	const raw = window.localStorage.getItem(SESSION_USER_KEY)
	if (!raw) return null

	try {
		return JSON.parse(raw) as LoginUser
	} catch {
		window.localStorage.removeItem(SESSION_USER_KEY)
		return null
	}
}

export const writeSessionUser = (user: LoginUser) => {
	if (!canUseStorage()) return
	window.localStorage.setItem(SESSION_USER_KEY, JSON.stringify(user))
}

export const clearSessionUser = () => {
	if (!canUseStorage()) return
	window.localStorage.removeItem(SESSION_USER_KEY)
}

export const isAuthenticated = () => Boolean(readSessionUser())

export const isAdminAuthenticated = () => {
	const user = readSessionUser()
	return Boolean(user && user.isAdmin)
}
