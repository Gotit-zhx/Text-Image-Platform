<script setup lang="ts">
defineProps<{
	visible: boolean
	email: string
	password: string
	confirmPassword: string
	isEmailValid: boolean
	isPasswordMatch: boolean
	canRegister: boolean
}>()

const emit = defineEmits<{
	(e: 'close'): void
	(e: 'update:email', value: string): void
	(e: 'update:password', value: string): void
	(e: 'update:confirmPassword', value: string): void
	(e: 'register'): void
	(e: 'back-login'): void
}>()

const handleEmailChange = (value: unknown) => {
	emit('update:email', String(value || ''))
}

const handlePasswordChange = (value: unknown) => {
	emit('update:password', String(value || ''))
}

const handleConfirmPasswordChange = (value: unknown) => {
	emit('update:confirmPassword', String(value || ''))
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
			<h3 class="login-title">邮箱注册</h3>

			<el-input
				:model-value="email"
				class="login-input"
				placeholder="请输入邮箱"
				@update:model-value="handleEmailChange"
			/>
			<el-input
				:model-value="password"
				class="login-input"
				type="password"
				show-password
				placeholder="请输入密码"
				@update:model-value="handlePasswordChange"
			/>
			<el-input
				:model-value="confirmPassword"
				class="login-input"
				type="password"
				show-password
				placeholder="请确认密码"
				@update:model-value="handleConfirmPasswordChange"
			/>

			<el-alert v-if="email && !isEmailValid" class="login-tip" type="error" :closable="false" title="请输入正确的邮箱格式" />
			<el-alert v-else-if="confirmPassword && !isPasswordMatch" class="login-tip" type="error" :closable="false" title="两次输入的密码不一致" />

			<el-button class="login-btn" type="primary" :disabled="!canRegister" @click="emit('register')">注册</el-button>

			<div class="login-footer single-link">
				<el-button link type="primary" @click="emit('back-login')">返回登录</el-button>
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

.login-tip {
	margin: -2px 0 10px;
}

.login-footer {
	margin-top: 16px;
	display: flex;
	justify-content: space-between;
	font-size: 14px;
}

.login-footer.single-link {
	justify-content: center;
}

:deep(.auth-dialog .el-dialog) {
	border-radius: 12px;
}

:deep(.auth-dialog .el-dialog__body) {
	padding: 16px 22px 20px;
}
</style>
