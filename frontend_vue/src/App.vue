<script setup lang="ts">
import { computed, ref } from 'vue'
import AppTopBar from './components/AppTopBar.vue'
import HomeContent from './components/HomeContent.vue'
import ProfileContent from './components/ProfileContent.vue'
import PublishPostContent from './components/PublishPostContent.vue'
import ArticleDetailContent from './components/ArticleDetailContent.vue'
import LoginModal from './components/LoginModal.vue'
import RegisterModal from './components/RegisterModal.vue'
import type { LoginUser, Post, PublishPayload } from './types'

const navItems = ['推荐', '热门', '最新', '关注']
const quickActions = ['发布图文']

const mockLoginUser: LoginUser = {
	id: 1001,
	name: '无敌暴龙战士Ultra',
	email: 'test@example.com',
	avatarText: 'U',
	fans: 0,
	follows: 0
}

const showLoginModal = ref(false)
const showRegisterModal = ref(false)
const currentPage = ref<'home' | 'profile' | 'publish' | 'detail'>('home')
const currentPostId = ref<number | null>(null)
const activeProfileMenu = ref(0)
const account = ref('')
const password = ref('')
const registerEmail = ref('')
const registerPassword = ref('')
const registerConfirmPassword = ref('')
const loginUser = ref<LoginUser | null>(mockLoginUser)

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
		fans: 0,
		follows: 0
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
		fans: 0,
		follows: 0
	}
	closeRegisterModal()
}

const mockLogout = () => {
	loginUser.value = null
	currentPage.value = 'home'
}

const goProfileCenter = () => {
	if (!isLoggedIn.value) return
	currentPage.value = 'profile'
}

const goHome = () => {
	currentPage.value = 'home'
}

const openPostDetail = (postId: number) => {
	currentPostId.value = postId
	currentPage.value = 'detail'
}

const currentPost = computed(() =>
	posts.value.find((item) => item.id === currentPostId.value) ?? null
)

const goPublish = () => {
	if (!isLoggedIn.value) {
		openLoginModal()
		return
	}
	currentPage.value = 'publish'
}

const posts = ref<Post[]>([
	{
		id: 1,
		title: '养成指南上新！爱玛养成材料预告',
		summary:
			'想要提前准备爱玛养成材料的绳匠们注意啦：前往养成指南，使用养成材料计算功能，可以提前了解升级所需资源。',
		author: '绝区零',
		time: '02-14',
		tags: ['爱芮', '旧梦的安可曲'],
		images: [
			'linear-gradient(135deg, #ffb2ca, #ff6bac)',
			'linear-gradient(135deg, #a7f0ff, #3f8cff)',
			'linear-gradient(135deg, #9cffb7, #28b463)'
		],
		comments: 226,
		likes: 20000
	},
	{
		id: 2,
		title: '战绩更新｜桌面小组件新增活动日历，快来使用吧！',
		summary:
			'绳匠们好呀~ 战绩工具更新啦！米游社2.102版本更新后，战绩桌面小组件新增活动日历，快来体验吧。',
		author: '绝区零',
		time: '02-14',
		tags: ['绝区零战绩', '旧梦的安可曲'],
		images: [
			'linear-gradient(135deg, #ff92c2, #ff5cb6)',
			'linear-gradient(135deg, #fff08c, #dfc84f)',
			'linear-gradient(135deg, #6fffd2, #2cb8b8)'
		],
		comments: 241,
		likes: 20000
	},
	{
		id: 3,
		title: '《绝区零》舞台演出回顾',
		summary: '闪耀时刻 游园阖刻 绝区行，期待下一次的再相会～',
		author: '绝区零',
		time: '02-13',
		tags: [],
		images: ['linear-gradient(135deg, #9d7bff, #3f52ff)'],
		comments: 198,
		likes: 17000
	}
])

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
</script>

<template>
	<div class="page">
		<AppTopBar
			:nav-items="navItems"
			:is-logged-in="isLoggedIn"
			:login-user="loginUser"
			@go-home="goHome"
			@open-login="openLoginModal"
			@go-profile="goProfileCenter"
			@logout="mockLogout"
		/>

		<HomeContent
			v-if="currentPage === 'home'"
			:posts="posts"
			:quick-actions="quickActions"
			@go-publish="goPublish"
			@open-detail="openPostDetail"
		/>

		<ProfileContent
			v-else-if="currentPage === 'profile'"
			:login-user="loginUser"
			:active-profile-menu="activeProfileMenu"
			@update:active-profile-menu="activeProfileMenu = $event"
			@logout="mockLogout"
		/>

		<PublishPostContent v-else-if="currentPage === 'publish'" @publish="handlePublish" />

		<ArticleDetailContent v-else :post="currentPost" :current-user-name="loginUser?.name || '我'" />

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
