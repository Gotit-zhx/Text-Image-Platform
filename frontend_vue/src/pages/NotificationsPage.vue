<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../api/client'
import type { Paged } from '../api/community'
import type { LoginUser } from '../types'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import UserAvatar from '../components/ui/UserAvatar.vue'
type Notice = {
  id: number
  title: string
  content: string
  event: string
  actor?: LoginUser
  targetId: number
  targetType: string
  postId?: number
  commentId?: number
  unavailable: boolean
  readAt?: string
  createdAt: string
  manageUrl?: string
}
const router = useRouter(),
  items = ref<Notice[]>([]),
  page = ref(0),
  hasMore = ref(false),
  pending = ref(false),
  error = ref(''),
  category = ref(''),
  actionPending = ref(false)
let version = 0,
  timer: ReturnType<typeof setInterval> | undefined,
  controller:AbortController|undefined
const load = async (reset = false,refresh=false) => {
  if(pending.value&&!reset)return
  if(reset){version++;controller?.abort();items.value=[];page.value=0;hasMore.value=false}
  const current=version
  controller=new AbortController()
  pending.value = true
  error.value = ''
  try {
    const known = new Set(items.value.map(item => item.id))
    let beforeId = reset || refresh ? undefined : items.value[items.value.length - 1]?.id
    const incoming: Notice[] = []
    let result: Paged<Notice>
    do {
      result = await apiRequest<Paged<Notice>>(
        `/notifications?category=${category.value}${beforeId ? `&beforeId=${beforeId}` : ''}`,
        {signal:controller.signal}
      )
      if (current !== version) return
      incoming.push(...result.items)
      beforeId = result.items[result.items.length - 1]?.id
    } while (refresh && beforeId && result.pagination.hasMore && !result.items.some(item => known.has(item.id)))
    if (current !== version) return
    const previous = new Map(items.value.map(item => [item.id, item]))
    for (const item of incoming) item.readAt ||= previous.get(item.id)?.readAt
    items.value=reset?incoming:[...new Map([...items.value,...incoming].map(n=>[n.id,n])).values()].sort((a,b)=>b.createdAt.localeCompare(a.createdAt)||b.id-a.id)
    if(!refresh){page.value++;hasMore.value=result.pagination.hasMore}
    else if(!result.pagination.hasMore)hasMore.value=false
  } catch (e) {
    if(current===version&&!(e instanceof Error&&e.name==='AbortError'))error.value = e instanceof Error ? e.message : '消息加载失败'
  } finally {
    if (current === version) pending.value = false
  }
}
const cancelLoad = () => {
  version++
  controller?.abort()
  pending.value = false
}
const open = async (item: Notice) => {
  const current = version
  try {
    await apiRequest(`/notifications/${item.id}/read`, { method: 'POST' })
    if (current !== version) return
    cancelLoad()
    item.readAt = new Date().toISOString()
    window.dispatchEvent(new Event('notifications-changed'))
    if (item.manageUrl) {
      router.push(item.manageUrl)
      return
    }
    if (!item.unavailable) {
      if (item.postId)
        router.push({
          path: `/detail/${item.postId}`,
          query: item.commentId ? { commentId: item.commentId } : {}
        })
      else if (item.targetType === 'user') router.push(`/u/${item.targetId}`)
      else router.push('/reports')
    }
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '操作失败'
  }
}
const readAll = async () => {
  if (actionPending.value) return
  actionPending.value = true
  cancelLoad()
  const readIds = new Set(items.value.map(item => item.id))
  try {
    await apiRequest('/notifications/read-all', { method: 'POST' })
    cancelLoad()
    items.value.forEach((n) => {if(readIds.has(n.id))n.readAt = new Date().toISOString()})
    window.dispatchEvent(new Event('notifications-changed'))
  } catch (e) {
    error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actionPending.value = false
  }
}
watch(category, () => load(true))
const visibility = () => {
  if (timer) clearInterval(timer)
  if (!document.hidden) {
    void load(!page.value,!!page.value)
    timer = setInterval(() => load(false,true), 30000)
  }
}
onMounted(() => {
  visibility()
  document.addEventListener('visibilitychange', visibility)
})
onBeforeUnmount(() => {
  version++
  controller?.abort()
  if (timer) clearInterval(timer)
  document.removeEventListener('visibilitychange', visibility)
})
</script>
<template>
  <main class="page-container notice-page">
    <header>
      <h1>消息通知</h1>
      <BaseButton :pending="pending" @click="load(!page,!!page)">刷新</BaseButton>
      <BaseButton :pending="actionPending" @click="readAll">全部已读</BaseButton>
    </header>
    <nav aria-label="通知分类">
      <button
        v-for="[value, label] in [
          ['', '全部'],
          ['social', '互动'],
          ['system', '系统']
        ]"
        :key="value"
        :class="{ active: category === value }"
        @click="category = value || ''"
      >
        {{ label }}
      </button>
    </nav>
    <UiState v-if="pending && !items.length" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    /><UiState
      v-if="!pending && !error && !items.length"
      kind="empty"
      title="暂时没有新消息"
    /><button
      v-for="item in items"
      :key="item.id"
      :data-notification-id="item.id"
      class="notice"
      :class="{ unread: !item.readAt }"
      @click="open(item)"
    >
      <UserAvatar :name="item.actor?.name || '系统'" :src="item.actor?.avatarUrl" /><span
        ><strong>{{ item.actor?.name }} {{ item.title }}</strong
        ><span v-if="item.content">{{ item.content }}</span
        ><span v-if="item.manageUrl" class="muted">查看原因、提交复核或申诉</span
        ><span v-if="item.unavailable" class="muted">相关内容已不可用，事件记录已保留。</span
        ><time
          >{{ new Date(item.createdAt).toLocaleString() }} ·
          {{ item.readAt ? '已读' : '未读' }}</time
        ></span
      ></button
    ><BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton>
  </main>
</template>
<style scoped>
.notice-page {
  max-width: 880px;
}
header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
nav {
  display: flex;
  gap: 16px;
  margin: 24px 0;
}
nav button {
  min-height: 44px;
  border: 0;
  background: none;
  color: var(--muted);
  padding: 6px 12px;
}
.active {
  border-bottom: 2px solid var(--accent) !important;
  color: var(--text) !important;
}
.notice {
  display: flex;
  gap: 16px;
  width: 100%;
  text-align: left;
  border: 0;
  border-bottom: 1px solid var(--border);
  background: none;
  padding: 24px 12px;
}
.notice > span {
  display: flex;
  flex-direction: column;
  gap: 6px;
  font-size: 14px;
}
.notice strong {
  font-weight: 600;
}
.notice time {
  font-size: 12px;
  color: var(--muted);
}
.unread {
  background: var(--accent-soft);
  border-radius: 10px;
}
.notice + button {
  margin-top: 4px;
}
</style>
