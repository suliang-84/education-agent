import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import type { AdminInfo } from '../types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('admin_token'))
  const adminInfo = ref<AdminInfo | null>(
    JSON.parse(localStorage.getItem('admin_info') || 'null')
  )

  const isLoggedIn = computed(() => !!token.value && !!adminInfo.value)

  function setAuth(newToken: string, info: AdminInfo) {
    token.value = newToken
    adminInfo.value = info
    localStorage.setItem('admin_token', newToken)
    localStorage.setItem('admin_info', JSON.stringify(info))
  }

  function clearAuth() {
    token.value = null
    adminInfo.value = null
    localStorage.removeItem('admin_token')
    localStorage.removeItem('admin_info')
  }

  return { token, adminInfo, isLoggedIn, setAuth, clearAuth }
})
