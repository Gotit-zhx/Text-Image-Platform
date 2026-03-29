<script setup lang="ts">
defineProps<{
	quickActions: string[]
}>()

const emit = defineEmits<{
	(e: 'go-publish'): void
}>()
</script>

<template>
	<aside class="creator-panel">
		<div class="panel-card">
			<div class="panel-title">快捷入口</div>
			<button v-for="action in quickActions" :key="action" class="publish-btn" @click="emit('go-publish')">
				<span class="publish-text">{{ action }}</span>
				<span class="publish-arrow">›</span>
			</button>
			<div class="community-tip">
				<p>✨ 社区建议</p>
				<span>标题简洁 + 正文分段，互动率更高</span>
			</div>
		</div>
	</aside>
</template>

<style scoped>
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
	box-shadow: 0 10px 28px rgba(32, 47, 85, 0.06);
}

.panel-title {
	font-size: 14px;
	font-weight: 700;
	color: #344062;
	margin-bottom: 10px;
}

.publish-btn {
	width: 100%;
	border: none;
	cursor: pointer;
	position: relative;
	border-radius: 8px;
	padding: 12px 12px;
	margin-bottom: 10px;
	background: linear-gradient(180deg, #ffe56f, #ffd435);
	color: #2c2a1a;
	font-size: 16px;
	font-weight: 700;
	display: flex;
	justify-content: center;
	align-items: center;
	transition: transform 0.18s ease, box-shadow 0.18s ease;
}

.publish-btn:hover {
	transform: translateY(-1px);
	box-shadow: 0 8px 20px rgba(255, 197, 17, 0.3);
}

.publish-text {
	text-align: center;
}

.publish-arrow {
	position: absolute;
	right: 12px;
}

.community-tip {
	margin-top: 12px;
	padding: 10px 12px;
	border-radius: 10px;
	background: #f7f9ff;
	border: 1px solid #e4eafe;
}

.community-tip p {
	margin: 0;
	font-size: 13px;
	font-weight: 600;
	color: #344062;
}

.community-tip span {
	display: block;
	margin-top: 4px;
	font-size: 12px;
	color: #6e7da3;
}

@media (max-width: 1024px) {
	.creator-panel {
		order: -1;
	}

	.panel-card {
		position: static;
	}
}
</style>
