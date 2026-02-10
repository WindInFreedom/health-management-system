// 统一日期格式化，默认中文本地化
// 可通过 locale 参数自定义地区，如 'en-US', 'ja-JP' 等
export function formatDate(date, options = {}, locale = 'zh-CN') {
  if (!date) return '--'
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date
  try {
    return d.toLocaleDateString(locale, options)
  } catch {
    return d.toISOString().slice(0, 10)
  }
}
