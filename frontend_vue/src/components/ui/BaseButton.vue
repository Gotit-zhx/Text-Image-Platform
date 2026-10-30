<script setup lang="ts">
withDefaults(
  defineProps<{
    pending?: boolean
    disabled?: boolean
    variant?: 'primary' | 'secondary' | 'danger'
    type?: 'button' | 'submit'
  }>(),
  { variant: 'secondary', type: 'button' }
)
</script>
<template>
  <button
    :type="type"
    class="base-button"
    :class="variant"
    :disabled="pending || disabled"
    :aria-busy="pending"
  >
    <span v-if="pending" class="spinner" aria-hidden="true" /><slot />
  </button>
</template>
<style scoped>
.base-button {
  min-height: 44px;
  padding: 9px 20px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  font-weight: 600;
  display: inline-flex;
  gap: 8px;
  align-items: center;
  justify-content: center;
  transition: background var(--duration);
}
.primary {
  background: var(--accent);
  border-color: var(--accent);
  color: white;
}
.primary:hover:not(:disabled) {
  background: var(--accent-hover);
}
.secondary:hover:not(:disabled) {
  background: var(--bg);
}
.danger {
  color: var(--danger);
  border-color: var(--danger);
}
.spinner {
  width: 14px;
  height: 14px;
  border: 2px solid currentColor;
  border-right-color: transparent;
  border-radius: 50%;
  animation: turn 0.8s linear infinite;
}
@keyframes turn {
  to {
    transform: rotate(360deg);
  }
}
</style>
