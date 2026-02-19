export type Post = {
	id: number
	title: string
	summary: string
	contentHtml?: string
	author: string
	time: string
	tags: string[]
	images: string[]
	comments: number
	likes: number
}

export type LoginUser = {
	id: number
	name: string
	email: string
	avatarText: string
	fans: number
	follows: number
}

export type PublishPayload = {
	title: string
	contentHtml: string
	tags: string[]
}
