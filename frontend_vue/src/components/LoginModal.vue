<script setup lang="ts">
defineProps<{
	visible: boolean
	account: string
	password: string
	canLogin: boolean
}>()

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'update:account', value: string): void
	(e: 'update:password', value: string): void
	(e: 'login'): void
	(e: 'open-register'): void
}>()

const handleAccountChange = (value: unknown) => {
	emit('update:account', String(value || ''))
}

const handlePasswordChange = (value: unknown) => {
	emit('update:password', String(value || ''))
}
</script>

<template>
	<el-dialog
		:model-value="visible"
		width="420px"
		:show-close="false"
		append-to-body
		class="auth-dialog"
		@close="emit('close')"
		@update:model-value="(value:boolean) => { if (!value) emit('close') }"
	>
		<div class="login-modal">
			<h3 class="login-title">密码登录</h3>

			<el-input
				:model-value="account"
				class="login-input"
				placeholder="手机号/邮箱"
				@update:model-value="handleAccountChange"
			/>
			<el-input
				:model-value="password"
				class="login-input"
				type="password"
				show-password
				placeholder="密码"
				@update:model-value="handlePasswordChange"
			/>

			<el-button class="login-btn" type="primary" :disabled="!canLogin" @click="emit('login')">登录</el-button>

			<div class="login-footer">
				<el-button link type="info">忘记密码</el-button>
				<el-button link type="primary" @click="emit('open-register')">注册账号</el-button>
			</div>
		</div>
	</el-dialog>
</template>

<style scoped>
.login-modal {
	width: 100%;
	padding: 4px 8px;
}

.login-title {
	margin: 0 0 18px;
	text-align: center;
	font-size: 24px;
	font-weight: 700;
	color: #222c3f;
}

.login-input {
	width: 100%;
	margin-bottom: 10px;
}

.login-btn {
	margin-top: 8px;
	width: 100%;
}

.login-footer {
	margin-top: 16px;
	display: flex;
	justify-content: space-between;
}

:deep(.auth-dialog .el-dialog) {
	border-radius: 12px;
}

:deep(.auth-dialog .el-dialog__body) {
	padding: 16px 22px 20px;
}
</style>
