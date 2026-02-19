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
</script>

<template>
	<div v-if="visible" class="login-overlay" @click="emit('close')">
		<div class="login-modal" @click.stop>
			<button class="login-close" @click="emit('close')">×</button>
			<div class="login-brand">miHoYo</div>
			<div class="login-sub-brand">TECH OTAKUS SAVE THE WORLD</div>
			<h3 class="login-title">邮箱注册</h3>

			<input
				:value="email"
				class="login-input"
				type="email"
				placeholder="请输入邮箱"
				@input="emit('update:email', ($event.target as HTMLInputElement).value)"
			/>
			<input
				:value="password"
				class="login-input"
				type="password"
				placeholder="请输入密码"
				@input="emit('update:password', ($event.target as HTMLInputElement).value)"
			/>
			<input
				:value="confirmPassword"
				class="login-input"
				type="password"
				placeholder="请确认密码"
				@input="emit('update:confirmPassword', ($event.target as HTMLInputElement).value)"
			/>

			<p v-if="email && !isEmailValid" class="login-tip">请输入正确的邮箱格式</p>
			<p v-else-if="confirmPassword && !isPasswordMatch" class="login-tip">两次输入的密码不一致</p>

			<button class="login-btn" :disabled="!canRegister" @click="emit('register')">注册</button>

			<div class="login-footer single-link">
				<a href="#" @click.prevent="emit('back-login')">返回登录</a>
			</div>
		</div>
	</div>
</template>

<style scoped>
.login-overlay {
	position: fixed;
	inset: 0;
	background: rgba(17, 20, 29, 0.62);
	display: grid;
	place-items: center;
	z-index: 40;
	padding: 16px;
}

.login-modal {
	position: relative;
	width: 100%;
	max-width: 365px;
	background: #fff;
	border-radius: 12px;
	padding: 28px 30px 22px;
	box-shadow: 0 18px 48px rgba(10, 15, 35, 0.28);
}

.login-close {
	position: absolute;
	right: 12px;
	top: 10px;
	border: none;
	background: transparent;
	font-size: 24px;
	line-height: 1;
	color: #b3b8c4;
	cursor: pointer;
}

.login-brand {
	text-align: center;
	font-size: 42px;
	line-height: 1;
	font-weight: 800;
	letter-spacing: 1px;
	color: #53c4ff;
	margin-top: 4px;
}

.login-sub-brand {
	text-align: center;
	font-size: 9px;
	color: #9dc5df;
	letter-spacing: 1.2px;
	margin-top: 2px;
	margin-bottom: 18px;
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
	height: 44px;
	border: 1px solid #e3e7ef;
	border-radius: 8px;
	padding: 0 12px;
	font-size: 14px;
	outline: none;
	margin-bottom: 10px;
	background: #fafbfd;
}

.login-input:focus {
	border-color: #8bc4ff;
	background: #fff;
}

.login-btn {
	margin-top: 8px;
	width: 100%;
	height: 44px;
	border: none;
	border-radius: 8px;
	font-size: 16px;
	font-weight: 700;
	background: #d8dce4;
	color: #8f97a8;
	cursor: pointer;
}

.login-btn:disabled {
	cursor: not-allowed;
}

.login-btn:not(:disabled) {
	background: linear-gradient(180deg, #42c8ff, #17a7f6);
	color: #fff;
}

.login-tip {
	margin: -2px 0 10px;
	font-size: 12px;
	color: #f56c6c;
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

.login-footer a {
	color: #57a7ee;
	text-decoration: none;
}
</style>
