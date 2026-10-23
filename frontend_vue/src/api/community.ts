import type { CommentRecord, LoginUser, Post, PublishPayload } from '../types'
import { apiRequest } from './client'
export const DEFAULT_COMMUNITY_STATS = { fans: 0, follows: 0 }
export type PostsPagination = { total: number; page: number; pageSize: number; hasMore: boolean }
export type PagedPostsResult = { posts: Post[]; pagination: PostsPagination }
export type Paged<T> = { items: T[]; pagination: PostsPagination }
export type UserProfileStats = LoginUser & { totalLikes: number }
export const getUserProfileStatsApi = (id: number) =>
  apiRequest<UserProfileStats>(`/community/users/${id}/profile`)
export const getPostApi = (id: number, manage = false) =>
  apiRequest<Post>(`/community/posts/${id}${manage ? '?manage=1' : ''}`)
export const deletePostApi = (id: number) =>
  apiRequest(`/community/posts/${id}`, { method: 'DELETE' })
export const searchPostsApi = (
  q: string,
  nav: string,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal }
) =>
  apiRequest<PagedPostsResult>(
    `/community/search?${new URLSearchParams({ q, nav, page: String(options?.page || 1), pageSize: String(options?.pageSize || 12) })}`,
    { signal: options?.signal }
  )
export const recommendPostsApi = (
  _k = 20,
  options?: { page?: number; pageSize?: number; signal?: AbortSignal }
) => searchPostsApi('', '推荐', options)
export const publishPostApi = (payload: PublishPayload, _author?: string) =>
  apiRequest<Post>('/community/posts', { method: 'POST', body: JSON.stringify(payload) })
export const saveEditedPostApi = (id: number, payload: PublishPayload) =>
  apiRequest<Post>(`/community/posts/${id}`, { method: 'PUT', body: JSON.stringify(payload) })
export const submitCommentApi = (
  id: number,
  content: string,
  _authorId?: number,
  _authorName?: string
) =>
  apiRequest<CommentRecord>(`/community/posts/${id}/comments`, {
    method: 'POST',
    body: JSON.stringify({ content })
  })
export const togglePostLikeApi = (id: number, isLiked: boolean) =>
  apiRequest<{ postId: number; isLiked: boolean; likes: number }>(`/community/posts/${id}/like`, {
    method: 'POST',
    body: JSON.stringify({ isLiked })
  })
export const togglePostFavoriteApi = (id: number, isFavorited: boolean) =>
  apiRequest<{ postId: number; isFavorited: boolean }>(`/community/posts/${id}/favorite`, {
    method: 'POST',
    body: JSON.stringify({ isFavorited })
  })
export const toggleAuthorFollowApi = (id: number, isFollowing: boolean) =>
  apiRequest<{authorId:number;isFollowing:boolean;fans:number}>(`/community/authors/${id}/follow`, {
    method: 'POST',
    body: JSON.stringify({ isFollowing })
  })
export const toggleCommentLikeApi = (id: number, isLiked: boolean) =>
  apiRequest<{ commentId: number; isLiked: boolean; likes: number }>(
    `/community/comments/${id}/like`,
    { method: 'POST', body: JSON.stringify({ isLiked }) }
  )
export const deleteCommentApi = (id: number) =>
  apiRequest(`/community/comments/${id}`, { method: 'DELETE' })
export const trackPostReadApi = (id: number) =>
  apiRequest(`/community/posts/${id}/read`, { method: 'POST' })
export const trackPostShareApi = (id: number) =>
  apiRequest(`/community/posts/${id}/share`, { method: 'POST' })
