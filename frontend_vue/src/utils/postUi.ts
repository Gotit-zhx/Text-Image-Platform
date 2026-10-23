export const formatCount = (count: number): string => {
	if (count >= 10000) {
		const value = count / 10000
		const formatted = (Math.floor(value * 10) / 10).toString().replace(/\.0$/, '')
		return `${formatted}万+`
	}

	return `${count}`
}

export const formatPostTime = (value: string): string => {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? value : date.toLocaleDateString('zh-CN', {month:'numeric',day:'numeric'})
}
