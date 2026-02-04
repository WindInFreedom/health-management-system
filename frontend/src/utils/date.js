// 统一日期格式化，默认中文本地化
// TODO: 如需改为其他地区格式或固定格式，请自行修改
export function formatDate(date, options = {}) {
  if (!date) return '--'
  const d = typeof date === 'string' || typeof date === 'number' ? new Date(date) : date
  try {
    return d.toLocaleDateString('zh-CN', options)
  } catch {
    return d.toISOString().slice(0, 10)
  }
}
