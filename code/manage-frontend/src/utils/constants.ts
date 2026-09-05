export const TOKEN_KEY = 'mesh_admin_token'
export const USER_KEY = 'mesh_admin_user'

export const FIVE_POWER_COLORS: Record<string, string> = {
  INSIGHT: '#52c41a',
  CONSTRUCT: '#f5222d',
  DEDUCE: '#1890ff',
  ADAPT: '#faad14',
  MIGRATE: '#722ed1',
}

export const DIFFICULTY_TAG_TYPES: Record<string, string> = {
  basic: 'success',
  advanced: 'warning',
  challenge: 'danger',
}

export const STATUS_TAG_TYPES: Record<string, string> = {
  draft: 'info',
  published: 'success',
  archived: '',
}

export const ANNOTATION_TAG_TYPES: Record<string, string> = {
  pending: 'warning',
  confirmed: 'success',
  rejected: 'danger',
}
