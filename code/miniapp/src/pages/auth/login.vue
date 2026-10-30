<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref } from 'vue'
import { authApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES } from '@/constants'
import { http } from '@/utils/request'
import SvgIcon from '@/components/SvgIcon.vue'


const { pageStyle } = useTheme()
const authStore = useAuthStore()
const loading = ref(false)

// 开发模式：是否显示开发登录入口
const IS_DEV = import.meta.env.VITE_APP_ENV === 'development'
const devPhone = ref('13800138000')  // 开发用测试手机号

/** 路由到首页（复用逻辑） */
function routeAfterLogin(resp: { access_token: string; refresh_token: string; user_info: any }) {
  authStore.setAuth({
    access_token: resp.access_token,
    refresh_token: resp.refresh_token,
    user_info: resp.user_info,
  })
  if (resp.user_info.has_five_power_profile) {
    uni.switchTab({ url: PAGES.TRAINING_HOME })
  } else {
    uni.reLaunch({ url: PAGES.TEST_HOME })
  }
}

/**
 * 开发环境专用登录：跳过微信授权，直接用手机号换 Token
 * 对应后端 POST /api/v1/auth/dev-login（仅 APP_ENV=development 时开放）
 */
async function handleDevLogin() {
  if (loading.value) return
  loading.value = true
  try {
    const resp = await http.post<any>('/auth/dev-login', {
      phone: devPhone.value,
      nickname: '开发测试',
      grade: 'G9',
      semester: 'S1',
    }, { skipAuth: true } as never)
    routeAfterLogin(resp)
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '开发登录失败'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    loading.value = false
  }
}

/**
 * 正式微信登录流程:
 * 1. wx.login() 获取临时 code
 * 2. 发送 code 到后端换取 Token 或 temp_token
 * 3. 新用户 → 绑定手机号页; 老用户 → 按 has_five_power_profile 路由
 */
async function handleWxLogin() {
  if (loading.value) return
  loading.value = true

  try {
    const loginRes = await new Promise<UniApp.LoginRes>((resolve, reject) => {
      uni.login({ provider: 'weixin', success: resolve, fail: reject })
    })

    const code = loginRes.code
    if (!code) throw new Error('未获取到微信授权码')

    const resp = await authApi.wxLogin({ code })

    if ('temp_token' in resp) {
      uni.navigateTo({
        url: `${PAGES.AUTH_BIND_PHONE}?temp_token=${resp.temp_token}`,
      })
    } else {
      routeAfterLogin(resp as any)
    }
  } catch (err: unknown) {
    const msg = err instanceof Error ? err.message : '登录失败，请重试'
    uni.showToast({ title: msg, icon: 'none' })
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="login-page">
    <!-- 全屏循环背景视频 + 压暗遮罩 -->
    <view class="bg-stage">
    <video
      class="bg-video"
      src="../../assets/login-background-h264.mp4"
      autoplay
      loop
      muted
      :controls="false"
      :show-center-play-btn="false"
      :show-play-btn="false"
      :show-fullscreen-btn="false"
      :show-progress="false"
      :enable-progress-gesture="false"
      :show-mute-btn="false"
      object-fit="cover"
    />
    </view>
    <view class="bg-mask" />

    <!-- 登录按钮区 -->
    <view class="btn-area">
      <button
        class="wx-login-btn"
        :class="{ 'wx-login-btn--loading': loading }"
        :disabled="loading"
        @tap="handleWxLogin"
      >
        <view class="btn-inner">
          <view v-if="!loading" class="wx-icon"><SvgIcon name="sparkles" :size="36" color="on-primary" /></view>
          <view v-else class="spinner" />
          <text class="btn-label">{{ loading ? '登录中...' : '微信一键登录' }}</text>
        </view>
      </button>

      <text class="hint-text">登录即代表同意《用户协议》和《隐私政策》</text>

      <!-- 开发模式快速登录入口（仅 development 环境显示） -->
      <view v-if="IS_DEV" class="dev-login-wrap">
        <view class="dev-divider"><text class="dev-divider-text">开发模式</text></view>
        <view class="dev-input-row">
          <input
            v-model="devPhone"
            class="dev-input"
            type="number"
            maxlength="11"
            placeholder="测试手机号"
          />
          <button
            class="dev-btn"
            :disabled="loading"
            @tap="handleDevLogin"
          >
            快速登录
          </button>
        </view>
        <text class="dev-hint">跳过微信授权 · 仅本地开发使用</text>
      </view>
    </view>

  </view>
</template>

<style lang="scss" scoped>

.login-page {
  position: relative;
  min-height: 100vh;
  background: #000011;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  overflow: hidden;
  padding: 0 $space-5 120rpx;
}

// 视频为 9:16 竖屏，机器人位于水平正中、垂直约 53% 处；
// 铺满整屏（fixed + 显式宽高，避免 video 高度回落到默认 225px），cover 裁切后机器人仍居中
.bg-stage {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 0;
}

.bg-video {
  width: 100%;
  height: 100%;
}

.bg-mask {
  position: fixed;
  top: 0;
  left: 0;
  width: 100vw;
  height: 100vh;
  z-index: 1;
  background: rgba(0, 0, 17, 0.2);
  pointer-events: none;
}

// 按钮区
.btn-area {
  position: relative;
  z-index: 2;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
}

.wx-login-btn {
  width: 100%;
  height: 100rpx;
  border-radius: $r-pill;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  border: none;
  padding: 0;
  transition: $transition-base;

  &::after {
    border: none;
  }

  &--loading {
    opacity: 0.85;
  }

  &[disabled] {
    background: $primary-hover;
  }
}

.btn-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;
}

.wx-icon {
  display: flex;
  align-items: center;
}

.btn-label {
  font-size: $font-size-lg;
  color: $on-primary;
  font-weight: 700;
}

.spinner {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 4rpx solid $on-primary-line;
  border-top-color: $on-primary;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}

.hint-text {
  font-size: $font-size-xs;
  color: rgba(255, 255, 255, 0.75);
  text-align: center;
}

// 开发模式快速登录
.dev-login-wrap {
  margin-top: $space-4;
  width: 100%;
}

.dev-divider {
  display: flex;
  align-items: center;
  margin-bottom: $space-3;

  &::before, &::after {
    content: '';
    flex: 1;
    height: 1rpx;
    background: $border;
  }

  &-text {
    font-size: $font-size-xs;
    padding: 4rpx $space-2;
    margin: 0 $space-2;
    background: $primary-light;
    border-radius: $r-pill;
    color: $primary;
  }
}

.dev-input-row {
  display: flex;
  gap: $space-2;
  align-items: center;
}

.dev-input {
  flex: 1;
  height: 80rpx;
  border: 1rpx solid $border-hover;
  border-radius: $r-pill;
  padding: 0 $space-3;
  font-size: $font-size-sm;
  color: $text-1;
  background: $bg-surface;

  &:focus {
    border-color: $primary;
    box-shadow: 0 0 0 6rpx rgba(94, 141, 249, 0.18);
  }
}

.dev-btn {
  height: 80rpx;
  padding: 0 $space-4;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  color: $on-primary;
  border-radius: $r-pill;
  font-size: $font-size-sm;
  font-weight: 600;
  border: none;
  white-space: nowrap;

  &::after { border: none; }
}

.dev-hint {
  display: block;
  font-size: $font-size-xs;
  color: rgba(255, 255, 255, 0.7);
  text-align: center;
  margin-top: $space-1;
}
</style>
