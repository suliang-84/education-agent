/**
 * 主题令牌（运行时）
 * 亮色值同 styles/global.scss 中 page{} 的默认变量；暗色值取自后台管理系统暗色主题
 * （近黑底 #0a0c10 · 玻璃面板 · 柔蓝 #a9beff）。
 * 页面通过 <page-meta :page-style="pageStyle"> 注入，CSS 变量向下继承。
 */
export type ThemeMode = 'system' | 'light' | 'dark'

export const DARK_VARS: Record<string, string> = {
  '--bg-page': '#0a0c10',
  '--bg-surface': '#0e1116',
  '--bg-muted': '#151a21',
  '--primary': '#a9beff',
  '--primary-hover': '#cadbf3',
  '--primary-light': 'rgba(169,190,255,0.10)',
  '--primary-border': 'rgba(169,190,255,0.28)',
  '--cta-gradient': 'linear-gradient(135deg, #cadbf3, #a9beff)',
  '--on-primary': '#0a0c10',
  '--on-primary-dim': 'rgba(10,12,16,0.62)',
  '--on-primary-line': 'rgba(10,12,16,0.22)',
  '--text-1': '#f9fafb',
  '--text-2': '#9ca3af',
  '--text-3': '#6b7280',
  '--text-disabled': '#374151',
  '--border': 'rgba(255,255,255,0.07)',
  '--border-hover': 'rgba(255,255,255,0.14)',
  '--shadow-sm': '0 8rpx 24rpx rgba(0,0,0,0.32), inset 0 1rpx 0 rgba(255,255,255,0.05)',
  '--shadow-md': '0 16rpx 40rpx rgba(0,0,0,0.40), inset 0 1rpx 0 rgba(255,255,255,0.06)',
  '--shadow-cta': '0 8rpx 28rpx rgba(169,190,255,0.25)',
  '--success': '#4ade80',
  '--warning': '#fcd34d',
  '--danger': '#f87171',
  '--success-light': 'rgba(74,222,128,0.12)',
  '--warning-light': 'rgba(252,211,77,0.12)',
  '--danger-light': 'rgba(248,113,113,0.12)',
  '--mask': 'rgba(0,0,0,0.60)',
  '--mask-surface': 'rgba(14,17,22,0.92)',
  '--glass-bg': 'rgba(12,14,18,0.72)',
  '--glass-border': 'rgba(255,255,255,0.09)',
  '--glass-edge': 'rgba(255,255,255,0.08)',
  '--glow-1': 'rgba(94,141,249,0.13)',
  '--glow-2': 'rgba(94,141,249,0.08)',
  // 玻璃面板（同后台二级页面子模块：云晕 + 半透明底 + 顶部高光 + 渐变高亮边 + 定时扫光）
  '--panel-bg': 'radial-gradient(360rpx circle at 8% -25%, rgba(94,141,249,0.20), transparent 62%), radial-gradient(420rpx circle at 104% 125%, rgba(124,112,255,0.13), transparent 62%), rgba(14,17,22,0.60)',
  '--panel-shadow': '0 4rpx 16rpx rgba(0,0,0,0.16), inset 0 1rpx 0 rgba(255,255,255,0.06)',
  '--panel-edge': 'rgba(94,141,249,0.85)',
  '--panel-shine-mid': 'rgba(255,255,255,0.05)',
  '--panel-shine-peak': 'rgba(255,255,255,0.10)',
  '--panel-shine-anim': 'panel-shine 9s ease-in-out infinite',
}

export function toStyleString(vars: Record<string, string>): string {
  return Object.keys(vars).map((k) => `${k}:${vars[k]}`).join(';')
}

export const DARK_STYLE = toStyleString(DARK_VARS)

// 原生导航栏 / TabBar / 页面背景
export const CHROME = {
  light: { front: '#000000', navBg: '#F3F5FB', pageBg: '#F3F5FB', tabBg: '#FFFFFF', tabText: '#94A3B8', tabSel: '#5E8DF9', tabBorder: 'white' },
  dark: { front: '#ffffff', navBg: '#0a0c10', pageBg: '#0a0c10', tabBg: '#0e1116', tabText: '#6b7280', tabSel: '#a9beff', tabBorder: 'black' },
}

// SvgIcon 命名色
export const ICON_COLORS: Record<'light' | 'dark', Record<string, string>> = {
  light: { primary: '#5E8DF9', muted: '#64748B', 'on-primary': '#FFFFFF' },
  dark: { primary: '#A9BEFF', muted: '#9CA3AF', 'on-primary': '#0A0C10' },
}
