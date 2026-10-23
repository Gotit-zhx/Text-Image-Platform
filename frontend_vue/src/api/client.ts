const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
export class ApiError extends Error {
  constructor(
    message: string,
    public status: number,
    public code = status
  ) {
    super(message)
  }
}
export const apiRequest = async <T>(path: string, init: RequestInit = {}): Promise<T> => {
  const controller = new AbortController()
  const abort = () => controller.abort()
  init.signal?.addEventListener('abort', abort, { once: true })
  if (init.signal?.aborted) controller.abort()
  const timer = setTimeout(abort, 15000)
  const method = (init.method || 'GET').toUpperCase()
  const headers = new Headers(init.headers)
  if (!(init.body instanceof FormData)) headers.set('Content-Type', 'application/json')
  try {
    if (!['GET', 'HEAD', 'OPTIONS'].includes(method)) {
      const response = await fetch(`${API_BASE_URL}/auth/csrf`, {
        credentials: 'include',
        signal: controller.signal
      })
      const envelope = await response.json().catch(() => null)
      if (!response.ok || !envelope?.data?.token)
        throw new ApiError('请求验证服务暂不可用，请稍后重试', response.status)
      headers.set('X-CSRFToken', envelope.data.token)
    }
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...init,
      method,
      headers,
      credentials: 'include',
      signal: controller.signal
    })
    const payload = await response.json().catch(() => null)
    if (!response.ok || (payload && 'code' in payload && payload.code !== 0)) {
      if (response.status === 401 && method !== 'GET' && !path.startsWith('/auth/'))
        window.dispatchEvent(new Event('session-expired'))
      throw new ApiError(
        payload?.message || `请求失败（${response.status}）`,
        response.status,
        payload?.code
      )
    }
    return payload && 'code' in payload ? payload.data : payload
  } catch (error) {
    if (error instanceof TypeError) throw new ApiError('无法连接服务器，请检查网络后重试', 0)
    if (error instanceof DOMException && error.name === 'AbortError' && !init.signal?.aborted)
      throw new ApiError('请求超时，输入已保留，请重试', 408)
    throw error
  } finally {
    clearTimeout(timer)
    init.signal?.removeEventListener('abort', abort)
  }
}
