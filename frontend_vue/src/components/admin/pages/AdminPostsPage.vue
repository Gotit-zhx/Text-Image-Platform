<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AdminPostItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminPostItem[]
	loading: boolean
	pagination: Pagination
	status: string
	keyword: string
}>()

const emit = defineEmits<{
	(e: 'refresh'): void
	(e: 'review', payload: { id: number; action: 'approve' | 'reject' | 'offline' }): void
	(e: 'query-change', payload: { page?: number; pageSize?: number; status?: string; keyword?: string }): void
}>()

const localStatus = ref(props.status)
const localKeyword = ref(props.keyword)

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
	emit('query-change', { page: 1, status: '', keyword: '' })
}
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">帖子审核</div>
			<div class="filters">
				<el-select v-model="localStatus" clearable placeholder="状态" style="width: 140px">
					<el-option label="待审核" value="pending" />
					<el-option label="已通过" value="approved" />
					<el-option label="已驳回" value="rejected" />
					<el-option label="已下架" value="offline" />
				</el-select>
				<el-input v-model="localKeyword" clearable placeholder="标题/作者关键词" style="width: 220px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table :data="props.items" :loading="loading" border>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="title" label="标题" min-width="220" show-overflow-tooltip />
			<el-table-column prop="author" label="作者" width="140" />
			<el-table-column prop="status" label="状态" width="120" />
			<el-table-column label="操作" width="230" fixed="right">
				<template #default="scope">
					<el-space>
						<el-button size="small" type="success" @click="emit('review', { id: scope.row.id, action: 'approve' })">通过</el-button>
						<el-button size="small" type="warning" @click="emit('review', { id: scope.row.id, action: 'reject' })">驳回</el-button>
						<el-button size="small" type="danger" @click="emit('review', { id: scope.row.id, action: 'offline' })">下架</el-button>
					</el-space>
				</template>
			</el-table-column>
		</el-table>

		<div class="pager">
			<el-pagination
				background
				layout="total, sizes, prev, pager, next, jumper"
				:total="props.pagination.total"
				:current-page="props.pagination.page"
				:page-size="props.pagination.pageSize"
				:page-sizes="[10, 20, 50, 100]"
				@size-change="(size:number) => emit('query-change', { page: 1, pageSize: size })"
				@current-change="(page:number) => emit('query-change', { page })"
			/>
		</div>
	</el-card>
</template>

<style scoped>
.panel { background: #fff; border: 1px solid #e6ebf2; border-radius: 10px; padding: 16px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.title { font-size: 16px; font-weight: 700; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
