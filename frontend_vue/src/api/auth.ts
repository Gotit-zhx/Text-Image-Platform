import type { LoginUser, ProfileEditPayload, PasswordChangePayload } from '../types'
import { apiRequest } from './client'
export const loginApi = (account: string, password: string, _stats?: unknown) =>
  apiRequest<LoginUser>('/auth/login', {
    method: 'POST',
    body: JSON.stringify({ account, password })
  })
export const registerApi = (email: string, password: string, _stats?: unknown) =>
  apiRequest<{ verificationRequired: boolean; message: string }>('/auth/register', {
    method: 'POST',
    body: JSON.stringify({ email, password })
  })
export const meApi = () => apiRequest<LoginUser>('/users/me')
export const logoutApi = () => apiRequest<{ success: boolean }>('/auth/logout', { method: 'POST' })
export const updateProfileApi = (payload: ProfileEditPayload) =>
  apiRequest<LoginUser>('/users/me/profile', { method: 'PUT', body: JSON.stringify(payload) })
export const changePasswordApi = (payload: PasswordChangePayload) =>
  apiRequest('/users/me/password', { method: 'POST', body: JSON.stringify(payload) })
export const emailActionApi = (email: string, purpose: 'reset' | 'verify') =>
  apiRequest<{ message: string }>(
    purpose === 'reset' ? '/auth/password-reset' : '/auth/resend-verification',
    { method: 'POST', body: JSON.stringify({ email }) }
  )
export const consumeTokenApi = (token: string, purpose: 'reset' | 'verify', newPassword = '') =>
  apiRequest(purpose === 'reset' ? '/auth/password-reset/confirm' : '/auth/verify-email', {
    method: 'POST',
    body: JSON.stringify({ token, newPassword })
  })
export const deactivateApi = (password: string, confirmation: string) =>
  apiRequest('/users/me/deactivate', {
    method: 'POST',
    body: JSON.stringify({ password, confirmation })
  })
