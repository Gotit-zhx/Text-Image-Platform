<script setup lang="ts">
import { computed, nextTick, ref } from 'vue'
import type { CommentRecord } from '../../types'

const props = defineProps<{
	currentUserName?: string
	comments: CommentRecord[]
}>()

const emit = defineEmits<{
	(e: 'submit-comment', content: string): void
	(e: 'toggle-comment-like', commentId: number): void
	(e: 'delete-comment', commentId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()

const commentInput = ref('')
const sortOption = ref<'hot' | 'latest' | 'earliest'>('hot')
const editorCardRef = ref<HTMLElement | null>(null)
const textareaRef = ref<HTMLTextAreaElement | null>(null)

const sortedComments = computed(() => {
	const list = [...props.comments]
	if (sortOption.value === 'hot') {
		return list.sort((a, b) => b.likes - a.likes)
	}
	if (sortOption.value === 'latest') {
		return list.sort((a, b) => (a.date < b.date ? 1 : -1))
	}
	return list.sort((a, b) => (a.date > b.date ? 1 : -1))
})

const handleSubmitComment = () => {
	const value = commentInput.value.trim()
	if (!value) return

	emit('submit-comment', value)

	commentInput.value = ''
}

const focusCommentEditor = () => {
	editorCardRef.value?.scrollIntoView({ behavior: 'smooth', block: 'center' })
	nextTick(() => {
		textareaRef.value?.focus()
	})
}

defineExpose({
	focusCommentEditor
})
</script>

<template>
	<div class="comment-section">
		<section ref="editorCardRef" class="comment-editor-card">
			<p class="editor-tip">看帖是喜欢，评论才是真爱：</p>
			<div class="editor-box">
				<textarea
					ref="textareaRef"
					v-model="commentInput"
					maxlength="1000"
					placeholder="善语结缘，温暖常伴..."
				/>
			</div>
			<div class="editor-actions">
				<button class="comment-btn" :disabled="!commentInput.trim()" @click="handleSubmitComment">评论</button>
			</div>
		</section>

		<section class="comment-list-card">
			<div class="comment-head">
				<div class="tabs">
					<span class="active">全部评论</span>
				</div>
				<div class="sort-wrap">
					<span>排序：</span>
					<select v-model="sortOption" class="sort-select">
						<option value="hot">热门</option>
						<option value="latest">最新</option>
						<option value="earliest">最早</option>
					</select>
				</div>
			</div>

			<article v-for="item in sortedComments" :key="item.id" class="comment-item">
				<div
					class="avatar"
					@click="emit('open-author-profile', { userId: item.authorId, userName: item.author, avatarText: item.author.slice(0, 1) })"
				></div>
				<div class="comment-body">
					<div class="comment-user-row">
						<span
							class="name"
							@click="emit('open-author-profile', { userId: item.authorId, userName: item.author, avatarText: item.author.slice(0, 1) })"
						>
							{{ item.author }}
						</span>
					</div>
					<p class="comment-content">{{ item.content }}</p>
					<div class="comment-bottom">
						<span class="date">{{ item.date }}</span>
						<span>回复</span>
						<button
							type="button"
							class="comment-like-btn"
							:class="{ liked: item.isLiked }"
							@click="emit('toggle-comment-like', item.id)"
						>
							👍 {{ item.likes }}
						</button>
						<button
							v-if="item.isMine"
							type="button"
							class="comment-delete-btn"
							@click="emit('delete-comment', item.id)"
						>
							删除
						</button>
					</div>
				</div>
			</article>
		</section>
	</div>
</template>

<style scoped>
.comment-editor-card,
.comment-list-card {
	margin-top: 12px;
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 16px 18px;
}

.editor-tip {
	margin: 0 0 10px;
	color: #adb4c0;
	font-size: 14px;
}

.editor-box {
	position: relative;
	border: 1px solid #e3e7ef;
	border-radius: 8px;
	padding: 10px;
}

.editor-box textarea {
	width: 100%;
	min-height: 86px;
	resize: vertical;
	border: none;
	outline: none;
	font-size: 14px;
	font-family: inherit;
}

.editor-actions {
	margin-top: 10px;
	display: flex;
	justify-content: flex-end;
	align-items: center;
}

.comment-btn {
	width: 94px;
	height: 36px;
	border: none;
	border-radius: 6px;
	background: linear-gradient(180deg, #2dc7ff, #0fb0f6);
	color: #fff;
	font-weight: 600;
	cursor: pointer;
}

.comment-btn:disabled {
	opacity: 0.45;
	cursor: not-allowed;
}

.comment-head {
	display: flex;
	justify-content: space-between;
	align-items: center;
	margin-bottom: 14px;
}

.tabs {
	display: flex;
	gap: 18px;
	font-size: 16px;
	font-weight: 600;
	color: #3f4658;
}

.tabs .active {
	color: #1cb0ff;
	padding-bottom: 10px;
	border-bottom: 2px solid #1cb0ff;
}

.sort-wrap {
	display: flex;
	align-items: center;
	gap: 6px;
	font-size: 15px;
	color: #868ea1;
}

.sort-select {
	border: none;
	background: transparent;
	font-size: 15px;
	color: #4b5368;
	outline: none;
	cursor: pointer;
}

.comment-item {
	display: flex;
	gap: 12px;
	padding-top: 12px;
}

.comment-item + .comment-item {
	margin-top: 18px;
	padding-top: 22px;
	border-top: 2px solid #dfe5ef;
}

.avatar {
	width: 48px;
	height: 48px;
	border-radius: 50%;
	background: linear-gradient(145deg, #ff9ec6, #a0d0ff);
	flex-shrink: 0;
}

.comment-body {
	flex: 1;
}

.comment-user-row {
	display: flex;
	gap: 8px;
	align-items: center;
}

.name {
	font-size: 18px;
	color: #4a5368;
	font-weight: 600;
}

.comment-content {
	margin: 12px 0;
	font-size: 17px;
	color: #464f62;
}

.comment-bottom {
	display: flex;
	gap: 16px;
	font-size: 14px;
	color: #a8afbd;
}

.comment-like-btn {
	border: none;
	background: transparent;
	padding: 0;
	font: inherit;
	color: inherit;
	cursor: pointer;
}

.comment-like-btn.liked {
	color: #ff7a59;
	font-weight: 600;
}

.comment-delete-btn {
	border: none;
	background: transparent;
	padding: 0;
	font: inherit;
	color: #8f97a8;
	cursor: pointer;
}

.comment-delete-btn:hover {
	color: #f56c6c;
}
</style>
