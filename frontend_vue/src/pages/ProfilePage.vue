<script setup lang="ts">
import { computed, ref, watch, onBeforeUnmount, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { LoginUser, Post, CommentRecord } from '../types'
import { apiRequest } from '../api/client'
import type { Paged } from '../api/community'
import { getUserProfileStatsApi, toggleAuthorFollowApi } from '../api/community'
import { updateProfileApi } from '../api/auth'
import { uploadImage } from '../api/media'
import HomePostCard from '../components/home/HomePostCard.vue'
import UiState from '../components/ui/UiState.vue'
import BaseButton from '../components/ui/BaseButton.vue'
import UserAvatar from '../components/ui/UserAvatar.vue'
import ReportDialog from '../components/ReportDialog.vue'
import ConfirmDialog from '../components/ui/ConfirmDialog.vue'
const props = defineProps<{ viewer: LoginUser | null; entities: Post[] }>()
const emit = defineEmits<{
  loaded: [posts: Post[]]
  updated: [user: LoginUser]
  login: []
  open: [id: number]
  like: [id: number]
  favorite: [id: number]
  follow: [id: number]
  'following-changed': [authorId: number, isFollowing: boolean]
  share: [id: number]
}>()
const route = useRoute(),
  router = useRouter(),
  profile = ref<
    LoginUser & {
      totalLikes?: number
      isFollowing?: boolean
      isBlocked?: boolean
      isMuted?: boolean
    }
  >(),
  pending = ref(false),
  error = ref(''),
  page = ref(0),
  hasMore = ref(false),
  ids = ref<number[]>([]),
  people = ref<LoginUser[]>([]),
  comments = ref<CommentRecord[]>([]),
  actionPending = ref(false),
  editing = ref(false),
  reporting = ref(false)
const sessionOwner = ref(props.viewer?.id)
watch(() => props.viewer?.id, (value) => {
  if (value) sessionOwner.value = value
})
const id = computed(() => Number(route.params.id || props.viewer?.id || sessionOwner.value)),
  self = computed(() => id.value === (props.viewer?.id || sessionOwner.value))
const tab = computed(() =>
  route.path === '/bookmarks' ? 'bookmarks' : String(route.query.tab || 'posts')
)
const status = computed(() => String(route.query.status || ''))
const tabs = computed(() =>
  self.value
    ? ['posts', 'bookmarks', 'comments', 'followers', 'following']
    : ['posts', 'followers', 'following']
)
const statusLabels: Record<string, string> = {
  '': '全部',
  approved: '已公开',
  pending: '待复核',
  rejected: '已驳回',
  offline: '已下架'
}
const labels: Record<string, string> = {
  posts: '作品',
  bookmarks: '收藏',
  comments: '我的评论',
  followers: '粉丝',
  following: '关注'
}
const list = computed(() =>
  ids.value.map((id) => props.entities.find((p) => p.id === id)).filter((p): p is Post => !!p)
)
const name = ref(''),
  signature = ref(''),
  avatar = ref(''),
  gender = ref<'male' | 'female' | 'private'>('private'),
  avatarPending = ref(false),
  confirmation = ref<'block' | 'mute'>()
let version = 0,
  controller: AbortController | undefined
const load = async (reset = false) => {
  if (!id.value) {
    emit('login')
    return
  }
  if (pending.value && !reset) return
  if (reset) {
    version++
    controller?.abort()
    page.value = 0
    ids.value = []
    people.value = []
    comments.value = []
  }
  const current = version
  controller = new AbortController()
  pending.value = true
  error.value = ''
  try {
    const result = await getUserProfileStatsApi(id.value)
    if (current !== version) return
    profile.value = result
    if (!self.value && ['bookmarks', 'comments'].includes(tab.value)) {
      await router.replace({ path: `/u/${id.value}`, query: { tab: 'posts' } })
      return
    }
    const endpoint =
      tab.value === 'posts'
        ? self.value
          ? '/users/me/posts'
          : `/community/users/${id.value}/posts`
        : tab.value === 'bookmarks'
          ? '/users/me/bookmarks'
          : tab.value === 'comments'
            ? '/users/me/comments'
            : `/community/users/${id.value}/${tab.value}`
    const query = new URLSearchParams({ page: String(page.value + 1), status: status.value })
    const data = await apiRequest<Paged<Post | LoginUser | CommentRecord>>(`${endpoint}?${query}`, {
      signal: controller.signal
    })
    if (current !== version) return
    if (['posts', 'bookmarks'].includes(tab.value)) {
      emit('loaded', data.items as Post[])
      ids.value = [...new Set([...ids.value, ...data.items.map((i) => i.id)])]
    } else if (tab.value === 'comments') comments.value.push(...(data.items as CommentRecord[]))
    else people.value.push(...(data.items as LoginUser[]))
    page.value = data.pagination.page
    hasMore.value = data.pagination.hasMore
  } catch (e) {
    if (current === version && !(e instanceof Error && e.name === 'AbortError'))
      error.value = e instanceof Error ? e.message : '资料加载失败'
  } finally {
    if (current === version) pending.value = false
  }
}
watch(
  () => [id.value, tab.value, status.value, props.viewer?.id],
  () => load(true),
  { immediate: true }
)

const follow = async () => {
  if (!props.viewer) {
    emit('login')
    return
  }
  if (actionPending.value) return
  const current = version
  actionPending.value = true
  try {
    const result = await toggleAuthorFollowApi(id.value, !profile.value?.isFollowing)
    if (current !== version) return
    emit('following-changed', result.authorId, result.isFollowing)
    await load(true)
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '操作失败'
  } finally {
    actionPending.value = false
  }
}
const relation = async () => {
  if (!props.viewer) {
    emit('login')
    return
  }
  if (!confirmation.value || actionPending.value) return
  const current = version
  actionPending.value = true
  try {
    await apiRequest(`/users/me/${confirmation.value === 'block' ? 'blocks' : 'mutes'}`, {
      method: 'POST',
      body: JSON.stringify({ userId: id.value })
    })
    if (current !== version) return
    confirmation.value = undefined
    await load(true)
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '关系操作失败'
  } finally {
    actionPending.value = false
  }
}
const beginEdit = () => {
  name.value = props.viewer?.name || ''
  signature.value = props.viewer?.signature || ''
  avatar.value = props.viewer?.avatarUrl || ''
  gender.value = props.viewer?.gender || 'private'
  editing.value = true
}
const uploadAvatar = async (event: Event) => {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  const current = version
  avatarPending.value = true
  try {
    const asset = await uploadImage(file, () => {}, new AbortController().signal)
    if (current === version) avatar.value = asset.url
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '头像上传失败'
  } finally {
    avatarPending.value = false
  }
}
const save = async () => {
  if (actionPending.value || avatarPending.value) return
  const current = version
  actionPending.value = true
  try {
    const result = await updateProfileApi({
      name: name.value,
      signature: signature.value,
      avatarUrl: avatar.value,
      gender: gender.value
    })
    if (current !== version) return
    emit('updated', result)
    editing.value = false
    await load(true)
  } catch (e) {
    if (current === version) error.value = e instanceof Error ? e.message : '保存失败'
  } finally {
    actionPending.value = false
  }
}
const author = (payload: { userId?: number }) => {
  if (payload.userId) router.push(`/u/${payload.userId}`)
}
onMounted(()=>{if(route.name==='settings-profile')beginEdit()})
onBeforeUnmount(() => {
  version++
  controller?.abort()
})
</script>
<template>
  <main class="page-container profile-page">
    <header v-if="profile" class="profile-header">
      <UserAvatar :src="profile.avatarUrl" :name="profile.name" :size="88" />
      <div class="profile-heading">
        <h1>{{ profile.name }}</h1>
        <p>{{ profile.signature || '记录生活，与灵感相遇。' }}</p>
        <div class="profile-stats">
          <RouterLink :to="{ path: `/u/${id}`, query: { tab: 'followers' } }"
            >{{ profile.fans }} 粉丝</RouterLink
          ><RouterLink :to="{ path: `/u/${id}`, query: { tab: 'following' } }"
            >{{ profile.follows }} 关注</RouterLink
          ><span>{{ profile.totalLikes || 0 }} 获赞</span>
        </div>
      </div>
      <div class="profile-actions">
        <template v-if="self"
          ><BaseButton @click="beginEdit">编辑资料</BaseButton
          ><RouterLink to="/settings/account" class="text-button">账号设置</RouterLink
          ><RouterLink to="/drafts" class="text-button">草稿箱</RouterLink></template
        ><template v-else
          ><BaseButton :pending="actionPending" @click="follow">{{
            profile.isFollowing ? '已关注' : '关注'
          }}</BaseButton
          ><button class="text-button" @click="confirmation = 'mute'">屏蔽</button
          ><button class="text-button" @click="confirmation = 'block'">拉黑</button
          ><button class="text-button" @click="reporting = true">举报用户</button></template
        >
      </div>
    </header>
    <nav class="profile-tabs" aria-label="个人主页分类">
      <RouterLink
        v-for="item in tabs"
        :key="item"
        :to="{ path: `/u/${id}`, query: { tab: item } }"
        :class="{ active: tab === item }"
        >{{ labels[item] }}</RouterLink
      >
    </nav>
    <div v-if="self && tab === 'posts'" class="status-tabs">
      <RouterLink
        v-for="state in ['', 'approved', 'pending', 'rejected', 'offline']"
        :key="state"
        :to="{ path: `/u/${id}`, query: { tab: 'posts', status: state || undefined } }"
        :class="{ active: status === state }"
        >{{ statusLabels[state] }}</RouterLink
      >
    </div>
    <UiState v-if="pending && !page" kind="loading" /><UiState
      v-if="error"
      kind="error"
      :description="error"
      @retry="load(true)"
    />
    <div v-if="['posts', 'bookmarks'].includes(tab)" class="profile-grid">
      <div v-for="post in list" :key="post.id">
        <HomePostCard
          :post="post"
          @open-detail="emit('open', $event)"
          @toggle-post-like="emit('like', $event)"
          @toggle-post-favorite="emit('favorite', $event)"
          @toggle-post-follow="emit('follow', $event)"
          @share-post="emit('share', $event)"
          @open-author-profile="author"
        />
        <div v-if="self" class="manage-row">
          <span>{{ statusLabels[post.moderationStatus || 'approved'] }}</span
          ><RouterLink :to="`/edit/${post.id}`">编辑</RouterLink
          ><RouterLink
            v-if="post.moderationStatus === 'offline' || post.moderationStatus === 'rejected'"
            :to="{ path: '/reports', query: { appealPost: post.id } }"
            >原因 / 复核 / 申诉</RouterLink
          >
        </div>
        <p v-if="self && post.reviewReason" class="review-reason">原因：{{ post.reviewReason }}</p>
      </div>
    </div>
    <article v-for="person in people" :key="person.id" class="person">
      <RouterLink :to="`/u/${person.id}`"
        ><UserAvatar :name="person.name" :src="person.avatarUrl" /><span>{{
          person.name
        }}</span></RouterLink
      ><RouterLink :to="`/u/${person.id}`" class="text-button">查看主页</RouterLink>
    </article>
    <article v-for="comment in comments" :key="comment.id" class="history-comment">
      <RouterLink :to="{ path: `/detail/${comment.postId}`, query: { commentId: comment.id } }"
        >{{ comment.postTitle || '查看作品' }}
        <p>{{ comment.content }}</p></RouterLink
      ><time>{{ new Date(comment.createdAt || comment.date).toLocaleString() }}</time>
    </article>
    <UiState
      v-if="!pending && !error && !list.length && !people.length && !comments.length"
      kind="empty"
      title="这里还没有内容"
    />
    <BaseButton v-if="hasMore" :pending="pending" @click="load()">加载更多</BaseButton>
    <el-dialog v-model="editing" title="编辑资料" width="min(560px,94vw)"
      ><form class="edit-profile" @submit.prevent="save">
        <label>昵称<input v-model="name" maxlength="80" required /></label
        ><label>简介<textarea v-model="signature" maxlength="300" /></label
        ><label
          >头像<input
            type="file"
            accept="image/png,image/jpeg,image/webp"
            @change="uploadAvatar" /></label
        ><UserAvatar v-if="avatar" :src="avatar" :name="name" :size="64" /><label
          >性别（仅本人）<select v-model="gender">
            <option value="private">保密</option>
            <option value="female">女</option>
            <option value="male">男</option>
          </select></label
        >
        <p v-if="error" role="alert">{{ error }}</p>
        <BaseButton type="submit" variant="primary" :pending="actionPending || avatarPending"
          >保存资料</BaseButton
        >
      </form></el-dialog
    >
    <ReportDialog
      :open="reporting"
      target-type="user"
      :target-id="id"
      :viewer-id="viewer?.id"
      @close="reporting = false"
      @login="emit('login')"
    />
    <ConfirmDialog
      :open="!!confirmation"
      :title="confirmation === 'block' ? '拉黑这位用户？' : '屏蔽这位用户？'"
      :description="
        confirmation === 'block'
          ? '双方将无法新增关注、评论和通知。公共作品仍可在未登录时访问，拉黑不是隐私访问控制。'
          : '仅从你的内容消费列表中隐藏，随时可在隐私设置解除。'
      "
      :pending="actionPending"
      @cancel="confirmation = undefined"
      @confirm="relation"
    />
  </main>
</template>
<style scoped>
.profile-header {
  display: flex;
  align-items: center;
  gap: 24px;
  margin-bottom: 28px;
}
.profile-heading {
  flex: 1;
  min-width: 0;
}
.profile-heading h1 {
  margin: 0;
}
.profile-heading p {
  font-size: 14px;
  color: var(--muted);
}
.profile-stats {
  display: flex;
  gap: 24px;
  font-size: 13px;
}
.profile-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  max-width: 260px;
}
.profile-tabs,
.status-tabs {
  display: flex;
  gap: 24px;
  overflow: auto;
  margin: 24px 0;
}
.profile-tabs a {
  padding: 8px 0;
  min-height: 44px;
  white-space: nowrap;
  border-bottom: 2px solid transparent;
  color: var(--muted);
}
.profile-tabs .active {
  border-color: var(--accent);
  color: var(--text);
}
.status-tabs {
  font-size: 12px;
  gap: 14px;
}
.status-tabs a {
  white-space: nowrap;
}
.status-tabs .active {
  color: var(--accent-hover);
}
.profile-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
  gap: 20px;
}
.person,
.person > a {
  display: flex;
  align-items: center;
  gap: 12px;
}
.person {
  justify-content: space-between;
  padding: 16px 0;
  border-bottom: 1px solid var(--border);
}
.history-comment {
  padding: 20px 0;
  border-bottom: 1px solid var(--border);
}
time {
  font-size: 12px;
  color: var(--muted);
}
.manage-row {
  display: flex;
  gap: 12px;
  flex-wrap: wrap;
  font-size: 12px;
  margin-top: 8px;
  color: var(--muted);
}
.manage-row a {
  color: var(--accent-hover);
}
.review-reason {
  font-size: 12px;
  color: var(--warning);
}
.edit-profile label {
  display: block;
  margin: 16px 0;
}
.edit-profile input:not([type='file']),
.edit-profile textarea,
.edit-profile select {
  display: block;
  width: 100%;
  min-height: 44px;
  border: 1px solid var(--border);
  padding: 10px;
  border-radius: var(--radius-control);
  background: var(--surface);
  color: var(--text);
}
@media (max-width: 767px) {
  .profile-header {
    flex-wrap: wrap;
    gap: 16px;
  }
  .profile-actions {
    max-width: 100%;
  }
  .profile-stats {
    gap: 16px;
  }
  .profile-grid {
    grid-template-columns: repeat(2, minmax(0, 1fr));
    gap: 16px 10px;
  }
}
</style>
