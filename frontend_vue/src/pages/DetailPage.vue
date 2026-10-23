<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import DOMPurify from 'dompurify'
import type { Post } from '../types'
import { getPostApi, deletePostApi } from '../api/community'
import AppIcon from '../components/ui/AppIcon.vue'
import UserAvatar from '../components/ui/UserAvatar.vue'
import UiState from '../components/ui/UiState.vue'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'
import DiscussionPanel from '../components/detail/DiscussionPanel.vue'
import ReportDialog from '../components/ReportDialog.vue'
import ImageViewer from '../components/detail/ImageViewer.vue'
const props = defineProps<{
  postId: number
  entities: Post[]
  viewerId?: number
  modal?: boolean
}>()
const emit = defineEmits<{
  loaded: [post: Post]
  deleted: [id: number]
  close: []
  login: []
  like: [id: number]
  favorite: [id: number]
  follow: [id: number]
  share: [id: number]
}>()
const route = useRoute(),
  pending = ref(false),
  error = ref(''),
  viewer = ref(false),
  imageIndex = ref(0),
  confirm = ref(false),
  deleting = ref(false),
  reporting = ref(false)
const post = computed(() => props.entities.find((p) => p.id === props.postId)),
  html = computed(() => DOMPurify.sanitize(post.value?.contentHtml || '')),
  images = computed(
    () => [...new Set([...(post.value?.images||[]),...Array.from((post.value?.contentHtml||'').matchAll(/<img[^>]*src=["']([^"']+)["']/gi),match=>match[1]||'')])].filter(src=>/^(https?:|data:image\/|\/media\/)/.test(src))
  )
const mobile = ref(window.innerWidth < 768)
const resize = () => {
  mobile.value = window.innerWidth < 768
}
onMounted(() => window.addEventListener('resize', resize))
let version = 0
const load = async (showLoading = false) => {
  const current = ++version
  if (showLoading) pending.value = true
  error.value = ''
  try {
    const result = await getPostApi(props.postId)
    if (current === version) emit('loaded', result)
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '内容不可用'
  } finally {
    if (current === version) pending.value = false
  }
}
watch(
  () => props.postId,
  () => load(true),
  { immediate: true }
)
let viewerOwner = props.viewerId
watch(
  () => props.viewerId,
  (next) => {
    const changedAccount = next !== undefined && viewerOwner !== undefined && next !== viewerOwner
    if (next !== undefined) viewerOwner = next
    void load(changedAccount)
  }
)
const remove = async () => {
  if (deleting.value) return
  const current = version, postId = props.postId
  deleting.value = true
  try {
    await deletePostApi(postId)
    if (current !== version) return
    confirm.value = false
    emit('deleted', postId)
    emit('close')
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    deleting.value = false
  }
}
const showImage=(index:number)=>{imageIndex.value=index;viewer.value=true}
const openBodyImage=(event:MouseEvent)=>{const target=event.target;if(target instanceof HTMLImageElement){const index=images.value.indexOf(target.getAttribute('src')||'');if(index>=0)showImage(index)}}
const focusId = computed(() => Number(route.query.commentId) || undefined)
onBeforeUnmount(() => {
  version++
  window.removeEventListener('resize', resize)
})
</script>
<template>
  <el-dialog
    v-if="modal"
    :model-value="true"
    :fullscreen="mobile"
    title="作品详情"
    width="min(1200px,94vw)"
    top="4vh"
    append-to-body
    :close-on-press-escape="!viewer"
    :close-on-click-modal="!viewer"
    @close="emit('close')"
    ><div class="detail-inner" :class="{ illustrated: images.length }">
      <UiState v-if="pending" kind="loading" /><UiState
        v-else-if="error"
        kind="unavailable"
        :description="error"
      /><template v-else-if="post"
        ><section v-if="images.length" class="gallery">
          <button
            v-for="(src, i) in images"
            :key="src"
            @click="showImage(i)"
            :aria-label="`查看第${i + 1}张图片`"
          >
            <img :src="src" :alt="`${post.title} 图片 ${i + 1}`" />
          </button>
        </section>
        <section class="article">
          <div class="author-row">
            <RouterLink :to="`/u/${post.authorId}`"
              ><UserAvatar :name="post.author" :src="post.authorAvatarUrl" />{{
                post.author
              }}</RouterLink
            ><button
              class="text-button"
              v-if="viewerId !== post.authorId"
              @click="emit('follow', post.id)"
            >
              {{ post.isFollowingAuthor ? '已关注' : '关注' }}
            </button>
          </div>
          <h1>{{ post.title }}</h1>
          <div class="prose" @click="openBodyImage" v-html="html" />
          <p class="tags">
            <span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span>
          </p>
          <time>{{ new Date(post.createdAt || post.time).toLocaleString() }}</time>
          <div class="interaction">
            <button :aria-label="post.isLiked?'取消点赞作品':'点赞作品'" :aria-pressed="!!post.isLiked" @click="emit('like', post.id)">
              <AppIcon name="heart" />{{ post.likes }}</button
            ><button :aria-pressed="!!post.isFavorited" @click="emit('favorite', post.id)">
              <AppIcon name="bookmark" />{{ post.isFavorited ? '已收藏' : '收藏' }}</button
            ><button @click="emit('share', post.id)"><AppIcon name="share" />分享</button>
          </div>
          <div v-if="viewerId === post.authorId" class="owner-actions">
            <RouterLink :to="`/edit/${post.id}`" class="text-button">编辑</RouterLink
            ><button class="text-button" @click="confirm = true">删除作品</button>
          </div>
          <button class="text-button" @click="reporting = true">举报作品</button
          ><DiscussionPanel
            :post-id="post.id"
            :viewer-id="viewerId"
            :focus-id="focusId"
            @changed="load()"
            @login="emit('login')"
          /></section
      ></template></div
  ></el-dialog>
  <main v-else class="detail-page page-container">
    <button class="text-button" @click="emit('close')"><AppIcon name="back" />返回</button
    ><UiState v-if="pending" kind="loading" /><UiState
      v-else-if="error"
      kind="unavailable"
      :description="error"
    /><template v-else-if="post"
      ><div class="author-row">
        <RouterLink :to="`/u/${post.authorId}`"
          ><UserAvatar :name="post.author" :src="post.authorAvatarUrl" />{{
            post.author
          }}</RouterLink
        ><button
          class="text-button"
          v-if="viewerId !== post.authorId"
          @click="emit('follow', post.id)"
        >
          {{ post.isFollowingAuthor ? '已关注' : '关注' }}
        </button>
      </div>
      <h1>{{ post.title }}</h1>
      <section v-if="images.length" class="page-gallery">
        <button
          v-for="(src, i) in images"
          :key="src"
          @click="showImage(i)"
          :aria-label="`查看第${i + 1}张图片`"
        >
          <img :src="src" :alt="`${post.title} 图片 ${i + 1}`" />
        </button>
      </section>
      <div class="prose" @click="openBodyImage" v-html="html" />
      <p class="tags">
        <span v-for="tag in post.tags" :key="tag" class="tag">#{{ tag }}</span>
      </p>
      <time>{{ new Date(post.createdAt || post.time).toLocaleString() }}</time>
      <div class="interaction">
        <button :aria-label="post.isLiked?'取消点赞作品':'点赞作品'" :aria-pressed="!!post.isLiked" @click="emit('like', post.id)">
          <AppIcon name="heart" />{{ post.likes }}</button
        ><button :aria-pressed="!!post.isFavorited" @click="emit('favorite', post.id)">
          <AppIcon name="bookmark" />{{ post.isFavorited ? '已收藏' : '收藏' }}</button
        ><button @click="emit('share', post.id)"><AppIcon name="share" />分享</button>
      </div>
      <div v-if="viewerId === post.authorId" class="owner-actions">
        <RouterLink :to="`/edit/${post.id}`" class="text-button">编辑</RouterLink
        ><button class="text-button" @click="confirm = true">删除作品</button>
      </div>
      <button class="text-button" @click="reporting = true">举报作品</button
      ><DiscussionPanel
        :post-id="post.id"
        :viewer-id="viewerId"
        :focus-id="focusId"
        @changed="load()"
        @login="emit('login')"
    /></template>
  </main>
  <ReportDialog
    :open="reporting"
    target-type="post"
    :target-id="postId"
    :viewer-id="viewerId"
    @close="reporting = false"
    @login="emit('login')"
  />
  <ImageViewer
    :images="images"
    :start="imageIndex"
    :open="viewer"
    @close="viewer = false"
  /><ConfirmDialog
    :open="confirm"
    title="删除这篇作品？"
    description="作品将从公开入口移除，分享链接将显示不可用。"
    :pending="deleting"
    @cancel="confirm = false"
    @confirm="remove"
  />
</template>
<style scoped>
.detail-page {
  max-width: 800px;
}
.detail-inner {
  max-height: 80vh;
  overflow: auto;
}
.detail-inner.illustrated {
  display: grid;
  grid-template-columns: 1.1fr 1fr;
  gap: 24px;
}
.gallery {
  overflow: auto;
  max-height: 78vh;
  background: var(--bg);
  border-radius: 12px;
}
.gallery button,
.page-gallery button {
  border: 0;
  padding: 0;
  background: var(--bg);
  width: 100%;
  cursor: zoom-in;
}
.gallery img {
  width: 100%;
  display: block;
}
.article {
  min-width: 0;
  overflow: auto;
  max-height: 78vh;
  padding: 0 12px;
}
.author-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.author-row > a {
  display: flex;
  align-items: center;
  gap: 10px;
  font-size: 14px;
  font-weight: 650;
}
.prose {
  font-size: 16px;
  line-height: 1.85;
  overflow-wrap: anywhere;
}
.prose :deep(img) {
  max-width: 100%;
  height: auto;
  cursor: zoom-in;
}
.prose :deep(pre) {
  max-width: 100%;
  overflow: auto;
  background: var(--bg);
  padding: 12px;
}
.prose :deep(a) {
  color: var(--accent-hover);
  text-decoration: underline;
}
.tags {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
time {
  font-size: 12px;
  color: var(--muted);
}
.interaction {
  display: flex;
  gap: 16px;
  margin: 18px 0;
}
.interaction button {
  display: flex;
  align-items: center;
  gap: 6px;
  border: 1px solid var(--border);
  background: var(--surface);
  border-radius: 10px;
  min-height: 44px;
  padding: 6px 12px;
  font-size: 13px;
}
.interaction button[aria-pressed='true'] {
  color: var(--accent-hover);
}
.owner-actions {
  display: flex;
  gap: 12px;
}
.page-gallery {
  display: flex;
  overflow: auto;
  gap: 8px;
  margin: 20px 0;
  scroll-snap-type: x mandatory;
}
.page-gallery button {
  min-width: 100%;
  scroll-snap-align: start;
}
.page-gallery img {
  max-height: 650px;
  object-fit: contain;
  border-radius: 12px;
}
@media (max-width: 767px) {
  .detail-inner.illustrated {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }
  .gallery {
    display: flex;
    overflow: auto;
    max-height: 45vh;
    flex-shrink: 0;
  }
  .gallery button {
    min-width: 100%;
  }
  .gallery img {
    height: 40vh;
    object-fit: contain;
  }
  .article {
    max-height: none;
    overflow: visible;
    padding: 0;
  }
  .detail-inner {
    max-height: 82vh;
  }
  h1 {
    font-size: 22px;
  }
  .interaction {
    gap: 8px;
  }
  .interaction button {
    padding: 6px 10px;
  }
  .detail-page {
    padding: 12px;
  }
  .page-gallery img {
    max-height: 440px;
  }
}
</style>
