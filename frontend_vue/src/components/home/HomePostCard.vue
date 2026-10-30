<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import type { Post } from '../../types'
import AppIcon from '../ui/AppIcon.vue'
import UserAvatar from '../ui/UserAvatar.vue'
import { formatCount, formatPostTime } from '../../utils/postUi'
const props = defineProps<{ post: Post; timeline?: boolean }>()
const failed = ref(false)
const images = computed(() =>
  props.post.images.filter((image) => /^(https?:|data:image\/|\/media\/)/.test(image))
)
watch(
  () => props.post.images,
  () => {
    failed.value = false
  }
)
const emit = defineEmits<{
  'open-detail': [id: number]
  'open-comment-detail': [id: number]
  'toggle-post-like': [id: number]
  'toggle-post-favorite': [id: number]
  'share-post': [id: number]
  'toggle-post-follow': [id: number]
  'open-author-profile': [payload: { userId?: number; userName: string; avatarText: string }]
}>()
const author = () =>
  emit('open-author-profile', {
    userId: props.post.authorId,
    userName: props.post.author,
    avatarText: props.post.author.slice(0, 1)
  })
</script>
<template>
  <article class="post-card" :class="{ timeline, textual: !images.length }">
    <div v-if="timeline" class="timeline-author">
      <button class="author" @click="author">
        <UserAvatar :src="post.authorAvatarUrl" :name="post.author" /><span>{{
          post.author
        }}</span></button
      ><time :datetime="post.createdAt || post.time" :title="post.createdAt || post.time">{{
        formatPostTime(post.createdAt || post.time)
      }}</time
      ><button class="text-button" @click="emit('toggle-post-follow', post.id)">
        {{ post.isFollowingAuthor ? '已关注' : '关注' }}
      </button>
    </div>
    <a
      :href="`/detail/${post.id}`"
      class="content-link"
      @click.prevent="emit('open-detail', post.id)"
    >
      <div v-if="images.length" class="cover" :class="{ gallery: timeline && images.length > 1 }">
        <template v-if="!failed"
          ><img
            v-for="(src, i) in images.slice(0, timeline ? 3 : 1)"
            :key="src"
            :src="src"
            :alt="`${post.title} 图片 ${i + 1}`"
            loading="lazy"
            width="440"
            height="550"
            @error="failed = true" /></template
        ><span v-else class="image-error">图片加载失败 · 打开正文</span
        ><span v-if="images.length > 1 && !timeline" class="image-count"
          >{{ images.length }} 图</span
        >
      </div>
      <div class="card-copy">
        <span v-if="!images.length" class="text-note">文字札记</span>
        <h2>{{ post.title }}</h2>
        <p v-if="timeline || !images.length" class="summary">{{ post.summary }}</p>
      </div>
    </a>
    <footer>
      <button v-if="!timeline" class="author" @click="author">
        <UserAvatar :src="post.authorAvatarUrl" :name="post.author" :size="24" /><span>{{
          post.author
        }}</span></button
      ><button
        class="like"
        :class="{ selected: post.isLiked }"
        :aria-label="`${post.isLiked ? '取消点赞' : '点赞'} ${post.title}`"
        :aria-pressed="!!post.isLiked"
        @click="emit('toggle-post-like', post.id)"
      >
        <AppIcon name="heart" :size="18" /><span>{{ formatCount(post.likes) }}</span></button
      ><template v-if="timeline"
        ><button class="like" aria-label="评论" @click="emit('open-comment-detail', post.id)">
          <AppIcon name="comment" :size="18" />{{ post.comments }}</button
        ><button
          class="like"
          :class="{ selected: post.isFavorited }"
          :aria-label="post.isFavorited ? '取消收藏' : '收藏'"
          @click="emit('toggle-post-favorite', post.id)"
        >
          <AppIcon name="bookmark" :size="18" /></button
        ><button class="like" aria-label="分享" @click="emit('share-post', post.id)">
          <AppIcon name="share" :size="18" /></button
      ></template>
    </footer>
  </article>
</template>
<style scoped>
.post-card {
  min-width: 0;
  background: var(--surface);
  border: 1px solid var(--border);
  border-radius: var(--radius);
  overflow: hidden;
  align-self: start;
  transition: border-color var(--duration);
}
.post-card:hover {
  border-color: var(--border-hover);
}
.content-link {
  display: block;
}
.cover {
  position: relative;
  aspect-ratio: 4/5;
  background: var(--media-placeholder);
  overflow: hidden;
}
.cover img {
  width: 100%;
  height: 100%;
  object-fit: cover;
  display: block;
}
.image-error {
  height: 100%;
  display: grid;
  place-items: center;
  color: var(--muted);
  font-size: 12px;
}
.image-count {
  position: absolute;
  top: 10px;
  right: 10px;
  background: #24242499;
  color: white;
  border-radius: 999px;
  padding: 2px 8px;
  font-size: 11px;
}
.card-copy {
  padding: 12px 14px 0;
}
.card-copy h2 {
  font-size: 16px;
  font-weight: 650;
  line-height: 1.5;
  margin: 0;
  display: -webkit-box;
  -webkit-line-clamp: 2;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.summary {
  margin: 12px 0 4px;
  color: var(--muted);
  font-size: 14px;
  display: -webkit-box;
  -webkit-line-clamp: 6;
  -webkit-box-orient: vertical;
  overflow: hidden;
}
.textual .card-copy {
  min-height: 260px;
  padding: 24px 18px 12px;
}
.textual .card-copy h2 {
  font-size: 20px;
  -webkit-line-clamp: 3;
}
.text-note {
  display: block;
  font-size: 11px;
  letter-spacing: 2px;
  color: var(--muted);
  margin-bottom: 24px;
}
footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 4px;
  padding: 6px 10px 8px;
}
.author,
.like {
  display: flex;
  gap: 6px;
  align-items: center;
  border: 0;
  background: none;
  min-height: 44px;
  min-width: 36px;
  padding: 4px;
  color: var(--muted);
  font-size: 12px;
}
.author {
  min-width: 0;
  max-width: 75%;
}
.author > span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.like {
  flex-shrink: 0;
}
.selected {
  color: var(--accent-hover);
}
.selected svg {
  fill: var(--accent-soft);
}
.timeline {
  padding: 20px;
  border-radius: 0;
  border-width: 0 0 1px;
  background: transparent;
}
.timeline-author {
  display: flex;
  align-items: center;
  gap: 10px;
}
.timeline-author .author {
  max-width: 60%;
  flex-shrink: 1;
  font-size: 14px;
  font-weight: 650;
  color: var(--text);
}
.timeline-author > .text-button {
  white-space: nowrap;
  flex-shrink: 0;
}
time {
  white-space: nowrap;
  flex-shrink: 0;
  font-size: 12px;
  color: var(--muted);
  margin-right: auto;
}
.timeline .content-link {
  display: flex;
  flex-direction: column-reverse;
}
.timeline .card-copy,
.timeline.textual .card-copy {
  min-height: 0;
  padding: 12px 0;
}
.timeline .card-copy h2 {
  font-size: 19px;
}
.timeline .text-note {
  display: none;
}
.timeline .cover {
  max-height: 440px;
  aspect-ratio: 4/3;
  border-radius: 10px;
}
.timeline .cover.gallery {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 4px;
  aspect-ratio: 2/1;
}
.timeline footer {
  justify-content: flex-start;
  gap: 24px;
  padding: 12px 0 0;
}
@media (max-width: 767px) {
  .card-copy {
    padding: 10px 10px 0;
  }
  .card-copy h2 {
    font-size: 14px;
  }
  .textual .card-copy {
    padding: 18px 12px 6px;
    min-height: 220px;
  }
  .textual .card-copy h2 {
    font-size: 17px;
  }
  .summary {
    font-size: 13px;
  }
  footer {
    padding: 4px 6px;
  }
  .timeline {
    padding: 16px 4px;
  }
  .timeline footer {
    gap: 24px;
  }
  .author {
    max-width: 70%;
  }
  .author > span:last-child {
    max-width: 84px;
  }
}
</style>
