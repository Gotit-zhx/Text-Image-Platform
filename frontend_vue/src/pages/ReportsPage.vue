<script setup lang="ts">
import { onBeforeUnmount, ref, watch } from 'vue'
import { useRoute } from 'vue-router'
import { apiRequest } from '../api/client'
import { getPostApi } from '../api/community'
import type { Post } from '../types'
import type { Paged } from '../api/community'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
const statusLabels: Record<string, string> = {
  approved: '已公开',
  pending: '待复核',
  rejected: '已驳回',
  offline: '已下架'
}
type CaseRecord = {
  id: number
  status: string
  outcome: string
  reason?: string
  description: string
  createdAt: string
  postId?: number
  targetType?: string
  targetId?: number
}
const route = useRoute(),
  kind = ref('reports'),
  items = ref<CaseRecord[]>([]),
  pending = ref(false),
  error = ref(''),
  page = ref(0),
  hasMore = ref(false),
  post = ref<Post>(),
  description = ref(''),
  acting = ref(false),
  message = ref('')
let version=0,controller:AbortController|undefined
const load = async (reset = false) => {
  if(pending.value&&!reset)return
  if(reset){version++;controller?.abort();items.value=[];page.value=0;hasMore.value=false}
  const current=version,category=kind.value,appealPost=route.query.appealPost
  controller=new AbortController()
  pending.value = true
  error.value = ''
  try {
    const result = await apiRequest<Paged<CaseRecord>>(
      `/${category}?page=${reset ? 1 : page.value + 1}`,{signal:controller.signal}
    )
    if(current!==version)return
    items.value = reset ? result.items : [...new Map([...items.value, ...result.items].map(item=>[item.id,item])).values()]
    page.value = result.pagination.page
    hasMore.value = result.pagination.hasMore
    const nextPost=appealPost?await getPostApi(Number(appealPost),true):undefined
    if(current===version)post.value=nextPost
  } catch (e) {
    if(current===version&&!(e instanceof Error&&e.name==='AbortError'))error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    if(current===version)pending.value = false
  }
}
const action = async (resubmit = false) => {
  if (!post.value || acting.value) return
  acting.value = true
  error.value = ''
  const current=version, postId=post.value.id, submittedDescription=description.value
  try {
    if (resubmit) await apiRequest(`/community/posts/${postId}/resubmit`, { method: 'POST' })
    else
      await apiRequest('/appeals', {
        method: 'POST',
        body: JSON.stringify({ postId, description: submittedDescription })
      })
    if(current!==version)return
    message.value = resubmit ? '已提交复核，等待审核结果。' : '申诉已提交。'
    if(description.value===submittedDescription)description.value = ''
    await load(true)
  } catch (e) {
    if(current===version)error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    acting.value = false
  }
}
watch(()=>[kind.value,route.query.appealPost],()=>load(true),{immediate:true})
watch(()=>route.query.appealPost,()=>{description.value='';message.value='';post.value=undefined})
onBeforeUnmount(()=>{version++;controller?.abort()})
</script>
<template>
  <main class="page-container">
    <h1>举报与申诉记录</h1>
    <section v-if="post" class="appeal-panel">
      <h2>{{ post.title }}</h2>
      <p>
        状态：{{ statusLabels[post.moderationStatus || 'approved'] }} · 原因：{{
          post.reviewReason || '暂无'
        }}
      </p>
      <RouterLink :to="`/edit/${post.id}`" class="text-button">修改作品</RouterLink
      ><BaseButton
        :pending="acting"
        :disabled="!['offline', 'rejected'].includes(post.moderationStatus || '')"
        @click="action(true)"
        >提交复核</BaseButton
      >
      <form @submit.prevent="action(false)">
        <label>申诉说明<textarea v-model="description" maxlength="2000" required /></label
        ><BaseButton type="submit" :pending="acting">提交申诉</BaseButton>
      </form>
    </section>
    <p v-if="message" role="status">{{ message }}</p>
    <nav>
      <button :class="{ active: kind === 'reports' }" @click="kind = 'reports'">我的举报</button
      ><button :class="{ active: kind === 'appeals' }" @click="kind = 'appeals'">我的申诉</button>
    </nav>
    <UiState v-if="pending && !items.length" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    /><UiState v-if="!pending && !error && !items.length" kind="empty" />
    <article v-for="item in items" :key="item.id">
      <h2>
        {{ item.reason || '作品申诉' }}
        <small>{{
          item.status === 'open' ? '待处理' : item.status === 'resolved' ? '已处置' : '不予处置'
        }}</small>
      </h2>
      <p>{{ item.description }}</p>
      <p v-if="item.outcome">处理结果：{{ item.outcome }}</p>
      <time>{{ new Date(item.createdAt).toLocaleString() }}</time>
    </article>
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton>
  </main>
</template>
<style scoped>
.page-container {
  max-width: 900px;
}
nav {
  display: flex;
  gap: 16px;
  margin: 24px 0;
}
nav button {
  border: 0;
  background: none;
  min-height: 44px;
}
.active {
  border-bottom: 2px solid var(--accent);
}
article,
.appeal-panel {
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
h2 {
  font-size: 17px;
}
small,
time {
  font-size: 12px;
  color: var(--muted);
}
textarea {
  display: block;
  width: 100%;
  min-height: 100px;
  border: 1px solid var(--border);
  border-radius: 10px;
  margin: 12px 0;
  padding: 10px;
}
</style>
