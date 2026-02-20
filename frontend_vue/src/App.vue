<script setup lang="ts">
import { computed, ref } from 'vue'
import AppTopBar from './components/AppTopBar.vue'
import HomeContent from './components/HomeContent.vue'
import ProfileContent from './components/ProfileContent.vue'
import PublishPostContent from './components/PublishPostContent.vue'
import ArticleDetailContent from './components/ArticleDetailContent.vue'
import LoginModal from './components/LoginModal.vue'
import RegisterModal from './components/RegisterModal.vue'
import type {
	CommentRecord,
	LoginUser,
	PasswordChangePayload,
	Post,
	ProfileEditPayload,
	PublishPayload,
	UserSimpleProfile,
	UserCommentRecord,
	UserTestData
} from './types'

const navItems = ['推荐', '热门', '更新', '关注']
const quickActions = ['发布图文']

const showLoginModal = ref(false)
const showRegisterModal = ref(false)
const currentPage = ref<'home' | 'profile' | 'publish' | 'edit' | 'detail'>('home')
const currentPostId = ref<number | null>(null)
const editingPostId = ref<number | null>(null)
const detailCommentFocusToken = ref(0)
const activeProfileMenu = ref(0)
const account = ref('')
const password = ref('')
const registerEmail = ref('')
const registerPassword = ref('')
const registerConfirmPassword = ref('')
const searchKeyword = ref('')
const activeNav = ref('推荐')
const userPassword = ref('123456')
const loginUser = ref<LoginUser | null>(null)
const viewedProfileUser = ref<LoginUser | null>(null)

const userTestData = ref<UserTestData>({
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
})

const interactionTestData = ref({
	likedPostIds: [101, 103],
	favoritedPostIds: [...userTestData.value.favoritePostIds],
	followedAuthorIds: [201, 203]
})

const canLogin = computed(() => account.value.trim() !== '' && password.value.trim() !== '')
const isLoggedIn = computed(() => !!loginUser.value)
const isRegisterEmailValid = computed(() => /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(registerEmail.value))
const isRegisterPasswordMatch = computed(
	() =>
		registerPassword.value.trim() !== '' &&
		registerConfirmPassword.value.trim() !== '' &&
		registerPassword.value === registerConfirmPassword.value
)
const canRegister = computed(() => isRegisterEmailValid.value && isRegisterPasswordMatch.value)

const normalizedSearchKeyword = computed(() => searchKeyword.value.trim().toLowerCase())

const handleSelectNav = (nav: string) => {
	activeNav.value = nav
	currentPage.value = 'home'
}

const openLoginModal = () => {
	if (isLoggedIn.value) return
	showLoginModal.value = true
	showRegisterModal.value = false
}

const closeLoginModal = () => {
	showLoginModal.value = false
}

const openRegisterModal = () => {
	showLoginModal.value = false
	showRegisterModal.value = true
}

const closeRegisterModal = () => {
	showRegisterModal.value = false
}

const backToLogin = () => {
	showRegisterModal.value = false
	showLoginModal.value = true
}

const mockLogin = () => {
	if (!canLogin.value) return
	const loginName = account.value.includes('@') ? account.value.split('@')[0] : account.value
	loginUser.value = {
		id: Date.now(),
		name: loginName || '测试用户',
		email: account.value,
		avatarText: (loginName || '测').slice(0, 1),
		fans: userTestData.value.fans.length,
		follows: userTestData.value.followings.length
	}
	closeLoginModal()
}

const mockRegister = () => {
	if (!canRegister.value) return
	const name = registerEmail.value.split('@')[0] || '新用户'
	loginUser.value = {
		id: Date.now(),
		name,
		email: registerEmail.value,
		avatarText: name.slice(0, 1),
		fans: userTestData.value.fans.length,
		follows: userTestData.value.followings.length
	}
	closeRegisterModal()
}

const mockLogout = () => {
	loginUser.value = null
	currentPage.value = 'home'
}

const goProfileCenter = () => {
	if (!isLoggedIn.value) return
	if (loginUser.value) {
		viewedProfileUser.value = { ...loginUser.value }
	}
	activeProfileMenu.value = 0
	currentPage.value = 'profile'
}

const openProfileEdit = () => {
	if (!isLoggedIn.value || !loginUser.value) return
	viewedProfileUser.value = { ...loginUser.value }
	activeProfileMenu.value = 5
	currentPage.value = 'profile'
}

const openAuthorProfile = (payload: { userId?: number; userName: string; avatarText: string }) => {
	if (
		loginUser.value &&
		(payload.userId === loginUser.value.id ||
			payload.userName === '我' ||
			payload.userName === loginUser.value.name)
	) {
		viewedProfileUser.value = { ...loginUser.value }
		activeProfileMenu.value = 0
		currentPage.value = 'profile'
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
	activeProfileMenu.value = 0
	currentPage.value = 'profile'
}

const goHome = () => {
	currentPage.value = 'home'
}

const openPostDetail = (postId: number, focusComment = false) => {
	currentPostId.value = postId
	currentPage.value = 'detail'
	if (focusComment) {
		detailCommentFocusToken.value += 1
	}
}

const openPostDetailWithComment = (postId: number) => {
	openPostDetail(postId, true)
}

const goEditPost = (postId: number) => {
	editingPostId.value = postId
	currentPage.value = 'edit'
}

const togglePostLike = (postId: number) => {
	const target = posts.value.find((item) => item.id === postId)
	if (!target) return

	const liked = Boolean(target.isLiked)
	target.isLiked = !liked
	target.likes = liked ? Math.max(0, target.likes - 1) : target.likes + 1

	if (target.isLiked) {
		if (!interactionTestData.value.likedPostIds.includes(postId)) {
			interactionTestData.value.likedPostIds.push(postId)
		}
		return
	}

	interactionTestData.value.likedPostIds = interactionTestData.value.likedPostIds.filter(
		(id) => id !== postId
	)
}

const togglePostFavorite = (postId: number) => {
	const target = posts.value.find((item) => item.id === postId)
	if (!target) return

	const favorited = Boolean(target.isFavorited)
	target.isFavorited = !favorited

	if (target.isFavorited) {
		if (!interactionTestData.value.favoritedPostIds.includes(postId)) {
			interactionTestData.value.favoritedPostIds.push(postId)
		}
		if (!userTestData.value.favoritePostIds.includes(postId)) {
			userTestData.value.favoritePostIds.push(postId)
		}
		return
	}

	interactionTestData.value.favoritedPostIds = interactionTestData.value.favoritedPostIds.filter(
		(id) => id !== postId
	)
	userTestData.value.favoritePostIds = userTestData.value.favoritePostIds.filter((id) => id !== postId)
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

	if (loginUser.value) {
		loginUser.value.follows = userTestData.value.followings.length
	}
}

const currentPost = computed(() =>
	posts.value.find((item) => item.id === currentPostId.value) ?? null
)

const comments = ref<CommentRecord[]>([
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
		authorId: loginUser.value?.id,
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
		authorId: loginUser.value?.id,
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
		authorId: loginUser.value?.id,
		author: '我',
		date: '02-18',
		content: '补给点信息很关键，感谢整理。',
		likes: 8,
		isLiked: false,
		isMine: true
	}
])

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

const syncPostCommentCount = (postId: number) => {
	const post = posts.value.find((item) => item.id === postId)
	if (!post) return
	post.comments = comments.value.filter((item) => item.postId === postId).length
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
}

const toggleCommentLike = (commentId: number) => {
	const target = comments.value.find((item) => item.id === commentId)
	if (!target) return

	if (target.isLiked) {
		target.isLiked = false
		target.likes = Math.max(0, target.likes - 1)
		return
	}

	target.isLiked = true
	target.likes += 1
}

const deleteComment = (commentId: number) => {
	const index = comments.value.findIndex((item) => item.id === commentId)
	if (index === -1) return
	const target = comments.value[index]
	if (!target || !target.isMine) return

	const postId = target.postId
	comments.value.splice(index, 1)
	syncPostCommentCount(postId)
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
	if (loginUser.value) {
		loginUser.value.follows = userTestData.value.followings.length
	}
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
	if (loginUser.value) {
		loginUser.value.follows = userTestData.value.followings.length
	}
}

const toggleProfileFollow = () => {
	if (!isLoggedIn.value) {
		openLoginModal()
		return
	}

	if (!profileUser.value) return

	if (!canFollowProfile.value) {
		window.alert('不能关注自己')
		return
	}

	const userId = profileUser.value.id
	const exists = userTestData.value.followings.some((item) => item.id === userId)
	if (exists) {
		toggleFollowingUser(userId)
		return
	}

	userTestData.value.followings.push({
		id: userId,
		name: profileUser.value.name,
		avatarText: profileUser.value.avatarText
	})
	if (!interactionTestData.value.followedAuthorIds.includes(userId)) {
		interactionTestData.value.followedAuthorIds.push(userId)
	}
	posts.value.forEach((item) => {
		if (item.authorId === userId || item.author === profileUser.value?.name) {
			item.isFollowingAuthor = true
		}
	})
	if (loginUser.value) {
		loginUser.value.follows = userTestData.value.followings.length
	}
}

const goPublish = () => {
	if (!isLoggedIn.value) {
		openLoginModal()
		return
	}
	currentPage.value = 'publish'
}

const posts = ref<Post[]>([
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
])

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

const navFilteredPosts = computed(() => {
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

const filteredHomePosts = computed(() => {
	const keyword = normalizedSearchKeyword.value
	if (!keyword) return navFilteredPosts.value

	return navFilteredPosts.value.filter((post) => {
		const source = [post.title, post.summary, post.author, ...(post.tags || [])]
			.join(' ')
			.toLowerCase()
		return source.includes(keyword)
	})
})

const handleSearch = () => {
	currentPage.value = 'home'
}

const handlePublish = (payload: PublishPayload) => {
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
	currentPage.value = 'home'
}

const handleSaveEditedPost = (payload: PublishPayload) => {
	const postId = editingPostId.value
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

	currentPage.value = 'profile'
}

const handleSaveProfile = (payload: ProfileEditPayload) => {
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
}

const handleChangePassword = (payload: PasswordChangePayload) => {
	if (!payload.newPassword || payload.newPassword !== payload.confirmPassword) return
	userPassword.value = payload.newPassword
}
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
			@logout="mockLogout"
			@select-nav="handleSelectNav"
			@update:search-keyword="searchKeyword = $event"
			@search="handleSearch"
		/>

		<HomeContent
			v-if="currentPage === 'home'"
			:posts="filteredHomePosts"
			:quick-actions="quickActions"
			:search-keyword="searchKeyword"
			@go-publish="goPublish"
			@open-detail="openPostDetail"
			@open-comment-detail="openPostDetailWithComment"
			@toggle-post-like="togglePostLike"
			@toggle-post-favorite="togglePostFavorite"
			@toggle-post-follow="togglePostFollow"
			@open-author-profile="openAuthorProfile"
		/>

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
			@update:active-profile-menu="activeProfileMenu = $event"
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
			@logout="mockLogout"
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
</style>
