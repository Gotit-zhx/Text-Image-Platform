<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import type { LoginUser } from '../types'

defineProps<{
	navItems: string[]
	activeNav: string
	isLoggedIn: boolean
	loginUser: LoginUser | null
	searchKeyword: string
}>()

const emit = defineEmits<{
	(e: 'go-home'): void
	(e: 'open-login'): void
	(e: 'go-profile'): void
	(e: 'logout'): void
	(e: 'select-nav', nav: string): void
	(e: 'update:searchKeyword', value: string): void
	(e: 'search'): void
}>()

const handleSearchKeywordChange = (value: unknown) => {
	emit('update:searchKeyword', String(value || ''))
}
</script>

<template>
	<header class="topbar">
		<div class="topbar-inner">
			<div class="brand-wrap" @click="emit('go-home')">
				<div class="logo">🍀</div>
				<div class="brand-text">百草园</div>
				<!-- <div class="divider">·</div>
				<div class="zone">百草园</div> -->
			</div>

			<nav class="nav">
				<a
					v-for="(item, idx) in navItems"
					:key="item"
					href="#"
					class="nav-item"
					:class="{ active: activeNav === item }"
					@click.prevent="emit('select-nav', item)"
				>
					{{ item }}
				</a>
			</nav>

			<div class="topbar-right">
				<div class="search">
					<el-input
						:model-value="searchKeyword"
						placeholder="搜索文章/作者/标签"
						class="search-input"
						@update:model-value="handleSearchKeywordChange"
						@keyup.enter="emit('search')"
					>
						<template #prefix>
							<el-icon><Search /></el-icon>
						</template>
					</el-input>
					<el-button type="primary" class="search-btn" :icon="Search" circle @click="emit('search')" />
				</div>
				<div v-if="isLoggedIn" class="user-entry">
					<div class="avatar" @click="emit('go-profile')">
						<img v-if="loginUser?.avatarUrl" :src="loginUser.avatarUrl" alt="avatar" />
						<span v-else>{{ loginUser?.avatarText || '' }}</span>
					</div>
					<div class="user-dropdown">
						<div class="user-dropdown-head">
							<div class="user-big-avatar">
								<img v-if="loginUser?.avatarUrl" :src="loginUser.avatarUrl" alt="avatar" />
								<span v-else>{{ loginUser?.avatarText || '' }}</span>
							</div>
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
							<el-button link type="primary" @click="emit('go-profile')">个人中心</el-button>
						</div>
						<div class="user-menu logout-area">
							<el-button link type="danger" @click="emit('logout')">退出登录</el-button>
						</div>
					</div>
				</div>
				<div v-else class="avatar" @click="emit('open-login')"></div>
			</div>
		</div>
	</header>
</template>

<style scoped>
.topbar {
	background: linear-gradient(100deg, #1b2040 0%, #111729 55%, #0d1324 100%);
	color: #eef3ff;
	position: sticky;
	top: 0;
	z-index: 10;
	border-bottom: 1px solid rgba(255, 255, 255, 0.08);
	backdrop-filter: blur(8px);
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
	cursor: pointer;
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
}

.brand-text,
.zone {
	font-weight: 600;
}

.brand-text {
	cursor: inherit;
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
	color: inherit;
	text-decoration: none;
	border-radius: 8px 8px 0 0;
	transition: all 0.2s ease;
}

.nav-item:hover {
	opacity: 1;
	background: rgba(255, 255, 255, 0.08);
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
	width: 340px;
	display: flex;
	align-items: center;
	gap: 8px;
}

.search-input {
	flex: 1;
}

.search-btn {
	--el-button-bg-color: #3a78ff;
	--el-button-border-color: #3a78ff;
	--el-button-hover-bg-color: #4c87ff;
	--el-button-hover-border-color: #4c87ff;
}

:deep(.search-input .el-input__wrapper) {
	border-radius: 999px;
	background: rgba(255, 255, 255, 0.14);
	box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.06);
}

:deep(.search-input .el-input__inner) {
	color: #eef3ff;
}

:deep(.search-input .el-input__inner::placeholder) {
	color: rgba(238, 243, 255, 0.7);
}

:deep(.search-input .el-input__prefix-inner) {
	color: rgba(238, 243, 255, 0.8);
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
	overflow: hidden;
	transition: transform 0.2s ease;
}

.avatar:hover {
	transform: translateY(-1px);
}

.avatar img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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
	border-radius: 12px;
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
	overflow: hidden;
}

.user-big-avatar img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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
	display: flex;
	justify-content: center;
}

.user-menu a {
	display: block;
	padding: 14px 32px;
	font-size: 16px;
	line-height: 1.2;
	color: #2f3748;
	text-decoration: none;
}

.user-menu a:hover {
	background: #f6f8fb;
}

.logout-area {
	border-bottom: none;
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
}

@media (max-width: 900px) {
	.nav {
		display: none;
	}

	.search {
		width: 240px;
	}
}
</style>
