/**
 * 通用工具函数
 */

/** 格式化相对时间（如：3天前） */
export function fromNow(dateStr: string): string {
  const date = new Date(dateStr)
  const now = new Date()
  const diffMs = now.getTime() - date.getTime()
  const diffMin = Math.floor(diffMs / 60000)
  const diffHour = Math.floor(diffMin / 60)
  const diffDay = Math.floor(diffHour / 24)

  if (diffMin < 1) return '刚刚'
  if (diffMin < 60) return `${diffMin}分钟前`
  if (diffHour < 24) return `${diffHour}小时前`
  if (diffDay < 7) return `${diffDay}天前`
  return formatDate(dateStr)
}

/** 格式化日期（YYYY-MM-DD） */
export function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
}

/** 格式化百分比（0.65 → 65%） */
export function formatPercent(val: number, decimals = 0): string {
  return `${(val * 100).toFixed(decimals)}%`
}

/** 手机号脱敏（138****8000） */
export function maskPhone(phone: string): string {
  if (!phone || phone.length < 11) return phone
  return `${phone.slice(0, 3)}****${phone.slice(-4)}`
}

/** 秒数转分:秒（如 90 → 1:30） */
export function formatSeconds(sec: number): string {
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return `${m}:${String(s).padStart(2, '0')}`
}

/** 防抖 */
export function debounce<T extends (...args: unknown[]) => void>(fn: T, delay = 300): T {
  let timer: ReturnType<typeof setTimeout>
  return ((...args: unknown[]) => {
    clearTimeout(timer)
    timer = setTimeout(() => fn(...args), delay)
  }) as T
}

/** 节流 */
export function throttle<T extends (...args: unknown[]) => void>(fn: T, interval = 500): T {
  let last = 0
  return ((...args: unknown[]) => {
    const now = Date.now()
    if (now - last >= interval) {
      last = now
      fn(...args)
    }
  }) as T
}

/** 深拷贝 */
export function deepClone<T>(obj: T): T {
  return JSON.parse(JSON.stringify(obj))
}

/** 判断是否为空（null / undefined / '' / [] / {}） */
export function isEmpty(val: unknown): boolean {
  if (val === null || val === undefined || val === '') return true
  if (Array.isArray(val)) return val.length === 0
  if (typeof val === 'object') return Object.keys(val as object).length === 0
  return false
}

/** 生成唯一 ID */
export function uuid(): string {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0
    const v = c === 'x' ? r : (r & 0x3) | 0x8
    return v.toString(16)
  })
}

/** 获取五力等级标签 */
export function getPowerLevel(score: number): { label: string; color: string } {
  if (score >= 80) return { label: '优势', color: '#10B981' }
  if (score >= 65) return { label: '良好', color: '#3B82F6' }
  if (score >= 50) return { label: '次重点', color: '#F59E0B' }
  return { label: '重点强化', color: '#EF4444' }
}
