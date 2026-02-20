import { ref, type ComputedRef, type Ref } from 'vue'
import { getMockCommunitySeed } from '../api/community'
import type {
	LoginUser,
	PasswordChangePayload,
	Post,
	ProfileEditPayload,
	PublishPayload
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
	const seed = getMockCommunitySeed()
	const userTestData = ref(seed.userTestData)
	const interactionTestData = ref(seed.interactionTestData)
	const posts = ref(seed.posts)
	const comments = ref(seed.comments)

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

		if (loginUser.value) {
			loginUser.value.fans = userTestData.value.fans.length
			loginUser.value.follows = userTestData.value.followings.length
		}
	}

	const syncPostCommentCount = (postId: number) => {
		const post = posts.value.find((item) => item.id === postId)
		if (!post) return
		post.comments = comments.value.filter((item) => item.postId === postId).length
	}

	const togglePostLike = (postId: number) => {
		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const liked = interactionTestData.value.likedPostIds.includes(postId)
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

	const togglePostFavorite = (postId: number) => {
		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const favorited = interactionTestData.value.favoritedPostIds.includes(postId)

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

	const togglePostFollow = (postId: number) => {
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
			userTestData.value.followings = userTestData.value.followings.filter((item) => item.id !== authorId)
		}

		syncDerivedState()
	}

	const submitComment = (postId: number, content: string) => {
		const now = new Date()
		const mm = String(now.getMonth() + 1).padStart(2, '0')
		const dd = String(now.getDate()).padStart(2, '0')

		comments.value.unshift({
			id: Date.now(),
			postId,
			authorId: loginUser.value?.id,
			author: loginUser.value?.name || '我',
			date: `${mm}-${dd}`,
			content,
			likes: 0,
			isLiked: false,
			isMine: true
		})

		syncPostCommentCount(postId)
		syncDerivedState()
	}

	const toggleCommentLike = (commentId: number) => {
		const target = comments.value.find((item) => item.id === commentId)
		if (!target) return

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

	const deleteComment = (commentId: number) => {
		const index = comments.value.findIndex((item) => item.id === commentId)
		if (index === -1) return
		const target = comments.value[index]
		if (!target || !target.isMine) return

		const postId = target.postId
		comments.value.splice(index, 1)
		syncPostCommentCount(postId)
		syncDerivedState()
	}

	const toggleFollowingUser = (userId: number) => {
		userTestData.value.followings = userTestData.value.followings.filter((item) => item.id !== userId)
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

	const toggleFanFollow = (userId: number) => {
		const exists = userTestData.value.followings.some((item) => item.id === userId)
		if (exists) {
			toggleFollowingUser(userId)
			return
		}

		const fan = userTestData.value.fans.find((item) => item.id === userId)
		if (!fan) return
		userTestData.value.followings.push({ ...fan })
		syncDerivedState()
	}

	const toggleProfileFollow = (profileUser: LoginUser | null, canFollowProfile: boolean) => {
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
			toggleFollowingUser(userId)
			return
		}

		userTestData.value.followings.push({
			id: userId,
			name: profileUser.name,
			avatarText: profileUser.avatarText
		})
		if (!interactionTestData.value.followedAuthorIds.includes(userId)) {
			interactionTestData.value.followedAuthorIds.push(userId)
		}
		posts.value.forEach((item) => {
			if (item.authorId === userId || item.author === profileUser.name) {
				item.isFollowingAuthor = true
			}
		})
		syncDerivedState()
	}

	const publishPost = (payload: PublishPayload) => {
		const plain = payload.contentHtml.replace(/<[^>]*>/g, '').trim()
		const summary = plain.length > 60 ? `${plain.slice(0, 60)}...` : plain
		const imageMatches = [...payload.contentHtml.matchAll(/<img[^>]+src=["']([^"']+)["'][^>]*>/g)]
		const imageList = imageMatches
			.map((item) => item[1])
			.filter((item): item is string => Boolean(item))
		const now = new Date()
		const mm = String(now.getMonth() + 1).padStart(2, '0')
		const dd = String(now.getDate()).padStart(2, '0')

		const newPost: Post = {
			id: Date.now(),
			title: payload.title,
			summary: summary || '（无正文）',
			contentHtml: payload.contentHtml,
			author: loginUser.value?.name || '匿名用户',
			time: `${mm}-${dd}`,
			tags: payload.tags,
			images: imageList,
			comments: 0,
			likes: 0
		}

		posts.value.unshift(newPost)
	}

	const saveEditedPost = (postId: number | null, payload: PublishPayload) => {
		if (!postId) return

		const target = posts.value.find((item) => item.id === postId)
		if (!target) return

		const plain = payload.contentHtml.replace(/<[^>]*>/g, '').trim()
		const summary = plain.length > 60 ? `${plain.slice(0, 60)}...` : plain
		const imageMatches = [...payload.contentHtml.matchAll(/<img[^>]+src=["']([^"']+)["'][^>]*>/g)]
		const imageList = imageMatches
			.map((item) => item[1])
			.filter((item): item is string => Boolean(item))

		target.title = payload.title
		target.contentHtml = payload.contentHtml
		target.summary = summary || '（无正文）'
		target.tags = [...payload.tags]
		target.images = imageList
	}

	const saveProfile = (payload: ProfileEditPayload) => {
		if (!loginUser.value) return

		const oldName = loginUser.value.name
		loginUser.value.avatarUrl = payload.avatarUrl
		loginUser.value.avatarText = (payload.name || oldName).slice(0, 1)
		loginUser.value.name = payload.name
		loginUser.value.gender = payload.gender

		if (viewedProfileUser.value && viewedProfileUser.value.id === loginUser.value.id) {
			viewedProfileUser.value = {
				...viewedProfileUser.value,
				avatarText: loginUser.value.avatarText,
				avatarUrl: payload.avatarUrl,
				name: payload.name,
				gender: payload.gender
			}
		}

		posts.value.forEach((item) => {
			if (item.author === oldName || item.authorId === loginUser.value?.id) {
				item.author = payload.name
				item.authorId = loginUser.value?.id
			}
		})

		comments.value.forEach((item) => {
			if (item.isMine || item.author === oldName || item.authorId === loginUser.value?.id) {
				item.author = payload.name
				item.authorId = loginUser.value?.id
			}
		})

		syncDerivedState()
	}

	const changePassword = (payload: PasswordChangePayload) => {
		if (!payload.newPassword || payload.newPassword !== payload.confirmPassword) return
		userPassword.value = payload.newPassword
	}

	syncDerivedState()

	return {
		userTestData,
		interactionTestData,
		posts,
		comments,
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
