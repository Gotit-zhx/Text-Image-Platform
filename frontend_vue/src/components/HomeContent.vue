<script setup lang="ts">
import type { Post } from '../types'
import HomePostCard from './home/HomePostCard.vue'
import HomeCreatorPanel from './home/HomeCreatorPanel.vue'

defineProps<{
	posts: Post[]
	quickActions: string[]
	searchKeyword?: string
}>()

const emit = defineEmits<{
	(e: 'go-publish'): void
	(e: 'open-detail', postId: number): void
	(e: 'open-comment-detail', postId: number): void
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'toggle-post-follow', postId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()
</script>

<template>
	<main class="layout">
		<section class="feed">
			<template v-if="posts.length">
				<HomePostCard
					v-for="post in posts"
					:key="post.id"
					:post="post"
					@open-detail="emit('open-detail', $event)"
					@open-comment-detail="emit('open-comment-detail', $event)"
					@toggle-post-like="emit('toggle-post-like', $event)"
					@toggle-post-favorite="emit('toggle-post-favorite', $event)"
					@toggle-post-follow="emit('toggle-post-follow', $event)"
					@open-author-profile="emit('open-author-profile', $event)"
				/>
			</template>
			<div v-else class="search-empty">
				<p>未找到相关内容{{ searchKeyword ? `：${searchKeyword}` : '' }}</p>
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

.search-empty {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 36px 20px;
	text-align: center;
	color: #9aa3b6;
}

@media (max-width: 1024px) {
	.layout {
		grid-template-columns: 1fr;
	}
}
</style>
