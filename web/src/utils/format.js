export function formatNumber(num, decimals = 2) {
  if (num === null || num === undefined) return '-'
  if (isNaN(num)) return '-'
  return Number(num).toFixed(decimals)
}

export function formatPercent(num) {
  if (num === null || num === undefined) return '-'
  return (Number(num) * 100).toFixed(2) + '%'
}

export function formatDate(dateStr) {
  if (!dateStr) return '-'
  return dateStr.substring(0, 10)
}

export function consumptionLevel(cost) {
  if (!cost) return { level: 'unknown', color: '#909399' }
  const c = Number(cost)
  if (c >= 1000) return { level: '高消耗', color: '#f56c6c' }
  if (c >= 100) return { level: '中消耗', color: '#e6a23c' }
  return { level: '低消耗', color: '#67c23a' }
}

