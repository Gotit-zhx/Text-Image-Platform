<script setup lang="ts">
import { computed, ref } from 'vue'

const props = defineProps<{
	currentUserName?: string
}>()

type CommentItem = {
	id: number
	author: string
	date: string
	content: string
	likes: number
}

const commentInput = ref('')
const sortOption = ref<'hot' | 'latest' | 'earliest'>('hot')

const comments = ref<CommentItem[]>([
	{
		id: 1,
		author: 'wufenghua',
		date: '02-14',
		content: '大保底吃满，抽不到了',
		likes: 242
	}
])

const sortedComments = computed(() => {
	const list = [...comments.value]
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

	const now = new Date()
	const mm = String(now.getMonth() + 1).padStart(2, '0')
	const dd = String(now.getDate()).padStart(2, '0')

	comments.value.unshift({
		id: Date.now(),
		author: props.currentUserName || '我',
		date: `${mm}-${dd}`,
		content: value,
		likes: 0
	})

	commentInput.value = ''
}
</script>

<template>
	<div class="comment-section">
		<section class="comment-editor-card">
			<p class="editor-tip">看帖是喜欢，评论才是真爱：</p>
			<div class="editor-box">
				<textarea v-model="commentInput" maxlength="1000" placeholder="善语结缘，温暖常伴..." />
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
				<div class="avatar"></div>
				<div class="comment-body">
					<div class="comment-user-row">
						<span class="name">{{ item.author }}</span>
					</div>
					<p class="comment-content">{{ item.content }}</p>
					<div class="comment-bottom">
						<span class="date">{{ item.date }}</span>
						<span>回复</span>
						<span>👍 {{ item.likes }}</span>
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
</style>
