<script setup lang="ts">
import {
  computed,
  defineAsyncComponent,
  nextTick,
  onMounted,
  onBeforeUnmount,
  ref,
  watch
} from 'vue'
import { useRoute, useRouter, type LocationQuery } from 'vue-router'
import { ElMessage } from 'element-plus'
import AppShell from './components/AppShell.vue'
import LoginModal from './components/LoginModal.vue'
import RegisterModal from './components/RegisterModal.vue'
import UiState from './components/ui/UiState.vue'
import { useAuthState } from './composables/useAuthState'
import {
  getPostApi,
  togglePostLikeApi,
  togglePostFavoriteApi,
  toggleAuthorFollowApi,
  trackPostReadApi,
  trackPostShareApi
} from './api/community'
import type { Post } from './types'

const FeedPage = defineAsyncComponent(() => import('./pages/FeedPage.vue'))
const SearchPage = defineAsyncComponent(() => import('./pages/SearchPage.vue'))
const DetailPage = defineAsyncComponent(() => import('./pages/DetailPage.vue'))
const ProfilePage = defineAsyncComponent(() => import('./pages/ProfilePage.vue'))
const PublishPostContent = defineAsyncComponent(() => import('./components/PublishPostContent.vue'))
const DraftsPage = defineAsyncComponent(() => import('./pages/DraftsPage.vue'))
const NotificationsPage = defineAsyncComponent(() => import('./pages/NotificationsPage.vue'))
const ReportsPage = defineAsyncComponent(() => import('./pages/ReportsPage.vue'))
const PrivacyPage = defineAsyncComponent(() => import('./pages/PrivacyPage.vue'))
const AccountSettings = defineAsyncComponent(() => import('./components/AccountSettings.vue'))
const AuthTokenPage = defineAsyncComponent(() => import('./components/AuthTokenPage.vue'))
const AdminConsole = defineAsyncComponent(() => import('./components/admin/AdminConsole.vue'))
const route = useRoute(),
  router = useRouter(),
  posts = ref<Post[]>([]),
  editing = ref<Post>(),
  editPending = ref(false),
  editError = ref('')
const {
  showLoginModal,
  showRegisterModal,
  account,
  password,
  registerEmail,
  registerPassword,
  registerConfirmPassword,
  authPending,
  authError,
  authMessage,
  authReady,
  authConfig,
  loginUser,
  canLogin,
  isLoggedIn,
  isRegisterEmailValid,
  isRegisterPasswordMatch,
  canRegister,
  openLoginModal,
  closeLoginModal,
  openRegisterModal,
  closeRegisterModal,
  backToLogin,
  submitLogin,
  submitRegister,
  submitLogout,
  refreshSession
} = useAuthState({ getUserStats: () => ({ fans: 0, follows: 0 }) })
const editorOwner = ref<number>()
let accountVersion = 0
watch(
  () => loginUser.value?.id,
  (id) => {
    accountVersion++
    if (id) editorOwner.value = id
  },
  { immediate: true }
)
const isAdmin = computed(() => String(route.name || '').startsWith('admin-'))
const detailId = computed(() => (route.name === 'detail' ? Number(route.params.id) : 0))
const background = ref<string | null>(null),
  listLocation = ref<{ path: string; query: LocationQuery }>({
    path: route.path,
    query: { ...route.query }
  })
const sourceFocus = ref<HTMLElement | null>(null)
let listVisited = false
const isList = (name: unknown) => ['home', 'following', 'search'].includes(String(name))
watch(
  // The initial route starts at '/' without a name; wait for router resolution.
  () => route.name ? route.fullPath : null,
  async (_, old) => {
    if (isList(route.name)) listVisited = true
    if (
      isList(route.name) &&
      JSON.stringify(listLocation.value) !==
        JSON.stringify({ path: route.path, query: { ...route.query } })
    )
      listLocation.value = { path: route.path, query: { ...route.query } }
    if (route.name !== 'detail') {
      background.value = null
      if (old?.startsWith('/detail/'))
        await nextTick().then(() => sourceFocus.value?.focus({ preventScroll: true }))
    } else if (window.history.state.background && listVisited)
      background.value = String(window.history.state.background)
    else background.value = null
  },
  { immediate: true }
)
const upsertPosts = (incoming: Post[]) => {
  for (const post of incoming) {
    const current = posts.value.find((p) => p.id === post.id)
    if (current) Object.assign(current, post)
    else posts.value.push(post)
  }
}
const openDetail = (id: number) => {
  const from = isList(route.name) ? route.fullPath : null
  sourceFocus.value = document.activeElement instanceof HTMLElement ? document.activeElement : null
  background.value = from
  if (loginUser.value) void trackPostReadApi(id).catch(() => {})
  router.push({ path: `/detail/${id}`, state: from ? { background: from } : undefined })
}
const closeDetail = () => {
  if (background.value) router.back()
  else router.push('/')
}
const pendingActions = ref<Set<string>>(new Set())
const syncFollowing = (authorId: number, isFollowing: boolean) => {
  posts.value.forEach((post) => {
    if (post.authorId === authorId) post.isFollowingAuthor = isFollowing
  })
}
const interact = async (id: number, action: 'like' | 'favorite' | 'follow') => {
  if (!loginUser.value) {
    openLoginModal()
    return
  }
  const post = posts.value.find((p) => p.id === id)
  if (!post) return
  const key = `${action}:${action === 'follow' ? post.authorId : id}`
  if (pendingActions.value.has(key)) return
  pendingActions.value.add(key)
  const current = accountVersion
  try {
    if (action === 'like') {
      const data = await togglePostLikeApi(id, !post.isLiked)
      if (current !== accountVersion) return
      post.isLiked = data.isLiked
      post.likes = data.likes
    }
    if (action === 'favorite') {
      const data = await togglePostFavoriteApi(id, !post.isFavorited)
      if (current !== accountVersion) return
      post.isFavorited = data.isFavorited
    }
    if (action === 'follow') {
      if (!post.authorId || post.authorId === loginUser.value.id) return
      const desired = !post.isFollowingAuthor
      const result = await toggleAuthorFollowApi(post.authorId, desired)
      if (current !== accountVersion) return
      syncFollowing(result.authorId, result.isFollowing)
    }
  } catch (e) {
    if (current === accountVersion) ElMessage.error(e instanceof Error ? e.message : '操作失败')
  } finally {
    pendingActions.value.delete(key)
  }
}
const share = async (id: number) => {
  const post = posts.value.find((p) => p.id === id)
  if (!post) return
  const url = new URL(`/detail/${id}`, window.location.origin).href
  try {
    if (navigator.share) await navigator.share({ title: post.title, text: post.summary, url })
    else {
      await navigator.clipboard.writeText(url)
      ElMessage.success('作品链接已复制')
    }
    if (loginUser.value) await trackPostShareApi(id)
  } catch (e) {
    if (!(e instanceof Error && e.name === 'AbortError')) ElMessage.error('分享未完成，请重试')
  }
}
const goPublish = () => {
  if (!loginUser.value) {
    router.push({ path: '/', query: { redirect: '/publish' } })
    return
  }
  router.push('/publish')
}
const login = async () => {
  await submitLogin()
}
const logout = async () => {
  try {
    await submitLogout()
    posts.value = []
    await router.push('/')
    editorOwner.value = undefined
  } catch (e) {
    ElMessage.error(e instanceof Error ? e.message : '退出失败，请重试')
  }
}
let editVersion = 0
watch(
  () => [route.name, route.params.id, authReady.value, editorOwner.value],
  async () => {
    if (route.name !== 'edit' || !authReady.value) return
    const version = ++editVersion
    editing.value = undefined
    editPending.value = true
    editError.value = ''
    try {
      const post = await getPostApi(Number(route.params.id), true)
      if (version === editVersion) {
        editing.value = post
        upsertPosts([post])
      }
    } catch (e) {
      if (version === editVersion) editError.value = e instanceof Error ? e.message : '作品不可用'
    } finally {
      if (version === editVersion) editPending.value = false
    }
  },
  { immediate: true }
)
watch(
  () => [authReady.value, isLoggedIn.value, route.query.redirect],
  () => {
    if (!authReady.value || isAdmin.value) return
    if (!loginUser.value && typeof route.query.redirect === 'string') {
      openLoginModal()
      return
    }
    const target = route.query.redirect
    if (
      loginUser.value &&
      typeof target === 'string' &&
      target.startsWith('/') &&
      !target.startsWith('//')
    )
      router.replace(target)
  }
)
const expired = () => {
  loginUser.value = null
  openLoginModal()
}
onMounted(async () => {
  window.addEventListener('session-expired', expired)
  await refreshSession()
})
onBeforeUnmount(() => {
  window.removeEventListener('session-expired', expired)
  editVersion++
})
</script>
<template>
  <AdminConsole v-if="isAdmin" />
  <AppShell v-else :user="loginUser" :registration-enabled="authConfig.registrationEnabled" @login="openLoginModal" @logout="logout">
    <UiState v-if="!authReady" kind="loading" />
    <template v-else>
      <FeedPage
        v-if="
          ['home', 'following'].includes(String(route.name)) ||
          (background && !background.startsWith('/search'))
        "
        :location="listLocation"
        :entities="posts"
        :viewer-id="loginUser?.id"
        @loaded="upsertPosts"
        @go-publish="goPublish"
        @open-detail="openDetail"
        @open-comment-detail="openDetail"
        @toggle-post-like="interact($event, 'like')"
        @toggle-post-favorite="interact($event, 'favorite')"
        @toggle-post-follow="interact($event, 'follow')"
        @share-post="share"
        @open-author-profile="$event.userId && router.push(`/u/${$event.userId}`)"
      />
      <SearchPage
        v-if="route.name === 'search' || background?.startsWith('/search')"
        :location="listLocation"
        :entities="posts"
        :viewer-id="loginUser?.id"
        @loaded="upsertPosts"
        @open="openDetail"
        @like="interact($event, 'like')"
        @favorite="interact($event, 'favorite')"
        @follow="interact($event, 'follow')"
        @share="share"
      />
      <DetailPage
        v-if="detailId"
        :post-id="detailId"
        :entities="posts"
        :viewer-id="loginUser?.id"
        :modal="!!background"
        @loaded="upsertPosts([$event])"
        @deleted="posts = posts.filter((p) => p.id !== $event)"
        @close="closeDetail"
        @login="openLoginModal"
        @like="interact($event, 'like')"
        @favorite="interact($event, 'favorite')"
        @follow="interact($event, 'follow')"
        @share="share"
      />
      <ProfilePage
        :key="`profile:${editorOwner}`"
        v-if="route.name === 'user' || route.name === 'bookmarks' || route.name === 'settings-profile'"
        :viewer="loginUser"
        :entities="posts"
        @loaded="upsertPosts"
        @updated="loginUser = $event"
        @following-changed="syncFollowing"
        @login="openLoginModal"
        @open="openDetail"
        @like="interact($event, 'like')"
        @favorite="interact($event, 'favorite')"
        @follow="interact($event, 'follow')"
        @share="share"
      />
      <PublishPostContent
        v-if="route.name === 'publish'"
        :key="`create:${editorOwner}`"
        :user-id="editorOwner"
        @saved="upsertPosts([$event])"
      />
      <template v-if="route.name === 'edit'"
        ><UiState v-if="editPending" kind="loading" /><UiState
          v-else-if="editError"
          kind="unavailable"
          :description="editError" /><PublishPostContent
          v-else-if="editing"
          :key="`${editing.id}:${editorOwner}`"
          mode="edit"
          :initial-post="editing"
          :user-id="editorOwner"
          @saved="upsertPosts([$event])"
      /></template>
      <DraftsPage v-if="route.name === 'drafts'" :key="`drafts:${editorOwner}`" />
      <NotificationsPage v-if="route.name === 'notifications'" :key="`notices:${editorOwner}`" />
      <PrivacyPage v-if="route.name === 'settings-privacy'" :key="`privacy:${editorOwner}`" />
      <ReportsPage v-if="route.name === 'reports'" :key="`reports:${editorOwner}`" />
      <AccountSettings
        :key="`account:${editorOwner}`"
        v-if="route.name === 'settings-account'"
        :user="loginUser"
        :email-available="authConfig.emailAvailable"
        @deactivated="logout"
      />
      <AuthTokenPage v-if="route.name === 'auth-token'" />
    </template>
    <LoginModal
      :visible="showLoginModal"
      :registration-enabled="authConfig.registrationEnabled"
      :email-available="authConfig.emailAvailable"
      :account="account"
      :password="password"
      :can-login="canLogin"
      :pending="authPending"
      :error="authError"
      @close="closeLoginModal"
      @update:account="account = $event"
      @update:password="password = $event"
      @login="login"
      @open-register="openRegisterModal"
    />
    <RegisterModal
      :visible="showRegisterModal"
      :email="registerEmail"
      :password="registerPassword"
      :confirm-password="registerConfirmPassword"
      :is-email-valid="isRegisterEmailValid"
      :is-password-match="isRegisterPasswordMatch"
      :can-register="canRegister"
      :pending="authPending"
      :error="authError"
      :message="authMessage"
      @close="closeRegisterModal"
      @update:email="registerEmail = $event"
      @update:password="registerPassword = $event"
      @update:confirm-password="registerConfirmPassword = $event"
      @register="submitRegister"
      @back-login="backToLogin"
    />
  </AppShell>
</template>
