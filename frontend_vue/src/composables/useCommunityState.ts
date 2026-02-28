// 审查状态：部分完成（初始化/搜索已接口化，发布/编辑/评论已改服务端优先，互动接口待后端接入）
import { ref, type ComputedRef, type Ref } from 'vue'
import { writeSessionUser } from '../auth/session'
import { updateProfileApi } from '../api/auth'
import {
	deleteCommentApi,
	getCommunitySeedApi,
	publishPostApi,
	saveEditedPostApi,
	submitCommentApi,
	toggleAuthorFollowApi,
	toggleCommentLikeApi,
	togglePostFavoriteApi,
	togglePostLikeApi
} from '../api/community'
import type {
	CommentRecord,
	InteractionTestData,
	LoginUser,
	PasswordChangePayload,
	Post,
	ProfileEditPayload,
	PublishPayload,
	UserNotificationItem,
	UserTestData
} from '../types'

type UseCommunityStateOptions = {
	loginUser: Ref<LoginUser | null>
	isLoggedIn: ComputedRef<boolean>
	openLoginModal: () => void
	viewedProfileUser: Ref<LoginUser | null>
	userPassword: Ref<string>
}

export const useCommunityState = ({
	loginUser,
	isLoggedIn,
	openLoginModal,
	viewedProfileUser,
	userPassword
}: UseCommunityStateOptions) => {
	const userTestData = ref<UserTestData>({
		fans: [],
		followings: [],
		fansTotal: 0,
		followingsTotal: 0,
		comments: [],
		favoritePostIds: []
	})
	const interactionTestData = ref<InteractionTestData>({
		likedPostIds: [],
		favoritedPostIds: [],
		followedAuthorIds: []
	})
	const posts = ref<Post[]>([])
	const comments = ref<CommentRecord[]>([])
	const notifications = ref<UserNotificationItem[]>([])
	const isCommunityReady = ref(false)
	const communityError = ref('')

	const initCommunityData = async () => {
		communityError.value = ''
		try {
			const seed = await getCommunitySeedApi()
			userTestData.value = seed.userTestData
			if (typeof userTestData.value.fansTotal !== 'number') {
				userTestData.value.fansTotal = userTestData.value.fans.length
			}
			if (typeof userTestData.value.followingsTotal !== 'number') {
				userTestData.value.followingsTotal = userTestData.value.followings.length
			}
			interactionTestData.value = seed.interactionTestData
			posts.value = seed.posts
			comments.value = seed.comments
			notifications.value = seed.notifications || []
			syncDerivedState()
			isCommunityReady.value = true
		} catch {
			isCommunityReady.value = false
			communityError.value = '社区数据加载失败'
		}
	}

	const syncDerivedState = () => {
		const commentCountMap = comments.value.reduce<Record<number, number>>((acc, item) => {
			acc[item.postId] = (acc[item.postId] || 0) + 1
			return acc
		}, {})

		const likedSet = new Set(interactionTestData.value.likedPostIds)
		const favoritedSet = new Set(interactionTestData.value.favoritedPostIds)
		const followedSet = new Set(interactionTestData.value.followedAuthorIds)

		posts.value.forEach((post) => {
			post.comments = commentCountMap[post.id] || 0
			post.isLiked = likedSet.has(post.id)
			post.isFavorited = favoritedSet.has(post.id)
			post.isFollowingAuthor = post.authorId ? followedSet.has(post.authorId) : false
		})

		userTestData.value.favoritePostIds = [...interactionTestData.value.favoritedPostIds]
		userTestData.value.comments = comments.value
			.filter((item) => item.isMine)
			.map((item) => ({
				id: item.id,
				postId: item.postId,
				postTitle: posts.value.find((post) => post.id === item.postId)?.title || '帖子已删除',
				content: item.content,
				date: item.date,
				likes: item.likes
			}))

		if (loginUser.value) {
			loginUser.value.fans = userTestData.value.fansTotal ?? userTestData.value.fans.length
			loginUser.value.follows =
				userTestData.value.followingsTotal ?? userTestData.value.followings.length
		}
	}

	const syncPostCommentCount = (postId: number) => {
		const post = posts.value.find((item) => item.id === postId)
		if (!post) return
		post.comments = comments.value.filter((item) => item.postId === postId).length
	}

	const togglePostLike = async (postId: number) => {
		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const liked = interactionTestData.value.likedPostIds.includes(postId)
		await togglePostLikeApi(postId, !liked)
		target.likes = liked ? Math.max(0, target.likes - 1) : target.likes + 1

		if (!liked) {
			if (!interactionTestData.value.likedPostIds.includes(postId)) {
				interactionTestData.value.likedPostIds.push(postId)
			}
			syncDerivedState()
			return
		}

		interactionTestData.value.likedPostIds = interactionTestData.value.likedPostIds.filter(
			(id) => id !== postId
		)
		syncDerivedState()
	}

	const togglePostFavorite = async (postId: number) => {
		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const favorited = interactionTestData.value.favoritedPostIds.includes(postId)
		await togglePostFavoriteApi(postId, !favorited)

		if (!favorited) {
			if (!interactionTestData.value.favoritedPostIds.includes(postId)) {
				interactionTestData.value.favoritedPostIds.push(postId)
			}
			syncDerivedState()
			return
		}

		interactionTestData.value.favoritedPostIds = interactionTestData.value.favoritedPostIds.filter(
			(id) => id !== postId
		)
		syncDerivedState()
	}

	const togglePostFollow = async (postId: number) => {
		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		if (
			loginUser.value &&
			(target.authorId === loginUser.value.id || target.author === loginUser.value.name)
		) {
			window.alert('不能关注自己')
			return
		}

		const authorId = target.authorId ?? postId
		const authorName = target.author || '未知作者'
		const authorAvatarText = authorName.slice(0, 1)
		const willFollow = !target.isFollowingAuthor
		await toggleAuthorFollowApi(authorId, willFollow)

		posts.value.forEach((item) => {
			const itemAuthorId = item.authorId ?? item.id
			if (itemAuthorId === authorId) {
				item.isFollowingAuthor = willFollow
			}
		})

		if (willFollow) {
			if (!interactionTestData.value.followedAuthorIds.includes(authorId)) {
				interactionTestData.value.followedAuthorIds.push(authorId)
			}
			userTestData.value.followingsTotal = (userTestData.value.followingsTotal || 0) + 1
			if (!userTestData.value.followings.some((item) => item.id === authorId)) {
				userTestData.value.followings.push({
					id: authorId,
					name: authorName,
					avatarText: authorAvatarText
				})
			}
		} else {
			interactionTestData.value.followedAuthorIds = interactionTestData.value.followedAuthorIds.filter(
				(id) => id !== authorId
			)
			userTestData.value.followingsTotal = Math.max(
				0,
				(userTestData.value.followingsTotal || 0) - 1
			)
			userTestData.value.followings = userTestData.value.followings.filter((item) => item.id !== authorId)
		}

		syncDerivedState()
	}

	const submitComment = async (postId: number, content: string) => {
		const newComment = await submitCommentApi(
			postId,
			content,
			loginUser.value?.id,
			loginUser.value?.name || '我'
		)

		comments.value.unshift(newComment)

		syncPostCommentCount(postId)
		syncDerivedState()
	}

	const toggleCommentLike = async (commentId: number) => {
		const target = comments.value.find((item) => item.id === commentId)
		if (!target) return

		await toggleCommentLikeApi(commentId, !target.isLiked)

		if (target.isLiked) {
			target.isLiked = false
			target.likes = Math.max(0, target.likes - 1)
			syncDerivedState()
			return
		}

		target.isLiked = true
		target.likes += 1
		syncDerivedState()
	}

	const deleteComment = async (commentId: number) => {
		const index = comments.value.findIndex((item) => item.id === commentId)
		if (index === -1) return
		const target = comments.value[index]
		if (!target || !target.isMine) return

		await deleteCommentApi(commentId)

		const postId = target.postId
		comments.value.splice(index, 1)
		syncPostCommentCount(postId)
		syncDerivedState()
	}

	const toggleFollowingUser = async (userId: number) => {
		await toggleAuthorFollowApi(userId, false)

		userTestData.value.followings = userTestData.value.followings.filter((item) => item.id !== userId)
		userTestData.value.followingsTotal = Math.max(0, (userTestData.value.followingsTotal || 0) - 1)
		interactionTestData.value.followedAuthorIds = interactionTestData.value.followedAuthorIds.filter(
			(id) => id !== userId
		)
		posts.value.forEach((item) => {
			if (item.authorId === userId) {
				item.isFollowingAuthor = false
			}
		})
		syncDerivedState()
	}

	const toggleFanFollow = async (userId: number) => {
		const exists = userTestData.value.followings.some((item) => item.id === userId)
		if (exists) {
			await toggleFollowingUser(userId)
			return
		}

		const fan = userTestData.value.fans.find((item) => item.id === userId)
		if (!fan) return
		await toggleAuthorFollowApi(userId, true)
		userTestData.value.followings.push({ ...fan })
		userTestData.value.followingsTotal = (userTestData.value.followingsTotal || 0) + 1
		syncDerivedState()
	}

	const toggleProfileFollow = async (profileUser: LoginUser | null, canFollowProfile: boolean) => {
		if (!isLoggedIn.value) {
			openLoginModal()
			return
		}

		if (!profileUser) return

		if (!canFollowProfile) {
			window.alert('不能关注自己')
			return
		}

		const userId = profileUser.id
		const exists = userTestData.value.followings.some((item) => item.id === userId)
		if (exists) {
			await toggleFollowingUser(userId)
			return
		}

		await toggleAuthorFollowApi(userId, true)

		userTestData.value.followings.push({
			id: userId,
			name: profileUser.name,
			avatarText: profileUser.avatarText
		})
		if (!interactionTestData.value.followedAuthorIds.includes(userId)) {
			interactionTestData.value.followedAuthorIds.push(userId)
		}
		userTestData.value.followingsTotal = (userTestData.value.followingsTotal || 0) + 1
		posts.value.forEach((item) => {
			if (item.authorId === userId || item.author === profileUser.name) {
				item.isFollowingAuthor = true
			}
		})
		syncDerivedState()
	}

	const publishPost = async (payload: PublishPayload) => {
		const newPost = await publishPostApi(payload, loginUser.value?.name || '匿名用户')
		posts.value.unshift(newPost)
	}

	const saveEditedPost = async (postId: number | null, payload: PublishPayload) => {
		if (!postId) return

		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const draft = await saveEditedPostApi(postId, payload)

		target.title = draft.title
		target.contentHtml = draft.contentHtml
		target.summary = draft.summary
		target.tags = [...draft.tags]
		target.images = draft.images
	}

	const saveProfile = async (payload: ProfileEditPayload) => {
		if (!loginUser.value) return

		const oldName = loginUser.value.name
		const persisted = await updateProfileApi(payload)
		loginUser.value = {
			...loginUser.value,
			...persisted
		}
		writeSessionUser(loginUser.value)

		if (viewedProfileUser.value && viewedProfileUser.value.id === loginUser.value.id) {
			viewedProfileUser.value = {
				...viewedProfileUser.value,
				avatarText: loginUser.value.avatarText,
				avatarUrl: loginUser.value.avatarUrl,
				name: loginUser.value.name,
				gender: loginUser.value.gender
			}
		}

		posts.value.forEach((item) => {
			if (item.author === oldName || item.authorId === loginUser.value?.id) {
				item.author = loginUser.value?.name || payload.name
				item.authorId = loginUser.value?.id
				item.authorAvatarText = loginUser.value?.avatarText
				item.authorAvatarUrl = loginUser.value?.avatarUrl
			}
		})

		comments.value.forEach((item) => {
			if (item.isMine || item.author === oldName || item.authorId === loginUser.value?.id) {
				item.author = loginUser.value?.name || payload.name
				item.authorId = loginUser.value?.id
				item.authorAvatarText = loginUser.value?.avatarText
				item.authorAvatarUrl = loginUser.value?.avatarUrl
			}
		})

		syncDerivedState()
	}

	const changePassword = (payload: PasswordChangePayload) => {
		if (!payload.newPassword || payload.newPassword !== payload.confirmPassword) return
		userPassword.value = payload.newPassword
	}

	return {
		userTestData,
		interactionTestData,
		posts,
		comments,
		notifications,
		isCommunityReady,
		communityError,
		initCommunityData,
		togglePostLike,
		togglePostFavorite,
		togglePostFollow,
		submitComment,
		toggleCommentLike,
		deleteComment,
		toggleFollowingUser,
		toggleFanFollow,
		toggleProfileFollow,
		publishPost,
		saveEditedPost,
		saveProfile,
		changePassword
	}
}
