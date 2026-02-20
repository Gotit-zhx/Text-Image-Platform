<template>
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

@media (max-width: 1024px) {
	.right-panel {
		position: static;
	}
}
</style>
