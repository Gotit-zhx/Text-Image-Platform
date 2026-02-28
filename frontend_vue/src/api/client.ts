const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || '/api'
const API_TIMEOUT_MS = 15000

type ApiEnvelope<T> = {
	code: number
	message: string
	data: T
	requestId?: string
}

const isEnvelope = <T>(payload: unknown): payload is ApiEnvelope<T> => {
	return (
		Boolean(payload) &&
		typeof payload === 'object' &&
		'code' in (payload as Record<string, unknown>) &&
		'message' in (payload as Record<string, unknown>) &&
		'data' in (payload as Record<string, unknown>)
	)
}

const toErrorMessage = (status: number, payload: unknown) => {
	if (payload && typeof payload === 'object' && 'message' in payload) {
		const message = (payload as { message?: string }).message
		if (message) return message
	}

	if (status === 401) return '登录已失效，请重新登录'
	if (status === 403) return '无权限执行该操作'
	if (status === 404) return '请求的资源不存在'
	return `API request failed: ${status}`
}

export const apiRequest = async <T>(path: string, init?: RequestInit): Promise<T> => {
	const controller = new AbortController()
	const timer = setTimeout(() => controller.abort(), API_TIMEOUT_MS)

	const response = await fetch(`${API_BASE_URL}${path}`, {
		credentials: 'include',
		signal: init?.signal ?? controller.signal,
		headers: {
			'Content-Type': 'application/json',
			...(init?.headers || {})
		},
		...init
	}).finally(() => {
		clearTimeout(timer)
	})

	let payload: unknown = null
	try {
		payload = await response.json()
	} catch {
		payload = null
	}

	if (!response.ok) {
		throw new Error(toErrorMessage(response.status, payload))
	}

	if (isEnvelope<T>(payload)) {
		if (payload.code !== 0) {
			throw new Error(payload.message || '请求失败')
		}
		return payload.data as T
	}

	return payload as T
}
