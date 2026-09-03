import { POWER_LABELS, DIFFICULTY_CONFIG, STATUS_CONFIG } from './constants'

export function formatDate(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit',
  })
}

export function formatDateOnly(dateStr: string): string {
  if (!dateStr) return '-'
  const date = new Date(dateStr)
  return date.toLocaleDateString('zh-CN')
}

export function getPowerLabel(power: string): string {
  return POWER_LABELS[power] || power
}

export function getDifficultyLabel(difficulty: string): string {
  return DIFFICULTY_CONFIG[difficulty]?.label || difficulty
}

export function getStatusLabel(status: string): string {
  return STATUS_CONFIG[status]?.label || status
}

export function truncate(str: string, maxLen = 50): string {
  if (!str) return ''
  return str.length > maxLen ? str.slice(0, maxLen) + '...' : str
}

export function formatPercent(value: number): string {
  return `${(value * 100).toFixed(1)}%`
}

export function formatCost(usd: number): string {
  return `$${usd.toFixed(3)}`
}
