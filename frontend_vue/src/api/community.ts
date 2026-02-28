// 审查状态：部分完成（已接入搜索与初始化接口，写接口已提供服务端优先占位）
import type { CommentRecord, InteractionTestData, Post, UserTestData } from '../types'
import { apiRequest } from './client'
import type { PublishPayload } from '../types'

const USE_MOCK_API = (import.meta.env.VITE_USE_MOCK_API || 'false') === 'true'

export const DEFAULT_COMMUNITY_STATS = {
	fans: 4,
	follows: 3
}

export type CommunitySeed = {
	userTestData: UserTestData
	interactionTestData: InteractionTestData
	posts: Post[]
	comments: CommentRecord[]
}

type PostDraft = {
	title: string
	summary: string
	contentHtml: string
	tags: string[]
	images: string[]
}

const extractPostDraft = (payload: PublishPayload): PostDraft => {
	const plain = payload.contentHtml.replace(/<[^>]*>/g, '').trim()
	const summary = plain.length > 60 ? `${plain.slice(0, 60)}...` : plain
	const imageMatches = [...payload.contentHtml.matchAll(/<img[^>]+src=["']([^"']+)["'][^>]*>/g)]
	const imageList = imageMatches
		.map((item) => item[1])
		.filter((item): item is string => Boolean(item))

	return {
		title: payload.title,
		summary: summary || '（无正文）',
		contentHtml: payload.contentHtml,
		tags: payload.tags,
		images: imageList
	}
}

const sortByLikesDesc = (list: Post[]) => [...list].sort((a, b) => b.likes - a.likes)
const sortByDateDesc = (list: Post[]) =>
	[...list].sort((a, b) => {
		const [am = 0, ad = 0] = a.time.split('-').map(Number)
		const [bm = 0, bd = 0] = b.time.split('-').map(Number)
		return bm * 100 + bd - (am * 100 + ad)
	})

const filterByNav = (posts: Post[], nav: string): Post[] => {
	if (nav === '热门') return sortByLikesDesc(posts)
	if (nav === '更新') return sortByDateDesc(posts)
	if (nav === '关注') return posts.filter((item) => item.isFollowingAuthor)
	return sortByLikesDesc(posts)
}

const mockSeed: CommunitySeed = {
	userTestData: {
		fans: [
			{ id: 3001, name: '青杉', avatarText: '青' },
			{ id: 3002, name: '夜航船', avatarText: '夜' },
			{ id: 3003, name: '半格信号', avatarText: '半' },
			{ id: 3004, name: '云上邮差', avatarText: '云' }
		],
		followings: [
			{ id: 4001, name: '镜头漫游者', avatarText: '镜' },
			{ id: 4002, name: '纸页慢生活', avatarText: '纸' },
			{ id: 4003, name: '山野日志', avatarText: '山' }
		],
		comments: [
			{
				id: 7001,
				postId: 101,
				postTitle: '城市夜景拍摄记录｜一条街拍到天亮',
				content: '这组光影对比太舒服了，最后一张构图很稳。',
				date: '02-20',
				likes: 32
			},
			{
				id: 7002,
				postId: 102,
				postTitle: '手账排版合集｜一周模板分享',
				content: '模板很实用，已经按你的思路做了我的周计划。',
				date: '02-19',
				likes: 15
			},
			{
				id: 7003,
				postId: 103,
				postTitle: '三天两晚徒步路线复盘',
				content: '补给点信息很关键，感谢整理。',
				date: '02-18',
				likes: 8
			}
		],
		favoritePostIds: [102, 104]
	},
	interactionTestData: {
		likedPostIds: [101, 103],
		favoritedPostIds: [102, 104],
		followedAuthorIds: [201, 203]
	},
	posts: [
		{
			id: 101,
			title: '城市夜景拍摄记录｜一条街拍到天亮',
			summary: '测试数据：用于点赞/收藏/关注状态验证，包含多图与较高互动量。',
			author: '风起时拍照',
			time: '02-20',
			tags: ['摄影', '夜景', '街拍'],
			images: [
				'linear-gradient(135deg, #2f3b73, #5f85ff)',
				'linear-gradient(135deg, #1f6d7a, #24c0c8)',
				'linear-gradient(135deg, #6e3d9a, #b16eff)'
			],
			comments: 128,
			likes: 3560,
			authorId: 201,
			isLiked: true,
			isFavorited: false,
			isFollowingAuthor: true
		},
		{
			id: 102,
			title: '手账排版合集｜一周模板分享',
			summary: '测试数据：用于收藏状态验证，当前设为已收藏、未点赞、未关注作者。',
			author: '纸页慢生活',
			time: '02-19',
			tags: ['手账', '模板', '效率'],
			images: [
				'linear-gradient(135deg, #ffd1a8, #ff9e80)',
				'linear-gradient(135deg, #ffe59a, #ffc85d)',
				'linear-gradient(135deg, #fff0c7, #ffd68e)'
			],
			comments: 64,
			likes: 892,
			authorId: 202,
			isLiked: false,
			isFavorited: true,
			isFollowingAuthor: false
		},
		{
			id: 103,
			title: '三天两晚徒步路线复盘',
			summary: '测试数据：用于关注状态验证，当前设为已关注作者且已点赞未收藏。',
			author: '山野日志',
			time: '02-18',
			tags: ['徒步', '旅行', '装备'],
			images: ['linear-gradient(135deg, #5ea46f, #8ed39f)'],
			comments: 212,
			likes: 12450,
			authorId: 203,
			isLiked: true,
			isFavorited: false,
			isFollowingAuthor: true
		},
		{
			id: 104,
			title: '咖啡拉花新手练习记录（失败合集）',
			summary: '测试数据：用于未交互场景验证，点赞/收藏/关注均为 false。',
			author: '清晨一杯',
			time: '02-17',
			tags: ['咖啡', '拉花', '日常'],
			images: ['linear-gradient(135deg, #8b5e3c, #c58b64)'],
			comments: 39,
			likes: 317,
			authorId: 204,
			isLiked: false,
			isFavorited: false,
			isFollowingAuthor: false
		}
	],
	comments: [
		{
			id: 9001,
			postId: 101,
			authorId: 5001,
			author: '测试用户A',
			date: '02-20',
			content: '测试评论：高赞样本。',
			likes: 320,
			isLiked: false,
			isMine: false
		},
		{
			id: 9002,
			postId: 102,
			authorId: 5002,
			author: '测试用户B',
			date: '02-19',
			content: '测试评论：中等点赞样本。',
			likes: 58,
			isLiked: true,
			isMine: false
		},
		{
			id: 7001,
			postId: 101,
			author: '我',
			date: '02-20',
			content: '这组光影对比太舒服了，最后一张构图很稳。',
			likes: 32,
			isLiked: false,
			isMine: true
		},
		{
			id: 7002,
			postId: 102,
			author: '我',
			date: '02-19',
			content: '模板很实用，已经按你的思路做了我的周计划。',
			likes: 15,
			isLiked: false,
			isMine: true
		},
		{
			id: 7003,
			postId: 103,
			author: '我',
			date: '02-18',
			content: '补给点信息很关键，感谢整理。',
			likes: 8,
			isLiked: false,
			isMine: true
		}
	]
}

export const getMockCommunitySeed = (): CommunitySeed => structuredClone(mockSeed)

export const getCommunitySeedApi = async (): Promise<CommunitySeed> => {
	if (USE_MOCK_API) {
		return getMockCommunitySeed()
	}

	return apiRequest<CommunitySeed>('/community/bootstrap')
}

export const searchPostsApi = async (
	keyword: string,
	nav: string,
	options?: { signal?: AbortSignal }
): Promise<Post[]> => {
	if (USE_MOCK_API) {
		const normalizedKeyword = keyword.trim().toLowerCase()
		const navFiltered = filterByNav(getMockCommunitySeed().posts, nav)
		if (!normalizedKeyword) return navFiltered

		return navFiltered.filter((post) => {
			const source = [post.title, post.summary, post.author, ...(post.tags || [])]
				.join(' ')
				.toLowerCase()
			return source.includes(normalizedKeyword)
		})
	}

	const query = new URLSearchParams({
		q: keyword,
		nav
	})

	const response = await apiRequest<{ posts: Post[] }>(`/community/search?${query.toString()}`, {
		signal: options?.signal
	})
	return response.posts
}

export const recommendPostsApi = async (k = 20): Promise<Post[]> => {
	if (USE_MOCK_API) {
		return sortByLikesDesc(getMockCommunitySeed().posts).slice(0, k)
	}

	const query = new URLSearchParams({ k: String(k) })
	const response = await apiRequest<{ posts: Post[] }>(`/community/recommend?${query.toString()}`)
	return response.posts
}

export const publishPostApi = async (payload: PublishPayload, authorName: string): Promise<Post> => {
	if (USE_MOCK_API) {
		const now = new Date()
		const mm = String(now.getMonth() + 1).padStart(2, '0')
		const dd = String(now.getDate()).padStart(2, '0')
		const draft = extractPostDraft(payload)

		return {
			id: Date.now(),
			title: draft.title,
			summary: draft.summary,
			contentHtml: draft.contentHtml,
			author: authorName,
			time: `${mm}-${dd}`,
			tags: draft.tags,
			images: draft.images,
			comments: 0,
			likes: 0
		}
	}

	return apiRequest<Post>('/community/posts', {
		method: 'POST',
		body: JSON.stringify({
			...extractPostDraft(payload),
			author: authorName
		})
	})
}

export const saveEditedPostApi = async (postId: number, payload: PublishPayload): Promise<PostDraft> => {
	if (USE_MOCK_API) {
		return extractPostDraft(payload)
	}

	return apiRequest<PostDraft>(`/community/posts/${postId}`, {
		method: 'PUT',
		body: JSON.stringify(extractPostDraft(payload))
	})
}

export const submitCommentApi = async (
	postId: number,
	content: string,
	authorId?: number,
	authorName = '我'
): Promise<CommentRecord> => {
	if (USE_MOCK_API) {
		const now = new Date()
		const mm = String(now.getMonth() + 1).padStart(2, '0')
		const dd = String(now.getDate()).padStart(2, '0')
		return {
			id: Date.now(),
			postId,
			authorId,
			author: authorName,
			date: `${mm}-${dd}`,
			content,
			likes: 0,
			isLiked: false,
			isMine: true
		}
	}

	return apiRequest<CommentRecord>(`/community/posts/${postId}/comments`, {
		method: 'POST',
		body: JSON.stringify({ content })
	})
}

export const togglePostLikeApi = async (postId: number, willLike: boolean) => {
	if (USE_MOCK_API) {
		return { postId, isLiked: willLike }
	}

	return apiRequest<{ postId: number; isLiked: boolean }>(`/community/posts/${postId}/like`, {
		method: 'POST',
		body: JSON.stringify({ isLiked: willLike })
	})
}

export const togglePostFavoriteApi = async (postId: number, willFavorite: boolean) => {
	if (USE_MOCK_API) {
		return { postId, isFavorited: willFavorite }
	}

	return apiRequest<{ postId: number; isFavorited: boolean }>(`/community/posts/${postId}/favorite`, {
		method: 'POST',
		body: JSON.stringify({ isFavorited: willFavorite })
	})
}

export const toggleAuthorFollowApi = async (authorId: number, willFollow: boolean) => {
	if (USE_MOCK_API) {
		return { authorId, isFollowing: willFollow }
	}

	return apiRequest<{ authorId: number; isFollowing: boolean }>(`/community/authors/${authorId}/follow`, {
		method: 'POST',
		body: JSON.stringify({ isFollowing: willFollow })
	})
}

export const toggleCommentLikeApi = async (commentId: number, willLike: boolean) => {
	if (USE_MOCK_API) {
		return { commentId, isLiked: willLike }
	}

	return apiRequest<{ commentId: number; isLiked: boolean }>(`/community/comments/${commentId}/like`, {
		method: 'POST',
		body: JSON.stringify({ isLiked: willLike })
	})
}

export const deleteCommentApi = async (commentId: number) => {
	if (USE_MOCK_API) {
		return { commentId, deleted: true }
	}

	return apiRequest<{ commentId: number; deleted: boolean }>(`/community/comments/${commentId}`, {
		method: 'DELETE'
	})
}
