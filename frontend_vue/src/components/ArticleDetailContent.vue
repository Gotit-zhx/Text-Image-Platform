<script setup lang="ts">
import { nextTick, ref, watch } from 'vue'
import type { CommentRecord, Post } from '../types'
import ArticleMainCard from './detail/ArticleMainCard.vue'
import CommentSection from './detail/CommentSection.vue'
import DetailSidePanel from './detail/DetailSidePanel.vue'

const props = defineProps<{
	post: Post | null
	currentUserName?: string
	focusCommentToken?: number
	comments: CommentRecord[]
}>()

const emit = defineEmits<{
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'toggle-post-follow', postId: number): void
	(e: 'submit-comment', postId: number, content: string): void
	(e: 'toggle-comment-like', commentId: number): void
	(e: 'delete-comment', commentId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()

type CommentSectionExpose = {
	focusCommentEditor: () => void
}

const commentSectionRef = ref<CommentSectionExpose | null>(null)

const focusCommentInput = () => {
	nextTick(() => {
		commentSectionRef.value?.focusCommentEditor()
	})
}

watch(
	() => props.focusCommentToken,
	(newValue, oldValue) => {
		if (newValue !== oldValue && props.post) {
			focusCommentInput()
		}
	}
)
</script>

<template>
	<main class="detail-layout">
		<section class="detail-main">
			<template v-if="post">
				<ArticleMainCard :post="post" @open-author-profile="emit('open-author-profile', $event)" />
				<CommentSection
					ref="commentSectionRef"
					:current-user-name="currentUserName"
					:comments="comments"
					@submit-comment="emit('submit-comment', post.id, $event)"
					@toggle-comment-like="emit('toggle-comment-like', $event)"
					@delete-comment="emit('delete-comment', $event)"
					@open-author-profile="emit('open-author-profile', $event)"
				/>
			</template>

			<div v-else class="empty">帖子不存在</div>
		</section>

		<DetailSidePanel
			:is-liked="post?.isLiked"
			:like-count="post?.likes ?? 0"
			:is-favorited="post?.isFavorited"
			:is-following-author="post?.isFollowingAuthor"
			@comment-click="focusCommentInput"
			@toggle-like="post && emit('toggle-post-like', post.id)"
			@toggle-favorite="post && emit('toggle-post-favorite', post.id)"
			@toggle-follow="post && emit('toggle-post-follow', post.id)"
		/>
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
