<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AdminAuditItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminAuditItem[]
	loading: boolean
	pagination: Pagination
	action: string
	targetType: string
}>()

const emit = defineEmits<{
	(e: 'refresh'): void
	(e: 'query-change', payload: { page?: number; pageSize?: number; action?: string; targetType?: string }): void
}>()

const localAction = ref(props.action)
const localTargetType = ref(props.targetType)

watch(
	() => props.action,
	(value) => {
		localAction.value = value
	}
)

watch(
	() => props.targetType,
	(value) => {
		localTargetType.value = value
	}
)

const handleSearch = () => {
	emit('query-change', {
		page: 1,
		action: localAction.value.trim(),
		targetType: localTargetType.value.trim()
	})
}

const handleReset = () => {
	localAction.value = ''
	localTargetType.value = ''
	emit('query-change', { page: 1, action: '', targetType: '' })
}
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">审计日志</div>
			<div class="filters">
				<el-input v-model="localAction" clearable placeholder="动作，如 post.review" style="width: 220px" @keyup.enter="handleSearch" />
				<el-input v-model="localTargetType" clearable placeholder="对象类型，如 post/comment" style="width: 220px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table :data="items" :loading="loading" border>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="actorName" label="操作者" width="140">
				<template #default="scope">{{ scope.row.actorName || '-' }}</template>
			</el-table-column>
			<el-table-column prop="action" label="动作" min-width="180" />
			<el-table-column label="对象" min-width="140">
				<template #default="scope">{{ scope.row.targetType }}#{{ scope.row.targetId }}</template>
			</el-table-column>
			<el-table-column prop="ip" label="IP" width="140" />
			<el-table-column prop="createdAt" label="时间" min-width="180" />
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
