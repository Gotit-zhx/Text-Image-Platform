<script setup lang="ts">
import { computed, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { QuillEditor } from '@vueup/vue-quill'
import '@vueup/vue-quill/dist/vue-quill.snow.css'
import type { Post, PublishPayload } from '../types'
import { publishPostApi, saveEditedPostApi } from '../api/community'
import { apiRequest } from '../api/client'
import { uploadImage, type MediaAsset, type DraftRecord } from '../api/media'
import ConfirmDialog from './ui/ConfirmDialog.vue'
import BaseButton from './ui/BaseButton.vue'
import UiState from './ui/UiState.vue'
const props = withDefaults(
  defineProps<{ mode?: 'create' | 'edit'; initialPost?: Post | null; userId?: number }>(),
  { mode: 'create', initialPost: null }
)
const emit = defineEmits<{ saved: [post: Post] }>()
const route = useRoute(),
  router = useRouter(),
  title = ref(''),
  content = ref(''),
  tagInput = ref(''),
  tags = ref<string[]>([])
const pending = ref(false),
  saving = ref(false),
  loading = ref(false),
  error = ref(''),
  saveMessage = ref(''),
  savedSnapshot = ref('')
const draftId = ref<number>(),
  draftVersion = ref<number>(),
  requestKey = ref(crypto.randomUUID()),
  draftKey = ref(crypto.randomUUID())
const labelEditor = (quill: {
  root: HTMLElement
  getModule: (name: string) => { container: HTMLElement }
}) => {
  quill.root.setAttribute('role', 'textbox')
  quill.root.setAttribute('aria-label', '正文')
  quill.root.setAttribute('aria-multiline', 'true')
  const labels: Record<string, string> = {
    bold: '加粗',
    italic: '斜体',
    underline: '下划线',
    list: '列表',
    link: '插入链接',
    clean: '清除格式'
  }
  for (const button of quill.getModule('toolbar').container.querySelectorAll('button')) {
    const key =
      Array.from(button.classList as DOMTokenList)
        .find((c) => c.startsWith('ql-'))
        ?.slice(3) || ''
    button.setAttribute('aria-label', labels[key] || '正文格式')
  }
}
const quillRef = ref<InstanceType<typeof QuillEditor> | null>(null)
type UploadItem = {
  key: string
  file?: File
  asset?: MediaAsset
  progress: number
  error: string
  controller?: AbortController
  preview: string
}
const uploads = ref<UploadItem[]>([]),
  input = ref<HTMLInputElement | null>(null)
const snapshot = computed(() =>
  JSON.stringify({
    title: title.value,
    contentHtml: content.value,
    tags: tags.value,
    mediaIds: uploads.value.filter((u) => u.asset).map((u) => u.asset!.id)
  })
)
const dirty = computed(() => snapshot.value !== savedSnapshot.value)
const busyUploads = computed(() => uploads.value.some((u) => !u.asset))
let timer: ReturnType<typeof setTimeout> | undefined,
  disposed = false
const backupKey = computed(
  () =>
    `baicaoyuan-recovery:${props.userId || 0}:${props.mode === 'edit' ? props.initialPost?.id || 'edit' : draftId.value || 'new'}`
)
const payload = (): PublishPayload => ({
  title: title.value,
  contentHtml: content.value,
  tags: [...tags.value],
  mediaIds: uploads.value.filter((u) => u.asset).map((u) => u.asset!.id),
  requestKey: requestKey.value,
  ...(draftId.value ? { draftId: draftId.value } : {})
})
const upload = async (item: UploadItem) => {
  if (!item.file) return
  const controller = new AbortController()
  item.controller = controller
  item.error = ''
  item.progress = 0
  try {
    item.asset = await uploadImage(item.file, (p) => (item.progress = p), controller.signal)
    item.progress = 100
  } catch (e) {
    item.error = e instanceof Error ? e.message : '上传失败'
  } finally {
    item.controller = undefined
  }
}
const addFiles = (files: FileList | File[]) => {
  if (pending.value) return
  for (const file of Array.from(files)) {
    if (uploads.value.length >= 9) {
      error.value = '最多9张图片'
      break
    }
    const item: UploadItem = {
      key: crypto.randomUUID(),
      file,
      progress: 0,
      error: '',
      preview: URL.createObjectURL(file)
    }
    uploads.value.push(item)
    void upload(uploads.value[uploads.value.length - 1]!)
  }
}
const remove = async (index: number) => {
  if (pending.value) return
  const item = uploads.value[index]
  if (!item) return
  item.controller?.abort()
  if(item.asset){const doc=new DOMParser().parseFromString(content.value,'text/html');for(const image of doc.querySelectorAll('img'))if(image.getAttribute('src')===item.asset.url)image.remove();content.value=doc.body.innerHTML}
  uploads.value.splice(index, 1)
  if (item.preview.startsWith('blob:')) URL.revokeObjectURL(item.preview)
  if (item.asset) {
    try {
      await apiRequest(`/media/${item.asset.id}`, { method: 'DELETE' })
    } catch {
      /* Linked assets remain protected until draft/post save releases them. */
    }
  }
}
const move = (index: number, delta: number) => {
  if (pending.value) return
  const target = index + delta
  if (target < 0 || target >= uploads.value.length) return
  const [item] = uploads.value.splice(index, 1)
  if (item) uploads.value.splice(target, 0, item)
}
const insert = (item: UploadItem) => {
  if (pending.value) return
  if (!item.asset) return
  const quill = quillRef.value?.getQuill()
  if (!quill) return
  const range = quill.getSelection(true)
  quill.insertEmbed(range?.index ?? quill.getLength(), 'image', item.asset.url, 'user')
}
const addTag = () => {
  if (pending.value) return
  const tag = tagInput.value.trim().replace(/^#+/, '')
  if (tag && !tags.value.includes(tag) && tags.value.length < 5 && tag.length <= 24) {
    tags.value.push(tag)
    tagInput.value = ''
  }
}
const pendingDraftCreate=ref<{body:string;snapshot:string}>()
const saveDraft = async () => {
  if (saving.value || pending.value || loading.value || busyUploads.value || props.mode === 'edit')
    return
  if (timer) clearTimeout(timer)
  saving.value = true
  error.value = ''
  saveMessage.value = '保存中…'
  const oldKey=backupKey.value
  const nextBody=JSON.stringify({...payload(),requestKey:draftKey.value,...(draftVersion.value?{version:draftVersion.value}:{})})
  if(!draftId.value&&!pendingDraftCreate.value)pendingDraftCreate.value={body:nextBody,snapshot:snapshot.value}
  const sent=draftId.value?snapshot.value:pendingDraftCreate.value!.snapshot
  try {
    const result = await apiRequest<DraftRecord>(draftId.value?`/drafts/${draftId.value}`:'/drafts',{
      method:draftId.value?'PUT':'POST',body:draftId.value?nextBody:pendingDraftCreate.value!.body
    })
    if (disposed) return
    pendingDraftCreate.value=undefined
    draftId.value = result.id
    draftVersion.value = result.version
    savedSnapshot.value = sent
    saveMessage.value = dirty.value
      ? '已保存提交版本，新修改待保存'
      : '已保存 · ' + new Date(result.updatedAt).toLocaleTimeString()
    localStorage.removeItem(oldKey)
    if(dirty.value&&props.userId)localStorage.setItem(backupKey.value,snapshot.value)
    if (!route.query.draft)
      await router.replace({ path: route.path, query: { ...route.query, draft: result.id } })
  } catch (e) {
    if (disposed) return
    saveMessage.value = '保存失败，本地恢复副本已保留'
    error.value = e instanceof Error ? e.message : '保存失败'
    if(draftId.value){try{const latest=await apiRequest<DraftRecord>(`/drafts/${draftId.value}`);if(disposed)return;const server=JSON.stringify({title:latest.title,contentHtml:latest.contentHtml,tags:latest.tags,mediaIds:latest.mediaIds});if(server===sent){draftVersion.value=latest.version;savedSnapshot.value=sent;saveMessage.value=dirty.value?'已确认提交版本，新修改待保存':'已确认服务器保存';error.value=''}}catch{}}
  } finally {
    saving.value = false
    if (dirty.value && !error.value && !disposed) timer = setTimeout(saveDraft, 1800)
  }
}
watch(snapshot, () => {
  if (loading.value) return
  if (timer) clearTimeout(timer)
  if (props.userId && dirty.value) localStorage.setItem(backupKey.value, snapshot.value)
  if (dirty.value && props.mode === 'create' && (title.value || content.value))
    timer = setTimeout(saveDraft, 1800)
})
const lastAttempt = ref('')
const submit = async () => {
  if (pending.value || saving.value || busyUploads.value) return
  if (!title.value.trim()) {
    error.value = '请输入标题'
    return
  }
  addTag()
  if (lastAttempt.value && lastAttempt.value !== snapshot.value)
    requestKey.value = crypto.randomUUID()
  lastAttempt.value = snapshot.value
  pending.value = true
  error.value = ''
  if (timer) clearTimeout(timer)
  try {
    const submitted=snapshot.value
    const post =
      props.mode === 'edit' && props.initialPost
        ? await saveEditedPostApi(props.initialPost.id, payload())
        : await publishPostApi(payload())
    if (disposed) return
    savedSnapshot.value = submitted
    emit('saved', post)
    if(snapshot.value!==submitted){error.value='作品已提交，提交期间的新修改已保留。请检查并继续编辑。';return}
    localStorage.removeItem(backupKey.value)
    await router.push(`/detail/${post.id}`)
  } catch (e) {
    if (!disposed) error.value = e instanceof Error ? e.message : '提交失败，输入已保留'
  } finally {
    pending.value = false
  }
}
const restore = ref<string | null>(null)
const applyRecovery = async () => {
  if (!restore.value) return
  try {
    const data = JSON.parse(restore.value)
    title.value = data.title
    content.value = data.contentHtml
    tags.value = data.tags
    const recovered: UploadItem[] = []
    let missing = false
    for (const id of data.mediaIds || []) {
      const existing = uploads.value.find((u) => u.asset?.id === id)
      if (existing) recovered.push(existing)
      else try {
        const asset = await apiRequest<MediaAsset>(`/media/${id}`)
        recovered.push({
          key: String(id),
          asset,
          progress: 100,
          error: '',
          preview: asset.thumbnailUrl
        })
      } catch { missing = true }
    }
    uploads.value = recovered
    saveMessage.value = '已恢复本地副本，请检查后保存'
    if (missing) error.value = '部分图片已不可用，文字与其余图片顺序已恢复，请重新上传'
  } catch {
    error.value = '部分图片已不可用，文字已保留，请重新上传'
  }
  restore.value = null
}
const populate = (data: {
  title: string
  contentHtml?: string
  tags: string[]
  media?: MediaAsset[]
}) => {
  title.value = data.title
  content.value = data.contentHtml || ''
  tags.value = [...data.tags]
  uploads.value = (data.media || []).map((a) => ({
    key: String(a.id),
    asset: a,
    progress: 100,
    error: '',
    preview: a.thumbnailUrl
  }))
  savedSnapshot.value = snapshot.value
}
onMounted(async () => {
  loading.value = true
  try {
    if (props.mode === 'edit' && props.initialPost) populate(props.initialPost)
    else if (route.query.draft) {
      const draft = await apiRequest<DraftRecord>(`/drafts/${route.query.draft}`)
      draftId.value = draft.id
      draftVersion.value = draft.version
      populate(draft)
    } else savedSnapshot.value = snapshot.value
    restore.value = props.userId ? localStorage.getItem(backupKey.value) : null
  } catch (e) {
    error.value = e instanceof Error ? e.message : '草稿加载失败'
  } finally {
    loading.value = false
  }
})
const beforeUnload = (e: BeforeUnloadEvent) => {
  if (dirty.value || busyUploads.value) {
    e.preventDefault()
    e.returnValue = ''
  }
}
window.addEventListener('beforeunload', beforeUnload)
const leaveOpen = ref(false)
let resolveLeave: ((value: boolean) => void) | undefined
const decideLeave = (leave: boolean) => {
  leaveOpen.value = false
  resolveLeave?.(leave)
  resolveLeave = undefined
}
const unregister = router.beforeEach((to, from) => {
  if (to.path === from.path) return true
  if (dirty.value || busyUploads.value) {
    leaveOpen.value = true
    return new Promise<boolean>((resolve) => {
      resolveLeave = resolve
    })
  }
  return true
})
onBeforeUnmount(() => {
  disposed = true
  unregister()
  window.removeEventListener('beforeunload', beforeUnload)
  if (timer) clearTimeout(timer)
  resolveLeave?.(true)
  uploads.value.forEach((u) => {
    u.controller?.abort()
    if (u.preview.startsWith('blob:')) URL.revokeObjectURL(u.preview)
  })
})
</script>
<template>
  <main class="editor-page page-container">
    <header>
      <h1>{{ mode === 'edit' ? '编辑作品' : '写下新的灵感' }}</h1>
      <RouterLink to="/drafts" class="text-button">我的草稿</RouterLink>
    </header>
    <UiState v-if="loading" kind="loading" />
    <template v-else>
      <div v-if="restore" class="recovery" role="status">
        发现同账号本地恢复副本。<button @click="applyRecovery">恢复副本</button
        ><button @click="restore = null">忽略</button>
      </div>
      <label class="title-field"
        >标题<input v-model="title" :readonly="pending" maxlength="255" placeholder="给这份记录起个名字"
      /></label>
      <div
        class="upload-zone"
        @dragover.prevent
        @drop.prevent="addFiles($event.dataTransfer?.files || [])"
      >
        <p>添加图片（最多9张，每张10MiB以内）</p>
        <input
          ref="input"
          type="file"
          aria-label="添加图片，最多9张，每张10MiB以内"
          :disabled="pending"
          accept="image/jpeg,image/png,image/webp,image/gif"
          multiple
          @change="
            addFiles(($event.target as HTMLInputElement).files || [])
            ;($event.target as HTMLInputElement).value = ''
          "
        />
        <div class="media-list">
          <article v-for="(item, index) in uploads" :key="item.key">
            <img :src="item.preview" alt="待发布图片" width="120" height="120" />
            <p>{{ item.asset ? '上传完成' : item.error || `${item.progress}%` }}</p>
            <progress
              v-if="!item.asset && !item.error"
              :value="item.progress"
              max="100"
              aria-label="上传进度"
            />
            <div>
              <button :disabled="pending || index === 0" @click="move(index, -1)" aria-label="图片前移">
                ←</button
              ><button
                :disabled="pending || index === uploads.length - 1"
                @click="move(index, 1)"
                aria-label="图片后移"
              >
                →</button
              ><button :disabled="pending" @click="remove(index)">{{ item.controller ? '取消' : '移除' }}</button
              ><button v-if="item.error" :disabled="pending" @click="upload(item)">重试</button
              ><button v-if="item.asset" :disabled="pending" @click="insert(item)">插入正文</button>
            </div>
          </article>
        </div>
      </div>
      <label class="editor-label">正文</label
      ><QuillEditor :read-only="pending"
        @ready="labelEditor"
        ref="quillRef"
        v-model:content="content"
        content-type="html"
        theme="snow"
        :toolbar="[
          ['bold', 'italic', 'underline'],
          [{ header: [1, 2, false] }],
          [{ list: 'ordered' }, { list: 'bullet' }],
          ['link'],
          ['clean']
        ]"
      />
      <div class="tag-editor">
        <span v-for="(tag, i) in tags" :key="tag" class="tag"
          >#{{ tag }}
          <button :disabled="pending" :aria-label="`移除标签${tag}`" @click="tags.splice(i, 1)">×</button></span
        ><input
          v-model="tagInput"
          :readonly="pending"
          maxlength="24"
          placeholder="添加标签，回车确认"
          aria-label="标签"
          @keydown.enter.prevent="addTag"
        /><BaseButton :disabled="pending" @click="addTag">添加</BaseButton>
      </div>
      <p v-if="error" role="alert" class="error">{{ error }}</p>
      <p role="status">{{ saveMessage }}</p>
      <footer>
        <BaseButton
          v-if="mode === 'create'"
          :pending="saving"
          :disabled="pending || busyUploads"
          @click="saveDraft"
          >保存草稿</BaseButton
        ><BaseButton
          variant="primary"
          :pending="pending"
          :disabled="saving || busyUploads"
          @click="submit"
          >{{ mode === 'edit' ? '确认保存' : '确认发布' }}</BaseButton
        >
      </footer>
    </template>
  </main>
  <ConfirmDialog
    :open="leaveOpen"
    title="离开尚未保存的创作？"
    description="内容尚未保存或仍在上传。本地恢复副本仅对当前账号可用；建议先保存草稿。"
    @cancel="decideLeave(false)"
    @confirm="decideLeave(true)"
  />
</template>
<style scoped>
.editor-page {
  max-width: 960px;
}
header,
footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
}
.title-field {
  display: block;
  margin: 24px 0;
  font-size: 13px;
  color: var(--muted);
}
.title-field input {
  display: block;
  width: 100%;
  margin-top: 8px;
  padding: 12px;
  border: 1px solid var(--border);
  border-radius: 10px;
  background: var(--surface);
  font-size: 20px;
  color: var(--text);
}
.upload-zone {
  padding: 16px;
  border: 1px dashed var(--border);
  border-radius: 12px;
  background: var(--surface);
  margin-bottom: 24px;
}
.upload-zone > p {
  margin-top: 0;
  color: var(--muted);
}
.media-list {
  display: flex;
  gap: 12px;
  overflow: auto;
  margin-top: 12px;
}
.media-list article {
  width: 144px;
  flex-shrink: 0;
  font-size: 12px;
}
.media-list img {
  object-fit: cover;
  border-radius: 8px;
  width: 144px;
  height: 120px;
}
.media-list button,
.tag button,
.recovery button {
  border: 0;
  background: none;
  padding: 6px;
  color: var(--accent-hover);
  min-height: 36px;
}
.media-list p {
  margin: 4px 0;
}
.tag-editor {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  align-items: center;
  margin-top: 24px;
}
.tag-editor input {
  padding: 10px;
  border: 1px solid var(--border);
  border-radius: 10px;
  max-width: 100%;
  min-width: 0;
}
.error {
  color: var(--danger);
}
.editor-label {
  display: block;
  margin-bottom: 8px;
  color: var(--muted);
  font-size: 13px;
}
footer {
  justify-content: flex-end;
  margin: 24px 0;
}
.recovery {
  padding: 12px;
  background: #fff4df;
  border-radius: 10px;
}
.editor-page :deep(.ql-container) {
  min-height: 280px;
  background: var(--surface);
  font: inherit;
  border-color: var(--border);
  border-radius: 0 0 10px 10px;
}
.editor-page :deep(.ql-toolbar) {
  background: var(--surface);
  border-color: var(--border);
  border-radius: 10px 10px 0 0;
}
.editor-page :deep(.ql-editor) {
  min-height: 280px;
  overflow-wrap: anywhere;
}
.editor-page :deep(.ql-tooltip) {
  left: 0 !important;
  max-width: 100%;
  white-space: normal;
}
</style>
