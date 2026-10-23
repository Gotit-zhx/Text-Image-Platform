export type Post = {
  id: number
  title: string
  summary: string
  media?: import('./api/media').MediaAsset[]
  mediaIds?: number[]
  contentHtml?: string
  author: string
  authorId?: number
  authorAvatarText?: string
  authorAvatarUrl?: string
  time: string
  createdAt?: string
  updatedAt?: string
  tags: string[]
  images: string[]
  comments: number
  likes: number
  moderationStatus?: 'pending' | 'approved' | 'rejected' | 'offline'
  reviewReason?: string
  isLiked?: boolean
  isFavorited?: boolean
  isFollowingAuthor?: boolean
}

export type UserNotificationItem = {
  id: number
  title: string
  content: string
  time: string
  action: string
  targetType: string
  targetId: number
  actorName?: string
}

export type LoginUser = {
  id: number
  name: string
  email: string
  emailVerified?: boolean
  avatarText: string
  avatarUrl?: string
  gender?: 'male' | 'female' | 'private'
  signature?: string
  fans: number
  follows: number
  roles?: string[]
  isAdmin?: boolean
  isSuperuser?: boolean
  permissions?: { moderate: boolean; operate: boolean; roles: boolean }
}

export type PublishPayload = {
  mediaIds?: number[]
  requestKey?: string
  draftId?: number
  title: string
  contentHtml: string
  tags: string[]
}

export type UserSimpleProfile = {
  id: number
  name: string
  avatarText: string
}

export type UserCommentRecord = {
  id: number
  postId: number
  postTitle: string
  content: string
  date: string
  likes: number
}

export type CommentRecord = {
  postTitle?: string
  createdAt?: string
  rootId?: number | null
  parentId?: number | null
  replyToId?: number | null
  replyToName?: string
  deleted?: boolean
  replyCount?: number
  id: number
  postId: number
  authorId?: number
  author: string
  authorAvatarText?: string
  authorAvatarUrl?: string
  date: string
  content: string
  likes: number
  isLiked: boolean
  isMine: boolean
}

export type UserTestData = {
  fans: UserSimpleProfile[]
  followings: UserSimpleProfile[]
  fansTotal?: number
  followingsTotal?: number
  comments: UserCommentRecord[]
  favoritePostIds: number[]
}

export type InteractionTestData = {
  likedPostIds: number[]
  favoritedPostIds: number[]
  followedAuthorIds: number[]
}

export type ProfileEditPayload = {
  signature?: string
  avatarUrl?: string
  name: string
  gender: 'male' | 'female' | 'private'
}

export type PasswordChangePayload = {
  oldPassword: string
  newPassword: string
  confirmPassword: string
}
