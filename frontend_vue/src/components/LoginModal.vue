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
</script>

<template>
	<div v-if="visible" class="login-overlay" @click="emit('close')">
		<div class="login-modal" @click.stop>
			<button class="login-close" @click="emit('close')">×</button>
			<div class="login-brand">miHoYo</div>
			<div class="login-sub-brand">TECH OTAKUS SAVE THE WORLD</div>
			<h3 class="login-title">密码登录</h3>
			<p class="login-mock-tip">测试账号：test@example.com / 123456</p>

			<input
				:value="account"
				class="login-input"
				type="text"
				placeholder="手机号/邮箱"
				@input="emit('update:account', ($event.target as HTMLInputElement).value)"
			/>
			<input
				:value="password"
				class="login-input"
				type="password"
				placeholder="密码"
				@input="emit('update:password', ($event.target as HTMLInputElement).value)"
			/>

			<button class="login-btn" :disabled="!canLogin" @click="emit('login')">登录</button>

			<div class="login-footer">
				<a href="#">忘记密码</a>
				<a href="#" @click.prevent="emit('open-register')">注册账号</a>
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

.login-mock-tip {
	margin: -8px 0 14px;
	text-align: center;
	font-size: 12px;
	color: #8f97a8;
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

.login-footer {
	margin-top: 16px;
	display: flex;
	justify-content: space-between;
	font-size: 14px;
}

.login-footer a {
	color: #57a7ee;
	text-decoration: none;
}
</style>
