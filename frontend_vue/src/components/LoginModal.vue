<script setup lang="ts">
import { ref, watch } from 'vue'
import { emailActionApi } from '../api/auth'
const recovery = ref(false), recoveryEmail = ref(''), recoveryPending = ref(false), recoveryMessage = ref('')
const requestEmail = async (purpose: 'reset' | 'verify') => {
  if (recoveryPending.value) return
  recoveryPending.value = true; recoveryMessage.value = ''
  try { recoveryMessage.value = (await emailActionApi(recoveryEmail.value, purpose)).message }
  catch (e) { recoveryMessage.value = e instanceof Error ? e.message : '请求失败' }
  finally { recoveryPending.value = false }
}

const props = defineProps<{
	visible: boolean
  registrationEnabled: boolean
  emailAvailable: boolean
  pending?: boolean
  error?: string
	account: string
	password: string
	canLogin: boolean
}>()
watch(() => props.visible, (visible) => {
  if (visible) {
    recovery.value = false
    recoveryMessage.value = ''
  }
})

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
    :title="recovery ? '邮箱与密码帮助' : '密码登录'"
		width="min(420px, 94vw)"
		:show-close="false"
		append-to-body
		class="auth-dialog"
		@close="emit('close')"
		@update:model-value="(value:boolean) => { if (!value) emit('close') }"
	>
		<div class="login-modal">
      <div v-if="recovery && emailAvailable" class="recovery-panel">
        <el-input v-model="recoveryEmail" type="email" aria-label="邮箱" placeholder="注册邮箱" />
        <div class="recovery-actions">
          <el-button :loading="recoveryPending" @click="requestEmail('reset')">申请重置密码</el-button>
          <el-button :disabled="recoveryPending" @click="requestEmail('verify')">重发验证邮件</el-button>
        </div>
        <p v-if="recoveryMessage" role="status">{{ recoveryMessage }}</p>
        <el-button link type="primary" @click="recovery = false">返回登录</el-button>
      </div>
      <div v-else>

			<el-input
				:model-value="account"
				class="login-input"
				placeholder="用户名/邮箱" aria-label="用户名或邮箱" autocomplete="username"
				@update:model-value="handleAccountChange"
			/>
			<el-input
				:model-value="password"
				class="login-input"
				type="password"
				show-password
				placeholder="密码" aria-label="密码" autocomplete="current-password" @keyup.enter="emit('login')"
				@update:model-value="handlePasswordChange"
			/>

			<el-button class="login-btn" type="primary" :disabled="!canLogin || pending" :loading="pending" @click="emit('login')">登录</el-button>

			<p v-if="error" role="alert">{{ error }}</p>
      <div class="login-footer">
				<el-button v-if="emailAvailable" link type="info" @click="recovery = true">忘记密码 / 重发验证</el-button>
				<el-button v-if="registrationEnabled" link type="primary" @click="emit('open-register')">注册账号</el-button>
			</div>
      <p v-if="!registrationEnabled" class="muted">此演示站暂未开放注册，请使用站点管理员提供的账号。</p>
      <p v-if="!emailAvailable" class="muted">邮件服务暂未启用，如需找回密码请联系站点管理员。</p>
      </div>
		</div>
	</el-dialog>
</template>

<style scoped>
.login-modal {
	width: 100%;
	padding: 4px 8px;
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
.recovery-panel {
  display: grid;
  gap: 12px;
}
.recovery-actions {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
}
.recovery-actions .el-button {
  margin: 0;
}

p[role='alert'] {
  color: var(--danger);
}
</style>
