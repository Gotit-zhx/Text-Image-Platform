<script setup lang="ts">
import { onBeforeUnmount, onMounted, ref, watch } from 'vue'
import type { Post } from '../types'
import HomePostCard from './home/HomePostCard.vue'
import HomeCreatorPanel from './home/HomeCreatorPanel.vue'

const props = defineProps<{
	posts: Post[]
	quickActions: string[]
	searchKeyword?: string
	isSearching?: boolean
	searchError?: string
	hasMore?: boolean
	isLoadingMore?: boolean
}>()

const emit = defineEmits<{
	(e: 'go-publish'): void
	(e: 'open-detail', postId: number): void
	(e: 'open-comment-detail', postId: number): void
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'share-post', postId: number): void
	(e: 'toggle-post-follow', postId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
	(e: 'load-more'): void
}>()

const loadMoreAnchorRef = ref<HTMLElement | null>(null)
let loadMoreObserver: IntersectionObserver | null = null

const tryLoadMore = () => {
	if (!props.hasMore || props.isLoadingMore) return
	emit('load-more')
}

onMounted(() => {
	if (!window.IntersectionObserver) return

	loadMoreObserver = new IntersectionObserver(
		(entries) => {
			if (entries.some((entry) => entry.isIntersecting)) {
				tryLoadMore()
			}
		},
		{ root: null, rootMargin: '240px 0px', threshold: 0.01 }
	)

	if (loadMoreAnchorRef.value) {
		loadMoreObserver.observe(loadMoreAnchorRef.value)
	}
})

onBeforeUnmount(() => {
	if (loadMoreObserver) {
		loadMoreObserver.disconnect()
		loadMoreObserver = null
	}
})

watch(loadMoreAnchorRef, (el, oldEl) => {
	if (!loadMoreObserver) return
	if (oldEl) loadMoreObserver.unobserve(oldEl)
	if (el) loadMoreObserver.observe(el)
})
</script>

<template>
	<main class="layout">
		<section class="feed">
			<div class="feed-hero">
				<div class="hero-title">社区动态</div>
				<div class="hero-desc">
					<template v-if="searchKeyword">当前搜索：{{ searchKeyword }}</template>
					<template v-else>发现最新内容与高质量讨论</template>
				</div>
				<div class="hero-meta">当前展示 {{ posts.length }} 条内容</div>
			</div>

			<div v-if="isSearching" class="search-tip">搜索中...</div>
			<div v-else-if="searchError" class="search-tip warning">{{ searchError }}</div>
			<template v-if="posts.length">
				<HomePostCard
					v-for="post in posts"
					:key="post.id"
					:post="post"
					@open-detail="emit('open-detail', $event)"
					@open-comment-detail="emit('open-comment-detail', $event)"
					@toggle-post-like="emit('toggle-post-like', $event)"
					@toggle-post-favorite="emit('toggle-post-favorite', $event)"
					@share-post="emit('share-post', $event)"
					@toggle-post-follow="emit('toggle-post-follow', $event)"
					@open-author-profile="emit('open-author-profile', $event)"
				/>
			</template>
			<div v-else class="search-empty">
				<p>未找到相关内容{{ searchKeyword ? `：${searchKeyword}` : '' }}</p>
			</div>

			<div v-if="hasMore || isLoadingMore" ref="loadMoreAnchorRef" class="load-more-zone">
				<span v-if="isLoadingMore">正在加载更多内容...</span>
				<button v-else-if="hasMore" class="load-more-button" @click="tryLoadMore">加载更多</button>
			</div>
		</section>

		<HomeCreatorPanel :quick-actions="quickActions" @go-publish="emit('go-publish')" />
	</main>
</template>

<style scoped>
.layout {
	max-width: 1180px;
	margin: 20px auto;
	padding: 0 16px;
	display: grid;
	grid-template-columns: 1fr 280px;
	gap: 16px;
}

.feed {
	display: flex;
	flex-direction: column;
	gap: 14px;
}

.feed-hero {
	background: linear-gradient(120deg, #f6f9ff 0%, #f1f8ff 100%);
	border: 1px solid #e4ebff;
	border-radius: 12px;
	padding: 14px 16px;
}

.hero-title {
	font-size: 17px;
	font-weight: 700;
	color: #223055;
}

.hero-desc {
	margin-top: 4px;
	font-size: 13px;
	color: #5d6c8f;
}

.hero-meta {
	margin-top: 8px;
	font-size: 12px;
	color: #7a86a2;
}

.search-empty {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 44px 20px;
	text-align: center;
	color: #9aa3b6;
}

.search-tip {
	background: linear-gradient(120deg, #eef3ff 0%, #f5f8ff 100%);
	border: 1px solid #d9e4ff;
	color: #3f5aa8;
	border-radius: 10px;
	padding: 10px 12px;
	font-size: 13px;
}

.search-tip.warning {
	background: #fff7ec;
	border-color: #ffe0b8;
	color: #a46a21;
}

.load-more-zone {
	display: flex;
	justify-content: center;
	align-items: center;
	min-height: 42px;
	color: #7c8599;
	font-size: 13px;
}

.load-more-button {
	border: 1px solid #d8e2f8;
	background: #f7faff;
	color: #3f5aa8;
	border-radius: 999px;
	padding: 6px 14px;
	font-size: 13px;
	cursor: pointer;
}

.load-more-button:hover {
	background: #eef4ff;
}

@media (max-width: 1024px) {
	.layout {
		grid-template-columns: 1fr;
	}
}
</style>
