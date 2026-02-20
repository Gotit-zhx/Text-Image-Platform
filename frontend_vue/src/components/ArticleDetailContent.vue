<script setup lang="ts">
import type { Post } from '../types'
import ArticleMainCard from './detail/ArticleMainCard.vue'
import CommentSection from './detail/CommentSection.vue'
import DetailSidePanel from './detail/DetailSidePanel.vue'

defineProps<{
	post: Post | null
	currentUserName?: string
}>()
</script>

<template>
	<main class="detail-layout">
		<section class="detail-main">
			<template v-if="post">
				<ArticleMainCard :post="post" />
				<CommentSection :current-user-name="currentUserName" />
			</template>

			<div v-else class="empty">帖子不存在</div>
		</section>

		<DetailSidePanel />
	</main>
</template>

<style scoped>
.detail-layout {
	max-width: 1180px;
	margin: 20px auto;
	padding: 0 16px;
	display: grid;
	grid-template-columns: 1fr 280px;
	gap: 16px;
}

.empty {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 24px;
	color: #8c94a7;
}

@media (max-width: 1024px) {
	.detail-layout {
		grid-template-columns: 1fr;
	}
}
</style>
