<script setup lang="ts">
defineProps<{
	overview: {
		postPendingCount: number
		commentHiddenCount: number
		todayActiveUsers: number
		auditEvents24h: number
	}
}>()
</script>

<template>
	<el-row :gutter="12">
		<el-col :lg="6" :md="12" :sm="12" :xs="24">
			<el-card><el-statistic title="待审核帖子" :value="overview.postPendingCount" /></el-card>
		</el-col>
		<el-col :lg="6" :md="12" :sm="12" :xs="24">
			<el-card><el-statistic title="已隐藏评论" :value="overview.commentHiddenCount" /></el-card>
		</el-col>
		<el-col :lg="6" :md="12" :sm="12" :xs="24">
			<el-card><el-statistic title="今日活跃用户" :value="overview.todayActiveUsers" /></el-card>
		</el-col>
		<el-col :lg="6" :md="12" :sm="12" :xs="24">
			<el-card><el-statistic title="24h审计事件" :value="overview.auditEvents24h" /></el-card>
		</el-col>
	</el-row>
</template>

<style scoped>
:deep(.el-card) { border-radius: 12px; }
</style>
