<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { consumeTokenApi } from '../api/auth'
const route = useRoute(),
  router = useRouter()
const reset = computed(() => route.params.action === 'reset')
const password = ref(''),
  confirmation = ref(''),
  pending = ref(false),
  error = ref(''),
  success = ref(false)
const submit = async () => {
  if (pending.value) return
  error.value = ''
  if (reset.value && password.value !== confirmation.value) {
    error.value = '两次密码不一致'
    return
  }
  pending.value = true
  try {
    await consumeTokenApi(
      String(route.query.token || ''),
      reset.value ? 'reset' : 'verify',
      password.value
    )
    success.value = true
    password.value = ''
    confirmation.value = ''
    await router.replace({ name: 'auth-token', params: { action: route.params.action } })
  } catch (e) {
    error.value = e instanceof Error ? e.message : '请求失败'
  } finally {
    pending.value = false
  }
}
</script>
<template>
  <main class="account-page">
    <h1>{{ reset ? '重置密码' : '验证邮箱' }}</h1>
    <p v-if="success" role="status">
      {{ reset ? '密码已重置，请使用新密码登录。' : '邮箱验证成功，请返回登录。' }}
    </p>
    <form v-else @submit.prevent="submit">
      <template v-if="reset"
        ><label
          >新密码<input
            v-model="password"
            type="password"
            autocomplete="new-password"
            required /></label
        ><label
          >确认新密码<input
            v-model="confirmation"
            type="password"
            autocomplete="new-password"
            required /></label
      ></template>
      <p v-else>确认使用此链接验证邮箱。链接24小时有效且仅可使用一次。</p>
      <p v-if="error" role="alert">{{ error }}</p>
      <button :disabled="pending">
        {{ pending ? '处理中…' : reset ? '确认重置' : '确认验证邮箱' }}
      </button>
    </form>
    <RouterLink to="/">返回百草园</RouterLink>
  </main>
</template>
<style scoped>
.account-page {
  max-width: 560px;
  margin: 32px auto;
  padding: 24px;
  background: white;
  border-radius: 12px;
}
label {
  display: block;
  margin: 16px 0;
}
input {
  display: block;
  min-height: 44px;
  width: 100%;
  padding: 10px;
}
button {
  min-height: 44px;
  margin: 12px 0;
  padding: 8px 20px;
}
p[role='alert'] {
  color: #b93e3e;
}
</style>
