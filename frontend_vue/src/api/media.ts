import { apiRequest, ApiError } from './client'
export type MediaAsset = {
  id: number
  url: string
  thumbnailUrl: string
  width: number
  height: number
  size: number
}
export type DraftRecord = {
  id: number
  title: string
  summary: string
  contentHtml: string
  tags: string[]
  media: MediaAsset[]
  mediaIds: number[]
  images: string[]
  version: number
  updatedAt: string
}
export const uploadImage = async (
  file: File,
  progress: (percent: number) => void,
  signal: AbortSignal
): Promise<MediaAsset> => {
  const { token } = await apiRequest<{ token: string }>('/auth/csrf', { signal })
  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest()
    const abort = () => xhr.abort()
    signal.addEventListener('abort', abort, { once: true })
    xhr.open('POST', `${import.meta.env.VITE_API_BASE_URL || '/api'}/media`)
    xhr.withCredentials = true
    xhr.setRequestHeader('X-CSRFToken', token)
    xhr.timeout = 30000
    xhr.upload.onprogress = (e) => {
      if (e.lengthComputable) progress(Math.round((e.loaded / e.total) * 100))
    }
    const finish = () => signal.removeEventListener('abort', abort)
    xhr.onload = () => {
      finish()
      if (xhr.status === 401) window.dispatchEvent(new Event('session-expired'))
      try {
        const result = JSON.parse(xhr.responseText)
        if (xhr.status >= 200 && xhr.status < 300) resolve(result.data)
        else reject(new ApiError(result.message || '上传失败', xhr.status, result.code))
      } catch {
        reject(new Error('上传响应无效'))
      }
    }
    xhr.onerror = () => {
      finish()
      reject(new Error('网络错误，图片未上传'))
    }
    xhr.ontimeout = () => {
      finish()
      reject(new Error('上传超时，请重试'))
    }
    xhr.onabort = () => {
      finish()
      reject(new Error('已取消上传'))
    }
    if (signal.aborted) {
      finish()
      reject(new Error('已取消上传'))
      return
    }
    const form = new FormData()
    form.append('file', file)
    xhr.send(form)
  })
}
