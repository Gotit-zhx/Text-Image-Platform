<script setup lang="ts">
import type { LoginUser } from '../types'

const profileMenus = ['我的发帖', '我的评论', '我的收藏', '我的粉丝', '我的关注']

defineProps<{
	loginUser: LoginUser | null
	activeProfileMenu: number
}>()

const emit = defineEmits<{
	(e: 'update:activeProfileMenu', value: number): void
	(e: 'logout'): void
}>()
</script>

<template>
	<main class="profile-page">
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
						v-for="(item, idx) in profileMenus"
						:key="item"
						class="profile-menu-item"
						:class="{ active: activeProfileMenu === idx }"
						@click="emit('update:activeProfileMenu', idx)"
					>
						<span class="menu-icon">●</span>
						{{ item }}
					</li>
				</ul>
				<div class="profile-side-logout">
					<a href="#" @click.prevent="emit('logout')">退出登录</a>
				</div>
			</aside>

			<section class="profile-content">
				<div class="profile-content-head">{{ profileMenus[activeProfileMenu] }}</div>
				<div class="profile-empty">
					<div class="empty-planet">✦</div>
					<p>暂无内容</p>
				</div>
			</section>
		</section>
	</main>
</template>

<style scoped>
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
	text-decoration: none;
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

@media (max-width: 1024px) {
	.profile-main-grid {
		grid-template-columns: 1fr;
	}
}
</style>
