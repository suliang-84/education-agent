<script setup lang="ts">
import { onLaunch, onShow, onHide } from '@dcloudio/uni-app'
import { flushChatDigest } from '@/utils/chatDigest'
import { useAuthStore } from '@/store/auth'
import { useThemeStore } from '@/store/theme'

onLaunch(() => {
  console.log('MESH App Launch')
  // 跟随系统深浅色
  const themeStore = useThemeStore()
  uni.onThemeChange?.((res: { theme: string }) => themeStore.setSystemTheme(res.theme))
})

// 小程序退到后台：如果聊过天，通知服务端更新摘要和个人洞察
onHide(() => {
  if (useAuthStore().isLoggedIn) flushChatDigest()
})

const LOGIN_ROUTE = 'pages/auth/login'

/** 当前所在页面路由：页面栈为空（冷启动）时取启动路径，均不带前导 / */
function currentRoute(): string {
  const pages = getCurrentPages()
  if (pages.length) return pages[pages.length - 1].route || ''
  return (uni.getLaunchOptionsSync().path || '').replace(/^\//, '')
}

onShow(() => {
  // 检查登录态，未登录跳转。
  // 已经在登录页（含冷启动入口即登录页）时不能再 reLaunch：否则登录页会被销毁重建一次，
  // 页面里的原生 <video> 背景组件会被连续创建两遍，容易出现空白
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn && currentRoute() !== LOGIN_ROUTE) {
    uni.reLaunch({ url: '/pages/auth/login' })
  }
})
</script>

<template>
  <div />
</template>

<style lang="scss">
@use '@/styles/global.scss';
</style>
