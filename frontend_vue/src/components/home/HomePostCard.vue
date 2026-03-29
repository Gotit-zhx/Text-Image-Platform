<script setup lang="ts">
import { computed } from 'vue'
import { ChatDotRound, Pointer, Share, Star } from '@element-plus/icons-vue'
import type { Post } from '../../types'
import { formatCount, resolvePostImageStyle } from '../../utils/postUi'

const props = defineProps<{
	post: Post
}>()

const displayImages = computed(() => {
	const images = props.post.images || []
	if (images.length === 0) return []
	if (images.length > 3) return []
	return images
})

const emit = defineEmits<{
	(e: 'open-detail', postId: number): void
	(e: 'open-comment-detail', postId: number): void
	(e: 'toggle-post-like', postId: number): void
	(e: 'toggle-post-favorite', postId: number): void
	(e: 'share-post', postId: number): void
	(e: 'toggle-post-follow', postId: number): void
	(e: 'open-author-profile', payload: { userId?: number; userName: string; avatarText: string }): void
}>()

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
						<span v-if="post.moderationStatus && post.moderationStatus !== 'approved'" class="status-tag">
							{{ post.moderationStatus }}
						</span>
					</div>
					<h3 class="title">{{ post.title }}</h3>
				</div>
			</div>

			<button class="follow" :class="{ followed: post.isFollowingAuthor }" @click.stop="emit('toggle-post-follow', post.id)">
				{{ post.isFollowingAuthor ? '已关注' : '关注' }}
			</button>
		</div>

		<p class="summary">{{ post.summary }}</p>

		<div v-if="displayImages.length" class="images" :class="{ single: displayImages.length === 1 }">
			<div
				v-for="(image, idx) in displayImages"
				:key="`${post.id}-${idx}`"
				class="img"
				:style="resolvePostImageStyle(image)"
			>
				<span class="img-watermark">图文</span>
			</div>
		</div>

		<div v-if="post.tags.length" class="tags">
			<span v-for="tag in post.tags" :key="tag" class="tag">{{ tag }}</span>
		</div>

		<div class="stats">
			<button class="stats-btn" @click.stop="emit('open-comment-detail', post.id)">
				<el-icon><ChatDotRound /></el-icon>
				{{ post.comments }}
			</button>
			<button class="stats-btn" :class="{ liked: post.isLiked }" @click.stop="emit('toggle-post-like', post.id)">
				<el-icon><Pointer /></el-icon>
				{{ formatCount(post.likes) }}
			</button>
			<button
				class="stats-btn"
				:class="{ favorited: post.isFavorited }"
				@click.stop="emit('toggle-post-favorite', post.id)"
			>
				<el-icon><Star /></el-icon>
				{{ post.isFavorited ? '已收藏' : '收藏' }}
			</button>
			<button class="stats-btn" @click.stop="emit('share-post', post.id)">
				<el-icon><Share /></el-icon>
				分享
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
	transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}

.card:hover {
	transform: translateY(-2px);
	border-color: #dce4f5;
	box-shadow: 0 10px 24px rgba(25, 40, 74, 0.08);
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

.status-tag {
	padding: 2px 8px;
	border-radius: 999px;
	font-size: 11px;
	line-height: 1.3;
	color: #7f5e00;
	background: #fff8de;
	border: 1px solid #ffe8a3;
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

.follow {
	height: 32px;
	min-width: 74px;
	border-radius: 999px;
	border: none;
	cursor: pointer;
	color: #fff;
	font-weight: 600;
	background: linear-gradient(180deg, #30c6ff, #13a6f6);
}

.follow.followed {
	background: #eef3f8;
	color: #74819a;
	border: 1px solid #d8e1ed;
}

.summary {
	margin: 10px 0 12px 46px;
	color: #697084;
	font-size: 14px;
	line-height: 1.6;
	display: -webkit-box;
	-webkit-line-clamp: 3;
	-webkit-box-orient: vertical;
	overflow: hidden;
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
	border: 1px solid #e6ebf3;
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
	display: inline-flex;
	align-items: center;
	gap: 4px;
	transition: color 0.15s ease;
}

.stats-btn:hover {
	color: #5a6787;
}

.stats-btn.liked {
	color: #ff7a59;
	font-weight: 600;
}

.stats-btn.favorited {
	color: #f2a100;
	font-weight: 600;
}

@media (max-width: 768px) {
	.title {
		font-size: 18px;
	}

	.summary,
	.images,
	.tags,
	.stats {
		margin-left: 0;
	}

	.images {
		max-width: none;
	}
}
</style>
