import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { TOKEN_KEY, USER_KEY } from '@/utils/constants'

interface AdminUser {
  id: number
  username: string
  role: string
}

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string>(localStorage.getItem(TOKEN_KEY) || '')
  const user = ref<AdminUser | null>(
    JSON.parse(localStorage.getItem(USER_KEY) || 'null')
  )

  function setAuth(accessToken: string, adminUser: AdminUser) {
    token.value = accessToken
    user.value = adminUser
    localStorage.setItem(TOKEN_KEY, accessToken)
    localStorage.setItem(USER_KEY, JSON.stringify(adminUser))
  }

  function clearAuth() {
    token.value = ''
    user.value = null
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
  }

  const isLoggedIn = () => !!token.value
  const isSuperAdmin = computed(() => user.value?.role === 'SUPER_ADMIN')

  return { token, user, setAuth, clearAuth, isLoggedIn, isSuperAdmin }
})
