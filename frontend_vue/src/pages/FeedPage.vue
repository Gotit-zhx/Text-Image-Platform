<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import type { LocationQuery } from 'vue-router'
import type { Post } from '../types'
import { searchPostsApi, recommendPostsApi } from '../api/community'
import HomePostCard from '../components/home/HomePostCard.vue'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
const props = defineProps<{
  entities: Post[]
  viewerId?: number
  location: { path: string; query: LocationQuery }
}>()
const emit = defineEmits<{
  loaded: [posts: Post[]]
  'go-publish': []
  'open-detail': [id: number]
  'open-comment-detail': [id: number]
  'toggle-post-like': [id: number]
  'toggle-post-favorite': [id: number]
  'share-post': [id: number]
  'toggle-post-follow': [id: number]
  'open-author-profile': [payload: { userId?: number; userName: string; avatarText: string }]
}>()
const route = computed(() => props.location),
  ids = ref<number[]>([]),
  page = ref(0),
  hasMore = ref(false),
  pending = ref(false),
  error = ref('')
const following = computed(() => route.value.path === '/following')
const keyword = computed(() => String(route.value.query.q || ''))
const nav = computed(() => (following.value ? '关注' : String(route.value.query.nav || '推荐')))
const posts = computed(() =>
  ids.value
    .map((id) => props.entities.find((post) => post.id === id))
    .filter((p): p is Post => !!p && (p.moderationStatus || 'approved') === 'approved')
)
let controller: AbortController | undefined,
  version = 0
const load = async (reset = false) => {
  if (pending.value && !reset) return
  if (reset) {
    controller?.abort()
    ids.value = []
    page.value = 0
    hasMore.value = false
    version++
  }
  const current = version
  controller = new AbortController()
  pending.value = true
  error.value = ''
  try {
    const options = { page: page.value + 1, pageSize: 12, signal: controller.signal }
    const result =
      nav.value === '推荐' && !keyword.value
        ? await recommendPostsApi(12, options)
        : await searchPostsApi(keyword.value, nav.value, options)
    if (current !== version) return
    emit('loaded', result.posts)
    ids.value = [...new Set([...ids.value, ...result.posts.map((p) => p.id)])]
    page.value = result.pagination.page
    hasMore.value = result.pagination.hasMore
  } catch (e) {
    if (current === version && !(e instanceof Error && e.name === 'AbortError'))
      error.value = e instanceof Error ? e.message : '加载失败'
  } finally {
    if (current === version) pending.value = false
  }
}
watch(
  () =>
    JSON.stringify([route.value.path, route.value.query.nav, route.value.query.q, props.viewerId]),
  () => load(true),
  { immediate: true }
)
onBeforeUnmount(() => {
  version++
  controller?.abort()
})
</script>
<template>
  <main class="page-container" :class="{ following }">
    <header class="feed-heading">
      <div>
        <p class="eyebrow">{{ following ? '与你关心的人，保持连接' : '生活的灵感，在这里生长' }}</p>
        <h1>{{ keyword ? `搜索：${keyword}` : following ? '关注动态' : '发现' }}</h1>
      </div>
      <BaseButton v-if="!following" @click="load(true)">刷新</BaseButton>
    </header>
    <nav v-if="!following && !keyword" class="feed-tabs" aria-label="发现排序">
      <RouterLink
        v-for="tab in ['推荐', '热门', '更新']"
        :key="tab"
        :to="{ path: '/', query: { nav: tab } }"
        :class="{ active: nav === tab }"
        >{{ tab === '更新' ? '最新' : tab }}</RouterLink
      >
    </nav>
    <UiState
      v-if="following && !viewerId"
      kind="forbidden"
      title="登录后查看关注动态"
      description="关注喜欢的作者，新的分享会出现在这里。"
    />
    <template v-else>
      <UiState v-if="pending && !posts.length" kind="loading" />
      <UiState
        v-else-if="!posts.length && !error"
        kind="empty"
        :title="
          keyword ? '没有找到相关内容' : following ? '还没有关注动态' : '第一篇分享，等待你来书写'
        "
        :description="
          following ? '去发现页寻找感兴趣的作者。' : '记录生活、分享见闻，让灵感在百草园相遇。'
        "
        ><RouterLink v-if="following" to="/" class="text-button">去发现</RouterLink
        ><BaseButton v-else @click="emit('go-publish')">发布图文</BaseButton></UiState
      >
      <div class="feed-grid" :class="{ timeline: following }">
        <HomePostCard
          v-for="post in posts"
          :key="post.id"
          :post="post"
          :timeline="following"
          @open-detail="emit('open-detail', $event)"
          @open-comment-detail="emit('open-comment-detail', $event)"
          @toggle-post-like="emit('toggle-post-like', $event)"
          @toggle-post-favorite="emit('toggle-post-favorite', $event)"
          @share-post="emit('share-post', $event)"
          @toggle-post-follow="emit('toggle-post-follow', $event)"
          @open-author-profile="emit('open-author-profile', $event)"
        />
      </div>
      <UiState v-if="error" kind="error" :description="error" @retry="load(page === 0)" />
      <div v-if="hasMore" class="load-more">
        <BaseButton :pending="pending" @click="load()">{{
          pending ? '正在加载…' : '加载更多'
        }}</BaseButton>
      </div>
    </template>
  </main>
</template>
<style scoped>
.feed-heading {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.eyebrow {
  font-size: 12px;
  letter-spacing: 1px;
  color: var(--muted);
  margin: 0 0 8px;
}
h1 {
  margin: 0;
}
.feed-tabs {
  display: flex;
  gap: 24px;
  margin: 0 0 24px;
}
.feed-tabs a {
  min-height: 40px;
  display: flex;
  align-items: center;
  padding: 4px 4px 8px;
  border-bottom: 2px solid transparent;
  color: var(--muted);
  font-size: 15px;
}
.feed-tabs .active {
  color: var(--text);
  border-color: var(--accent);
  font-weight: 650;
}
.feed-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px 18px;
}
.feed-grid.timeline {
  display: flex;
  flex-direction: column;
  gap: 0;
}
.following {
  max-width: 800px;
}
.load-more {
  display: flex;
  justify-content: center;
  margin: 32px 0;
}
@media (max-width: 767px) {
  .feed-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px 10px;
  }
  .feed-tabs {
    gap: 24px;
    margin-bottom: 16px;
  }
  .eyebrow {
    font-size: 11px;
  }
  .feed-heading {
    margin-bottom: 12px;
  }
}
@media (max-width: 359px) {
  .feed-grid {
    grid-template-columns: 1fr;
  }
}
</style>
