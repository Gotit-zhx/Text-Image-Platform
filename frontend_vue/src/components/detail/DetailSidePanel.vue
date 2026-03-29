<script setup lang="ts">
import { ChatDotRound, Pointer, Share, Star } from '@element-plus/icons-vue'
defineProps<{
	isLiked?: boolean
	likeCount?: number
	isFavorited?: boolean
	isFollowingAuthor?: boolean
}>()

const emit = defineEmits<{
	(e: 'comment-click'): void
	(e: 'toggle-like'): void
	(e: 'toggle-favorite'): void
	(e: 'toggle-follow'): void
	(e: 'share-post'): void
}>()
</script>

<template>
	<aside class="right-panel">
		<div class="follow-card">
			<div class="tab">关注</div>
			<button class="follow-btn" :class="{ followed: isFollowingAuthor }" @click="emit('toggle-follow')">
				{{ isFollowingAuthor ? '已关注作者' : '关注作者' }}
			</button>
		</div>

		<div class="action-card">
			<button class="action-item" :class="{ liked: isLiked }" title="点赞" @click="emit('toggle-like')">
				<el-icon><Pointer /></el-icon>
				{{ likeCount ?? 0 }}
			</button>
			<button class="action-item" title="评论" @click="emit('comment-click')">
				<el-icon><ChatDotRound /></el-icon>
			</button>
			<button
				class="action-item"
				:class="{ favorited: isFavorited }"
				title="收藏"
				@click="emit('toggle-favorite')"
			>
				<el-icon><Star /></el-icon>
				{{ isFavorited ? '已收藏' : '收藏' }}
			</button>
			<button class="action-item" title="分享" @click="emit('share-post')">
				<el-icon><Share /></el-icon>
				分享
			</button>
		</div>
	</aside>
</template>

<style scoped>
.right-panel {
	position: sticky;
	top: 84px;
	align-self: start;
	display: flex;
	flex-direction: column;
	gap: 12px;
}

.follow-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 12px;
	padding: 14px;
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

.follow-btn.followed {
	background: #eef3f8;
	color: #74819a;
	border: 1px solid #d8e1ed;
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
	font-size: 14px;
	display: inline-flex;
	justify-content: center;
	align-items: center;
	gap: 4px;
}

.action-item.liked {
	color: #ff7a59;
	border-color: #ffcdbf;
	background: #fff7f4;
	font-weight: 600;
}

.action-item.favorited {
	color: #f2a100;
	border-color: #ffe2a2;
	background: #fff9e9;
	font-weight: 600;
}

@media (max-width: 1024px) {
	.right-panel {
		position: static;
	}
}
</style>
