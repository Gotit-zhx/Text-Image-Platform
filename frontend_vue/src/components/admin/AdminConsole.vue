<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { useAdminState } from '../../composables/useAdminState'
import AdminLoginPage from './pages/AdminLoginPage.vue'
import AdminDashboardPage from './pages/AdminDashboardPage.vue'
import AdminPostsPage from './pages/AdminPostsPage.vue'
import AdminCommentsPage from './pages/AdminCommentsPage.vue'
import AdminUsersPage from './pages/AdminUsersPage.vue'
import AdminAuditLogsPage from './pages/AdminAuditLogsPage.vue'

const route = useRoute()
const router = useRouter()

const {
	adminUser,
	loading,
	error,
	overview,
	posts,
	postsPagination,
	comments,
	commentsPagination,
	users,
	usersPagination,
	logs,
	logsPagination,
	adminLogin,
	loadAdminSession,
	adminLogout,
	loadOverview,
	loadPosts,
	reviewPost,
	loadComments,
	hideComment,
	restoreComment,
	deleteComment,
	loadUsers,
	updateUserRoles,
	loadLogs
} = useAdminState()

const postsQuery = reactive({ page: 1, pageSize: 10, status: '', keyword: '' })
const commentsQuery = reactive({ page: 1, pageSize: 10, visibility: '', keyword: '' })
const usersQuery = reactive({ page: 1, pageSize: 10, keyword: '' })
const logsQuery = reactive({ page: 1, pageSize: 10, action: '', targetType: '' })

const isLoginPage = computed(() => route.name === 'admin-login')
const currentTab = computed(() => {
	if (route.name === 'admin-posts') return 'posts'
	if (route.name === 'admin-comments') return 'comments'
	if (route.name === 'admin-users') return 'users'
	if (route.name === 'admin-audit-logs') return 'logs'
	return 'dashboard'
})

const loadCurrent = async () => {
	if (currentTab.value === 'dashboard') await loadOverview()
	if (currentTab.value === 'posts') await loadPosts({ ...postsQuery })
	if (currentTab.value === 'comments') await loadComments({ ...commentsQuery })
	if (currentTab.value === 'users') await loadUsers({ ...usersQuery })
	if (currentTab.value === 'logs') await loadLogs({ ...logsQuery })
}

const goTab = (tab: string) => {
	const map: Record<string, string> = {
		dashboard: 'admin-dashboard',
		posts: 'admin-posts',
		comments: 'admin-comments',
		users: 'admin-users',
		logs: 'admin-audit-logs'
	}
	router.push({ name: map[tab] || 'admin-dashboard' })
}

const handleAdminLogin = async (payload: { account: string; password: string }) => {
	const user = await adminLogin(payload.account, payload.password)
	if (!user) return
	router.replace({ name: 'admin-dashboard' })
	await loadCurrent()
}

const handleLogout = async () => {
	await adminLogout()
	router.replace({ name: 'admin-login' })
}

const handleReviewPost = async (payload: { id: number; action: 'approve' | 'reject' | 'offline' }) => {
	await reviewPost(payload.id, payload.action)
	ElMessage.success('操作成功')
	await loadPosts({ ...postsQuery })
}

const handlePostsQueryChange = async (payload: {
	page?: number
	pageSize?: number
	status?: string
	keyword?: string
}) => {
	Object.assign(postsQuery, payload)
	await loadPosts({ ...postsQuery })
}

const handleHideComment = async (id: number) => {
	await hideComment(id)
	ElMessage.success('已隐藏评论')
	await loadComments({ ...commentsQuery })
}

const handleRestoreComment = async (id: number) => {
	await restoreComment(id)
	ElMessage.success('已恢复评论')
	await loadComments({ ...commentsQuery })
}

const handleDeleteComment = async (id: number) => {
	await deleteComment(id)
	ElMessage.success('已删除评论')
	await loadComments({ ...commentsQuery })
}

const handleCommentsQueryChange = async (payload: {
	page?: number
	pageSize?: number
	visibility?: string
	keyword?: string
}) => {
	Object.assign(commentsQuery, payload)
	await loadComments({ ...commentsQuery })
}

const handleSetRoles = async (payload: { id: number; roles: string[] }) => {
	await updateUserRoles(payload.id, payload.roles)
	ElMessage.success('角色已更新')
	await loadUsers({ ...usersQuery })
}

const handleUsersQueryChange = async (payload: { page?: number; pageSize?: number; keyword?: string }) => {
	Object.assign(usersQuery, payload)
	await loadUsers({ ...usersQuery })
}

const handleLogsQueryChange = async (payload: {
	page?: number
	pageSize?: number
	action?: string
	targetType?: string
}) => {
	Object.assign(logsQuery, payload)
	await loadLogs({ ...logsQuery })
}

onMounted(async () => {
	if (isLoginPage.value) return
	await loadAdminSession()
	await loadCurrent()
})

watch(
	() => currentTab.value,
	async () => {
		if (isLoginPage.value) return
		await loadCurrent()
	}
)
</script>

<template>
	<AdminLoginPage v-if="isLoginPage" :loading="loading" :error="error" @login="handleAdminLogin" />
	<el-container v-else class="admin-layout">
		<el-aside class="sidebar" width="220px">
			<div class="brand">后台管理</div>
			<el-menu :default-active="currentTab" class="menu" @select="goTab">
				<el-menu-item index="dashboard">Dashboard</el-menu-item>
				<el-menu-item index="posts">帖子审核</el-menu-item>
				<el-menu-item index="comments">评论管理</el-menu-item>
				<el-menu-item index="users">用户角色</el-menu-item>
				<el-menu-item index="logs">审计日志</el-menu-item>
			</el-menu>
		</el-aside>
		<el-container>
			<el-header class="toolbar">
				<div class="operator">{{ adminUser?.name }}（{{ adminUser?.roles?.join(', ') || '-' }}）</div>
				<el-button @click="handleLogout">退出</el-button>
			</el-header>
			<el-main class="content">
				<el-alert v-if="error" class="error" type="error" :closable="false" :title="error" />
				<AdminDashboardPage v-if="currentTab === 'dashboard'" :overview="overview" />
				<AdminPostsPage
					v-else-if="currentTab === 'posts'"
					:items="posts"
					:loading="loading"
					:pagination="postsPagination"
					:status="postsQuery.status"
					:keyword="postsQuery.keyword"
					@refresh="loadPosts({ ...postsQuery })"
					@review="handleReviewPost"
					@query-change="handlePostsQueryChange"
				/>
				<AdminCommentsPage
					v-else-if="currentTab === 'comments'"
					:items="comments"
					:loading="loading"
					:pagination="commentsPagination"
					:visibility="commentsQuery.visibility"
					:keyword="commentsQuery.keyword"
					@refresh="loadComments({ ...commentsQuery })"
					@hide="handleHideComment"
					@restore="handleRestoreComment"
					@delete="handleDeleteComment"
					@query-change="handleCommentsQueryChange"
				/>
				<AdminUsersPage
					v-else-if="currentTab === 'users'"
					:items="users"
					:loading="loading"
					:pagination="usersPagination"
					:keyword="usersQuery.keyword"
					@refresh="loadUsers({ ...usersQuery })"
					@set-roles="handleSetRoles"
					@query-change="handleUsersQueryChange"
				/>
				<AdminAuditLogsPage
					v-else
					:items="logs"
					:loading="loading"
					:pagination="logsPagination"
					:action="logsQuery.action"
					:target-type="logsQuery.targetType"
					@refresh="loadLogs({ ...logsQuery })"
					@query-change="handleLogsQueryChange"
				/>
			</el-main>
		</el-container>
	</el-container>
</template>

<style scoped>
.admin-layout { min-height: 100vh; background: #f4f6fb; }
.sidebar { background: #17223b; color: #fff; }
.brand { color: #fff; font-size: 20px; font-weight: 700; padding: 18px 16px 12px; }
.menu { border-right: none; background: transparent; }
.menu :deep(.el-menu-item) { color: #c9d3ea; }
.menu :deep(.el-menu-item.is-active) { color: #fff; background: #2f88ff; }
.toolbar { background: #fff; border-bottom: 1px solid #e7ecf3; display: flex; align-items: center; justify-content: space-between; }
.operator { font-size: 14px; color: #30384a; }
.content { padding: 16px; }
.error { margin-bottom: 12px; }
</style>
