export type Post = {
	id: number
	title: string
	summary: string
	contentHtml?: string
	author: string
	authorId?: number
	time: string
	tags: string[]
	images: string[]
	comments: number
	likes: number
	isLiked?: boolean
	isFavorited?: boolean
	isFollowingAuthor?: boolean
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
	date: string
	content: string
	likes: number
	isLiked: boolean
	isMine: boolean
}

export type UserTestData = {
	fans: UserSimpleProfile[]
	followings: UserSimpleProfile[]
	comments: UserCommentRecord[]
	favoritePostIds: number[]
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
