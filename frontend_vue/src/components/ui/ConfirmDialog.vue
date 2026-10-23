<script setup lang="ts">
import BaseButton from './BaseButton.vue'
defineProps<{ open: boolean; title: string; description: string; pending?: boolean }>()
defineEmits<{ cancel: []; confirm: [] }>()
</script>
<template>
  <el-dialog
    :model-value="open"
    :title="title"
    width="min(440px,94vw)"
    :close-on-click-modal="!pending"
    :close-on-press-escape="!pending"
    @close="$emit('cancel')"
    ><p>{{ description }}</p>
    <template #footer
      ><BaseButton :disabled="pending" @click="$emit('cancel')">取消</BaseButton
      ><BaseButton variant="danger" :pending="pending" @click="$emit('confirm')"
        >确认</BaseButton
      ></template
    ></el-dialog
  >
</template>
