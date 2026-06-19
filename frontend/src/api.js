const BASE = import.meta.env.VITE_API_BASE || 'http://127.0.0.1:8000'
const PREFIX = '/api/v1'

async function req(path, options = {}) {
  let res
  try {
    res = await fetch(BASE + PREFIX + path, {
      headers: { 'Content-Type': 'application/json' },
      ...options,
    })
  } catch (e) {
    const err = new Error('백엔드에 연결할 수 없어요. uvicorn 실행 중인지 확인하세요.')
    err.network = true
    throw err
  }
  let data = null
  try { data = await res.json() } catch (_) { /* 빈 응답 */ }
  if (!res.ok) {
    const msg = data && data.detail ? data.detail : `요청 실패 (${res.status})`
    const err = new Error(msg)
    err.status = res.status
    throw err
  }
  return data
}

export const api = {
  getConfig: () => req('/config'),
  updateConfig: (body) => req('/config', { method: 'PUT', body: JSON.stringify(body) }),
  startSession: (body = {}) => req('/session', { method: 'POST', body: JSON.stringify(body) }),
  currentSession: () => req('/session/current'),
  calculate: (body = {}) => req('/daily/calculate', { method: 'POST', body: JSON.stringify(body) }),
  today: () => req('/daily/today'),
  dailyList: (sessionId) => req('/daily/list' + (sessionId ? `?session_id=${sessionId}` : '')),
  sessionHistory: () => req('/session/history'),
  closeSession: (id, status) => req(`/session/${id}/close?status=${status}`, { method: 'POST' }),
  reopenSession: (id) => req(`/session/${id}/reopen`, { method: 'POST' }),
  statsSummary: () => req('/stats/summary'),
  marketCheck: () => req('/market/check'),
  exportBackup: () => req('/backup/export'),
  importBackup: (data) => req('/backup/import', { method: 'POST', body: JSON.stringify(data) }),
  execute: (fills) => req('/daily/execute', { method: 'POST', body: JSON.stringify({ fills }) }),
  listTransactions: () => req('/daily/transactions'),
  updateTransaction: (id, body) => req(`/daily/transactions/${id}`, { method: 'PUT', body: JSON.stringify(body) }),
  deleteTransaction: (id) => req(`/daily/transactions/${id}`, { method: 'DELETE' }),
}

export { BASE }
