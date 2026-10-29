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
    <!-- 顶部装饰圆 -->
    <view class="deco-circle deco-circle--top" />
    <view class="deco-circle deco-circle--bottom" />

    <!-- 中央 Logo + Tagline -->
    <view class="hero">
      <view class="logo-wrap">
        <view class="logo-icon"><SvgIcon name="brain" :size="80" color="on-primary" /></view>
        <text class="logo-text">MESH</text>
      </view>
      <text class="tagline">AI 驱动的个性化认知训练</text>
      <text class="sub-tagline">洞察 · 建构 · 推演 · 调适 · 迁移</text>
    </view>

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

    <!-- 底部产品说明 -->
    <view class="footer">
      <text class="footer-text">
        MESH 基于认知科学五力模型，为每位学生量身定制学习路径，
        让每一道题的练习都有意义。
      </text>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.login-page {
  position: relative;
  min-height: 100vh;
  background:
    radial-gradient(circle at 85% 8%, rgba(94, 141, 249, 0.22) 0%, transparent 45%),
    radial-gradient(circle at 10% 92%, rgba(122, 162, 255, 0.20) 0%, transparent 45%),
    $bg-page;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  padding: 0 $space-5;
}

.deco-circle {
  position: absolute;
  border-radius: 50%;
  pointer-events: none;

  &--top {
    width: 520rpx;
    height: 520rpx;
    top: -160rpx;
    right: -120rpx;
    background: radial-gradient(circle, rgba(94, 141, 249, 0.16) 0%, transparent 70%);
  }

  &--bottom {
    width: 440rpx;
    height: 440rpx;
    bottom: -120rpx;
    left: -100rpx;
    background: radial-gradient(circle, rgba(122, 162, 255, 0.16) 0%, transparent 70%);
  }
}

// 毛玻璃卡片区
.hero {
  position: relative;
  width: 100%;
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 64rpx $space-4 $space-5;
  margin-bottom: $space-4;
  background: var(--glass-bg);
  backdrop-filter: blur(20px);
  -webkit-backdrop-filter: blur(20px);
  border: 1rpx solid var(--glass-border);
  border-radius: $r-2xl;
  box-shadow: $shadow-md, inset 0 2rpx 0 var(--glass-edge);
}

.logo-wrap {
  display: flex;
  flex-direction: column;
  align-items: center;
  margin-bottom: $space-4;
}

.logo-icon {
  width: 144rpx;
  height: 144rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $r-xl;
  background: $cta-gradient;
  box-shadow: $shadow-cta;
  margin-bottom: $space-3;
}

.logo-text {
  font-size: 64rpx;
  font-weight: 800;
  color: $text-1;
  letter-spacing: 12rpx;
}

.tagline {
  font-size: $font-size-xl;
  color: $text-1;
  font-weight: 600;
  margin-bottom: $space-2;
}

.sub-tagline {
  font-size: $font-size-sm;
  color: $primary;
  letter-spacing: 4rpx;
  padding: 6rpx $space-3;
  background: $primary-light;
  border: 1rpx solid $primary-border;
  border-radius: $r-pill;
}

// 按钮区
.btn-area {
  position: relative;
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
  color: $text-3;
  text-align: center;
}

.footer {
  position: absolute;
  bottom: 80rpx;
  left: $space-6;
  right: $space-6;
}

.footer-text {
  font-size: $font-size-xs;
  color: $text-3;
  text-align: center;
  line-height: 1.8;
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
  color: $text-3;
  text-align: center;
  margin-top: $space-1;
}
</style>
