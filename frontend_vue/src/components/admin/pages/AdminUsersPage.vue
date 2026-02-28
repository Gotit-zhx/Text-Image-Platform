<script setup lang="ts">
import { ref, watch } from 'vue'
import type { AdminUserItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminUserItem[]
	loading: boolean
	pagination: Pagination
	keyword: string
}>()

const emit = defineEmits<{
	(e: 'refresh'): void
	(e: 'set-roles', payload: { id: number; roles: string[] }): void
	(e: 'query-change', payload: { page?: number; pageSize?: number; keyword?: string }): void
}>()

const roleCandidates = ['super_admin', 'content_moderator', 'operations', 'auditor']
const localKeyword = ref(props.keyword)

watch(
	() => props.keyword,
	(value) => {
		localKeyword.value = value
	}
)

const handleSearch = () => {
	emit('query-change', { page: 1, keyword: localKeyword.value.trim() })
}

const handleReset = () => {
	localKeyword.value = ''
	emit('query-change', { page: 1, keyword: '' })
}

const toggleRole = (roles: string[], role: string) =>
	roles.includes(role) ? roles.filter((item) => item !== role) : [...roles, role]
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">用户角色</div>
			<div class="filters">
				<el-input v-model="localKeyword" clearable placeholder="用户/邮箱关键词" style="width: 240px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table :data="items" :loading="loading" border>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="用户" width="150" />
			<el-table-column prop="email" label="邮箱" min-width="220" />
			<el-table-column label="角色" min-width="280">
				<template #default="scope">
					<el-space wrap>
						<el-tag v-for="role in scope.row.roles" :key="role" type="info">{{ role }}</el-tag>
						<span v-if="!scope.row.roles.length">-</span>
					</el-space>
				</template>
			</el-table-column>
			<el-table-column label="操作" min-width="320" fixed="right">
				<template #default="scope">
					<el-space wrap>
						<el-button
							v-for="role in roleCandidates"
							:key="role"
							size="small"
							@click="emit('set-roles', { id: scope.row.id, roles: toggleRole(scope.row.roles, role) })"
						>
							{{ role }}
						</el-button>
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
