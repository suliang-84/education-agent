/**
 * 主题 Store：跟随系统 / 手动浅色 / 手动深色
 */
import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import type { ThemeMode } from '@/styles/theme'

const STORAGE_KEY = 'mesh_theme_mode'

function readSystemTheme(): 'light' | 'dark' {
  try {
    const info: any = uni.getAppBaseInfo ? uni.getAppBaseInfo() : uni.getSystemInfoSync()
    return info?.theme === 'dark' ? 'dark' : 'light'
  } catch {
    return 'light'
  }
}

function readMode(): ThemeMode {
  try {
    const v = uni.getStorageSync(STORAGE_KEY)
    return v === 'light' || v === 'dark' ? v : 'system'
  } catch {
    return 'system'
  }
}

export const useThemeStore = defineStore('theme', () => {
  const mode = ref<ThemeMode>(readMode())
  const systemTheme = ref<'light' | 'dark'>(readSystemTheme())

  const isDark = computed(() => (mode.value === 'system' ? systemTheme.value === 'dark' : mode.value === 'dark'))

  function setMode(m: ThemeMode) {
    mode.value = m
    try { uni.setStorageSync(STORAGE_KEY, m) } catch { /* ignore */ }
  }

  function setSystemTheme(t: string) {
    systemTheme.value = t === 'dark' ? 'dark' : 'light'
  }

  return { mode, isDark, systemTheme, setMode, setSystemTheme }
})
