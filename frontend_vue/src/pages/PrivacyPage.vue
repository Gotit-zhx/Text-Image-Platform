<script setup lang="ts">
import { onMounted, onBeforeUnmount, ref } from 'vue'
import { apiRequest } from '../api/client'
import type { Paged } from '../api/community'
import type { LoginUser } from '../types'
import BaseButton from '../components/ui/BaseButton.vue'
import UiState from '../components/ui/UiState.vue'
const tab = ref('blocks'),
  items = ref<LoginUser[]>([]),
  page = ref(0),
  hasMore = ref(false),
  pending = ref(false),
  error = ref('')
let version=0,controller:AbortController|undefined
const load = async (reset = false) => {
  if (pending.value&&!reset) return
  if(reset){version++;controller?.abort();items.value=[];page.value=0;hasMore.value=false}
  const current=version,kind=tab.value
  controller=new AbortController()
  pending.value = true
  error.value = ''
  try {
    const data = await apiRequest<Paged<LoginUser>>(
      `/users/me/${kind}?page=${reset ? 1 : page.value + 1}`, {signal:controller.signal}
    )
    if(current!==version)return
    items.value = reset ? data.items : [...new Map([...items.value, ...data.items].map(item=>[item.id,item])).values()]
    page.value = data.pagination.page
    hasMore.value = data.pagination.hasMore
  } catch (e) {
    if(current===version&&!(e instanceof Error&&e.name==='AbortError'))error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    if(current===version)pending.value = false
  }
}
const removing = ref<Set<number>>(new Set())
const remove = async (id: number) => {
  if (removing.value.has(id)) return
  removing.value.add(id)
  const current=version,kind=tab.value
  try {
    await apiRequest(`/users/me/${kind}/${id}`, { method: 'DELETE' })
    if(current===version)items.value = items.value.filter((u) => u.id !== id)
  } catch (e) {
    if(current===version)error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    removing.value.delete(id)
  }
}
onMounted(() => load(true))
onBeforeUnmount(()=>{version++;controller?.abort()})
</script>
<template>
  <main class="page-container">
    <h1>隐私与关系</h1>
    <p class="muted">
      屏蔽仅影响你的内容消费；拉黑限制双方新增关注、评论和通知。公共作品仍可能在未登录状态访问。
    </p>
    <label
      >管理列表
      <select v-model="tab" @change="load(true)">
        <option value="blocks">拉黑</option>
        <option value="mutes">屏蔽</option>
      </select></label
    ><UiState v-if="pending&&!items.length" kind="loading"/><UiState v-if="error" kind="error" :description="error" @retry="load(true)" /><UiState
      v-if="!pending && !error && !items.length"
      kind="empty"
    />
    <article v-for="user in items" :key="user.id" class="relation">
      <RouterLink :to="`/u/${user.id}`">{{ user.name }}</RouterLink
      ><BaseButton :pending="removing.has(user.id)" @click="remove(user.id)"
        >解除{{ tab === 'blocks' ? '拉黑' : '屏蔽' }}</BaseButton
      >
    </article>
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton>
  </main>
</template>
<style scoped>
.relation {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
select {
  min-height: 44px;
  padding: 8px;
  border: 1px solid var(--border);
  border-radius: var(--radius-control);
  background: var(--surface);
  color: var(--text);
}
</style>
