import { onBeforeUnmount, ref } from 'vue'
import {
adminLoginApi,
adminLogoutApi,
adminMeApi,
deleteAdminCommentApi,
getAdminAuditLogsApi,
getAdminPostDetailApi,
getAdminCommentsApi,
getAdminOverviewApi,
getAdminPostsApi,
getAdminUsersApi,
hideAdminCommentApi,
restoreAdminCommentApi,
reviewAdminPostApi,
reviewAdminPostBatchApi,
updateAdminUserAdminApi,
type AdminPostDetail,
type AdminAuditItem,
type AdminCommentItem,
type AdminPostItem,
type AdminUserItem,
type Pagination
} from '../api/admin'
import type { LoginUser } from '../types'
import { clearSessionUser, readSessionUser, writeSessionUser } from '../auth/session'

const defaultPagination: Pagination = { total: 0, page: 1, pageSize: 10 }

export const useAdminState = () => {
const adminUser = ref<LoginUser | null>(readSessionUser('admin'))
const loading = ref(false)
const error = ref('')

const overview = ref({
postPendingCount: 0,
commentHiddenCount: 0,
auditEvents24h: 0
})

const posts = ref<AdminPostItem[]>([])
const currentPostDetail = ref<AdminPostDetail | null>(null)
const postsPagination = ref<Pagination>({ ...defaultPagination })

const comments = ref<AdminCommentItem[]>([])
const commentsPagination = ref<Pagination>({ ...defaultPagination })

const users = ref<AdminUserItem[]>([])
const usersPagination = ref<Pagination>({ ...defaultPagination })

const logs = ref<AdminAuditItem[]>([])
const logsPagination = ref<Pagination>({ ...defaultPagination })

let pendingCount = 0, mutationPending = false, sequence = 0, activeRead = 0, disposed = false
const latestRead: Record<string, number> = {}
const begin = () => { pendingCount++; loading.value = true }
const end = () => { pendingCount--; loading.value = pendingCount > 0 }
const resetAccountData = () => {
activeRead = ++sequence
for (const key of Object.keys(latestRead)) latestRead[key] = activeRead
posts.value = []; comments.value = []; users.value = []; logs.value = []
currentPostDetail.value = null
postsPagination.value = { ...defaultPagination }
commentsPagination.value = { ...defaultPagination }
usersPagination.value = { ...defaultPagination }
logsPagination.value = { ...defaultPagination }
overview.value = { postPendingCount: 0, commentHiddenCount: 0, auditEvents24h: 0 }
error.value = ''
}
const readLatest = async <T>(key: string, fetcher: () => Promise<T>, apply: (value: T) => void) => {
const current = ++sequence
latestRead[key] = current
activeRead = current
begin()
error.value = ''
try {
const result = await fetcher()
if (!disposed && latestRead[key] === current) apply(result)
} catch (e) {
if (!disposed && activeRead === current) {
error.value = e instanceof Error ? e.message : '请求失败'
throw e
}
} finally { end() }
}
onBeforeUnmount(() => { disposed = true })

const withLoading = async (runner: () => Promise<void>) => {
if(mutationPending)throw new Error('已有操作正在处理，请稍后重试')
mutationPending = true
begin()
error.value = ''
try {
await runner()
} catch (e) {
error.value = e instanceof Error ? e.message : '请求失败'
throw e
} finally {
mutationPending = false
end()
}
}

const adminLogin = async (account: string, password: string) => {
let loggedUser: LoginUser | null = null
await withLoading(async () => {
const user = await adminLoginApi(account, password)
resetAccountData()
adminUser.value = user
writeSessionUser(user, 'admin')
loggedUser = user
})
return loggedUser
}

const loadAdminSession = async () => {
try {
const user = await adminMeApi()
if (adminUser.value?.id !== user.id) resetAccountData()
adminUser.value = user
writeSessionUser(user, 'admin')
return user
} catch {
resetAccountData()
adminUser.value = null
clearSessionUser('admin')
return null
}
}

const adminLogout = async () => {
await adminLogoutApi()
resetAccountData()
adminUser.value = null
clearSessionUser('admin')
}

const loadOverview = async () => {
await readLatest('overview', getAdminOverviewApi, value => { overview.value = value })
}

const loadPosts = async (params: { page?: number; pageSize?: number; status?: string; keyword?: string } = {}) => {
await readLatest('posts', () => getAdminPostsApi(params), result => {
posts.value = result.items
postsPagination.value = result.pagination
})
}

const reviewPost = async (postId: number, action: string, reason = '') => {
await withLoading(async () => {
await reviewAdminPostApi(postId, action, reason)
})
}

const reviewPostsBatch = async (postIds: number[], action: string, reason = '') => {
await withLoading(async () => {
await reviewAdminPostBatchApi(postIds, action, reason)
})
}

const loadPostDetail = async (postId: number) => {
let detail: AdminPostDetail | null = null
currentPostDetail.value = null
await readLatest('post-detail', () => getAdminPostDetailApi(postId), result => {
detail = result
currentPostDetail.value = result
})
return detail
}

const loadComments = async (params: {
page?: number
pageSize?: number
visibility?: string
keyword?: string
} = {}) => {
await readLatest('comments', () => getAdminCommentsApi(params), result => {
comments.value = result.items
commentsPagination.value = result.pagination
})
}

const hideComment = async (id: number) => {
await withLoading(async () => {
await hideAdminCommentApi(id)
})
}

const restoreComment = async (id: number) => {
await withLoading(async () => {
await restoreAdminCommentApi(id)
})
}

const deleteComment = async (id: number) => {
await withLoading(async () => {
await deleteAdminCommentApi(id)
})
}

const loadUsers = async (params: { page?: number; pageSize?: number; keyword?: string } = {}) => {
await readLatest('users', () => getAdminUsersApi(params), result => {
users.value = result.items
usersPagination.value = result.pagination
})
}

const updateUserAdmin = async (id: number, isAdmin: boolean) => {
await withLoading(async () => {
await updateAdminUserAdminApi(id, isAdmin)
})
}

const loadLogs = async (params: { page?: number; pageSize?: number; action?: string; targetType?: string } = {}) => {
await readLatest('logs', () => getAdminAuditLogsApi(params), result => {
logs.value = result.items
logsPagination.value = result.pagination
})
}

return {
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
}
}
