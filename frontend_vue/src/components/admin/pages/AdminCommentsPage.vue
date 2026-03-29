<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AdminCommentItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminCommentItem[]
	loading: boolean
	pagination: Pagination
	visibility: string
	keyword: string
}>()

const emit = defineEmits<{
	(e: 'refresh'): void
	(e: 'hide', id: number): void
	(e: 'restore', id: number): void
	(e: 'delete', id: number): void
	(e: 'query-change', payload: { page?: number; pageSize?: number; visibility?: string; keyword?: string }): void
}>()

const localVisibility = ref(props.visibility)
const localKeyword = ref(props.keyword)

watch(
	() => props.visibility,
	(value) => {
		localVisibility.value = value
	}
)

watch(
	() => props.keyword,
	(value) => {
		localKeyword.value = value
	}
)

const handleSearch = () => {
	emit('query-change', {
		page: 1,
		visibility: localVisibility.value,
		keyword: localKeyword.value.trim()
	})
}

const handleReset = () => {
	localVisibility.value = ''
	localKeyword.value = ''
	emit('query-change', { page: 1, visibility: '', keyword: '' })
}
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">评论管理</div>
			<div class="filters">
				<el-select v-model="localVisibility" clearable placeholder="可见性" style="width: 140px">
					<el-option label="可见" value="visible" />
					<el-option label="隐藏" value="hidden" />
				</el-select>
				<el-input v-model="localKeyword" clearable placeholder="评论/作者关键词" style="width: 220px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table :data="items" :loading="loading" border>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="content" label="评论" min-width="260" show-overflow-tooltip />
			<el-table-column prop="author" label="作者" width="130" />
			<el-table-column label="状态" width="110">
				<template #default="scope">
					<el-tag :type="scope.row.isHidden ? 'warning' : 'success'">{{ scope.row.isHidden ? '已隐藏' : '可见' }}</el-tag>
				</template>
			</el-table-column>
			<el-table-column label="操作" width="200" fixed="right">
				<template #default="scope">
					<el-space>
						<el-button v-if="!scope.row.isHidden" size="small" type="warning" @click="emit('hide', scope.row.id)">隐藏</el-button>
						<el-button v-else size="small" type="success" @click="emit('restore', scope.row.id)">恢复</el-button>
						<el-button size="small" type="danger" @click="emit('delete', scope.row.id)">删除</el-button>
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
