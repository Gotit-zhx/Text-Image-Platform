export type Post = {
	id: number
	title: string
	summary: string
	contentHtml?: string
	author: string
	authorId?: number
	authorAvatarText?: string
	authorAvatarUrl?: string
	time: string
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
	avatarText: string
	avatarUrl?: string
	gender?: 'male' | 'female' | 'private'
	signature?: string
	fans: number
	follows: number
	roles?: string[]
	isAdmin?: boolean
}

export type PublishPayload = {
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
	avatarUrl?: string
	name: string
	gender: 'male' | 'female' | 'private'
}

export type PasswordChangePayload = {
	newPassword: string
	confirmPassword: string
}
