<script setup lang="ts">
import { computed, ref } from 'vue'

type Post = {
	id: number
	title: string
	summary: string
	author: string
	time: string
	tags: string[]
	images: string[]
	comments: number
	likes: number
}

type LoginUser = {
	id: number
	name: string
	email: string
	avatarText: string
	fans: number
	follows: number
}

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
const currentPage = ref<'home' | 'profile'>('home')
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
		avatarText: (name || '新').slice(0, 1),
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

const formatCount = (count: number): string => {
	if (count >= 10000) {
		const value = count / 10000
		const formatted = (Math.floor(value * 10) / 10).toString().replace(/\.0$/, '')
		return `${formatted}万+`
	}

	return `${count}`
}

const posts: Post[] = [
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
]
</script>

<template>
	<div class="page">
		<header class="topbar">
			<div class="topbar-inner">
				<div class="brand-wrap">
					<div class="logo" @click="goHome">米</div>
					<div class="brand-text" @click="goHome">米游社</div>
					<div class="divider">·</div>
					<div class="zone">绝区零</div>
				</div>

				<nav class="nav">
					<a
						v-for="item in navItems"
						:key="item"
						href="#"
						class="nav-item"
						:class="{ active: item === '首页' }"
					>
						{{ item }}
					</a>
				</nav>

				<div class="topbar-right">
					<div class="search">🔍</div>
					<div v-if="isLoggedIn" class="user-entry">
						<div class="avatar">{{ loginUser?.avatarText || '' }}</div>
						<div class="user-dropdown">
							<div class="user-dropdown-head">
								<div class="user-big-avatar">{{ loginUser?.avatarText || '' }}</div>
								<div class="user-name">{{ loginUser?.name }}</div>
								<div class="user-stats">
									<div class="user-stat">
										<p>{{ loginUser?.fans ?? 0 }}</p>
										<span>粉丝</span>
									</div>
									<div class="user-stat">
										<p>{{ loginUser?.follows ?? 0 }}</p>
										<span>关注</span>
									</div>
								</div>
							</div>
							<div class="user-menu">
								<a href="#" @click.prevent="goProfileCenter">个人中心</a>
							</div>
							<div class="user-menu logout-area">
								<a href="#" @click.prevent="mockLogout">退出登录</a>
							</div>
						</div>
					</div>
					<div v-else class="avatar" @click="openLoginModal"></div>
				</div>
			</div>
		</header>

		<main v-if="currentPage === 'home'" class="layout">
			<section class="feed">
				<article v-for="post in posts" :key="post.id" class="card">
					<div class="card-head">
						<div class="author-wrap">
							<div class="author-avatar"></div>
							<div class="author-meta">
								<div class="meta-line">
									<span class="author">{{ post.author }}</span>
									<span class="time">{{ post.time }}</span>
								</div>
								<h3 class="title">
									<!-- <span class="official">官方</span> -->
									{{ post.title }}
								</h3>
							</div>
						</div>

						<button class="follow">关注</button>
					</div>

					<p class="summary">{{ post.summary }}</p>

					<div class="images" :class="{ single: post.images.length === 1 }">
						<div
							v-for="(image, idx) in post.images"
							:key="`${post.id}-${idx}`"
							class="img"
							:style="{ background: image }"
						>
							<span class="img-watermark">图文</span>
						</div>
					</div>

					<div v-if="post.tags.length" class="tags">
						<span v-for="tag in post.tags" :key="tag" class="tag">{{ tag }}</span>
					</div>

					<div class="stats">
						<span>💬 {{ post.comments }}</span>
						<span>👍 {{ formatCount(post.likes) }}</span>
					</div>
				</article>
			</section>

			<aside class="creator-panel">
				<div class="panel-card">
					<button v-for="action in quickActions" :key="action" class="publish-btn">
						<span class="publish-text">{{ action }}</span>
						<span class="publish-arrow">›</span>
					</button>
				</div>
			</aside>
		</main>

		<main v-else class="profile-page">
			<section class="profile-summary-card">
				<div class="profile-summary-left">
					<div class="profile-avatar">{{ loginUser?.avatarText || '' }}</div>
					<div>
						<div class="profile-name-row">
							<h2>{{ loginUser?.name || '用户' }}</h2>
							<span class="level-badge">Lv.1</span>
						</div>
						<p class="profile-id">通行证ID: {{ loginUser?.id || 0 }}</p>
						<div class="profile-summary-stats">
							<span><b>{{ loginUser?.fans ?? 0 }}</b> 粉丝</span>
							<span><b>{{ loginUser?.follows ?? 0 }}</b> 关注</span>
							<span><b>0</b> 获赞</span>
						</div>
					</div>
				</div>
				<button class="profile-edit-btn">编辑</button>
			</section>

			<section class="profile-main-grid">
				<aside class="profile-sidebar">
					<h3>个人中心</h3>
					<ul>
						<li
							v-for="(item, idx) in ['我的发帖', '我的评论', '我的收藏', '我的粉丝', '我的关注']"
							:key="item"
							class="profile-menu-item"
							:class="{ active: activeProfileMenu === idx }"
							@click="activeProfileMenu = idx"
						>
							<span class="menu-icon">●</span>
							{{ item }}
						</li>
					</ul>
					<div class="profile-side-logout">
						<a href="#" @click.prevent="mockLogout">退出登录</a>
					</div>
				</aside>

				<section class="profile-content">
					<div class="profile-content-head">{{ ['我的发帖', '我的评论', '我的收藏', '我的粉丝', '我的关注'][activeProfileMenu] }}</div>
					<div class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>暂无内容</p>
					</div>
				</section>
			</section>
		</main>

		<div v-if="showLoginModal" class="login-overlay" @click="closeLoginModal">
			<div class="login-modal" @click.stop>
				<button class="login-close" @click="closeLoginModal">×</button>
				<div class="login-brand">miHoYo</div>
				<div class="login-sub-brand">TECH OTAKUS SAVE THE WORLD</div>
				<h3 class="login-title">密码登录</h3>
				<p class="login-mock-tip">测试账号：test@example.com / 123456</p>

				<input v-model="account" class="login-input" type="text" placeholder="手机号/邮箱" />
				<input v-model="password" class="login-input" type="password" placeholder="密码" />

				<button class="login-btn" :disabled="!canLogin" @click="mockLogin">登录</button>

				<div class="login-footer">
					<a href="#">忘记密码</a>
					<a href="#" @click.prevent="openRegisterModal">注册账号</a>
				</div>
			</div>
		</div>

		<div v-if="showRegisterModal" class="login-overlay" @click="closeRegisterModal">
			<div class="login-modal" @click.stop>
				<button class="login-close" @click="closeRegisterModal">×</button>
				<div class="login-brand">miHoYo</div>
				<div class="login-sub-brand">TECH OTAKUS SAVE THE WORLD</div>
				<h3 class="login-title">邮箱注册</h3>

				<input v-model="registerEmail" class="login-input" type="email" placeholder="请输入邮箱" />
				<input
					v-model="registerPassword"
					class="login-input"
					type="password"
					placeholder="请输入密码"
				/>
				<input
					v-model="registerConfirmPassword"
					class="login-input"
					type="password"
					placeholder="请确认密码"
				/>

				<p v-if="registerEmail && !isRegisterEmailValid" class="login-tip">请输入正确的邮箱格式</p>
				<p v-else-if="registerConfirmPassword && !isRegisterPasswordMatch" class="login-tip">
					两次输入的密码不一致
				</p>

				<button class="login-btn" :disabled="!canRegister" @click="mockRegister">注册</button>

				<div class="login-footer single-link">
					<a href="#" @click.prevent="backToLogin">返回登录</a>
				</div>
			</div>
		</div>
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

a {
	color: inherit;
	text-decoration: none;
}

.page {
	min-height: 100vh;
}

.topbar {
	background: linear-gradient(90deg, #1d2140 0%, #101628 100%);
	color: #eef3ff;
	position: sticky;
	top: 0;
	z-index: 10;
}

.topbar-inner {
	max-width: 1180px;
	margin: 0 auto;
	height: 64px;
	padding: 0 16px;
	display: flex;
	align-items: center;
	gap: 18px;
}

.brand-wrap {
	display: flex;
	align-items: center;
	gap: 8px;
	min-width: 186px;
}

.logo {
	width: 30px;
	height: 30px;
	border-radius: 8px;
	background: #58c9ff;
	color: #fff;
	font-weight: 800;
	display: grid;
	place-items: center;
	cursor: pointer;
}

.brand-text,
.zone {
	font-weight: 600;
}

.brand-text {
	cursor: pointer;
}

.divider {
	opacity: 0.65;
}

.nav {
	display: flex;
	align-items: center;
	gap: 6px;
	flex: 1;
}

.nav-item {
	font-size: 14px;
	padding: 22px 12px 20px;
	border-bottom: 2px solid transparent;
	opacity: 0.85;
}

.nav-item.active {
	opacity: 1;
	background: rgba(255, 255, 255, 0.1);
	border-bottom-color: #6b8dff;
}

.topbar-right {
	display: flex;
	align-items: center;
	gap: 12px;
}

.search {
	width: 120px;
	height: 30px;
	border-radius: 999px;
	display: flex;
	align-items: center;
	justify-content: flex-end;
	padding-right: 10px;
	background: rgba(255, 255, 255, 0.14);
}

.avatar {
	width: 32px;
	height: 32px;
	border-radius: 50%;
	background: radial-gradient(circle at 35% 35%, #fff, #d6d8df);
	border: 2px solid rgba(255, 255, 255, 0.3);
	cursor: pointer;
	display: grid;
	place-items: center;
	font-size: 14px;
	font-weight: 700;
	color: #586178;
}

.user-entry {
	position: relative;
	height: 64px;
	display: flex;
	align-items: center;
}

.user-dropdown {
	position: absolute;
	top: calc(100% - 4px);
	right: 0;
	width: 320px;
	background: #fff;
	border-radius: 0 0 10px 10px;
	border: 1px solid #e7eaf0;
	box-shadow: 0 14px 36px rgba(20, 29, 48, 0.18);
	overflow: hidden;
	display: none;
	z-index: 20;
}

.user-entry:hover .user-dropdown {
	display: block;
}

.user-dropdown-head {
	padding: 22px 20px 18px;
	display: flex;
	flex-direction: column;
	align-items: center;
	border-bottom: 1px solid #edf0f5;
}

.user-big-avatar {
	width: 106px;
	height: 106px;
	border-radius: 50%;
	display: grid;
	place-items: center;
	font-size: 42px;
	font-weight: 700;
	color: #5f6a84;
	background: #c3ebfb;
	border: 2px solid #a8dff6;
}

.user-name {
	margin-top: 14px;
	font-size: 18px;
	line-height: 1.2;
	color: #2f3748;
	font-weight: 500;
}

.user-stats {
	margin-top: 16px;
	width: 100%;
	display: flex;
	justify-content: center;
	gap: 72px;
}

.user-stat {
	text-align: center;
}

.user-stat p {
	margin: 0;
	font-size: 38px;
	line-height: 1;
	color: #525a6d;
}

.user-stat span {
	display: block;
	margin-top: 8px;
	font-size: 14px;
	line-height: 1;
	color: #b4bac6;
}

.user-menu {
	padding: 12px 0;
	border-bottom: 1px solid #edf0f5;
}

.user-menu a {
	display: block;
	padding: 14px 32px;
	font-size: 16px;
	line-height: 1.2;
	color: #2f3748;
}

.user-menu a:hover {
	background: #f6f8fb;
}

.logout-area {
	border-bottom: none;
}

.layout {
	max-width: 1180px;
	margin: 20px auto;
	padding: 0 16px;
	display: grid;
	grid-template-columns: 1fr 280px;
	gap: 16px;
}

.profile-page {
	max-width: 1180px;
	margin: 20px auto;
	padding: 0 16px;
	display: flex;
	flex-direction: column;
	gap: 16px;
}

.profile-summary-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 8px;
	padding: 18px 24px;
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
}

.profile-summary-left {
	display: flex;
	gap: 18px;
}

.profile-avatar {
	width: 104px;
	height: 104px;
	border-radius: 50%;
	display: grid;
	place-items: center;
	font-size: 40px;
	font-weight: 700;
	color: #5f6a84;
	background: #c3ebfb;
	border: 2px solid #a8dff6;
}

.profile-name-row {
	display: flex;
	align-items: center;
	gap: 8px;
}

.profile-name-row h2 {
	margin: 2px 0 0;
	font-size: 30px;
	line-height: 1.2;
}

.level-badge {
	font-size: 12px;
	line-height: 1;
	padding: 3px 8px;
	border-radius: 3px;
	background: #4ec3ff;
	color: #fff;
}

.profile-id {
	margin: 6px 0 0;
	font-size: 13px;
	color: #b1b7c3;
}

.profile-summary-stats {
	margin-top: 22px;
	display: flex;
	gap: 34px;
	font-size: 16px;
	color: #a5adbd;
}

.profile-summary-stats b {
	color: #2f3748;
	margin-right: 4px;
}

.profile-edit-btn {
	height: 32px;
	min-width: 78px;
	border-radius: 4px;
	border: 1px solid #53bcff;
	background: #fff;
	color: #53bcff;
	cursor: pointer;
}

.profile-main-grid {
	display: grid;
	grid-template-columns: 245px 1fr;
	gap: 16px;
}

.profile-sidebar {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 8px;
	padding: 12px 0;
}

.profile-sidebar h3 {
	margin: 0;
	padding: 0 24px 12px;
	font-size: 16px;
	font-weight: 600;
	border-bottom: 1px solid #edf0f5;
}

.profile-sidebar ul {
	list-style: none;
	margin: 0;
	padding: 8px 0;
}

.profile-menu-item {
	height: 44px;
	padding: 0 24px;
	display: flex;
	align-items: center;
	gap: 10px;
	font-size: 15px;
	color: #636e84;
	cursor: pointer;
}

.profile-menu-item:hover {
	background: #f7f9fc;
}

.profile-menu-item.active {
	color: #18b0ff;
}

.menu-icon {
	font-size: 10px;
	opacity: 0.7;
}

.profile-side-logout {
	margin-top: 6px;
	padding-top: 10px;
	border-top: 1px solid #edf0f5;
}

.profile-side-logout a {
	display: block;
	padding: 10px 24px;
	font-size: 15px;
	color: #636e84;
}

.profile-content {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 8px;
	min-height: 460px;
	display: flex;
	flex-direction: column;
}

.profile-content-head {
	height: 44px;
	padding: 0 20px;
	display: flex;
	align-items: center;
	border-bottom: 1px solid #edf0f5;
	font-size: 18px;
	color: #2f3748;
}

.profile-empty {
	flex: 1;
	display: flex;
	flex-direction: column;
	justify-content: center;
	align-items: center;
	color: #c2c8d4;
	gap: 8px;
}

.empty-planet {
	width: 100px;
	height: 100px;
	border-radius: 50%;
	border: 2px solid #e6eaf2;
	display: grid;
	place-items: center;
	font-size: 40px;
}

.feed {
	display: flex;
	flex-direction: column;
	gap: 14px;
}

.card {
	background: #fff;
	border-radius: 12px;
	border: 1px solid #e9edf3;
	padding: 16px 20px 14px;
}

.card-head {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 10px;
}

.author-wrap {
	display: flex;
	gap: 10px;
}

.author-avatar {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	background: linear-gradient(145deg, #f4bf80, #e88e47);
	box-shadow: inset 0 0 0 2px #fff;
	border: 1px solid #e7d3bf;
}

.meta-line {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	font-size: 12px;
	color: #8c94a7;
}

.author {
	font-size: 13px;
	font-weight: 600;
	color: #515869;
}

.title {
	margin: 6px 0 0;
	font-size: 22px;
	line-height: 1.35;
	font-weight: 700;
	letter-spacing: 0.3px;
}

.follow {
	height: 32px;
	min-width: 74px;
	border-radius: 999px;
	border: none;
	cursor: pointer;
	color: #fff;
	font-weight: 600;
	background: linear-gradient(180deg, #30c6ff, #13a6f6);
}

.summary {
	margin: 10px 0 12px 46px;
	color: #697084;
	font-size: 14px;
	line-height: 1.6;
}

.images {
	margin-left: 46px;
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 8px;
	max-width: 520px;
}

.images.single {
	grid-template-columns: 1fr;
	max-width: 180px;
}

.img {
	position: relative;
	border-radius: 8px;
	aspect-ratio: 16 / 10;
	overflow: hidden;
}

.img-watermark {
	position: absolute;
	right: 8px;
	bottom: 8px;
	font-size: 11px;
	color: rgba(255, 255, 255, 0.95);
	background: rgba(0, 0, 0, 0.35);
	border-radius: 999px;
	padding: 2px 8px;
}

.tags {
	margin: 10px 0 8px 46px;
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.tag {
	background: #f3f5f8;
	color: #798197;
	font-size: 12px;
	border-radius: 999px;
	padding: 4px 10px;
}

.stats {
	margin-left: 46px;
	color: #9aa3b6;
	display: flex;
	justify-content: flex-end;
	gap: 18px;
	font-size: 13px;
}

.creator-panel {
	position: relative;
}

.panel-card {
	background: #fff;
	border-radius: 12px;
	border: 1px solid #e9edf3;
	padding: 16px;
	position: sticky;
	top: 84px;
}

.publish-btn {
	width: 100%;
	border: none;
	cursor: pointer;
	position: relative;
	border-radius: 8px;
	padding: 12px 12px;
	margin-bottom: 10px;
	background: linear-gradient(180deg, #ffe35f, #ffd835);
	color: #2c2a1a;
	font-size: 16px;
	font-weight: 700;
	display: flex;
	justify-content: center;
	align-items: center;
}

.publish-text {
	text-align: center;
}

.publish-arrow {
	position: absolute;
	right: 12px;
}

.login-overlay {
	position: fixed;
	inset: 0;
	background: rgba(17, 20, 29, 0.62);
	display: grid;
	place-items: center;
	z-index: 40;
	padding: 16px;
}

.login-modal {
	position: relative;
	width: 100%;
	max-width: 365px;
	background: #fff;
	border-radius: 12px;
	padding: 28px 30px 22px;
	box-shadow: 0 18px 48px rgba(10, 15, 35, 0.28);
}

.login-close {
	position: absolute;
	right: 12px;
	top: 10px;
	border: none;
	background: transparent;
	font-size: 24px;
	line-height: 1;
	color: #b3b8c4;
	cursor: pointer;
}

.login-brand {
	text-align: center;
	font-size: 42px;
	line-height: 1;
	font-weight: 800;
	letter-spacing: 1px;
	color: #53c4ff;
	margin-top: 4px;
}

.login-sub-brand {
	text-align: center;
	font-size: 9px;
	color: #9dc5df;
	letter-spacing: 1.2px;
	margin-top: 2px;
	margin-bottom: 18px;
}

.login-title {
	margin: 0 0 18px;
	text-align: center;
	font-size: 24px;
	font-weight: 700;
	color: #222c3f;
}

.login-mock-tip {
	margin: -8px 0 14px;
	text-align: center;
	font-size: 12px;
	color: #8f97a8;
}

.login-input {
	width: 100%;
	height: 44px;
	border: 1px solid #e3e7ef;
	border-radius: 8px;
	padding: 0 12px;
	font-size: 14px;
	outline: none;
	margin-bottom: 10px;
	background: #fafbfd;
}

.login-input:focus {
	border-color: #8bc4ff;
	background: #fff;
}

.login-btn {
	margin-top: 8px;
	width: 100%;
	height: 44px;
	border: none;
	border-radius: 8px;
	font-size: 16px;
	font-weight: 700;
	background: #d8dce4;
	color: #8f97a8;
	cursor: pointer;
}

.login-btn:disabled {
	cursor: not-allowed;
}

.login-btn:not(:disabled) {
	background: linear-gradient(180deg, #42c8ff, #17a7f6);
	color: #fff;
}

.login-tip {
	margin: -2px 0 10px;
	font-size: 12px;
	color: #f56c6c;
}

.login-footer {
	margin-top: 16px;
	display: flex;
	justify-content: space-between;
	font-size: 14px;
}

.login-footer.single-link {
	justify-content: center;
}

.login-footer a {
	color: #57a7ee;
}


@media (max-width: 1024px) {
	.layout {
		grid-template-columns: 1fr;
	}

	.profile-main-grid {
		grid-template-columns: 1fr;
	}

	.creator-panel {
		order: -1;
	}

	.panel-card {
		position: static;
	}
}

@media (max-width: 768px) {
	.topbar-inner {
		gap: 8px;
	}

	.brand-wrap {
		min-width: auto;
	}

	.nav {
		overflow-x: auto;
		white-space: nowrap;
	}

	.title {
		font-size: 18px;
	}

	.summary,
	.images,
	.tags,
	.stats {
		margin-left: 0;
	}

	.images {
		max-width: none;
	}
}
</style>
