<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import DOMPurify from 'dompurify'
import AdminPagination from '../AdminPagination.vue'
import { ElMessage } from 'element-plus'
import type { AdminPostDetail, AdminPostItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminPostItem[]
	loading: boolean
  canWrite?: boolean
	pagination: Pagination
	status: string
	keyword: string
	currentDetail: AdminPostDetail | null
  reviewPost: (payload: {id:number;action:'approve'|'reject'|'offline';reason:string}) => Promise<void>
  reviewBatch: (payload: {ids:number[];action:'approve'|'reject'|'offline';reason:string}) => Promise<void>
}>()

const emit = defineEmits(['refresh', 'review', 'batch-review', 'open-detail', 'query-change'])

const localStatus = ref(props.status)
const localKeyword = ref(props.keyword)
const selectedIds = ref<number[]>([])
const reasonDialogVisible = ref(false)
const reasonText = ref('')
const pendingAction = ref<'approve' | 'reject' | 'offline' | null>(null)
const pendingIds = ref<number[]>([])
const detailDrawerVisible = ref(false)
const reviewPending = ref(false), reviewError = ref('')

watch(
	() => props.status,
	(value) => {
		localStatus.value = value
	}
)

watch(
	() => props.keyword,
	(value) => {
		localKeyword.value = value
	}
)

const handleSearch = () => {
	emit('query-change', { page: 1, status: localStatus.value, keyword: localKeyword.value.trim() })
}

const handleReset = () => {
	localStatus.value = ''
	localKeyword.value = ''
	selectedIds.value = []
	emit('query-change', { page: 1, status: '', keyword: '' })
}

const actionTextMap: Record<'approve' | 'reject' | 'offline', string> = {
	approve: '通过',
	reject: '驳回',
	offline: '下架'
}

const submitReview = async () => {
	if (reviewPending.value || !pendingAction.value || !pendingIds.value.length) return
	const action = pendingAction.value
	if ((action === 'reject' || action === 'offline') && !reasonText.value.trim()) {
		ElMessage.warning('请填写原因')
		return
	}
  reviewPending.value = true
  reviewError.value = ''
  try {
    if (pendingIds.value.length === 1) {
      await props.reviewPost({ id: pendingIds.value[0]!, action, reason: reasonText.value.trim() })
    } else {
      await props.reviewBatch({ ids: [...pendingIds.value], action, reason: reasonText.value.trim() })
    }
    reasonDialogVisible.value = false
    reasonText.value = ''
    pendingAction.value = null
    pendingIds.value = []
  } catch (e) {
    reviewError.value = e instanceof Error ? e.message : '审核失败，处理原因已保留'
    if (!reasonDialogVisible.value) ElMessage.error(reviewError.value)
  } finally { reviewPending.value = false }
}

const requestReview = (ids: number[], action: 'approve' | 'reject' | 'offline') => {
	if (!props.canWrite || !ids.length || reviewPending.value) return
  reviewError.value = ''
	pendingIds.value = ids
	pendingAction.value = action
	if (action === 'approve') {
		reasonText.value = ''
		submitReview()
		return
	}
	reasonText.value = ''
	reasonDialogVisible.value = true
}

const openDetail = async (id: number) => {
	emit('open-detail', id)
	detailDrawerVisible.value = true
}

const handleSelectionChange = (rows: AdminPostItem[]) => {
	selectedIds.value = rows.map((row) => row.id)
}

const getStatusTagType = (status: string) => {
	if (status === 'approved') return 'success'
	if (status === 'rejected') return 'warning'
	if (status === 'offline') return 'danger'
	return 'info'
}

const statusLabelMap: Record<string, string> = {
	pending: '待审核',
	approved: '已通过',
	rejected: '已驳回',
	offline: '已下架'
}

const formatStatus = (status: string) => statusLabelMap[status] || status

const sanitizedDetailHtml = computed(() =>
	DOMPurify.sanitize(props.currentDetail?.contentHtml || '', {
		ALLOWED_TAGS: [
			'p',
			'br',
			'strong',
			'em',
			'u',
			's',
			'a',
			'blockquote',
			'ul',
			'ol',
			'li',
			'h1',
			'h2',
			'h3',
			'h4',
			'h5',
			'h6',
			'pre',
			'code',
			'img',
			'span',
			'div',
			'table',
			'thead',
			'tbody',
			'tr',
			'th',
			'td'
		],
		ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class'],
		ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel|blob):|\/|data:image\/)/i,
		FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
		FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'onmouseover', 'onfocus']
	})
)
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">帖子审核</div>
			<div class="filters">
				<el-select v-model="localStatus" aria-label="帖子审核状态" clearable placeholder="状态" style="width: 140px">
					<el-option label="待审核" value="pending" />
					<el-option label="已通过" value="approved" />
					<el-option label="已驳回" value="rejected" />
					<el-option label="已下架" value="offline" />
				</el-select>
				<el-input v-model="localKeyword" aria-label="帖子标题或作者关键词" clearable placeholder="标题/作者关键词" style="width: 220px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button v-if="canWrite" type="success" :disabled="!selectedIds.length" @click="requestReview(selectedIds, 'approve')">
					批量通过
				</el-button>
				<el-button v-if="canWrite" type="warning" :disabled="!selectedIds.length" @click="requestReview(selectedIds, 'reject')">
					批量驳回
				</el-button>
				<el-button v-if="canWrite" type="danger" :disabled="!selectedIds.length" @click="requestReview(selectedIds, 'offline')">
					批量下架
				</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table
			:data="props.items"
			v-loading="loading"
			:aria-busy="loading"
			border
			@selection-change="handleSelectionChange"
		>
			<el-table-column v-if="canWrite" type="selection" width="46" />
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
			<el-table-column prop="author" label="作者" width="140" />
			<el-table-column label="状态" width="120">
				<template #default="scope">
					<el-tag :type="getStatusTagType(scope.row.status)">{{ formatStatus(scope.row.status) }}</el-tag>
				</template>
			</el-table-column>
			<el-table-column label="审核原因" min-width="180" show-overflow-tooltip>
				<template #default="scope">{{ scope.row.reviewReason || '-' }}</template>
			</el-table-column>
			<el-table-column label="操作" width="280" fixed="right">
				<template #default="scope">
					<el-space>
						<el-button size="small" @click="openDetail(scope.row.id)">详情</el-button>
						<el-button v-if="canWrite" size="small" type="success" @click="requestReview([scope.row.id], 'approve')">通过</el-button>
						<el-button v-if="canWrite" size="small" type="warning" @click="requestReview([scope.row.id], 'reject')">驳回</el-button>
						<el-button v-if="canWrite" size="small" type="danger" @click="requestReview([scope.row.id], 'offline')">下架</el-button>
					</el-space>
				</template>
			</el-table-column>
		</el-table>

		<div class="pager">
			<AdminPagination
				background
				:total="props.pagination.total"
				:current-page="props.pagination.page"
				:page-size="props.pagination.pageSize"
				:page-sizes="[10, 20, 50, 100]"
				@size-change="(size:number) => emit('query-change', { page: 1, pageSize: size })"
				@current-change="(page:number) => emit('query-change', { page })"
			/>
		</div>

		<el-dialog v-model="reasonDialogVisible" :close-on-click-modal="!reviewPending" :close-on-press-escape="!reviewPending" :show-close="!reviewPending" :title="`请填写${pendingAction ? actionTextMap[pendingAction] : ''}原因`" width="520px">
			<el-input
				v-model="reasonText"
				aria-label="审核处理原因"
        :readonly="reviewPending"
				type="textarea"
				:rows="4"
				maxlength="200"
				show-word-limit
				placeholder="请填写处理原因（最多 200 字）"
			/>
      <p v-if="reviewError" role="alert">{{ reviewError }}</p>
			<template #footer>
				<el-button :disabled="reviewPending" @click="reasonDialogVisible = false">取消</el-button>
				<el-button v-if="canWrite" type="primary" :loading="reviewPending" @click="submitReview">确认</el-button>
			</template>
		</el-dialog>

		<el-drawer v-model="detailDrawerVisible" title="帖子详情" size="48%" destroy-on-close>
			<template v-if="props.currentDetail">
				<h3>{{ props.currentDetail.title }}</h3>
				<p><strong>作者：</strong>{{ props.currentDetail.author }}</p>
				<p><strong>状态：</strong>{{ formatStatus(props.currentDetail.status) }}</p>
				<p><strong>审核原因：</strong>{{ props.currentDetail.reviewReason || '-' }}</p>
				<p><strong>摘要：</strong>{{ props.currentDetail.summary || '-' }}</p>
				<div class="detail-html" v-html="sanitizedDetailHtml" />
			</template>
			<el-empty v-else description="暂无详情" />
		</el-drawer>
	</el-card>
</template>

<style scoped>
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.title { font-size: 16px; font-weight: 700; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
.detail-html {
	margin-top: 12px;
	padding: 12px;
	background: var(--bg);
	border: 1px solid var(--border);
	border-radius: 8px;
	line-height: 1.75;
	color: var(--text);
	word-break: break-word;
	overflow-wrap: anywhere;
	overflow-x: auto;
}

:deep(.detail-html img) {
	max-width: 100%;
	height: auto;
	display: block;
	margin: 10px auto;
	border-radius: 8px;
}

:deep(.detail-html p) {
	margin: 8px 0;
}

:deep(.detail-html pre) {
	padding: 10px;
	border-radius: 6px;
	background: #1f2430;
	color: #e6e6e6;
	overflow-x: auto;
}

:deep(.detail-html table) {
	width: 100%;
	border-collapse: collapse;
	margin: 10px 0;
	font-size: 13px;
}

:deep(.detail-html th),
:deep(.detail-html td) {
	border: 1px solid var(--border);
	padding: 8px;
}

:deep(.detail-html blockquote) {
	margin: 8px 0;
	padding: 8px 12px;
	border-left: 3px solid var(--accent);
	background: var(--bg);
	color: var(--muted);
}
</style>
