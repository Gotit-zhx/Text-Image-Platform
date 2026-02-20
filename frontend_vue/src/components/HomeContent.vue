<script setup lang="ts">
import type { Post } from '../types'
import HomePostCard from './home/HomePostCard.vue'
import HomeCreatorPanel from './home/HomeCreatorPanel.vue'

defineProps<{
	posts: Post[]
	quickActions: string[]
}>()

const emit = defineEmits<{
	(e: 'go-publish'): void
	(e: 'open-detail', postId: number): void
}>()
</script>

<template>
	<main class="layout">
		<section class="feed">
			<HomePostCard
				v-for="post in posts"
				:key="post.id"
				:post="post"
				@open-detail="emit('open-detail', $event)"
			/>
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

@media (max-width: 1024px) {
	.layout {
		grid-template-columns: 1fr;
	}
}
</style>
