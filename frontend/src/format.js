export const usd = (v) =>
  v == null ? '—' : '$' + Number(v).toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })

export const krw = (v) =>
  v == null ? '—' : '₩' + Math.round(Number(v)).toLocaleString('ko-KR')

export const pct = (v) =>
  v == null ? '—' : (v > 0 ? '+' : '') + Number(v).toFixed(2) + '%'

export const qty = (v) =>
  v == null ? '—' : Number(v).toLocaleString('ko-KR') + '주'

// 모드: 로직 키(전반전/후반전/쿼터) → 직관적 표현
export const MODE_EASY = { 전반전: '모으기', 후반전: '버티기', 쿼터: '쉬기' }
export const modeEasy = (m) => MODE_EASY[m] || m
