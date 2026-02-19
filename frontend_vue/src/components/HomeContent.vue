<script setup lang="ts">
import type { Post } from '../types'

defineProps<{
	posts: Post[]
	quickActions: string[]
}>()

const emit = defineEmits<{
	(e: 'go-publish'): void
	(e: 'open-detail', postId: number): void
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
	<main class="layout">
		<section class="feed">
			<article v-for="post in posts" :key="post.id" class="card" @click="emit('open-detail', post.id)">
				<div class="card-head">
					<div class="author-wrap">
						<div class="author-avatar"></div>
						<div class="author-meta">
							<div class="meta-line">
								<span class="author">{{ post.author }}</span>
								<span class="time">{{ post.time }}</span>
							</div>
							<h3 class="title">{{ post.title }}</h3>
						</div>
					</div>

					<button class="follow" @click.stop>关注</button>
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
					<span>💬 {{ post.comments }}</span>
					<span>👍 {{ formatCount(post.likes) }}</span>
				</div>
			</article>
		</section>

		<aside class="creator-panel">
			<div class="panel-card">
				<button
					v-for="action in quickActions"
					:key="action"
					class="publish-btn"
					@click="emit('go-publish')"
				>
					<span class="publish-text">{{ action }}</span>
					<span class="publish-arrow">›</span>
				</button>
			</div>
		</aside>
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

.creator-panel {
	position: relative;
}

.panel-card {
	background: #fff;
	border-radius: 12px;
	border: 1px solid #e9edf3;
	padding: 16px;
	position: sticky;
	top: 84px;
}

.publish-btn {
	width: 100%;
	border: none;
	cursor: pointer;
	position: relative;
	border-radius: 8px;
	padding: 12px 12px;
	margin-bottom: 10px;
	background: linear-gradient(180deg, #ffe35f, #ffd835);
	color: #2c2a1a;
	font-size: 16px;
	font-weight: 700;
	display: flex;
	justify-content: center;
	align-items: center;
}

.publish-text {
	text-align: center;
}

.publish-arrow {
	position: absolute;
	right: 12px;
}

@media (max-width: 1024px) {
	.layout {
		grid-template-columns: 1fr;
	}

	.creator-panel {
		order: -1;
	}

	.panel-card {
		position: static;
	}
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
