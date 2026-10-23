<script setup lang="ts">
import BaseButton from './BaseButton.vue'
defineProps<{
  kind: 'loading' | 'empty' | 'error' | 'unavailable' | 'forbidden'
  title?: string
  description?: string
}>()
defineEmits<{ retry: [] }>()
</script>
<template>
  <div
    class="ui-state"
    aria-live="polite"
    :role="kind === 'error' ? 'alert' : 'status'"
    :aria-busy="kind === 'loading'"
  >
    <div v-if="kind === 'loading'" class="skeletons">
      <div v-for="i in 4" :key="i" class="skeleton" />
    </div>
    <template v-else
      ><h2>
        {{
          title ||
          {
            empty: '这里还没有内容',
            error: '暂时无法加载',
            unavailable: '内容已不可用',
            forbidden: '需要登录或相应权限'
          }[kind]
        }}
      </h2>
      <p v-if="description">{{ description }}</p>
      <BaseButton v-if="kind === 'error'" @click="$emit('retry')">重试</BaseButton><slot
    /></template>
  </div>
</template>
<style scoped>
.ui-state {
  padding: 48px 16px;
  text-align: center;
  color: var(--muted);
}
h2 {
  font-size: 19px;
  color: var(--text);
}
.skeletons {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  gap: 20px;
}
.skeleton {
  height: 280px;
  background: var(--border);
  border-radius: var(--radius);
  animation: pulse 1.3s ease-in-out infinite alternate;
}
@keyframes pulse {
  to {
    opacity: 0.4;
  }
}
</style>
