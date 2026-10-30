<script setup lang="ts">
withDefaults(defineProps<{
  total: number
  currentPage: number
  pageSize: number
  pageSizes?: number[]
  background?: boolean
}>(), { pageSizes: () => [10, 20, 50, 100], background: true })
const emit = defineEmits<{
  'size-change': [size: number]
  'current-change': [page: number]
}>()
</script>
<template>
  <el-pagination
    class="admin-pagination"
    :background="background"
    :total="total"
    :current-page="currentPage"
    :page-size="pageSize"
    layout="total,slot,prev,pager,next,jumper"
    @current-change="emit('current-change', $event)"
  >
    <label class="page-size">每页条数
      <select :value="pageSize" @change="emit('size-change', Number(($event.target as HTMLSelectElement).value))">
        <option v-for="size in pageSizes" :key="size" :value="size">{{ size }}</option>
      </select>
    </label>
  </el-pagination>
</template>
<style scoped>
.admin-pagination { flex-wrap: wrap; justify-content: flex-end; gap: 8px; white-space: normal; }
.page-size { display: flex; align-items: center; gap: 6px; font-size: 12px; }
select { min-height: 36px; padding: 4px 8px; border: 1px solid var(--border); border-radius: var(--radius-control); background: var(--surface); }
</style>
