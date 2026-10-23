<script setup lang="ts">
import { ref, watch, onBeforeUnmount, nextTick } from 'vue'
import type { CommentRecord } from '../../types'
import type { Paged } from '../../api/community'
import { apiRequest } from '../../api/client'
import UiState from '../ui/UiState.vue'
import BaseButton from '../ui/BaseButton.vue'
import UserAvatar from '../ui/UserAvatar.vue'
import ReportDialog from '../ReportDialog.vue'
import ConfirmDialog from '../ui/ConfirmDialog.vue'
const props = defineProps<{ postId: number; viewerId?: number; focusId?: number }>()
const emit = defineEmits<{ changed: []; login: [] }>()
const roots = ref<CommentRecord[]>([]),
  replyMap = ref<
    Record<number, { items: CommentRecord[]; page: number; hasMore: boolean; pending: boolean }>
  >({})
const page = ref(0),
  hasMore = ref(false),
  pending = ref(false),
  error = ref(''),
  sort = ref('latest'),
  text = ref(''),
  sending = ref(false),
  replyTo = ref<CommentRecord>(),
  requestKey = ref(crypto.randomUUID()),
  deleting = ref<CommentRecord>(),
  removing = ref(false),
  reporting = ref<CommentRecord>()
const textarea = ref<HTMLTextAreaElement | null>(null),
  actionPending = ref<Set<number>>(new Set())
let version = 0,
  controller: AbortController | undefined,
  contextVersion = 0,
  viewerOwner = props.viewerId
const load = async (reset = false) => {
  if (pending.value && !reset) return
  if (reset) {
    version++
    controller?.abort()
    roots.value = []
    page.value = 0
    replyMap.value = {}
  }
  const current = version
  controller = new AbortController()
  pending.value = true
  error.value = ''
  try {
    const result = await apiRequest<Paged<CommentRecord>>(
      `/community/posts/${props.postId}/comments?page=${page.value + 1}&sort=${sort.value}`,
      { signal: controller.signal }
    )
    if (current !== version) return
    roots.value = [...new Map([...roots.value, ...result.items].map((c) => [c.id, c])).values()]
    page.value = result.pagination.page
    hasMore.value = result.pagination.hasMore
    if (reset && props.focusId) await locate(props.focusId)
  } catch (e) {
    if (current === version && !(e instanceof Error && e.name === 'AbortError'))
      error.value = e instanceof Error ? e.message : '评论加载失败'
  } finally {
    if (current === version) pending.value = false
  }
}
const replies = async (root: CommentRecord) => {
  if (!replyMap.value[root.id])
    replyMap.value[root.id] = { items: [], page: 0, hasMore: true, pending: false }
  const state = replyMap.value[root.id]!
  if (state.pending || !state.hasMore) return
  state.pending = true
  const current=version
  try {
    const result = await apiRequest<Paged<CommentRecord>>(
      `/community/comments/${root.id}/replies?page=${state.page + 1}`
    )
    if(current!==version)return
    state.items = [...new Map([...state.items, ...result.items].map((c) => [c.id, c])).values()]
    state.page = result.pagination.page
    state.hasMore = result.pagination.hasMore
  } catch (e) {
    if(current===version)error.value = e instanceof Error ? e.message : '回复加载失败'
  } finally {
    state.pending = false
  }
}
const lastAttempt = ref('')
const send = async () => {
  if (sending.value || !text.value.trim()) return
  if (!props.viewerId) {
    emit('login')
    return
  }
  const sentText=text.value,sentReply=replyTo.value?.id,sentPost=props.postId
  const context = contextVersion
  const attempt = JSON.stringify({ text: text.value, reply: replyTo.value?.id })
  if (lastAttempt.value && lastAttempt.value !== attempt) requestKey.value = crypto.randomUUID()
  lastAttempt.value = attempt
  sending.value = true
  error.value = ''
  try {
    await apiRequest(`/community/posts/${props.postId}/comments`, {
      method: 'POST',
      body: JSON.stringify({
        content: text.value,
        replyToId: replyTo.value?.id || null,
        requestKey: requestKey.value
      })
    })
    if(context!==contextVersion||props.postId!==sentPost)return
    if(text.value===sentText)text.value=''
    if(replyTo.value?.id===sentReply)replyTo.value=undefined
    requestKey.value = crypto.randomUUID()
    emit('changed')
    await load(true)
  } catch (e) {
    if(context===contextVersion)error.value = e instanceof Error ? e.message : '发送失败，输入已保留'
  } finally {
    if(context===contextVersion)sending.value = false
  }
}
const like = async (comment: CommentRecord) => {
  if (!props.viewerId) {
    emit('login')
    return
  }
  if (actionPending.value.has(comment.id)) return
  const context = contextVersion
  actionPending.value.add(comment.id)
  try {
    const result = await apiRequest<{ likes: number; isLiked: boolean }>(
      `/community/comments/${comment.id}/like`,
      { method: 'POST', body: JSON.stringify({ isLiked: !comment.isLiked }) }
    )
    if(context===contextVersion)Object.assign(comment, result)
  } catch (e) {
    if(context===contextVersion)error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    if(context===contextVersion)actionPending.value.delete(comment.id)
  }
}
const remove = async () => {
  if (!deleting.value || removing.value) return
  const context = contextVersion, commentId = deleting.value.id
  removing.value = true
  try {
    await apiRequest(`/community/comments/${commentId}`, { method: 'DELETE' })
    if(context!==contextVersion)return
    deleting.value = undefined
    emit('changed')
    await load(true)
  } catch (e) {
    if(context===contextVersion)error.value = e instanceof Error ? e.message : '删除失败'
  } finally {
    if(context===contextVersion)removing.value = false
  }
}
const reply = (comment: CommentRecord) => {
  replyTo.value = comment
  textarea.value?.focus()
}
watch(()=>props.postId,()=>{
  contextVersion++
  sending.value=false;removing.value=false;actionPending.value.clear();deleting.value=undefined;reporting.value=undefined
  text.value='';replyTo.value=undefined;requestKey.value=crypto.randomUUID();lastAttempt.value=''
  load(true)
},{immediate:true})
watch(sort,()=>load(true))
watch(()=>props.viewerId,(next)=>{
  if(next!==undefined&&viewerOwner!==undefined&&next!==viewerOwner){
    contextVersion++
    text.value='';replyTo.value=undefined;requestKey.value=crypto.randomUUID();lastAttempt.value=''
    sending.value=false;removing.value=false;actionPending.value.clear();deleting.value=undefined;reporting.value=undefined
  }
  if(next!==undefined)viewerOwner=next
  void load(true)
})
const locate = async (id: number) => {
  const current=version,postId=props.postId
  try {
    const target = await apiRequest<CommentRecord>(`/community/comments/${id}/detail`)
    const root = target.rootId
      ? await apiRequest<CommentRecord>(`/community/comments/${target.rootId}/detail`)
      : target
    if(current!==version||target.postId!==postId)return
    if (!roots.value.some((c) => c.id === root.id)) roots.value.unshift(root)
    if (target.rootId) {
      const current = replyMap.value[root.id]?.items || []
      replyMap.value[root.id] = {
        items: [...new Map([...current, target].map((c) => [c.id, c])).values()],
        page: 0,
        hasMore: true,
        pending: false
      }
    }
    await nextTick()
    document.getElementById('comment-' + id)?.scrollIntoView({ block: 'center' })
  } catch (e) {
    if(current===version)error.value = e instanceof Error ? e.message : '目标评论不可用'
  }
}
watch(
  () => props.focusId,
  (id) => {
    if (id) void locate(id)
  },
  { immediate: true }
)
onBeforeUnmount(() => {
  contextVersion++
  version++
  controller?.abort()
})
</script>
<template>
  <section class="discussion" aria-label="评论区">
    <h2>评论与讨论</h2>
    <form @submit.prevent="send">
      <p v-if="replyTo" class="reply-target">
        回复 @{{ replyTo.author }}
        <button type="button" @click="replyTo = undefined">取消回复</button>
      </p>
      <label class="sr-only" :for="`reply-input-${postId}`">写评论</label
      ><textarea
        :id="`reply-input-${postId}`"
        ref="textarea"
        v-model="text" :readonly="sending"
        maxlength="2000"
        placeholder="分享你的想法…"
      />
      <div class="send-row">
        <span class="muted">{{ text.length }} / 2000</span
        ><BaseButton type="submit" variant="primary" :pending="sending" :disabled="!text.trim()">{{
          viewerId ? '发送评论' : '登录后评论'
        }}</BaseButton>
      </div>
    </form>
    <div class="sort">
      <label
        >排序
        <select v-model="sort" :disabled="sending">
          <option value="latest">最新</option>
          <option value="hot">热门</option>
        </select></label
      >
    </div>
    <UiState v-if="pending && !roots.length" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    />
    <p v-if="!pending && !error && !roots.length" class="muted">还没有评论，留下第一条想法。</p>
    <template v-for="root in roots" :key="root.id"
      ><div
        v-for="item in [root, ...(replyMap[root.id]?.items || [])]"
        :id="`comment-${item.id}`"
        :key="item.id"
        class="comment"
        :class="{ child: !!item.rootId }"
      >
        <UserAvatar :src="item.authorAvatarUrl" :name="item.author" :size="28" />
        <div class="comment-body">
          <RouterLink v-if="item.authorId" :to="`/u/${item.authorId}`" class="comment-author">{{
            item.author
          }}</RouterLink
          ><span v-else class="muted">{{ item.author }}</span>
          <p>
            <span v-if="item.replyToId" class="muted">回复 @{{ item.replyToName }}：</span
            >{{ item.content }}
          </p>
          <div class="comment-actions">
            <time>{{ new Date(item.createdAt || item.date).toLocaleString() }}</time
            ><button v-if="!item.deleted" @click="reply(item)">回复</button
            ><button
              v-if="!item.deleted"
              :disabled="actionPending.has(item.id)"
              :aria-pressed="item.isLiked"
              @click="like(item)"
            >
              {{ item.isLiked ? '已赞' : '赞' }} {{ item.likes }}</button
            ><button v-if="!item.deleted" @click="reporting = item">举报</button
            ><button v-if="item.isMine" @click="deleting = item">删除</button>
          </div>
        </div>
      </div>
      <button
        v-if="root.replyCount && (!replyMap[root.id] || replyMap[root.id]?.hasMore)"
        class="text-button more-replies"
        :disabled="replyMap[root.id]?.pending"
        @click="replies(root)"
      >
        展开更多回复（{{ root.replyCount }}）
      </button></template
    >
    <ReportDialog
      v-if="reporting"
      :open="true"
      target-type="comment"
      :target-id="reporting.id"
      :viewer-id="viewerId"
      @close="reporting = undefined"
      @login="emit('login')"
    />
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多评论</BaseButton
    ><ConfirmDialog
      :open="!!deleting"
      title="删除这条评论？"
      description="正文将不可用，有回复时保留占位与讨论上下文。"
      :pending="removing"
      @cancel="deleting = undefined"
      @confirm="remove"
    />
  </section>
</template>
<style scoped>
.discussion {
  border-top: 1px solid var(--border);
  margin-top: 28px;
  padding-top: 20px;
}
h2 {
  font-size: 18px;
}
textarea {
  display: block;
  width: 100%;
  min-height: 100px;
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px;
  resize: vertical;
  background: var(--bg);
  color: var(--text);
}
.send-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin: 10px 0 20px;
  font-size: 12px;
}
.sort {
  text-align: right;
  font-size: 13px;
  margin-bottom: 16px;
}
.sort select {
  border: 1px solid var(--border);
  border-radius: 8px;
  min-height: 36px;
  background: white;
  padding: 4px 8px;
}
.comment {
  display: flex;
  gap: 10px;
  padding: 16px 0;
  border-top: 1px solid var(--border);
}
.comment.child {
  margin-left: 34px;
}
.comment-body {
  min-width: 0;
  flex: 1;
}
.comment-author {
  font-size: 13px;
  font-weight: 650;
}
.comment p {
  margin: 6px 0;
  font-size: 14px;
  white-space: pre-wrap;
}
.comment-actions {
  display: flex;
  gap: 12px;
  align-items: center;
  flex-wrap: wrap;
  font-size: 11px;
  color: var(--muted);
}
.comment-actions button,
.reply-target button {
  border: 0;
  background: none;
  padding: 6px 2px;
  min-height: 36px;
  color: inherit;
}
.comment-actions button[aria-pressed='true'] {
  color: var(--accent-hover);
}
.more-replies {
  margin-left: 34px;
}
.reply-target {
  font-size: 13px;
  color: var(--accent-hover);
}
</style>
