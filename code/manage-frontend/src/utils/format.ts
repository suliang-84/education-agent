import dayjs from 'dayjs'
import 'dayjs/locale/zh-cn'
import relativeTime from 'dayjs/plugin/relativeTime'

dayjs.extend(relativeTime)
dayjs.locale('zh-cn')

export function formatDate(date: string, fmt = 'YYYY-MM-DD HH:mm:ss'): string {
  if (!date) return '-'
  return dayjs(date).format(fmt)
}

export function fromNow(date: string): string {
  if (!date) return '-'
  return dayjs(date).fromNow()
}

export function formatPercent(val: number): string {
  return `${(val * 100).toFixed(1)}%`
}

export function formatCost(val: number): string {
  return `$${val.toFixed(2)}`
}
