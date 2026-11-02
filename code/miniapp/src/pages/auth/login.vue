<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import { ref } from 'vue'
import { onReady, onShow } from '@dcloudio/uni-app'
import { authApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES } from '@/constants'
import { http } from '@/utils/request'
import SvgIcon from '@/components/SvgIcon.vue'
import bgVideoPkgPath from '@/assets/login-background.mp4'


const { pageStyle } = useTheme()
const authStore = useAuthStore()
const loading = ref(false)

// ── 背景视频 ─────────────────────────────────────────────────
// 微信 <video> 的 src 只支持网络地址 / 本地临时文件 / 云文件 ID，不支持代码包内的文件（/assets/xxx.mp4）。
// 所以运行时先把包内视频复制到用户数据目录，再用复制后的路径播放（不依赖网络）。
const BG_VIDEO_ID = 'bgVideo'
const bgVideoSrc = ref('')
const videoFailed = ref(false)

function prepareBgVideo() {
  const fs = uni.getFileSystemManager()
  // 文件名带内容哈希（来自编译产物文件名），视频更新后自动换新文件
  const name = bgVideoPkgPath.split('/').pop() || 'login-background.mp4'
  const dest = `${(uni as unknown as { env: { USER_DATA_PATH: string } }).env.USER_DATA_PATH}/${name}`
  const use = () => { bgVideoSrc.value = dest }
  fs.access({
    path: dest,
    success: use,                                     // 已复制过，直接用
    fail: () => fs.copyFile({
      srcPath: bgVideoPkgPath,
      destPath: dest,
      success: use,
      fail: (e: { errMsg?: string }) => {
        videoFailed.value = true                      // 复制失败 → 退回静态封面
        console.error('[login] 背景视频复制失败：', e?.errMsg)
      },
    }),
  })
}
prepareBgVideo()

// 仅依赖 autoplay 不稳：部分机型不会自动起播，从后台返回页面后也不会恢复，这里显式 play()
function playBgVideo() {
  if (bgVideoSrc.value) uni.createVideoContext(BG_VIDEO_ID)?.play()
}
onReady(playBgVideo)
onShow(() => setTimeout(playBgVideo, 100))   // 稍作延迟，等原生组件挂载完成

function onBgVideoError(e: Event) {
  videoFailed.value = true
  const detail = (e as unknown as { detail?: { errMsg?: string } }).detail
  console.error('[login] 背景视频加载失败：', detail?.errMsg || e)
}

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
    <!-- 视频下方的静态封面：视频正常渲染时被盖住；视频未渲染（兼容性 / 加载失败）时仍能看到画面 -->
    <image class="bg-poster" src="../../assets/login-background-poster.jpg" mode="aspectFill" />
    <video
      v-if="bgVideoSrc && !videoFailed"
      :id="BG_VIDEO_ID"
      class="bg-video"
      :src="bgVideoSrc"
      autoplay
      loop
      muted
      :controls="false"
      :show-loading="false"
      :show-center-play-btn="false"
      :show-play-btn="false"
      :show-fullscreen-btn="false"
      :show-progress="false"
      :enable-progress-gesture="false"
      :show-mute-btn="false"
      object-fit="cover"
      @error="onBgVideoError"
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
  height: 100vh;
  min-height: 100vh;
  background: #000011;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: flex-end;
  overflow: hidden;
  padding: 0 $space-5 120rpx;
}

// 视频已转为 720×1280（9:16）H.264 无音轨 30fps（H.265 在部分安卓微信中无法播放，背景视频也不需要声音）；
// 机器人位于水平正中、垂直约 53% 处，占宽约 56%；
// 铺满整屏（absolute 相对 .login-page + 显式宽高，避免 video 高度回落到默认 225px；
// 不用 fixed，原生组件放在 fixed 容器内在部分机型上不渲染），cover 在 9:19.5 的长屏上左右各裁约 9%，机器人仍完整居中
.bg-stage {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  z-index: 0;
}

.bg-poster {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.bg-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.bg-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
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
