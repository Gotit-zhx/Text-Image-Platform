<script setup lang="ts">
import type { LoginUser } from '../types'
import type { Post } from '../types'
import type { PasswordChangePayload } from '../types'
import type { ProfileEditPayload } from '../types'
import type { UserCommentRecord } from '../types'
import type { UserSimpleProfile } from '../types'
import { computed, ref, watch } from 'vue'
import ProfilePostCard from './profile/ProfilePostCard.vue'

const profileMenus = ['我的发帖', '我的评论', '我的收藏', '我的粉丝', '我的关注', '编辑资料']
const otherProfileMenus = ['TA的发帖']

const props = defineProps<{
	loginUser: LoginUser | null
	isSelfProfile: boolean
	isProfileFollowed: boolean
	canFollowProfile: boolean
	activeProfileMenu: number
	myPosts: Post[]
	myComments: UserCommentRecord[]
	myFavoritePosts: Post[]
	myFans: UserSimpleProfile[]
	myFollowings: UserSimpleProfile[]
}>()

const displayMenus = computed(() => (props.isSelfProfile ? profileMenus : otherProfileMenus))

const emit = defineEmits<{
	(e: 'update:activeProfileMenu', value: number): void
	(e: 'logout'): void
	(e: 'open-detail', postId: number): void
	(e: 'edit-post', postId: number): void
	(e: 'open-comment-detail', postId: number): void
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'delete-my-comment', commentId: number): void
	(e: 'toggle-following-user', userId: number): void
	(e: 'toggle-fan-follow', userId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
	(e: 'toggle-profile-follow'): void
	(e: 'open-profile-edit'): void
	(e: 'save-profile', payload: ProfileEditPayload): void
	(e: 'change-password', payload: PasswordChangePayload): void
}>()

const avatarUrlInput = ref('')
const nameInput = ref('')
const genderInput = ref<'male' | 'female' | 'private'>('private')
const saveTip = ref('')
const fileInputRef = ref<HTMLInputElement | null>(null)

const showPasswordModal = ref(false)
const newPasswordInput = ref('')
const confirmPasswordInput = ref('')
const passwordTip = ref('')

watch(
	() => props.loginUser,
	(user) => {
		avatarUrlInput.value = user?.avatarUrl || ''
		nameInput.value = user?.name || ''
		genderInput.value = user?.gender || 'private'
		confirmPasswordInput.value = ''
		newPasswordInput.value = ''
		saveTip.value = ''
		passwordTip.value = ''
	},
	{ immediate: true }
)

const canSaveProfile = computed(() => {
	const name = nameInput.value.trim()
	return Boolean(name)
})

const handleSaveProfile = () => {
	if (!canSaveProfile.value) {
		saveTip.value = '请完整填写资料'
		return
	}

	emit('save-profile', {
		avatarUrl: avatarUrlInput.value || undefined,
		name: nameInput.value.trim(),
		gender: genderInput.value
	})
	saveTip.value = '已提交保存'
}

const openFileSelect = () => {
	fileInputRef.value?.click()
}

const handleAvatarFileChange = (event: Event) => {
	const target = event.target as HTMLInputElement
	const file = target.files?.[0]
	if (!file) return
	const reader = new FileReader()
	reader.onload = () => {
		avatarUrlInput.value = String(reader.result || '')
	}
	reader.readAsDataURL(file)
	target.value = ''
}

const openPasswordModal = () => {
	showPasswordModal.value = true
	newPasswordInput.value = ''
	confirmPasswordInput.value = ''
	passwordTip.value = ''
}

const closePasswordModal = () => {
	showPasswordModal.value = false
}

const handleChangePassword = () => {
	if (!newPasswordInput.value.trim() || !confirmPasswordInput.value.trim()) {
		passwordTip.value = '请输入完整密码信息'
		return
	}

	if (newPasswordInput.value !== confirmPasswordInput.value) {
		passwordTip.value = '两次输入的新密码不一致'
		return
	}

	emit('change-password', {
		newPassword: newPasswordInput.value,
		confirmPassword: confirmPasswordInput.value
	})
	passwordTip.value = '修改成功'
	setTimeout(() => {
		closePasswordModal()
	}, 400)
}
</script>

<template>
	<main class="profile-page">
		<section class="profile-summary-card">
			<div class="profile-summary-left">
				<div class="profile-avatar">
					<img v-if="loginUser?.avatarUrl" :src="loginUser.avatarUrl" alt="avatar" />
					<span v-else>{{ loginUser?.avatarText || '' }}</span>
				</div>
				<div>
					<div class="profile-name-row">
						<h2>{{ loginUser?.name || '用户' }}</h2>
					</div>
					<p class="profile-id">通行证ID: {{ loginUser?.id || 0 }}</p>
					<div class="profile-summary-stats">
						<span><b>{{ loginUser?.fans ?? 0 }}</b> 粉丝</span>
						<span><b>{{ loginUser?.follows ?? 0 }}</b> 关注</span>
						<span><b>0</b> 获赞</span>
					</div>
				</div>
			</div>
			<button v-if="isSelfProfile" class="profile-edit-btn" @click="emit('open-profile-edit')">编辑</button>
			<button
				v-else
				class="profile-follow-btn"
				:class="{ followed: isProfileFollowed, disabled: !canFollowProfile }"
				:disabled="!canFollowProfile"
				@click="emit('toggle-profile-follow')"
			>
				{{ !canFollowProfile ? '不能关注自己' : isProfileFollowed ? '已关注' : '关注' }}
			</button>
		</section>

		<section class="profile-main-grid">
			<aside class="profile-sidebar">
				<h3>个人中心</h3>
				<ul>
					<li
						v-for="(item, idx) in displayMenus"
						:key="item"
						class="profile-menu-item"
						:class="{ active: activeProfileMenu === idx }"
						@click="emit('update:activeProfileMenu', idx)"
					>
						<span class="menu-icon">●</span>
						{{ item }}
					</li>
				</ul>
				<div v-if="isSelfProfile" class="profile-side-logout">
					<a href="#" @click.prevent="emit('logout')">退出登录</a>
				</div>
			</aside>

			<section class="profile-content">
				<div v-if="!(isSelfProfile && activeProfileMenu === 5)" class="profile-content-head">
					{{ displayMenus[activeProfileMenu] }}
				</div>
				<div v-if="activeProfileMenu === 0" class="my-posts-wrap">
					<template v-if="myPosts.length">
						<ProfilePostCard
							v-for="post in myPosts"
							:key="post.id"
							:post="post"
							action-text="编辑"
							@open-detail="emit('open-detail', $event)"
							@action-click="emit('edit-post', $event)"
							@open-comment-detail="emit('open-comment-detail', $event)"
							@toggle-post-like="emit('toggle-post-like', $event)"
							@toggle-post-favorite="emit('toggle-post-favorite', $event)"
							@open-author-profile="emit('open-author-profile', $event)"
						/>
					</template>
					<div v-else class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>{{ isSelfProfile ? '你还没有发布过帖子' : 'TA还没有发布过帖子' }}</p>
					</div>
				</div>
				<div v-else-if="isSelfProfile && activeProfileMenu === 1" class="my-comments-wrap">
					<template v-if="myComments.length">
						<article v-for="item in myComments" :key="item.id" class="comment-card">
							<div class="comment-top">
								<button class="post-link" @click="emit('open-comment-detail', item.postId)">
									{{ item.postTitle }}
								</button>
								<span class="comment-date">{{ item.date }}</span>
							</div>
							<p class="comment-content">{{ item.content }}</p>
							<div class="comment-actions">
								<span>👍 {{ item.likes }}</span>
								<button class="delete-btn" @click="emit('delete-my-comment', item.id)">删除</button>
							</div>
						</article>
					</template>
					<div v-else class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>你还没有发布过评论</p>
					</div>
				</div>
				<div v-else-if="isSelfProfile && activeProfileMenu === 2" class="my-posts-wrap">
					<template v-if="myFavoritePosts.length">
						<ProfilePostCard
							v-for="post in myFavoritePosts"
							:key="post.id"
							:post="post"
							action-text="取消收藏"
							@action-click="emit('toggle-post-favorite', $event)"
							@open-detail="emit('open-detail', $event)"
							@open-comment-detail="emit('open-comment-detail', $event)"
							@toggle-post-like="emit('toggle-post-like', $event)"
							@toggle-post-favorite="emit('toggle-post-favorite', $event)"
							@open-author-profile="emit('open-author-profile', $event)"
						/>
					</template>
					<div v-else class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>你还没有收藏过文章</p>
					</div>
				</div>
				<div v-else-if="isSelfProfile && activeProfileMenu === 3" class="user-list-wrap">
					<template v-if="myFans.length">
						<article v-for="user in myFans" :key="user.id" class="user-row">
							<div
								class="user-left"
								@click="emit('open-author-profile', { userId: user.id, userName: user.name, avatarText: user.avatarText })"
							>
								<div class="user-avatar">{{ user.avatarText }}</div>
								<div class="user-name">{{ user.name }}</div>
							</div>
							<button class="user-action-btn" @click="emit('toggle-fan-follow', user.id)">
								{{ myFollowings.some((item) => item.id === user.id) ? '已关注' : '回关' }}
							</button>
						</article>
					</template>
					<div v-else class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>暂无粉丝数据</p>
					</div>
				</div>
				<div v-else-if="isSelfProfile && activeProfileMenu === 4" class="user-list-wrap">
					<template v-if="myFollowings.length">
						<article v-for="user in myFollowings" :key="user.id" class="user-row">
							<div
								class="user-left"
								@click="emit('open-author-profile', { userId: user.id, userName: user.name, avatarText: user.avatarText })"
							>
								<div class="user-avatar">{{ user.avatarText }}</div>
								<div class="user-name">{{ user.name }}</div>
							</div>
							<button class="user-action-btn unfollow" @click="emit('toggle-following-user', user.id)">
								取消关注
							</button>
						</article>
					</template>
					<div v-else class="profile-empty">
						<div class="empty-planet">✦</div>
						<p>你还没有关注任何人</p>
					</div>
				</div>
				<div v-else-if="isSelfProfile && activeProfileMenu === 5" class="edit-profile-wrap">
					<div class="edit-header">编辑资料</div>
					<div class="avatar-edit-block">
						<div class="avatar-large-preview">
							<img v-if="avatarUrlInput" :src="avatarUrlInput" alt="avatar" />
							<span v-else>{{ (nameInput || '用').slice(0, 1) }}</span>
						</div>
						<div class="avatar-actions">
							<button class="avatar-change-btn" @click="openFileSelect">修改头像</button>
							<input
								ref="fileInputRef"
								type="file"
								accept="image/*"
								class="hidden-file-input"
								@change="handleAvatarFileChange"
							/>
						</div>
					</div>

					<div class="edit-row">
						<label>昵称</label>
						<div>
							<input v-model="nameInput" type="text" maxlength="20" placeholder="请输入昵称" />
							<p class="field-tip">{{ nameInput.length }} / 20</p>
						</div>
					</div>

					<div class="edit-row">
						<label>性别</label>
						<div class="gender-group">
							<label><input v-model="genderInput" type="radio" value="male" /> 男</label>
							<label><input v-model="genderInput" type="radio" value="female" /> 女</label>
							<label><input v-model="genderInput" type="radio" value="private" /> 保密</label>
						</div>
					</div>

					<div class="edit-actions">
						<button class="save-btn" :disabled="!canSaveProfile" @click="handleSaveProfile">保存</button>
						<button class="password-btn" @click="openPasswordModal">修改密码</button>
					</div>
					<p v-if="saveTip" class="save-tip">{{ saveTip }}</p>
				</div>
				<div v-else class="profile-empty">
					<div class="empty-planet">✦</div>
					<p>暂无内容</p>
				</div>
			</section>
		</section>

		<div v-if="showPasswordModal" class="pwd-modal-mask" @click.self="closePasswordModal">
			<div class="pwd-modal-card">
				<h3>修改密码</h3>
				<input v-model="newPasswordInput" type="password" placeholder="请输入新密码" />
				<input v-model="confirmPasswordInput" type="password" placeholder="请再次输入新密码" />
				<p v-if="passwordTip" class="pwd-tip">{{ passwordTip }}</p>
				<div class="pwd-actions">
					<button class="pwd-cancel" @click="closePasswordModal">取消</button>
					<button class="pwd-confirm" @click="handleChangePassword">确认修改</button>
				</div>
			</div>
		</div>
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
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 40px;
	font-weight: 700;
	color: #5f6a84;
	background: #c3ebfb;
	border: 2px solid #a8dff6;
}

.profile-avatar img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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

.profile-follow-btn {
	height: 32px;
	min-width: 78px;
	border-radius: 999px;
	border: none;
	cursor: pointer;
	color: #fff;
	font-weight: 600;
	background: linear-gradient(180deg, #30c6ff, #13a6f6);
}

.profile-follow-btn.followed {
	background: #eef3f8;
	color: #74819a;
	border: 1px solid #d8e1ed;
}

.profile-follow-btn.disabled {
	background: #eef3f8;
	color: #9ca6b8;
	border: 1px solid #d8e1ed;
	cursor: not-allowed;
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

.my-posts-wrap {
	padding: 14px;
	display: flex;
	flex-direction: column;
	gap: 14px;
}

.my-comments-wrap {
	padding: 14px;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.comment-card {
	border: 1px solid #e9edf3;
	border-radius: 10px;
	padding: 12px 14px;
	background: #fff;
}

.comment-top {
	display: flex;
	justify-content: space-between;
	align-items: center;
	gap: 10px;
}

.post-link {
	border: none;
	background: transparent;
	padding: 0;
	font-size: 15px;
	font-weight: 600;
	color: #2f3748;
	cursor: pointer;
	text-align: left;
}

.comment-date {
	font-size: 12px;
	color: #98a1b3;
}

.comment-content {
	margin: 10px 0;
	font-size: 14px;
	line-height: 1.6;
	color: #4f586c;
}

.comment-actions {
	display: flex;
	justify-content: space-between;
	align-items: center;
	font-size: 13px;
	color: #9aa3b6;
}

.delete-btn {
	border: none;
	background: transparent;
	padding: 0;
	font-size: 13px;
	color: #8f97a8;
	cursor: pointer;
}

.delete-btn:hover {
	color: #f56c6c;
}

.user-list-wrap {
	padding: 0;
}

.user-row {
	height: 88px;
	display: flex;
	justify-content: space-between;
	align-items: center;
	padding: 0 20px;
	border-bottom: 1px solid #edf0f5;
}

.user-left {
	display: flex;
	align-items: center;
	gap: 12px;
	cursor: pointer;
}

.user-avatar {
	width: 52px;
	height: 52px;
	border-radius: 50%;
	display: grid;
	place-items: center;
	font-size: 20px;
	font-weight: 700;
	color: #5f6a84;
	background: #c3ebfb;
	border: 1px solid #a8dff6;
}

.user-name {
	font-size: 18px;
	color: #343c4d;
}

.user-action-btn {
	height: 36px;
	min-width: 96px;
	border: 1px solid #8fd2ff;
	border-radius: 999px;
	background: #f2fbff;
	color: #18a8f2;
	font-size: 14px;
	cursor: pointer;
}

.user-action-btn.unfollow {
	border-color: #d8e1ed;
	background: #eef3f8;
	color: #74819a;
}

.edit-profile-wrap {
	padding: 0 0 20px;
	display: flex;
	flex-direction: column;
	gap: 18px;
}

.edit-header {
	height: 52px;
	display: flex;
	align-items: center;
	padding: 0 20px;
	font-size: 18px;
	color: #2f3748;
	border-bottom: 1px solid #edf0f5;
}

.avatar-edit-block {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 12px;
	padding-top: 14px;
}

.avatar-large-preview {
	width: 128px;
	height: 128px;
	border-radius: 50%;
	overflow: hidden;
	display: flex;
	align-items: center;
	justify-content: center;
	font-size: 44px;
	font-weight: 700;
	color: #5f6a84;
	background: #c3ebfb;
	border: 2px solid #a8dff6;
}

.avatar-large-preview img {
	width: 100%;
	height: 100%;
	object-fit: cover;
}

.avatar-actions {
	display: flex;
	flex-direction: column;
	align-items: center;
	gap: 0;
}

.avatar-change-btn {
	height: 34px;
	padding: 0 16px;
	border: 1px solid #8fd2ff;
	border-radius: 999px;
	background: #f2fbff;
	color: #18a8f2;
	cursor: pointer;
	font-size: 14px;
}

.hidden-file-input {
	display: none;
}

.edit-row {
	display: grid;
	grid-template-columns: 84px minmax(0, 560px);
	align-items: center;
	gap: 12px;
	padding: 0 20px;
}

.edit-row label {
	font-size: 14px;
	color: #4f586c;
}

.edit-row input {
	height: 38px;
	border: 1px solid #e3e7ef;
	border-radius: 6px;
	padding: 0 10px;
	font-size: 14px;
	outline: none;
	width: 100%;
}

.field-tip {
	margin: 6px 0 0;
	font-size: 12px;
	color: #a6aebb;
}

.gender-group {
	display: flex;
	align-items: center;
	gap: 28px;
}

.gender-group label {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 14px;
	color: #3a4256;
	white-space: nowrap;
}

.edit-actions {
	display: flex;
	justify-content: center;
	gap: 12px;
	margin-top: 2px;
}

.save-btn {
	width: 120px;
	height: 36px;
	border: 1px solid #49bfff;
	border-radius: 6px;
	background: #fff;
	color: #18a8f2;
	font-weight: 600;
	cursor: pointer;
}

.save-btn:disabled {
	opacity: 0.45;
	cursor: not-allowed;
}

.save-tip {
	margin: 0;
	text-align: center;
	font-size: 13px;
	color: #18b0ff;
}

.password-btn {
	width: 120px;
	height: 36px;
	border: 1px solid #e3e7ef;
	border-radius: 6px;
	background: #fff;
	color: #677189;
	font-weight: 600;
	cursor: pointer;
}

.pwd-modal-mask {
	position: fixed;
	inset: 0;
	background: rgba(14, 20, 32, 0.46);
	display: flex;
	align-items: center;
	justify-content: center;
	z-index: 100;
}

.pwd-modal-card {
	width: 380px;
	background: #fff;
	border-radius: 12px;
	padding: 18px;
	box-shadow: 0 18px 50px rgba(20, 29, 48, 0.25);
	display: flex;
	flex-direction: column;
	gap: 10px;
}

.pwd-modal-card h3 {
	margin: 0 0 4px;
	font-size: 18px;
	color: #2f3748;
}

.pwd-modal-card input {
	height: 38px;
	border: 1px solid #e3e7ef;
	border-radius: 6px;
	padding: 0 10px;
	font-size: 14px;
	outline: none;
}

.pwd-tip {
	margin: 0;
	font-size: 12px;
	color: #18b0ff;
}

.pwd-actions {
	display: flex;
	justify-content: flex-end;
	gap: 10px;
	margin-top: 4px;
}

.pwd-cancel,
.pwd-confirm {
	height: 34px;
	border-radius: 6px;
	padding: 0 14px;
	cursor: pointer;
	font-size: 14px;
}

.pwd-cancel {
	border: 1px solid #d9e0eb;
	background: #fff;
	color: #65708a;
}

.pwd-confirm {
	border: none;
	background: linear-gradient(180deg, #2dc7ff, #0fb0f6);
	color: #fff;
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
