<script setup lang="ts">
import { computed, ref } from 'vue'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import type { PublishPayload } from '../types'

const emit = defineEmits<{
	(e: 'publish', payload: PublishPayload): void
}>()

const title = ref('')
const content = ref('')
const tagInput = ref('')
const tags = ref<string[]>([])
const submitTip = ref('')
const quillRef = ref<InstanceType<typeof QuillEditor> | null>(null)

const titleCount = computed(() => title.value.length)
const contentCount = computed(() => {
	const plain = content.value.replace(/<[^>]*>/g, '').trim()
	return plain.length
})

const toolbarOptions = [
	['bold', 'italic', 'underline'],
	[{ header: [1, 2, false] }],
	[{ list: 'ordered' }, { list: 'bullet' }],
	['image'],
	['link'],
	['clean']
]

const handleImageUpload = () => {
	const input = document.createElement('input')
	input.type = 'file'
	input.accept = 'image/*'
	input.onchange = () => {
		const file = input.files?.[0]
		if (!file) return
		const reader = new FileReader()
		reader.onload = () => {
			const quill = quillRef.value?.getQuill?.()
			if (!quill) return
			const range = quill.getSelection(true)
			const index = range?.index ?? quill.getLength()
			quill.insertEmbed(index, 'image', reader.result, 'user')
			quill.setSelection(index + 1)
		}
		reader.readAsDataURL(file)
	}
	input.click()
}

const handleEditorReady = (quill: any) => {
	quill.getModule('toolbar')?.addHandler('image', handleImageUpload)
}

const normalizeTag = (raw: string) => raw.trim().replace(/^#+/, '')

const handleAddTag = () => {
	const value = normalizeTag(tagInput.value)
	if (!value) return
	if (tags.value.includes(value)) {
		submitTip.value = '标签已存在'
		return
	}
	if (tags.value.length >= 5) {
		submitTip.value = '最多添加5个标签'
		return
	}
	tags.value.push(value)
	tagInput.value = ''
	submitTip.value = ''
}

const handleRemoveTag = (index: number) => {
	tags.value.splice(index, 1)
}

const handlePublish = () => {
	const plainContent = content.value.replace(/<[^>]*>/g, '').trim()
	if (!title.value.trim()) {
		submitTip.value = '请先填写标题'
		return
	}

	if (!plainContent) {
		submitTip.value = '请先填写内容'
		return
	}

	if (tagInput.value.trim()) {
		handleAddTag()
	}

	emit('publish', {
		title: title.value.trim(),
		contentHtml: content.value,
		tags: [...tags.value]
	})

	submitTip.value = '发布成功（模拟）'
	title.value = ''
	content.value = ''
	tagInput.value = ''
	tags.value = []
}
</script>

<template>
	<main class="publish-page">
		<section class="publish-card">
			<h2>发布帖子</h2>

			<div class="form-row">
				<label>标题：</label>
				<div class="field-wrap">
					<input v-model="title" maxlength="30" type="text" placeholder="标题(必填)" />
					<span class="counter">{{ titleCount }}/30</span>
				</div>
			</div>

			<div class="form-row content-row">
				<label>内容：</label>
				<div class="field-wrap">
					<div class="editor-wrap">
						<QuillEditor
							ref="quillRef"
							v-model:content="content"
							content-type="html"
							theme="snow"
							:toolbar="toolbarOptions"
							@ready="handleEditorReady"
							placeholder="请尽情发挥吧..."
						/>
					</div>
					<span class="counter content-counter">{{ contentCount }}/30000</span>
				</div>
			</div>

			<div class="form-row">
				<label>设置标签：</label>
				<div class="field-wrap tag-wrap">
					<div class="tag-input-row">
						<input
							v-model="tagInput"
							type="text"
							placeholder="输入标签后点击添加"
							@keydown.enter.prevent="handleAddTag"
						/>
						<button class="tag-add-btn" type="button" @click="handleAddTag">添加</button>
					</div>
					<div v-if="tags.length" class="tag-list">
						<span v-for="(item, idx) in tags" :key="`${item}-${idx}`" class="tag-chip">
							{{ item }}
							<button type="button" class="tag-remove" @click="handleRemoveTag(idx)">×</button>
						</span>
					</div>
				</div>
			</div>

			<div class="submit-wrap">
				<button class="submit-btn" @click="handlePublish">发布</button>
			</div>
			<p v-if="submitTip" class="submit-tip">{{ submitTip }}</p>
		</section>
	</main>
</template>

<style scoped>
.publish-page {
	max-width: 1180px;
	margin: 20px auto;
	padding: 0 16px;
}

.publish-card {
	background: #fff;
	border: 1px solid #e9edf3;
	border-radius: 6px;
	padding: 0 0 32px;
}

.publish-card h2 {
	margin: 0;
	padding: 18px 24px;
	font-size: 28px;
	line-height: 1;
	border-bottom: 1px solid #edf0f5;
}

.form-row {
	display: grid;
	grid-template-columns: 90px 1fr;
	gap: 16px;
	padding: 18px 40px 0;
	align-items: start;
}

.form-row > label {
	line-height: 40px;
	font-size: 16px;
	color: #2f3748;
}

.field-wrap {
	position: relative;
}

.field-wrap input {
	width: 100%;
	height: 40px;
	border: 1px solid #e3e7ef;
	border-radius: 4px;
	padding: 0 12px;
	font-size: 14px;
	outline: none;
}

.field-wrap input:focus {
	border-color: #87c6ff;
}

.counter {
	position: absolute;
	right: 12px;
	top: 11px;
	font-size: 12px;
	color: #b8becb;
}

.content-row {
	align-items: start;
}

.editor-wrap {
	border: 1px solid #e3e7ef;
	border-radius: 4px;
	overflow: hidden;
	background: #fff;
}

:deep(.ql-toolbar.ql-snow) {
	border: none;
	border-bottom: 1px solid #edf0f5;
}

:deep(.ql-container.ql-snow) {
	border: none;
	min-height: 260px;
}

:deep(.ql-container) {
	min-height: 260px;
}

:deep(.ql-editor) {
	min-height: 220px;
}

.content-counter {
	top: auto;
	bottom: 12px;
}

.tag-wrap {
	max-width: 300px;
}

.tag-input-row {
	display: flex;
	gap: 8px;
}

.tag-input-row input {
	flex: 1;
}

.tag-add-btn {
	width: 64px;
	height: 40px;
	border: 1px solid #8fd2ff;
	border-radius: 4px;
	background: #f2fbff;
	color: #18a8f2;
	cursor: pointer;
	font-size: 13px;
}

.tag-list {
	margin-top: 10px;
	display: flex;
	gap: 8px;
	flex-wrap: wrap;
}

.tag-chip {
	display: inline-flex;
	align-items: center;
	gap: 6px;
	padding: 4px 8px;
	border-radius: 999px;
	background: #eef7ff;
	color: #2f7fc6;
	font-size: 12px;
}

.tag-remove {
	border: none;
	background: transparent;
	color: #6b90b5;
	cursor: pointer;
	line-height: 1;
	font-size: 14px;
	padding: 0;
}

.submit-wrap {
	display: flex;
	justify-content: center;
	margin-top: 40px;
}

.submit-btn {
	width: 160px;
	height: 36px;
	border: none;
	border-radius: 4px;
	cursor: pointer;
	background: linear-gradient(180deg, #2dc7ff, #0fb0f6);
	color: #fff;
	font-size: 14px;
}

.submit-tip {
	margin: 12px 0 0;
	text-align: center;
	font-size: 13px;
	color: #18b0ff;
}
</style>
