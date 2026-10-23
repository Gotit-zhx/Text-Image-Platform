<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { apiRequest } from '../api/client'
import BaseButton from './ui/BaseButton.vue'
const props = defineProps<{
  open: boolean
  targetType: 'post' | 'comment' | 'user'
  targetId: number
  viewerId?: number
}>()
const emit = defineEmits<{ close: []; login: [] }>()
const reason = ref('不友善或骚扰'),
  description = ref(''),
  pending = ref(false),
  error = ref(''),
  success = ref(false)
let version = 0, owner = props.viewerId
watch(() => [props.targetType, props.targetId, props.viewerId] as const, (next, previous) => {
  if (next[0] !== previous[0] || next[1] !== previous[1] || (next[2] && owner && next[2] !== owner)) {
    version++
    reason.value = '不友善或骚扰'
    description.value = ''
    error.value = ''
    success.value = false
    pending.value = false
  }
  if (next[2]) owner = next[2]
})
onBeforeUnmount(() => { version++ })
const submit = async () => {
  if (!props.viewerId) {
    emit('login')
    return
  }
  if (pending.value) return
  pending.value = true
  const current = version
  error.value = ''
  try {
    await apiRequest('/reports', {
      method: 'POST',
      body: JSON.stringify({
        targetType: props.targetType,
        targetId: props.targetId,
        reason: reason.value,
        description: description.value
      })
    })
    if (current !== version) return
    success.value = true
    description.value = ''
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '举报失败'
  } finally {
    if (current === version) pending.value = false
  }
}
</script>
<template>
  <el-dialog
    :model-value="open"
    title="举报内容或用户"
    width="min(500px,94vw)"
    @close="emit('close')"
    ><p v-if="success" role="status">举报已记录，可在举报与申诉记录查看处理结果。</p>
    <form v-else @submit.prevent="submit">
      <label
        >原因<select v-model="reason" :disabled="pending">
          <option>不友善或骚扰</option>
          <option>违法或危险内容</option>
          <option>垃圾广告</option>
          <option>侵权或隐私泄露</option>
          <option>其他</option>
        </select></label
      ><label
        >补充说明<textarea
          v-model="description"
          :readonly="pending"
          maxlength="2000"
          placeholder="补充可供审核的说明（可选）"
        />
      </label>
      <p v-if="error" role="alert">{{ error }}</p>
      <BaseButton type="submit" variant="primary" :pending="pending">确认举报</BaseButton>
    </form></el-dialog
  >
</template>
<style scoped>
label {
  display: block;
  margin: 12px 0;
}
select,
textarea {
  display: block;
  width: 100%;
  min-height: 44px;
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 8px;
}
textarea {
  min-height: 120px;
}
p[role='alert'] {
  color: var(--danger);
}
</style>
