<script setup lang="ts">
import { ref, watch } from 'vue'
const props = withDefaults(defineProps<{ src?: string; name: string; size?: number }>(), {
  size: 32
})
const failed = ref(false)
watch(
  () => props.src,
  () => {
    failed.value = false
  }
)
</script>
<template>
  <span class="user-avatar" :style="{ width: size + 'px', height: size + 'px' }" aria-hidden="true"
    ><img v-if="src && !failed" :src="src" alt="" @error="failed = true" /><span v-else>{{
      name.slice(0, 1) || '人'
    }}</span></span
  >
</template>
<style scoped>
.user-avatar {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  border-radius: 50%;
  flex-shrink: 0;
  overflow: hidden;
  background: var(--avatar-bg);
  color: var(--avatar-text);
  font-size: 13px;
  font-weight: 600;
}
.user-avatar img {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
</style>
