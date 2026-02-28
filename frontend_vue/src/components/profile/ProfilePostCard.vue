<script setup lang="ts">
import type { Post } from '../../types'

defineProps<{
	post: Post
	actionText?: string
}>()

const emit = defineEmits<{
	(e: 'open-detail', postId: number): void
	(e: 'action-click', postId: number): void
	(e: 'open-comment-detail', postId: number): void
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()

const formatCount = (count: number): string => {
	if (count >= 10000) {
		const value = count / 10000
		const formatted = (Math.floor(value * 10) / 10).toString().replace(/\.0$/, '')
		return `${formatted}万+`
	}

	return `${count}`
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
	<article class="card" @click="emit('open-detail', post.id)">
		<div class="card-head">
			<div class="author-wrap">
				<div
					class="author-avatar"
					@click.stop="emit('open-author-profile', { userId: post.authorId, userName: post.author, avatarText: post.authorAvatarText || post.author.slice(0, 1) })"
				>
					<img v-if="post.authorAvatarUrl" :src="post.authorAvatarUrl" alt="avatar" />
					<span v-else>{{ post.authorAvatarText || post.author.slice(0, 1) }}</span>
				</div>
				<div class="author-meta">
					<div class="meta-line">
						<span
							class="author"
							@click.stop="emit('open-author-profile', { userId: post.authorId, userName: post.author, avatarText: post.authorAvatarText || post.author.slice(0, 1) })"
						>
							{{ post.author }}
						</span>
						<span class="time">{{ post.time }}</span>
					</div>
					<h3 class="title">{{ post.title }}</h3>
				</div>
			</div>

			<button class="edit-btn" @click.stop="emit('action-click', post.id)">{{ actionText || '编辑' }}</button>
		</div>

		<p class="summary">{{ post.summary }}</p>

		<div v-if="post.images.length" class="images" :class="{ single: post.images.length === 1 }">
			<div
				v-for="(image, idx) in post.images"
				:key="`${post.id}-${idx}`"
				class="img"
				:style="getImageStyle(image)"
			>
				<span class="img-watermark">图文</span>
			</div>
		</div>

		<div v-if="post.tags.length" class="tags">
			<span v-for="tag in post.tags" :key="tag" class="tag">{{ tag }}</span>
		</div>

		<div class="stats">
			<button class="stats-btn" @click.stop="emit('open-comment-detail', post.id)">
				💬 {{ post.comments }}
			</button>
			<button class="stats-btn" :class="{ liked: post.isLiked }" @click.stop="emit('toggle-post-like', post.id)">
				👍 {{ formatCount(post.likes) }}
			</button>
			<button
				class="stats-btn"
				:class="{ favorited: post.isFavorited }"
				@click.stop="emit('toggle-post-favorite', post.id)"
			>
				⭐ {{ post.isFavorited ? '已收藏' : '收藏' }}
			</button>
		</div>
	</article>
</template>

<style scoped>
.card {
	background: #fff;
	border-radius: 12px;
	border: 1px solid #e9edf3;
	padding: 16px 20px 14px;
	cursor: pointer;
}

.card-head {
	display: flex;
	justify-content: space-between;
	align-items: flex-start;
	gap: 10px;
}

.author-wrap {
	display: flex;
	gap: 10px;
}

.author-avatar {
	width: 36px;
	height: 36px;
	border-radius: 50%;
	background: linear-gradient(145deg, #f4bf80, #e88e47);
	box-shadow: inset 0 0 0 2px #fff;
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

.meta-line {
	display: flex;
	align-items: center;
	flex-wrap: wrap;
	gap: 8px;
	font-size: 12px;
	color: #8c94a7;
}

.author {
	font-size: 13px;
	font-weight: 600;
	color: #515869;
}

.title {
	margin: 6px 0 0;
	font-size: 22px;
	line-height: 1.35;
	font-weight: 700;
	letter-spacing: 0.3px;
}

.edit-btn {
	height: 32px;
	min-width: 74px;
	border-radius: 999px;
	border: 1px solid #8fd2ff;
	cursor: pointer;
	color: #18a8f2;
	font-weight: 600;
	background: #f2fbff;
}

.summary {
	margin: 10px 0 12px 46px;
	color: #697084;
	font-size: 14px;
	line-height: 1.6;
}

.images {
	margin-left: 46px;
	display: grid;
	grid-template-columns: repeat(3, minmax(0, 1fr));
	gap: 8px;
	max-width: 520px;
}

.images.single {
	grid-template-columns: 1fr;
	max-width: 180px;
}

.img {
	position: relative;
	border-radius: 8px;
	aspect-ratio: 16 / 10;
	overflow: hidden;
}

.img-watermark {
	position: absolute;
	right: 8px;
	bottom: 8px;
	font-size: 11px;
	color: rgba(255, 255, 255, 0.95);
	background: rgba(0, 0, 0, 0.35);
	border-radius: 999px;
	padding: 2px 8px;
}

.tags {
	margin: 10px 0 8px 46px;
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.tag {
	background: #f3f5f8;
	color: #798197;
	font-size: 12px;
	border-radius: 999px;
	padding: 4px 10px;
}

.stats {
	margin-left: 46px;
	color: #9aa3b6;
	display: flex;
	justify-content: flex-end;
	gap: 18px;
	font-size: 13px;
}

.stats-btn {
	border: none;
	background: transparent;
	padding: 0;
	font: inherit;
	color: inherit;
	cursor: pointer;
}

.stats-btn.liked {
	color: #ff7a59;
	font-weight: 600;
}

.stats-btn.favorited {
	color: #f2a100;
	font-weight: 600;
}
</style>
