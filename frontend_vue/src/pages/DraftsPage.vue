<script setup lang="ts">
import { onMounted, ref } from 'vue'
import type { DraftRecord } from '../api/media'
import type { Paged } from '../api/community'
import { apiRequest } from '../api/client'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'
const items = ref<DraftRecord[]>([]),
  pending = ref(false),
  error = ref(''),
  page = ref(0),
  hasMore = ref(false),
  deleting = ref<DraftRecord>(),
  removing = ref(false)
const load = async (reset = false) => {
  if (pending.value) return
  pending.value = true
  error.value = ''
  try {
    const result = await apiRequest<Paged<DraftRecord>>(
      `/drafts?page=${reset ? 1 : page.value + 1}`
    )
    items.value = reset ? result.items : [...items.value, ...result.items]
    page.value = result.pagination.page
    hasMore.value = result.pagination.hasMore
  } catch (e) {
    error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    pending.value = false
  }
}
const remove = async () => {
  if (!deleting.value || removing.value) return
  removing.value = true
  try {
    await apiRequest(`/drafts/${deleting.value.id}`, { method: 'DELETE' })
    items.value = items.value.filter((d) => d.id !== deleting.value!.id)
    deleting.value = undefined
  } catch (e) {
    error.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    removing.value = false
  }
}
onMounted(() => load(true))
</script>
<template>
  <main class="page-container">
    <h1>我的草稿</h1>
    <UiState v-if="pending && !items.length" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    /><UiState v-if="!pending && !error && !items.length" kind="empty" title="还没有草稿"
      ><RouterLink to="/publish" class="text-button">开始记录</RouterLink></UiState
    >
    <article v-for="draft in items" :key="draft.id" class="draft">
      <div>
        <h2>{{ draft.title || '未命名草稿' }}</h2>
        <time>{{ new Date(draft.updatedAt).toLocaleString() }}</time>
      </div>
      <RouterLink :to="{ path: '/publish', query: { draft: draft.id } }" class="text-button"
        >继续编辑</RouterLink
      ><button class="text-button" @click="deleting = draft">删除</button>
    </article>
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton
    ><ConfirmDialog
      :open="!!deleting"
      title="删除这份草稿？"
      description="草稿正文将删除，作品不受影响。"
      :pending="removing"
      @cancel="deleting = undefined"
      @confirm="remove"
    />
  </main>
</template>
<style scoped>
.draft {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
.draft > div {
  margin-right: auto;
  min-width: 0;
}
.draft h2 {
  font-size: 18px;
  margin: 0;
}
.draft time {
  font-size: 12px;
  color: var(--muted);
}
.draft a,
.draft button {
  white-space: nowrap;
}
</style>
