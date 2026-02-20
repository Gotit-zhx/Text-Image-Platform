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
			<button v-for="action in quickActions" :key="action" class="publish-btn" @click="emit('go-publish')">
				<span class="publish-text">{{ action }}</span>
				<span class="publish-arrow">›</span>
			</button>
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
	.creator-panel {
		order: -1;
	}

	.panel-card {
		position: static;
	}
}
</style>
