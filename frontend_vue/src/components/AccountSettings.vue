<script setup lang="ts">
import { ref } from 'vue'
import type { LoginUser } from '../types'
import { emailActionApi, deactivateApi, changePasswordApi } from '../api/auth'
const props = defineProps<{ user: LoginUser | null; emailAvailable: boolean }>()
const emit = defineEmits<{ deactivated: [] }>()
const password = ref(''),
  confirmation = ref(''),
  oldPassword = ref(''),
  newPassword = ref(''),
  confirmPassword = ref('')
const pending = ref(false),
  message = ref(''),
  error = ref('')
const action = async (runner: () => Promise<unknown>, done: string) => {
  if (pending.value) return
  pending.value = true
  error.value = ''
  message.value = ''
  try {
    await runner()
    message.value = done
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    pending.value = false
  }
}
const verify = () =>
  action(
    () => emailActionApi(props.user?.email || '', 'verify'),
    '如邮箱符合条件，验证邮件将发送到邮箱；本地开发环境请查看邮件输出。'
  )
const change = () =>
  action(async () => {
    if (newPassword.value !== confirmPassword.value) throw new Error('两次密码不一致')
    await changePasswordApi({
      oldPassword: oldPassword.value,
      newPassword: newPassword.value,
      confirmPassword: confirmPassword.value
    })
    oldPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
  }, '密码已更新，其他旧会话将失效。')
const deactivate = () =>
  action(async () => {
    await deactivateApi(password.value, confirmation.value)
    password.value = ''
    emit('deactivated')
  }, '账号已注销')
</script>
<template>
  <main class="account-page">
    <h1>账号设置</h1>
    <nav><RouterLink to="/settings/profile" class="text-button">编辑资料</RouterLink>
      <RouterLink to="/settings/privacy" class="text-button">隐私与关系</RouterLink
      ><RouterLink to="/reports" class="text-button">举报与申诉记录</RouterLink>
    </nav>
    <p v-if="!user">请先登录后管理账号。</p>
    <template v-else>
      <p>{{ user.email }} · {{ user.emailVerified ? '已验证' : '待验证' }}</p>
      <button v-if="!user.emailVerified && emailAvailable" :disabled="pending" @click="verify">重发邮箱验证</button>
      <p v-if="!user.emailVerified && !emailAvailable" class="muted">邮件服务暂未启用，请联系站点管理员验证邮箱。</p>
      <form @submit.prevent="change">
        <h2>修改密码</h2>
        <label
          >旧密码<input
            v-model="oldPassword"
            type="password"
            autocomplete="current-password"
            required
        /></label>
        <label
          >新密码<input v-model="newPassword" type="password" autocomplete="new-password" required
        /></label>
        <label
          >确认新密码<input
            v-model="confirmPassword"
            type="password"
            autocomplete="new-password"
            required
        /></label>
        <button :disabled="pending">更新密码</button>
      </form>
      <details>
        <summary>注销账号</summary>
        <p>注销将停用账号、退出所有会话、匿名化公开资料并隐藏作品；必要关联和管理审计保留。</p>
        <form @submit.prevent="deactivate">
          <label
            >当前密码<input
              v-model="password"
              type="password"
              autocomplete="current-password"
              required
          /></label>
          <label>输入“注销百草园账号”确认<input v-model="confirmation" required /></label>
          <button :disabled="pending || confirmation !== '注销百草园账号'">确认注销账号</button>
        </form>
      </details>
    </template>
    <p v-if="message" role="status">{{ message }}</p>
    <p v-if="error" role="alert">{{ error }}</p>
  </main>
</template>
<style scoped>
.account-page {
  max-width: 640px;
  margin: 24px auto;
  padding: 24px;
  background: white;
  border-radius: 12px;
}
label {
  display: block;
  margin: 12px 0;
}
input {
  display: block;
  min-height: 44px;
  width: 100%;
  padding: 10px;
}
button {
  min-height: 44px;
  padding: 8px 16px;
}
form,
details {
  margin: 24px 0;
}
summary {
  cursor: pointer;
  color: #b93e3e;
}
p[role='alert'] {
  color: #b93e3e;
}
</style>
