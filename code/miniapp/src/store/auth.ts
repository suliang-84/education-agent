/**
 * 认证状态 Store
 * 管理 Token、用户信息、登录状态
 */
import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { STORAGE_KEYS } from '@/constants'
import type { UserInfo } from '@/api/auth'

export const useAuthStore = defineStore('auth', () => {
  const accessToken = ref<string>(uni.getStorageSync(STORAGE_KEYS.ACCESS_TOKEN) || '')
  const refreshToken = ref<string>(uni.getStorageSync(STORAGE_KEYS.REFRESH_TOKEN) || '')
  const userInfo = ref<UserInfo | null>(
    (() => {
      try {
        const s = uni.getStorageSync(STORAGE_KEYS.USER_INFO)
        return s ? JSON.parse(s) : null
      } catch {
        return null
      }
    })()
  )

  const isLoggedIn = computed(() => !!accessToken.value)
  const hasFivePowerProfile = computed(() => userInfo.value?.has_five_power_profile ?? false)
  const studentId = computed(() => userInfo.value?.student_id ?? null)

  function setAuth(data: { access_token: string; refresh_token: string; user_info: UserInfo }) {
    accessToken.value = data.access_token
    refreshToken.value = data.refresh_token
    userInfo.value = data.user_info
    uni.setStorageSync(STORAGE_KEYS.ACCESS_TOKEN, data.access_token)
    uni.setStorageSync(STORAGE_KEYS.REFRESH_TOKEN, data.refresh_token)
    uni.setStorageSync(STORAGE_KEYS.USER_INFO, JSON.stringify(data.user_info))
  }

  function updateUserInfo(partial: Partial<UserInfo>) {
    if (userInfo.value) {
      userInfo.value = { ...userInfo.value, ...partial }
      uni.setStorageSync(STORAGE_KEYS.USER_INFO, JSON.stringify(userInfo.value))
    }
  }

  function setProfileFlag(flag: boolean) {
    updateUserInfo({ has_five_power_profile: flag })
  }

  function clearAuth() {
    accessToken.value = ''
    refreshToken.value = ''
    userInfo.value = null
    uni.removeStorageSync(STORAGE_KEYS.ACCESS_TOKEN)
    uni.removeStorageSync(STORAGE_KEYS.REFRESH_TOKEN)
    uni.removeStorageSync(STORAGE_KEYS.USER_INFO)
  }

  return {
    accessToken,
    refreshToken,
    userInfo,
    isLoggedIn,
    hasFivePowerProfile,
    studentId,
    setAuth,
    updateUserInfo,
    setProfileFlag,
    clearAuth,
  }
})
