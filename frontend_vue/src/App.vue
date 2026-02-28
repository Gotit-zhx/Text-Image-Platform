<script setup lang="ts">
// 审查状态：部分完成（鉴权/路由/搜索已接入，社区写链路与权限守卫持续加固中）
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import AppTopBar from './components/AppTopBar.vue'
import HomeContent from './components/HomeContent.vue'
import ProfileContent from './components/ProfileContent.vue'
import PublishPostContent from './components/PublishPostContent.vue'
import ArticleDetailContent from './components/ArticleDetailContent.vue'
import LoginModal from './components/LoginModal.vue'
import RegisterModal from './components/RegisterModal.vue'
import { DEFAULT_COMMUNITY_STATS, recommendPostsApi, searchPostsApi } from './api/community'
import { useAuthState } from './composables/useAuthState'
import { useCommunityState } from './composables/useCommunityState'
import type {
	LoginUser,
	PasswordChangePayload,
	Post,
	ProfileEditPayload,
	PublishPayload,
	UserCommentRecord,
	UserSimpleProfile
} from './types'

const navItems = ['推荐', '热门', '更新', '关注']
const quickActions = ['发布图文']

const router = useRouter()
const route = useRoute()

const currentPage = computed<'home' | 'profile' | 'publish' | 'edit' | 'detail'>(() => {
	if (
		route.name === 'home' ||
		route.name === 'profile' ||
		route.name === 'publish' ||
		route.name === 'edit' ||
		route.name === 'detail'
	) {
		return route.name
	}
	return 'home'
})

const currentPostId = computed<number | null>(() => {
	if (route.name !== 'detail') return null
	const raw = Number(route.params.id)
	return Number.isFinite(raw) ? raw : null
})

const editingPostId = computed<number | null>(() => {
	if (route.name !== 'edit') return null
	const raw = Number(route.params.id)
	return Number.isFinite(raw) ? raw : null
})

const detailCommentFocusToken = computed(() => {
	if (route.name !== 'detail') return 0
	const raw = Number(route.query.focusTs ?? 0)
	return Number.isFinite(raw) ? raw : 0
})

const activeProfileMenu = computed(() => {
	if (route.name !== 'profile') return 0
	const raw = Number(route.query.menu ?? 0)
	return Number.isFinite(raw) && raw >= 0 ? raw : 0
})
const searchKeyword = ref('')

const activeNav = computed(() => {
	const navQuery = String(route.query.nav || '推荐')
	return navItems.includes(navQuery) ? navQuery : '推荐'
})

const viewedProfileUser = ref<LoginUser | null>(null)
const serverSearchPosts = ref<Post[] | null>(null)
const serverRecommendedPosts = ref<Post[] | null>(null)
const searchRequestId = ref(0)
const isSearching = ref(false)
const searchError = ref('')
const searchAbortController = ref<AbortController | null>(null)
const isRecommending = ref(false)
const recommendError = ref('')

const {
	showLoginModal,
	showRegisterModal,
	account,
	password,
	registerEmail,
	registerPassword,
	registerConfirmPassword,
	userPassword,
	loginUser,
	canLogin,
	isLoggedIn,
	isRegisterEmailValid,
	isRegisterPasswordMatch,
	canRegister,
	openLoginModal,
	closeLoginModal,
	openRegisterModal,
	closeRegisterModal,
	backToLogin,
	mockLogin,
	mockRegister,
	mockLogout,
	refreshSession
} = useAuthState({
	getUserStats: () => ({ ...DEFAULT_COMMUNITY_STATS })
})

const {
	userTestData,
	interactionTestData,
	posts,
	comments,
	isCommunityReady,
	communityError,
	initCommunityData,
	togglePostLike: togglePostLikeAction,
	togglePostFavorite: togglePostFavoriteAction,
	togglePostFollow: togglePostFollowAction,
	submitComment: submitCommentAction,
	toggleCommentLike: toggleCommentLikeAction,
	deleteComment: deleteCommentAction,
	toggleFollowingUser: toggleFollowingUserAction,
	toggleFanFollow: toggleFanFollowAction,
	toggleProfileFollow: toggleProfileFollowAction,
	publishPost,
	saveEditedPost,
	saveProfile,
	changePassword
} = useCommunityState({
	loginUser,
	isLoggedIn,
	openLoginModal,
	viewedProfileUser,
	userPassword
})

onMounted(async () => {
	await refreshSession()
	await initCommunityData()
})

const normalizedSearchKeyword = computed(() => searchKeyword.value.trim().toLowerCase())

const handleSelectNav = (nav: string) => {
	router.push({
		name: 'home',
		query: {
			nav,
			...(searchKeyword.value.trim() ? { q: searchKeyword.value.trim() } : {})
		}
	})
}

const setActiveProfileMenu = (menu: number) => {
	if (route.name !== 'profile') return
	router.replace({
		name: 'profile',
		query: {
			...route.query,
			menu: String(menu)
		}
	})
}

const goProfileCenter = () => {
	if (!isLoggedIn.value) return
	if (loginUser.value) {
		viewedProfileUser.value = { ...loginUser.value }
	}
	router.push({ name: 'profile', query: { menu: '0' } })
}

const openProfileEdit = () => {
	if (!isLoggedIn.value || !loginUser.value) return
	viewedProfileUser.value = { ...loginUser.value }
	router.push({ name: 'profile', query: { menu: '5' } })
}

const openAuthorProfile = (payload: { userId?: number; userName: string; avatarText: string }) => {
	if (
		loginUser.value &&
		(payload.userId === loginUser.value.id ||
			payload.userName === '我' ||
			payload.userName === loginUser.value.name)
	) {
		viewedProfileUser.value = { ...loginUser.value }
		router.push({ name: 'profile', query: { menu: '0' } })
		return
	}

	const fromPost = posts.value.find(
		(item) => item.authorId === payload.userId || item.author === payload.userName
	)
	const fromFans = userTestData.value.fans.find((item) => item.id === payload.userId)
	const fromFollowing = userTestData.value.followings.find((item) => item.id === payload.userId)

	const profileName = fromPost?.author || fromFans?.name || fromFollowing?.name || payload.userName
	const profileAvatar =
		fromFans?.avatarText || fromFollowing?.avatarText || payload.avatarText || profileName.slice(0, 1)
	const profileId = payload.userId ?? fromPost?.authorId ?? Date.now()

	viewedProfileUser.value = {
		id: profileId,
		name: profileName,
		email: `${profileName}@example.com`,
		avatarText: profileAvatar,
		fans: 0,
		follows: 0
	}
	router.push({
		name: 'profile',
		query: {
			menu: '0',
			userId: String(profileId),
			userName: profileName,
			avatarText: profileAvatar
		}
	})
}

const goHome = () => {
	router.push({ name: 'home' })
}

const openPostDetail = (postId: number, focusComment = false) => {
	router.push({
		name: 'detail',
		params: { id: String(postId) },
		query: focusComment ? { focusTs: String(Date.now()) } : undefined
	})
}

const openPostDetailWithComment = (postId: number) => {
	openPostDetail(postId, true)
}

const ensureLoggedIn = () => {
	if (isLoggedIn.value) return true
	openLoginModal()
	return false
}

const runGuardedAction = async (action: () => Promise<void>) => {
	try {
		await action()
	} catch {
		window.alert('操作失败，请稍后重试')
	}
}

const goEditPost = (postId: number) => {
	if (!ensureLoggedIn() || !loginUser.value) return

	const targetPost = posts.value.find((item) => item.id === postId)
	if (!targetPost) return

	const isAuthor = targetPost.authorId
		? targetPost.authorId === loginUser.value.id
		: targetPost.author === loginUser.value.name

	if (!isAuthor) {
		window.alert('仅作者可编辑该帖子')
		return
	}

	router.push({ name: 'edit', params: { id: String(postId) } })
}

const togglePostLike = async (postId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await togglePostLikeAction(postId)
	})
}

const togglePostFavorite = async (postId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await togglePostFavoriteAction(postId)
	})
}

const togglePostFollow = async (postId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await togglePostFollowAction(postId)
	})
}

const submitComment = async (postId: number, content: string) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await submitCommentAction(postId, content)
	})
}

const toggleCommentLike = async (commentId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await toggleCommentLikeAction(commentId)
	})
}

const deleteComment = async (commentId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await deleteCommentAction(commentId)
	})
}

const toggleFollowingUser = async (userId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await toggleFollowingUserAction(userId)
	})
}

const toggleFanFollow = async (userId: number) => {
	if (!ensureLoggedIn()) return
	await runGuardedAction(async () => {
		await toggleFanFollowAction(userId)
	})
}

const currentPost = computed(() =>
	posts.value.find((item) => item.id === currentPostId.value) ?? null
)

const currentPostComments = computed(() => {
	if (!currentPostId.value) return []
	return comments.value.filter((item) => item.postId === currentPostId.value)
})

const currentEditingPost = computed(() =>
	posts.value.find((item) => item.id === editingPostId.value) ?? null
)

const myPosts = computed(() => {
	if (!loginUser.value) return []
	return posts.value.filter((post) => post.author === loginUser.value?.name)
})

const myComments = computed<UserCommentRecord[]>(() => {
	return comments.value
		.filter((item) => item.isMine)
		.map((item) => {
			const postTitle = posts.value.find((post) => post.id === item.postId)?.title || '帖子已删除'
			return {
				id: item.id,
				postId: item.postId,
				postTitle,
				content: item.content,
				date: item.date,
				likes: item.likes
			}
		})
})

const myFavoritePosts = computed(() => posts.value.filter((post) => post.isFavorited))

const myFans = computed(() => userTestData.value.fans)
const myFollowings = computed(() => userTestData.value.followings)

const profileUser = computed(() => viewedProfileUser.value || loginUser.value)
const isSelfProfile = computed(
	() => !!loginUser.value && !!profileUser.value && loginUser.value.id === profileUser.value.id
)

const profilePosts = computed(() => {
	if (!profileUser.value) return []
	if (isSelfProfile.value) {
		return posts.value.filter((post) => post.author === loginUser.value?.name)
	}
	return posts.value.filter(
		(post) => post.authorId === profileUser.value?.id || post.author === profileUser.value?.name
	)
})

const profileComments = computed<UserCommentRecord[]>(() => {
	if (!profileUser.value) return []
	if (isSelfProfile.value) return myComments.value

	return comments.value
		.filter((item) => item.authorId === profileUser.value?.id || item.author === profileUser.value?.name)
		.map((item) => {
			const postTitle = posts.value.find((post) => post.id === item.postId)?.title || '帖子已删除'
			return {
				id: item.id,
				postId: item.postId,
				postTitle,
				content: item.content,
				date: item.date,
				likes: item.likes
			}
		})
})

const profileFavoritePosts = computed(() => (isSelfProfile.value ? myFavoritePosts.value : []))
const profileFans = computed<UserSimpleProfile[]>(() => (isSelfProfile.value ? myFans.value : []))
const profileFollowings = computed<UserSimpleProfile[]>(() => (isSelfProfile.value ? myFollowings.value : []))

const isProfileFollowed = computed(() => {
	if (!profileUser.value) return false
	return userTestData.value.followings.some(
		(item) => item.id === profileUser.value?.id || item.name === profileUser.value?.name
	)
})

const canFollowProfile = computed(() => {
	if (!loginUser.value || !profileUser.value) return false
	return loginUser.value.id !== profileUser.value.id
})

const toggleProfileFollow = async () => {
	await runGuardedAction(async () => {
		await toggleProfileFollowAction(profileUser.value, canFollowProfile.value)
	})
}

const goPublish = () => {
	if (!isLoggedIn.value) {
		openLoginModal()
		return
	}
	router.push({ name: 'publish' })
}

const sortByLikesDesc = (list: Post[]) => [...list].sort((a, b) => b.likes - a.likes)
const sortByDateDesc = (list: Post[]) =>
	[...list].sort((a, b) => {
		const [am = 0, ad = 0] = a.time.split('-').map(Number)
		const [bm = 0, bd = 0] = b.time.split('-').map(Number)
		return bm * 100 + bd - (am * 100 + ad)
	})

// 推荐接口占位：后续由后端推荐系统替换。
const getRecommendedPosts = (source: Post[]) => {
	return sortByLikesDesc(source)
}

const postMapById = computed(() => {
	const map = new Map<number, Post>()
	posts.value.forEach((item) => map.set(item.id, item))
	return map
})

const resolvePostList = (list: Post[]) =>
	list.map((item) => postMapById.value.get(item.id) ?? item)

const navFilteredPosts = computed(() => {
	if (activeNav.value === '推荐' && serverRecommendedPosts.value && serverRecommendedPosts.value.length) {
		return resolvePostList(serverRecommendedPosts.value)
	}

	if (activeNav.value === '热门') {
		return sortByLikesDesc(posts.value)
	}

	if (activeNav.value === '更新') {
		return sortByDateDesc(posts.value)
	}

	if (activeNav.value === '关注') {
		return posts.value.filter(
			(post) =>
				post.isFollowingAuthor ||
				(post.authorId ? interactionTestData.value.followedAuthorIds.includes(post.authorId) : false)
		)
	}

	return getRecommendedPosts(posts.value)
})

const localFilteredHomePosts = computed(() => {
	const keyword = normalizedSearchKeyword.value
	if (!keyword) return navFilteredPosts.value

	return navFilteredPosts.value.filter((post) => {
		const source = [post.title, post.summary, post.author, ...(post.tags || [])]
			.join(' ')
			.toLowerCase()
		return source.includes(keyword)
	})
})

const filteredHomePosts = computed(() => {
	if (normalizedSearchKeyword.value && serverSearchPosts.value) {
		return resolvePostList(serverSearchPosts.value)
	}
	return localFilteredHomePosts.value
})

const runSearch = async () => {
	const keyword = searchKeyword.value.trim()
	if (!keyword) {
		searchAbortController.value?.abort()
		searchAbortController.value = null
		serverSearchPosts.value = null
		searchError.value = ''
		isSearching.value = false
		return
	}

	searchAbortController.value?.abort()
	searchAbortController.value = new AbortController()

	const currentRequestId = searchRequestId.value + 1
	searchRequestId.value = currentRequestId
	isSearching.value = true
	searchError.value = ''

	try {
		const result = await searchPostsApi(keyword, activeNav.value, {
			signal: searchAbortController.value.signal
		})
		if (searchRequestId.value !== currentRequestId) return
		serverSearchPosts.value = result
		searchError.value = ''
	} catch (error) {
		if (searchRequestId.value !== currentRequestId) return
		if (error instanceof Error && error.name === 'AbortError') return
		serverSearchPosts.value = null
		searchError.value = '搜索服务暂不可用，已回退本地结果'
	} finally {
		if (searchRequestId.value === currentRequestId) {
			isSearching.value = false
		}
	}
}

const loadRecommendPosts = async () => {
	if (!isCommunityReady.value) return
	isRecommending.value = true
	recommendError.value = ''
	try {
		serverRecommendedPosts.value = await recommendPostsApi(20)
	} catch {
		serverRecommendedPosts.value = null
		recommendError.value = '推荐服务暂不可用，已回退热门内容'
	} finally {
		isRecommending.value = false
	}
}

const handleSearch = () => {
	const keyword = searchKeyword.value.trim()
	router.push({
		name: 'home',
		query: {
			nav: activeNav.value,
			...(keyword ? { q: keyword } : {})
		}
	})
}

const handlePublish = async (payload: PublishPayload) => {
	await publishPost(payload)
	router.push({ name: 'home' })
}

const handleSaveEditedPost = async (payload: PublishPayload) => {
	if (!ensureLoggedIn() || !loginUser.value) return

	const postId = editingPostId.value
	if (!postId) return

	const targetPost = posts.value.find((item) => item.id === postId)
	if (!targetPost) {
		router.replace({ name: 'home' })
		return
	}

	const isAuthor = targetPost.authorId
		? targetPost.authorId === loginUser.value.id
		: targetPost.author === loginUser.value.name

	if (!isAuthor) {
		window.alert('仅作者可编辑该帖子')
		router.replace({ name: 'detail', params: { id: String(postId) } })
		return
	}

	await saveEditedPost(editingPostId.value, payload)
	router.push({ name: 'profile', query: { menu: '0' } })
}

const handleSaveProfile = (payload: ProfileEditPayload) => {
	saveProfile(payload)
}

const handleChangePassword = (payload: PasswordChangePayload) => {
	changePassword(payload)
}

const handleLogout = async () => {
	await mockLogout()
	viewedProfileUser.value = null
	router.push({ name: 'home' })
}

watch(
	[() => route.fullPath, () => loginUser.value],
	() => {
		if (route.name !== 'profile') {
			viewedProfileUser.value = null
			return
		}

		const routeUserIdRaw = route.query.userId
		const routeUserNameRaw = route.query.userName
		const routeAvatarTextRaw = route.query.avatarText

		if (!routeUserIdRaw && !routeUserNameRaw) {
			viewedProfileUser.value = loginUser.value ? { ...loginUser.value } : null
			return
		}

		const routeUserId = routeUserIdRaw ? Number(routeUserIdRaw) : undefined
		const routeUserName = String(routeUserNameRaw || '')
		const routeAvatarText = String(routeAvatarTextRaw || routeUserName.slice(0, 1))

		if (loginUser.value && (routeUserId === loginUser.value.id || routeUserName === loginUser.value.name)) {
			viewedProfileUser.value = { ...loginUser.value }
			return
		}

		const fromPost = posts.value.find(
			(item) => item.authorId === routeUserId || item.author === routeUserName
		)
		const fromFans = userTestData.value.fans.find((item) => item.id === routeUserId)
		const fromFollowing = userTestData.value.followings.find((item) => item.id === routeUserId)

		const profileName =
			fromPost?.author || fromFans?.name || fromFollowing?.name || routeUserName || '未知用户'
		const profileAvatar =
			fromFans?.avatarText ||
			fromFollowing?.avatarText ||
			routeAvatarText ||
			profileName.slice(0, 1)
		const profileId = routeUserId ?? fromPost?.authorId ?? Date.now()

		viewedProfileUser.value = {
			id: profileId,
			name: profileName,
			email: `${profileName}@example.com`,
			avatarText: profileAvatar,
			fans: 0,
			follows: 0
		}
	},
	{ immediate: true }
)

watch(
	() => route.query.q,
	(newValue) => {
		searchKeyword.value = typeof newValue === 'string' ? newValue : ''
		runSearch()
	},
	{ immediate: true }
)

watch(
	() => route.query.nav,
	() => {
		if (activeNav.value === '推荐') {
			loadRecommendPosts()
		}

		if (searchKeyword.value.trim()) {
			runSearch()
		}
	}
)

watch(
	() => [isCommunityReady.value, isLoggedIn.value],
	() => {
		if (!isCommunityReady.value) return
		loadRecommendPosts()
	},
	{ immediate: true }
)

watch(
	() => [userTestData.value.fans.length, userTestData.value.followings.length, loginUser.value?.id],
	() => {
		if (!loginUser.value) return
		loginUser.value.fans = userTestData.value.fans.length
		loginUser.value.follows = userTestData.value.followings.length
	},
	{ immediate: true }
)

watch(
	() => [route.name, route.params.id, loginUser.value?.id, posts.value.length],
	() => {
		if (route.name !== 'edit') return
		if (!loginUser.value) return

		const routePostId = Number(route.params.id)
		if (!Number.isFinite(routePostId)) {
			router.replace({ name: 'home' })
			return
		}

		const targetPost = posts.value.find((item) => item.id === routePostId)
		if (!targetPost) {
			router.replace({ name: 'home' })
			return
		}

		const isAuthor = targetPost.authorId
			? targetPost.authorId === loginUser.value.id
			: targetPost.author === loginUser.value.name

		if (!isAuthor) {
			window.alert('仅作者可编辑该帖子')
			router.replace({ name: 'detail', params: { id: String(routePostId) } })
		}
	},
	{ immediate: true }
)

watch(
	() => [isLoggedIn.value, route.query.redirect],
	() => {
		if (!isLoggedIn.value && typeof route.query.redirect === 'string') {
			openLoginModal()
			return
		}

		if (!isLoggedIn.value) return
		const redirectTarget = route.query.redirect
		if (typeof redirectTarget !== 'string' || !redirectTarget.startsWith('/')) return
		router.replace(redirectTarget)
	}
)
</script>

<template>
	<div class="page">
		<AppTopBar
			:nav-items="navItems"
			:active-nav="activeNav"
			:is-logged-in="isLoggedIn"
			:login-user="loginUser"
			:search-keyword="searchKeyword"
			@go-home="goHome"
			@open-login="openLoginModal"
			@go-profile="goProfileCenter"
			@logout="handleLogout"
			@select-nav="handleSelectNav"
			@update:search-keyword="searchKeyword = $event"
			@search="handleSearch"
		/>

		<HomeContent
			v-if="currentPage === 'home' && isCommunityReady"
			:posts="filteredHomePosts"
			:quick-actions="quickActions"
			:search-keyword="searchKeyword"
			:is-searching="isSearching"
			:search-error="searchError"
			@go-publish="goPublish"
			@open-detail="openPostDetail"
			@open-comment-detail="openPostDetailWithComment"
			@toggle-post-like="togglePostLike"
			@toggle-post-favorite="togglePostFavorite"
			@toggle-post-follow="togglePostFollow"
			@open-author-profile="openAuthorProfile"
		/>

		<main v-else-if="!isCommunityReady" class="loading-box">
			{{ communityError || '正在加载社区数据...' }}
		</main>

		<ProfileContent
			v-else-if="currentPage === 'profile'"
			:login-user="profileUser"
			:is-self-profile="isSelfProfile"
			:is-profile-followed="isProfileFollowed"
			:can-follow-profile="canFollowProfile"
			:active-profile-menu="activeProfileMenu"
			:my-posts="profilePosts"
			:my-comments="profileComments"
			:my-favorite-posts="profileFavoritePosts"
			:my-fans="profileFans"
			:my-followings="profileFollowings"
			@update:active-profile-menu="setActiveProfileMenu"
			@open-detail="openPostDetail"
			@edit-post="goEditPost"
			@open-comment-detail="openPostDetailWithComment"
			@toggle-post-like="togglePostLike"
			@toggle-post-favorite="togglePostFavorite"
			@delete-my-comment="deleteComment"
			@toggle-following-user="toggleFollowingUser"
			@toggle-fan-follow="toggleFanFollow"
			@open-author-profile="openAuthorProfile"
			@toggle-profile-follow="toggleProfileFollow"
			@open-profile-edit="openProfileEdit"
			@save-profile="handleSaveProfile"
			@change-password="handleChangePassword"
			@logout="handleLogout"
		/>

		<PublishPostContent v-else-if="currentPage === 'publish'" @publish="handlePublish" />

		<PublishPostContent
			v-else-if="currentPage === 'edit'"
			mode="edit"
			:initial-post="currentEditingPost"
			@save-edit="handleSaveEditedPost"
		/>

		<ArticleDetailContent
			v-else
			:post="currentPost"
			:current-user-name="loginUser?.name || '我'"
			:focus-comment-token="detailCommentFocusToken"
			:comments="currentPostComments"
			@toggle-post-like="togglePostLike"
			@toggle-post-favorite="togglePostFavorite"
			@toggle-post-follow="togglePostFollow"
			@submit-comment="submitComment"
			@toggle-comment-like="toggleCommentLike"
			@delete-comment="deleteComment"
			@open-author-profile="openAuthorProfile"
		/>

		<LoginModal
			:visible="showLoginModal"
			:account="account"
			:password="password"
			:can-login="canLogin"
			@close="closeLoginModal"
			@update:account="account = $event"
			@update:password="password = $event"
			@login="mockLogin"
			@open-register="openRegisterModal"
		/>

		<RegisterModal
			:visible="showRegisterModal"
			:email="registerEmail"
			:password="registerPassword"
			:confirm-password="registerConfirmPassword"
			:is-email-valid="isRegisterEmailValid"
			:is-password-match="isRegisterPasswordMatch"
			:can-register="canRegister"
			@close="closeRegisterModal"
			@update:email="registerEmail = $event"
			@update:password="registerPassword = $event"
			@update:confirm-password="registerConfirmPassword = $event"
			@register="mockRegister"
			@back-login="backToLogin"
		/>
	</div>
</template>

<style>
:root {
	color-scheme: light;
}

* {
	box-sizing: border-box;
}

body {
	margin: 0;
	font-family: 'PingFang SC', 'Microsoft YaHei', 'Helvetica Neue', Helvetica, Arial, sans-serif;
	background: #eff1f5;
	color: #1d2433;
}

.page {
	min-height: 100vh;
}

.loading-box {
	max-width: 1180px;
	margin: 20px auto;
	padding: 36px 20px;
	border-radius: 12px;
	border: 1px solid #e9edf3;
	background: #fff;
	color: #6f7890;
	text-align: center;
}
</style>
