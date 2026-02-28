<script setup lang="ts">
import { computed, ref } from 'vue'

const emit = defineEmits<{
	(e: 'login', payload: { account: string; password: string }): void
}>()

defineProps<{
	loading: boolean
	error: string
}>()

const account = ref('admin@example.com')
const password = ref('123456')
const canSubmit = computed(() => account.value.trim() && password.value.trim())

const handleSubmit = () => {
	emit('login', { account: account.value.trim(), password: password.value })
}
</script>

<template>
	<div class="admin-login-wrap">
		<el-card class="admin-login-card" shadow="hover">
			<h2>后台管理登录</h2>
			<el-form label-position="top">
				<el-form-item label="账号">
					<el-input v-model="account" placeholder="管理员账号或邮箱" />
				</el-form-item>
				<el-form-item label="密码">
					<el-input v-model="password" type="password" show-password placeholder="请输入密码" @keydown.enter="handleSubmit" />
				</el-form-item>
			</el-form>
			<el-alert v-if="error" class="error" :closable="false" type="error" :title="error" />
			<el-button type="primary" :loading="loading" :disabled="!canSubmit" class="login-btn" @click="handleSubmit">
				登录
			</el-button>
		</el-card>
	</div>
</template>

<style scoped>
.admin-login-wrap { min-height: 100vh; display: grid; place-items: center; background: #f4f6fb; }
.admin-login-card { width: 420px; border-radius: 12px; }
.login-btn { width: 100%; margin-top: 8px; }
.error { margin-bottom: 8px; }
</style>
