import type { LoginUser } from '../types'
import { apiRequest } from '../api/client'
type SessionScope = 'community' | 'admin'
const users: Record<SessionScope, LoginUser | null> = { community: null, admin: null }
const loading: Partial<Record<SessionScope, Promise<LoginUser | null>>> = {}
export const readSessionUser = (scope: SessionScope = 'community') => users[scope]
export const writeSessionUser = (user: LoginUser, scope: SessionScope = 'community') => {
  users[scope] = user
}
export const clearSessionUser = (scope: SessionScope = 'community') => {
  users[scope] = null
  localStorage.removeItem(scope === 'admin' ? 'frontend_vue_admin_user' : 'frontend_vue_login_user')
}
export const ensureSession = (scope: SessionScope = 'community'): Promise<LoginUser | null> => {
  if (!loading[scope])
    loading[scope] = apiRequest<LoginUser>(scope === 'admin' ? '/admin/auth/me' : '/users/me')
      .then((user) => {
        users[scope] = user
        return user
      })
      .catch(() => {
        clearSessionUser(scope)
        return null
      })
      .finally(() => {
        delete loading[scope]
      })
  return loading[scope]!
}
export const isAuthenticated = () => Boolean(users.community)
export const isAdminAuthenticated = () => Boolean(users.admin?.isAdmin)
