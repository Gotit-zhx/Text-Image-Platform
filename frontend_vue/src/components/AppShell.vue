<script setup lang="ts">
import { computed, ref, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { apiRequest } from '../api/client'
import type { LoginUser } from '../types'
import AppIcon from './ui/AppIcon.vue'
import BaseButton from './ui/BaseButton.vue'
import UserAvatar from './ui/UserAvatar.vue'
const props = defineProps<{ user: LoginUser | null; registrationEnabled: boolean }>()
const emit = defineEmits<{ login: []; logout: [] }>()
const router = useRouter(),
  route = useRoute(),
  query = ref('')
watch(
  () => route.query.q,
  (q) => {
    query.value = String(q || '')
  },
  { immediate: true }
)
const nav = computed(() => [
  { label: '发现', icon: 'discover', path: '/' },
  { label: '关注', icon: 'following', path: '/following' },
  { label: '通知', icon: 'notifications', path: '/notifications', auth: true },
  { label: '收藏', icon: 'bookmark', path: '/bookmarks', auth: true },
  { label: '个人主页', icon: 'user', path: '/profile', auth: true },
  { label: '设置', icon: 'settings', path: '/settings/account', auth: true }
])
const active = (path: string) =>
  path === '/'
    ? route.path === '/'
    : path.includes('?')
      ? route.fullPath === path
      : route.path === path
const navigate = (item: { path: string; auth?: boolean }) => {
  if (item.auth && !props.user) {
    emit('login')
    return
  }
  router.push(item.path)
}
const search = () =>
  router.push({ path: '/search', query: { q: query.value.trim() || undefined, type: 'posts' } })
const unread = ref(0)
let poll: ReturnType<typeof setInterval> | undefined
let unreadVersion = 0
const fetchUnread = async () => {
  if (!props.user || document.hidden) return
  const viewerId = props.user.id
  const current = ++unreadVersion
  try {
    const result = await apiRequest<{ count: number }>('/notifications/unread')
    if(current===unreadVersion&&props.user?.id===viewerId)unread.value = result.count
  } catch {}
}
const visibility = () => {
  unreadVersion++
  if (poll) clearInterval(poll)
  if (props.user && !document.hidden) {
    void fetchUnread()
    poll = setInterval(fetchUnread, 30000)
  }
}
watch(
  () => props.user?.id,
  () => {
    unread.value = 0
    visibility()
  }
)
watch(
  () => route.fullPath,
  () => {
    void fetchUnread()
  }
)
onMounted(() => {
  visibility()
  document.addEventListener('visibilitychange', visibility)
  window.addEventListener('notifications-changed', fetchUnread)
})
onBeforeUnmount(() => {
  unreadVersion++
  if (poll) clearInterval(poll)
  document.removeEventListener('visibilitychange', visibility)
  window.removeEventListener('notifications-changed', fetchUnread)
})
</script>
<template>
  <a class="skip-link" href="#community-main">跳到内容</a>
  <aside class="shell-sidebar">
    <RouterLink class="brand" to="/" aria-label="百草园首页"
      ><AppIcon name="leaf" :size="30" /><span>百草园</span></RouterLink
    >
    <nav aria-label="主导航">
      <button
        v-for="item in nav"
        :key="item.label"
        class="nav-item"
        :class="{ active: active(item.path) }"
        :aria-label="item.label"
        :aria-current="active(item.path) ? 'page' : undefined"
        :title="item.label"
        @click="navigate(item)"
      >
        <AppIcon :name="item.icon" /><span
          >{{ item.label
          }}<small v-if="item.icon === 'notifications' && unread" class="badge">{{
            unread > 99 ? '99+' : unread
          }}</small></span
        >
      </button>
    </nav>
    <BaseButton
      class="publish-button"
      variant="primary"
      aria-label="发布图文"
      @click="navigate({ path: '/publish', auth: true })"
      ><AppIcon name="plus" /><span>发布图文</span></BaseButton
    >
    <div class="sidebar-account">
      <template v-if="user"
        ><button class="account-button" :aria-label="user.name" @click="navigate({ path: '/profile' })">
          <UserAvatar :src="user.avatarUrl" :name="user.name" /><span>{{ user.name }}</span></button
        ><button class="text-button logout" @click="emit('logout')">退出登录</button
        ><RouterLink v-if="user.isAdmin" class="text-button" to="/admin"
          >管理后台</RouterLink
        ></template
      ><BaseButton v-else @click="emit('login')"
        ><AppIcon name="user" /><span>{{ registrationEnabled ? '登录 / 注册' : '登录' }}</span></BaseButton
      >
    </div>
  </aside>
  <div class="shell-body">
    <header class="shell-header">
      <RouterLink class="mobile-brand" to="/">百草园</RouterLink>
      <form class="shell-search" role="search" @submit.prevent="search">
        <AppIcon name="search" :size="20" /><input
          v-model="query"
          aria-label="搜索帖子、作者和标签"
          placeholder="搜索帖子、作者和标签"
          type="search"
        /><button type="submit" aria-label="搜索">搜索</button>
      </form>
      <button
        class="header-account"
        :aria-label="user ? '我的主页' : '登录'"
        @click="user ? navigate({ path: '/profile' }) : emit('login')"
      >
        <UserAvatar v-if="user" :src="user.avatarUrl" :name="user.name" /><span v-else>登录</span>
      </button>
    </header>
    <div id="community-main" tabindex="-1"><slot /></div>
  </div>
  <nav class="mobile-nav" aria-label="手机主导航">
    <button
      v-for="item in [
        nav[0]!,
        nav[1]!,
        { label: '发布', icon: 'plus', path: '/publish', auth: true },
        nav[2]!,
        nav[4]!
      ]"
      :key="item.label"
      :class="{ active: active(item.path), create: item.icon === 'plus' }"
      @click="navigate(item)"
    >
      <AppIcon :name="item.icon" /><span>{{
        item.label === '个人主页' ? '我的' : item.label
      }}</span>
    </button>
  </nav>
</template>
<style scoped>
.badge {
  margin-left: 8px;
  border-radius: 999px;
  background: var(--accent);
  color: white;
  padding: 1px 5px;
  font-size: 10px;
}
.skip-link {
  position: fixed;
  top: -80px;
  left: 12px;
  z-index: 120;
  background: white;
  padding: 12px;
}
.skip-link:focus {
  top: 8px;
}
.shell-sidebar {
  width: var(--sidebar);
  position: fixed;
  inset: 0 auto 0 0;
  background: var(--surface);
  border-right: 1px solid var(--border);
  padding: 30px 20px 20px;
  display: flex;
  flex-direction: column;
  z-index: 20;
}
.brand {
  display: flex;
  gap: 10px;
  align-items: center;
  font-size: 25px;
  font-weight: 750;
  letter-spacing: 1px;
  padding: 0 10px 34px;
}
.brand svg {
  color: var(--accent);
}
nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nav-item {
  display: flex;
  gap: 16px;
  align-items: center;
  min-height: 48px;
  border: 0;
  border-radius: 12px;
  padding: 0 16px;
  background: transparent;
  text-align: left;
  font-size: 16px;
  color: var(--muted);
}
.nav-item:hover {
  background: var(--bg);
  color: var(--text);
}
.nav-item.active {
  background: #fff0ed;
  color: var(--accent-hover);
  font-weight: 650;
}
.publish-button {
  margin-top: 28px;
  width: 100%;
}
.sidebar-account {
  margin-top: auto;
  padding-top: 32px;
}
.account-button {
  display: flex;
  gap: 10px;
  align-items: center;
  border: 0;
  background: none;
  max-width: 100%;
  padding: 8px 0;
}
.account-button > span:last-child {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.logout {
  font-size: 13px;
  color: var(--muted);
}
.shell-body {
  margin-left: var(--sidebar);
  min-width: 0;
  padding-bottom: 20px;
}
.shell-header {
  height: 88px;
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 16px 32px;
  border-bottom: 1px solid var(--border);
  background: var(--surface);
}
.shell-search {
  display: flex;
  align-items: center;
  gap: 10px;
  background: var(--bg);
  border: 1px solid var(--border);
  border-radius: 999px;
  padding: 0 6px 0 18px;
  width: min(560px, 100%);
  height: 46px;
}
.shell-search > svg {
  color: var(--muted);
  flex-shrink: 0;
}
.shell-search input {
  min-width: 0;
  width: 100%;
  border: 0;
  background: none;
  outline-offset: 4px;
  font-size: 14px;
}
.shell-search button {
  border: 0;
  background: none;
  min-height: 40px;
  min-width: 56px;
  color: var(--muted);
  font-size: 13px;
}
.header-account {
  border: 0;
  background: none;
  margin-left: auto;
  min-height: 44px;
  padding: 4px 8px;
  flex-shrink: 0;
}
.mobile-brand,
.mobile-nav {
  display: none;
}
@media (min-width: 768px) and (max-width: 1279px) {
  .shell-sidebar {
    padding: 28px 10px;
  }
  .brand {
    padding: 0 10px 32px;
  }
  .brand span,
  .nav-item span,
  .publish-button span,
  .sidebar-account span,
  .logout {
    display: none;
  }
  .nav-item {
    padding: 0;
    justify-content: center;
  }
  .publish-button {
    padding: 8px;
  }
  .sidebar-account .base-button {
    padding: 10px;
  }
  .shell-header {
    padding: 16px 24px;
  }
}
@media (max-width: 767px) {
  .shell-sidebar {
    display: none;
  }
  .shell-body {
    margin: 0;
    padding-bottom: calc(78px + env(safe-area-inset-bottom));
  }
  .shell-header {
    height: 72px;
    padding: 12px;
    gap: 10px;
  }
  .mobile-brand {
    display: block;
    font-size: 19px;
    font-weight: 750;
    white-space: nowrap;
    letter-spacing: 1px;
  }
  .shell-search {
    height: 42px;
    gap: 6px;
    padding-left: 12px;
  }
  .shell-search button {
    display: none;
  }
  .shell-search input {
    font-size: 13px;
  }
  .header-account {
    padding: 2px;
  }
  .mobile-nav {
    position: fixed;
    z-index: 20;
    bottom: 0;
    inset-inline: 0;
    display: flex;
    flex-direction: row;
    justify-content: space-around;
    gap: 0;
    padding: 8px 4px calc(8px + env(safe-area-inset-bottom));
    background: var(--surface);
    border-top: 1px solid var(--border);
  }
  .mobile-nav button {
    border: 0;
    background: none;
    min-width: 56px;
    min-height: 48px;
    font-size: 11px;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 2px;
    color: var(--muted);
  }
  .mobile-nav .active {
    color: var(--accent-hover);
  }
  .mobile-nav .create > svg {
    background: var(--accent);
    color: white;
    border-radius: 10px;
    width: 34px;
    padding: 5px;
    height: 28px;
  }
  .shell-search svg {
    display: none;
  }
}
</style>
