<script setup lang="ts">
import { computed, ref } from 'vue'

const emit = defineEmits<{
	(e: 'login', payload: { account: string; password: string }): void
}>()

const props = defineProps<{
	loading: boolean
	error: string
}>()

const account = ref('')
const password = ref('')
const canSubmit = computed(() => account.value.trim() && password.value.trim())

const handleSubmit = () => {
	if (props.loading || !canSubmit.value) return
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
.admin-login-wrap { min-height: 100dvh; display: grid; place-items: center; background: var(--bg); }
.admin-login-card { width: min(420px,94vw); border-radius: var(--radius); }
.login-btn { width: 100%; margin-top: 8px; }
.error { margin-bottom: 8px; }
</style>
