export function normalizeListResponse(data) {
  // 兼容 DRF 非分页和分页返回
  return Array.isArray(data) ? data : (data?.results ?? [])
}