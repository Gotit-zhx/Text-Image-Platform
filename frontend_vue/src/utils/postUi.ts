export const formatCount = (count: number): string => {
	if (count >= 10000) {
		const value = count / 10000
		const formatted = (Math.floor(value * 10) / 10).toString().replace(/\.0$/, '')
		return `${formatted}万+`
	}

	return `${count}`
}

export const resolvePostImageStyle = (image: string) => {
	if (/^(linear-gradient|radial-gradient|conic-gradient)\(/.test(image)) {
		return { background: image }
	}

	return {
		backgroundImage: `url(${image})`,
		backgroundSize: 'cover',
		backgroundPosition: 'center'
	}
}
