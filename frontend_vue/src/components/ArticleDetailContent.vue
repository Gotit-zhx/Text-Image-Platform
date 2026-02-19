<script setup lang="ts">
import { computed, ref } from 'vue'
import type { Post } from '../types'

const props = defineProps<{
	post: Post | null
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
const commentCount = computed(() => commentInput.value.length)
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

const getImageStyle = (image: string) => {
	if (/^(linear-gradient|radial-gradient|conic-gradient)\(/.test(image)) {
		return { background: image }
	}

	return {
		backgroundImage: `url(${image})`,
		backgroundSize: 'cover',
		backgroundPosition: 'center'
	}
}
</script>

<template>
	<main class="detail-layout">
		<section class="detail-main">
			<article v-if="post" class="detail-card">
				<div class="detail-meta">
					<div class="author-avatar"></div>
					<div>
						<div class="author-line">
							<span class="author">{{ post.author }}</span>
							<span class="time">{{ post.time }}</span>
						</div>
						<h1>{{ post.title }}</h1>
					</div>
				</div>

				<div
					v-if="!post.contentHtml && post.images.length"
					class="images"
					:class="{ single: post.images.length === 1 }"
				>
					<div
						v-for="(image, idx) in post.images"
						:key="`${post.id}-${idx}`"
						class="img"
						:style="getImageStyle(image)"
					/>
				</div>

				<div v-if="post.contentHtml" class="content-html" v-html="post.contentHtml"></div>
				<p v-else class="summary">{{ post.summary }}</p>

				<div v-if="post.tags.length" class="tags">
					<span v-for="tag in post.tags" :key="tag" class="tag"># {{ tag }}</span>
				</div>
			</article>

			<section v-if="post" class="comment-editor-card">
				<p class="editor-tip">看帖是喜欢，评论才是真爱：</p>
				<div class="editor-box">
					<textarea v-model="commentInput" maxlength="1000" placeholder="善语结缘，温暖常伴..." />
					<!-- <span class="editor-counter">{{ commentCount }} / 1000</span> -->
				</div>
				<div class="editor-actions">
					<button class="comment-btn" :disabled="!commentInput.trim()" @click="handleSubmitComment">
						评论
					</button>
				</div>
			</section>

			<section v-if="post" class="comment-list-card">
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

			<div v-else class="empty">帖子不存在</div>
		</section>

		<aside class="right-panel">
			<div class="follow-card">
				<div class="tab">关注</div>
				<button class="follow-btn">关注作者</button>
			</div>

			<div class="action-card">
				<button class="action-item" title="点赞">👍</button>
				<button class="action-item" title="评论">💬</button>
				<button class="action-item" title="收藏">⭐</button>
			</div>
		</aside>
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

.right-panel {
	position: sticky;
	top: 84px;
	align-self: start;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.detail-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 18px 20px;
}

.detail-meta {
	display: flex;
	gap: 10px;
	align-items: center;
}

.author-avatar {
	width: 38px;
	height: 38px;
	border-radius: 50%;
	background: linear-gradient(145deg, #f4bf80, #e88e47);
	border: 1px solid #e7d3bf;
}

.author-line {
	display: flex;
	gap: 10px;
	font-size: 12px;
	color: #8c94a7;
}

.author {
	font-size: 13px;
	font-weight: 600;
	color: #515869;
}

h1 {
	margin: 6px 0 0;
	font-size: 24px;
}

.images {
	margin-top: 14px;
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 8px;
}

.images.single {
	grid-template-columns: 1fr;
	max-width: 360px;
}

.img {
	border-radius: 8px;
	aspect-ratio: 16 / 10;
}

.content-html,
.summary {
	margin-top: 16px;
	color: #3a4357;
	line-height: 1.8;
}

:deep(.content-html img) {
	max-width: 100%;
	border-radius: 8px;
}

.tags {
	margin-top: 14px;
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.tag {
	font-size: 12px;
	padding: 4px 10px;
	border-radius: 999px;
	background: #f3f5f8;
	color: #798197;
}

.follow-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 14px;
}

.action-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 12px;
	display: flex;
	justify-content: space-between;
	gap: 10px;
}

.action-item {
	flex: 1;
	height: 40px;
	border: 1px solid #e8edf5;
	border-radius: 8px;
	background: #f9fbfe;
	cursor: pointer;
	font-size: 20px;
}

.tab {
	font-size: 15px;
	font-weight: 600;
	padding-bottom: 10px;
	border-bottom: 1px solid #edf0f5;
	margin-bottom: 12px;
}

.follow-btn {
	width: 100%;
	height: 36px;
	border: none;
	border-radius: 999px;
	cursor: pointer;
	color: #fff;
	font-weight: 600;
	background: linear-gradient(180deg, #30c6ff, #13a6f6);
}

.empty {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 24px;
	color: #8c94a7;
}

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

.editor-counter {
	position: absolute;
	right: 10px;
	bottom: 8px;
	font-size: 12px;
	color: #b8becb;
}

.editor-actions {
	margin-top: 10px;
	display: flex;
	justify-content: space-between;
	align-items: center;
}

.left-icons {
	color: #9da5b6;
	font-size: 22px;
	letter-spacing: 10px;
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

.sort {
	font-size: 15px;
	color: #868ea1;
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


@media (max-width: 1024px) {
	.detail-layout {
		grid-template-columns: 1fr;
	}

	.right-panel {
		position: static;
	}
}
</style>
