<script setup lang="ts">
import { computed, onMounted, reactive, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { useAdminState } from '../../composables/useAdminState'
import AdminLoginPage from './pages/AdminLoginPage.vue'
import AdminCasesPage from './pages/AdminCasesPage.vue'
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
	currentPostDetail,
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
	reviewPostsBatch,
	loadPostDetail,
	loadComments,
	hideComment,
	restoreComment,
	deleteComment,
	loadUsers,
	updateUserAdmin,
	loadLogs
} = useAdminState()

const postsQuery = reactive({ page: 1, pageSize: 10, status: '', keyword: '' })
const commentsQuery = reactive({ page: 1, pageSize: 10, visibility: '', keyword: '' })
const usersQuery = reactive({ page: 1, pageSize: 10, keyword: '' })
const logsQuery = reactive({ page: 1, pageSize: 10, action: '', targetType: '' })

const isLoginPage = computed(() => route.name === 'admin-login')
const currentTab = computed(() => {
	if (route.name === 'admin-reports') return 'reports'
	if (route.name === 'admin-appeals') return 'appeals'
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
		reports: 'admin-reports',
		appeals: 'admin-appeals',
		posts: 'admin-posts',
		comments: 'admin-comments',
		users: 'admin-users',
		logs: 'admin-audit-logs'
	}
	router.push({ name: map[tab] || 'admin-dashboard' })
}

const safe=async(runner:()=>Promise<unknown>)=>{try{await runner()}catch(e){ElMessage.error(e instanceof Error?e.message:'操作失败')}}

const handleAdminLogin = async (payload: { account: string; password: string }) => {
	const user = await adminLogin(payload.account, payload.password)
	if (!user) return
	await router.replace({ name: 'admin-dashboard' })
	await loadCurrent()
}

const handleLogout = async () => {
	await safe(async () => {
		await adminLogout()
		await router.replace({ name: 'admin-login' })
	})
}

const handleReviewPost = async (payload: { id: number; action: 'approve' | 'reject' | 'offline'; reason?: string }) => {
	await reviewPost(payload.id, payload.action, payload.reason || '')
	ElMessage.success('操作成功')
	try { await loadPosts({ ...postsQuery }) } catch { /* The review already succeeded; the list exposes its refresh error. */ }
}

const handleReviewPostsBatch = async (payload: {
	ids: number[]
	action: 'approve' | 'reject' | 'offline'
	reason?: string
}) => {
	await reviewPostsBatch(payload.ids, payload.action, payload.reason || '')
	ElMessage.success(`已批量处理 ${payload.ids.length} 条`)
	try { await loadPosts({ ...postsQuery }) } catch { /* Keep the confirmed review separate from a failed refresh. */ }
}

const handleOpenPostDetail = async (id: number) => {
	await loadPostDetail(id)
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
  await ElMessageBox.confirm('删除后正文不可恢复，有回复时保留占位。','确认删除评论',{type:'warning',confirmButtonText:'确认删除',cancelButtonText:'取消'})
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

const handleSetAdmin = async (payload: { id: number; isAdmin: boolean }) => {
	await updateUserAdmin(payload.id, payload.isAdmin)
	ElMessage.success(payload.isAdmin ? '已设为管理员' : '已取消管理员')
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
	try{await loadCurrent()}catch{}
})

watch(
	() => currentTab.value,
	async () => {
		if (isLoginPage.value) return
		try{await loadCurrent()}catch{}
	}
)
</script>

<template>
	<AdminLoginPage v-if="isLoginPage" :loading="loading" :error="error" @login="safe(()=>handleAdminLogin($event))" />
	<el-container v-else class="admin-layout">
		<el-aside class="sidebar" width="220px">
			<div class="brand">后台管理</div>
			<el-menu :default-active="currentTab" class="menu" @select="goTab">
				<el-menu-item index="dashboard">控制台</el-menu-item>
				<el-menu-item index="posts">帖子审核</el-menu-item>
				<el-menu-item index="comments">评论管理</el-menu-item>
				<el-menu-item index="users">用户管理</el-menu-item>
				<el-menu-item index="reports">举报受理</el-menu-item><el-menu-item index="appeals">申诉复核</el-menu-item>
        <el-menu-item index="logs">审计日志</el-menu-item>
			</el-menu>
		</el-aside>
		<el-container>
			<el-header class="toolbar">
				<RouterLink to="/" class="text-button">返回社区</RouterLink><div class="operator">{{ adminUser?.name }}（{{ adminUser?.isAdmin ? '管理员' : '普通用户' }}）</div>
				<el-button @click="handleLogout">退出</el-button>
			</el-header>
			<el-main class="content">
				<el-alert v-if="error" class="error" type="error" :closable="false" :title="error" />
				<AdminDashboardPage v-if="currentTab === 'dashboard'" :overview="overview" />
				<AdminCasesPage v-else-if="currentTab === 'reports' || currentTab === 'appeals'" :key="currentTab" :kind="currentTab" :can-moderate="!!adminUser?.permissions?.moderate" :can-operate="!!adminUser?.permissions?.operate" />
				<AdminPostsPage
					v-else-if="currentTab === 'posts'"
					:items="posts"
					:loading="loading"
					:pagination="postsPagination"
					:status="postsQuery.status"
					:keyword="postsQuery.keyword"
					@refresh="safe(()=>loadPosts({ ...postsQuery }))"
          :review-post="handleReviewPost"
          :review-batch="handleReviewPostsBatch"
					@open-detail="safe(()=>handleOpenPostDetail($event))"
					@query-change="safe(()=>handlePostsQueryChange($event))"
					:current-detail="currentPostDetail" :can-write="!!adminUser?.permissions?.moderate"
				/>
				<AdminCommentsPage
					v-else-if="currentTab === 'comments'"
					:items="comments"
					:loading="loading"
					:pagination="commentsPagination"
					:visibility="commentsQuery.visibility" :can-write="!!adminUser?.permissions?.moderate"
					:keyword="commentsQuery.keyword"
					@refresh="safe(()=>loadComments({ ...commentsQuery }))"
					@hide="safe(()=>handleHideComment($event))"
					@restore="safe(()=>handleRestoreComment($event))"
					@delete="safe(()=>handleDeleteComment($event))"
					@query-change="safe(()=>handleCommentsQueryChange($event))"
				/>
				<AdminUsersPage
					v-else-if="currentTab === 'users'"
					:items="users"
					:loading="loading"
					:pagination="usersPagination"
					:keyword="usersQuery.keyword" :can-operate="!!adminUser?.permissions?.operate" :can-roles="!!adminUser?.permissions?.roles"
					@refresh="safe(()=>loadUsers({ ...usersQuery }))"
					@set-admin="safe(()=>handleSetAdmin($event))"
					@query-change="safe(()=>handleUsersQueryChange($event))"
				/>
				<AdminAuditLogsPage
					v-else
					:items="logs"
					:loading="loading"
					:pagination="logsPagination"
					:action="logsQuery.action"
					:target-type="logsQuery.targetType"
					@refresh="safe(()=>loadLogs({ ...logsQuery }))"
					@query-change="safe(()=>handleLogsQueryChange($event))"
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
@media(max-width:767px){.admin-layout{flex-direction:column}.sidebar{width:100%!important}.menu{display:flex;overflow:auto}.brand{font-size:16px;padding:8px}.menu :deep(.el-menu-item){padding:0 12px}.content{padding:8px;min-width:0}.toolbar{height:auto;min-height:64px;gap:8px;flex-wrap:wrap}.operator{font-size:12px}}
</style>
