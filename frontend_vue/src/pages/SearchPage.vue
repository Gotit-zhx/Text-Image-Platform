<script setup lang="ts">
import { computed, onBeforeUnmount, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { apiRequest } from '../api/client'
import type { Paged, PagedPostsResult } from '../api/community'
import type { Post, LoginUser } from '../types'
import HomePostCard from '../components/home/HomePostCard.vue'
import UserAvatar from '../components/ui/UserAvatar.vue'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
const props = defineProps<{
  entities: Post[]
  viewerId?: number
  location: { path: string; query: Record<string, unknown> }
}>()
const emit = defineEmits<{
  loaded: [posts: Post[]]
  open: [id: number]
  like: [id: number]
  favorite: [id: number]
  follow: [id: number]
  share: [id: number]
}>()
const router = useRouter(),
  ids = ref<number[]>([]),
  people = ref<LoginUser[]>([]),
  page = ref(0),
  hasMore = ref(false),
  pending = ref(false),
  error = ref(''),
  tagInput = ref('')
const keyword = computed(() => String(props.location.query.q || '')),
  type = computed(() => String(props.location.query.type || 'posts')),
  tag = computed(() => String(props.location.query.tag || ''))
const posts = computed(() =>
  ids.value.map((id) => props.entities.find((p) => p.id === id)).filter((p): p is Post => !!p)
)
let version = 0,
  controller: AbortController | undefined
const load = async (reset = false) => {
  if (pending.value && !reset) return
  if (reset) {
    version++
    controller?.abort()
    ids.value = []
    people.value = []
    page.value = 0
  }
  const current = version
  controller = new AbortController()
  pending.value = true
  error.value = ''
  try {
    const query = new URLSearchParams({
      q: keyword.value,
      type: type.value,
      tag: tag.value,
      page: String(page.value + 1)
    })
    const result = await apiRequest<Paged<LoginUser> | PagedPostsResult>(
      `/community/search?${query}`,
      { signal: controller.signal }
    )
    if (current !== version) return
    if ('posts' in result) {
      emit('loaded', result.posts)
      ids.value = [...new Set([...ids.value, ...result.posts.map((p) => p.id)])]
    } else
      people.value = [...new Map([...people.value, ...result.items].map((u) => [u.id, u])).values()]
    page.value = result.pagination.page
    hasMore.value = result.pagination.hasMore
  } catch (e) {
    if (current === version && !(e instanceof Error && e.name === 'AbortError'))
      error.value = e instanceof Error ? e.message : '搜索失败'
  } finally {
    if (current === version) pending.value = false
  }
}
const filter = () =>
  router.push({
    path: '/search',
    query: { ...props.location.query, tag: tagInput.value.trim() || undefined } as Record<
      string,
      string
    >
  })
watch(
  () => JSON.stringify([keyword.value, type.value, tag.value, props.viewerId]),
  () => {
    tagInput.value = tag.value
    load(true)
  },
  { immediate: true }
)
onBeforeUnmount(() => {
  version++
  controller?.abort()
})
</script>
<template>
  <main class="page-container">
    <header>
      <h1>{{ keyword ? `“${keyword}” 的搜索结果` : '搜索百草园' }}</h1>
      <RouterLink to="/search?type=posts" class="text-button">清空筛选</RouterLink>
    </header>
    <nav aria-label="搜索类型">
      <RouterLink
        v-for="kind in ['posts', 'users']"
        :key="kind"
        :to="{ path: '/search', query: { q: keyword, type: kind, tag: tag || undefined } }"
        :class="{ active: type === kind }"
        >{{ kind === 'posts' ? '作品' : '用户' }}</RouterLink
      >
    </nav>
    <form v-if="type === 'posts'" @submit.prevent="filter">
      <input v-model="tagInput" aria-label="标签筛选" placeholder="按标签筛选" /><BaseButton
        type="submit"
        >筛选</BaseButton
      >
    </form>
    <UiState v-if="pending && !page" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    /><UiState
      v-if="!pending && !error && !posts.length && !people.length"
      kind="empty"
      title="没有找到相关结果"
      description="试试其他关键词或清空标签筛选。"
    />
    <div v-if="type === 'posts'" class="search-grid">
      <HomePostCard
        v-for="post in posts"
        :key="post.id"
        :post="post"
        @open-detail="emit('open', $event)"
        @toggle-post-like="emit('like', $event)"
        @toggle-post-favorite="emit('favorite', $event)"
        @toggle-post-follow="emit('follow', $event)"
        @share-post="emit('share', $event)"
        @open-author-profile="$event.userId && router.push(`/u/${$event.userId}`)"
      />
    </div>
    <article v-for="person in people" :key="person.id" class="person">
      <RouterLink :to="`/u/${person.id}`"
        ><UserAvatar :name="person.name" :src="person.avatarUrl" /><span>{{
          person.name
        }}</span></RouterLink
      ><span>{{ person.fans }} 粉丝</span>
    </article>
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton>
  </main>
</template>
<style scoped>
header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
nav {
  display: flex;
  gap: 24px;
  margin: 16px 0;
}
nav a {
  min-height: 44px;
  padding: 6px 2px;
  border-bottom: 2px solid transparent;
}
.active {
  border-color: var(--accent);
}
form {
  display: flex;
  gap: 8px;
  margin: 16px 0 24px;
}
form input {
  min-width: 0;
  padding: 10px 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: white;
}
.search-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 24px 18px;
}
.person,
.person a {
  display: flex;
  align-items: center;
  gap: 12px;
}
.person {
  justify-content: space-between;
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
.person > span {
  font-size: 12px;
  color: var(--muted);
}
@media (max-width: 767px) {
  .search-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px 10px;
  }
  header {
    align-items: flex-start;
  }
  header h1 {
    font-size: 20px;
  }
}
</style>
