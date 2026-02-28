<script setup lang="ts">
// 审查状态：部分完成（已接入净化与 URL 协议限制，仍需后端内容审计协同）
import { computed } from 'vue'
import DOMPurify from 'dompurify'
import type { Post } from '../../types'

const props = defineProps<{
	post: Post
}>()

const emit = defineEmits<{
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()

const isSafeImageUrl = (value: string) => {
	if (!value) return false
	if (value.startsWith('/')) return true
	if (value.startsWith('data:image/')) return true

	try {
		const parsed = new URL(value)
		return parsed.protocol === 'https:' || parsed.protocol === 'http:' || parsed.protocol === 'blob:'
	} catch {
		return false
	}
}

const getImageStyle = (image: string) => {
	if (/^(linear-gradient|radial-gradient|conic-gradient)\(/.test(image)) {
		return { background: image }
	}

	if (!isSafeImageUrl(image)) {
		return { background: '#f3f5f8' }
	}

	return {
		backgroundImage: `url(${image})`,
		backgroundSize: 'cover',
		backgroundPosition: 'center'
	}
}

const sanitizedContentHtml = computed(() =>
	DOMPurify.sanitize(props.post.contentHtml || '', {
		ALLOWED_TAGS: [
			'p',
			'br',
			'strong',
			'em',
			'u',
			's',
			'a',
			'blockquote',
			'ul',
			'ol',
			'li',
			'h1',
			'h2',
			'h3',
			'h4',
			'h5',
			'h6',
			'pre',
			'code',
			'img',
			'span',
			'div'
		],
		ALLOWED_ATTR: ['href', 'target', 'rel', 'src', 'alt', 'title', 'class'],
		ALLOWED_URI_REGEXP: /^(?:(?:https?|mailto|tel|blob):|\/|data:image\/)/i,
		FORBID_TAGS: ['script', 'style', 'iframe', 'object', 'embed', 'form', 'input', 'button'],
		FORBID_ATTR: ['style', 'onerror', 'onload', 'onclick', 'onmouseover', 'onfocus']
	})
)
</script>

<template>
	<article class="detail-card">
		<div class="detail-meta">
			<div
				class="author-avatar"
				@click="emit('open-author-profile', { userId: post.authorId, userName: post.author, avatarText: post.authorAvatarText || post.author.slice(0, 1) })"
			>
				<img v-if="post.authorAvatarUrl" :src="post.authorAvatarUrl" alt="avatar" />
				<span v-else>{{ post.authorAvatarText || post.author.slice(0, 1) }}</span>
			</div>
			<div>
				<div class="author-line">
					<span
						class="author"
						@click="emit('open-author-profile', { userId: post.authorId, userName: post.author, avatarText: post.authorAvatarText || post.author.slice(0, 1) })"
					>
						{{ post.author }}
					</span>
					<span class="time">{{ post.time }}</span>
				</div>
				<h1>{{ post.title }}</h1>
			</div>
		</div>

		<div v-if="!post.contentHtml && post.images.length" class="images" :class="{ single: post.images.length === 1 }">
			<div v-for="(image, idx) in post.images" :key="`${post.id}-${idx}`" class="img" :style="getImageStyle(image)" />
		</div>

		<div v-if="post.contentHtml" class="content-html" v-html="sanitizedContentHtml"></div>
		<p v-else class="summary">{{ post.summary }}</p>

		<div v-if="post.tags.length" class="tags">
			<span v-for="tag in post.tags" :key="tag" class="tag"># {{ tag }}</span>
		</div>
	</article>
</template>

<style scoped>
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
	display: grid;
	place-items: center;
	overflow: hidden;
	color: #fff;
	font-size: 14px;
	font-weight: 700;
}

.author-avatar img {
	width: 100%;
	height: 100%;
	object-fit: cover;
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
</style>
