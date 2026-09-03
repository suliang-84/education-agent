// 五力颜色配置
export const POWER_COLORS: Record<string, { primary: string; light: string; label: string }> = {
  INSIGHT: { primary: '#8B5CF6', light: '#EDE9FE', label: '洞察力' },
  STRUCTURE: { primary: '#3B82F6', light: '#DBEAFE', label: '建构力' },
  INFERENCE: { primary: '#0EA5E9', light: '#E0F2FE', label: '推演力' },
  ADAPTATION: { primary: '#10B981', light: '#D1FAE5', label: '调适力' },
  TRANSFER: { primary: '#F59E0B', light: '#FEF3C7', label: '迁移力' },
}

export const POWER_LABELS: Record<string, string> = {
  INSIGHT: '洞察力',
  STRUCTURE: '建构力',
  INFERENCE: '推演力',
  ADAPTATION: '调适力',
  TRANSFER: '迁移力',
  insight: '洞察力',
  structure: '建构力',
  inference: '推演力',
  adaptation: '调适力',
  transfer: '迁移力',
}

// 难度标签配置
export const DIFFICULTY_CONFIG: Record<string, { label: string; color: string; bg: string }> = {
  basic: { label: '基础', color: '#065F46', bg: '#D1FAE5' },
  advanced: { label: '进阶', color: '#92400E', bg: '#FEF3C7' },
  challenge: { label: '挑战', color: '#991B1B', bg: '#FEE2E2' },
}

// 题目状态配置
export const STATUS_CONFIG: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'success' },
  archived: { label: '已归档', type: 'warning' },
}

// 标注状态配置
export const ANNOTATION_STATUS_CONFIG: Record<string, { label: string; type: string }> = {
  pending: { label: '待审核', type: 'warning' },
  confirmed: { label: '已确认', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

// 向量化状态
export const EMBEDDING_STATUS_CONFIG: Record<string, { label: string; color: string }> = {
  pending: { label: '待处理', color: '#F59E0B' },
  completed: { label: '已完成', color: '#10B981' },
  failed: { label: '失败', color: '#EF4444' },
}

// 等级颜色
export const LEVEL_COLORS: Record<string, string> = {
  weak: '#EF4444',
  medium: '#F59E0B',
  good: '#22C55E',
  strong: '#059669',
}

// 年级选项
export const GRADE_OPTIONS = [
  { value: 'G7', label: '初一（七年级）' },
  { value: 'G8', label: '初二（八年级）' },
  { value: 'G9', label: '初三（九年级）' },
  { value: 'G10', label: '高一' },
  { value: 'G11', label: '高二' },
  { value: 'G12', label: '高三' },
]
