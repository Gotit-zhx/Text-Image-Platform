<script setup lang="ts">
import { ref, watch } from 'vue'
import AdminPagination from '../AdminPagination.vue'
import {apiRequest} from '../../../api/client'
import type { AdminUserItem } from '../../../api/admin'
import type { Pagination } from '../../../api/admin'

const props = defineProps<{
	items: AdminUserItem[]
	loading: boolean
  canOperate?: boolean
  canRoles?: boolean
	pagination: Pagination
	keyword: string
}>()

const emit = defineEmits<{
	(e: 'refresh'): void
	(e: 'set-admin', payload: { id: number; isAdmin: boolean }): void
	(e: 'query-change', payload: { page?: number; pageSize?: number; keyword?: string }): void
}>()
const target=ref<AdminUserItem>(),action=ref('mute'),reason=ref(''),pending=ref(false),error=ref(''),roleList=ref<string[]>([])
const submitStatus=async()=>{if(!target.value||pending.value)return;pending.value=true;error.value='';try{await apiRequest(`/admin/users/${target.value.id}/status`,{method:'POST',body:JSON.stringify({action:action.value,reason:reason.value})});target.value=undefined;emit('refresh')}catch(e){error.value=e instanceof Error?e.message:'处置失败'}finally{pending.value=false}}
const submitRoles=async()=>{if(!target.value||pending.value)return;pending.value=true;error.value='';try{await apiRequest(`/admin/users/${target.value.id}/roles`,{method:'PUT',body:JSON.stringify({roles:roleList.value})});target.value=undefined;emit('refresh')}catch(e){error.value=e instanceof Error?e.message:'授权失败'}finally{pending.value=false}}
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
</script>

<template>
	<el-card class="panel" shadow="never">
		<div class="head">
			<div class="title">用户管理</div>
			<div class="filters">
				<el-input v-model="localKeyword" aria-label="用户关键词" clearable placeholder="用户/邮箱关键词" style="width: 240px" @keyup.enter="handleSearch" />
				<el-button type="primary" @click="handleSearch">查询</el-button>
				<el-button @click="handleReset">重置</el-button>
				<el-button @click="emit('refresh')">刷新</el-button>
			</div>
		</div>
		<el-table v-loading="loading" :data="items" :aria-busy="loading" border>
			<el-table-column prop="id" label="ID" width="80" />
			<el-table-column prop="name" label="用户" width="150" />
			<el-table-column v-if="canRoles" prop="email" label="邮箱" min-width="220" />
			<el-table-column label="管理员" width="120">
				<template #default="scope">
					<el-tag :type="scope.row.isAdmin ? 'success' : 'info'">
						{{ scope.row.isAdmin ? '是' : '否' }}
					</el-tag>
				</template>
			</el-table-column>
			<el-table-column v-if="canRoles||canOperate" label="操作" min-width="180" fixed="right">
				<template #default="scope">
          <el-button v-if="canOperate" size="small" @click="target=scope.row;action='mute';reason=''">账号处置</el-button>
          <el-button v-if="canRoles" size="small" @click="target=scope.row;action='roles';roleList=[...(scope.row.roles||[])]">分配角色</el-button>

				</template>
			</el-table-column>
		</el-table>
    <el-dialog :model-value="!!target" :title="action==='roles'?'调整角色':'账号处置'" width="min(500px,94vw)" @close="target=undefined"><p>{{target?.name}}</p><template v-if="action==='roles'"><el-checkbox-group v-model="roleList"><el-checkbox value="content_moderator">内容审核员</el-checkbox><el-checkbox value="operations">运营</el-checkbox><el-checkbox value="auditor">只读审计员</el-checkbox></el-checkbox-group><p>超级管理员由显式管理命令授权；最后一个超级管理员受保护。</p></template><template v-else><el-select v-model="action"><el-option label="禁言7天" value="mute"/><el-option label="封禁" value="ban"/><el-option label="解除限制" value="restore"/></el-select><el-input v-model="reason" type="textarea" maxlength="500" placeholder="处理原因"/></template><el-alert v-if="error" :title="error" type="error"/><el-button type="primary" :loading="pending" :disabled="action!=='roles'&&!reason.trim()" @click="action==='roles'?submitRoles():submitStatus()">确认操作</el-button></el-dialog>
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
	</el-card>
</template>

<style scoped>
.panel { background: var(--surface); border: 1px solid var(--border); border-radius: var(--radius); padding: 16px; }
.head { display: flex; justify-content: space-between; align-items: center; margin-bottom: 12px; gap: 12px; flex-wrap: wrap; }
.title { font-size: 16px; font-weight: 700; }
.filters { display: flex; gap: 8px; flex-wrap: wrap; }
.pager { display: flex; justify-content: flex-end; margin-top: 12px; }
</style>
