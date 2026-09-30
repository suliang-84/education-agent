<script setup lang="ts">
import { onLaunch, onShow } from '@dcloudio/uni-app'
import { useAuthStore } from '@/store/auth'

onLaunch(() => {
  console.log('MESH App Launch')
})

onShow(() => {
  // 检查登录态，未登录跳转
  const authStore = useAuthStore()
  if (!authStore.isLoggedIn) {
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
