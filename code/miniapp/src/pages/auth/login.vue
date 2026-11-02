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

// ── 登录卡片贴紧机器人底边（适配不同机型）──────────────────────
// 视频按 cover 铺满页面：缩放比 s = max(W/540, H/960)，纵向居中裁剪。
// 视频帧里机器人底边的位置固定（比例 ROBOT_BOTTOM_IN_VIDEO），所以屏幕上的位置可以算出来，
// 再把卡片顶边放到这条线上：长屏、短屏、平板都能贴紧，不会出现缝隙或盖住机器人。
// 视频被重新裁剪后，只需要改下面这个比例：(原视频里机器人底边像素 683 − 顶部裁掉的像素 127) / 960
const VIDEO_W = 540
const VIDEO_H = 960
const ROBOT_BOTTOM_IN_VIDEO = (683 - 127) / 960
const robotBottom = ref(0)   // 机器人底边在页面里的 y（px）；0 表示还没算出来，CSS 兜底 57%
const cardTop = ref(0)       // 卡片顶边 y（px）
let bottomInset = 0

function layoutCard(W: number, H: number, cardH = 0) {
  const s = Math.max(W / VIDEO_W, H / VIDEO_H)
  const rb = (H - VIDEO_H * s) / 2 + ROBOT_BOTTOM_IN_VIDEO * VIDEO_H * s
  robotBottom.value = Math.round(rb)
  let top = rb - uni.upx2px(4)                                   // 微小重叠，避免出现发丝缝
  const footerReserve = uni.upx2px(100) + bottomInset            // 底部页脚占位
  if (cardH && top + cardH > H - footerReserve) {                // 卡片放不下（矮屏 / 开发入口展开）→ 整体上移，保证不被截断
    top = Math.max(0, H - footerReserve - cardH)
  }
  cardTop.value = Math.round(top)
}

function relayout() {
  const q = uni.createSelectorQuery()
  q.select('.bg-stage').boundingClientRect()
  q.select('.login-card').boundingClientRect()
  q.exec((r: Array<{ width: number; height: number } | null>) => {
    const stage = r?.[0]
    const card = r?.[1]
    if (stage?.width && stage?.height) layoutCard(stage.width, stage.height, card?.height || 0)
  })
}

// 首次渲染前先用系统信息估算，避免卡片先出现在错误位置再跳动
{
  const info = uni.getSystemInfoSync()
  bottomInset = Math.max(0, info.screenHeight - (info.safeArea?.bottom ?? info.screenHeight))
  layoutCard(info.windowWidth, info.windowHeight)
}
onReady(relayout)                       // 渲染后用实际的页面区域和卡片高度精修
uni.onWindowResize?.(relayout)          // 折叠屏展开 / 横竖屏切换

function onBgVideoError(e: Event) {
  videoFailed.value = true
  const detail = (e as unknown as { detail?: { errMsg?: string } }).detail
  console.error('[login] 背景视频加载失败：', detail?.errMsg || e)
}

// 开发模式：是否显示开发登录入口
const IS_DEV = import.meta.env.VITE_APP_ENV === 'development'
// 临时开关：设为 true 才显示开发登录入口（便于查看正式环境下的登录页效果）
const SHOW_DEV_LOGIN = IS_DEV && false
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
  <view class="login-page" :style="robotBottom ? { '--robot-bottom': robotBottom + 'px' } : {}">
    <!-- 全屏循环背景视频 -->
    <view class="bg-stage">
      <!-- 视频下方的静态封面：视频未就绪 / 加载失败时仍能看到画面 -->
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

    <!-- 底部玻璃卡片：品牌 + 登录（与后台登录卡片同一视觉语言） -->
    <view class="login-card" :style="cardTop ? { top: cardTop + 'px' } : {}">
      <view class="card-body">
        <text class="brand-sys-name">MESH · AI助教</text>
        <text class="brand-headline">五力成长，从每次训练开始</text>

        <button
          class="submit-btn"
          :class="{ 'submit-btn--loading': loading }"
          :disabled="loading"
          @tap="handleWxLogin"
        >
          <view class="btn-inner">
            <SvgIcon v-if="!loading" name="sparkles" :size="36" color="#1a2a3a" />
            <view v-else class="spinner" />
            <text class="btn-label">{{ loading ? '登录中...' : '微信一键登录' }}</text>
          </view>
        </button>

        <text class="hint-text">登录即代表同意《用户协议》和《隐私政策》</text>

        <!-- 开发模式快速登录入口（仅 development 环境显示） -->
        <view v-if="SHOW_DEV_LOGIN" class="dev-login-wrap">
          <view class="dev-divider"><text class="dev-divider-text">开发模式</text></view>
          <text class="field-label">测试手机号</text>
          <view class="dev-input-row">
            <view class="field-wrap">
              <SvgIcon name="phone" :size="30" color="rgba(255,255,255,0.45)" />
              <input
                v-model="devPhone"
                class="field-input"
                type="number"
                maxlength="11"
                placeholder="请输入测试手机号"
                placeholder-style="color: rgba(255,255,255,0.35)"
              />
            </view>
            <button class="dev-btn" :disabled="loading" @tap="handleDevLogin">快速登录</button>
          </view>
          <text class="dev-hint">跳过微信授权 · 仅本地开发使用</text>
        </view>
      </view>
    </view>

    <text class="page-footer">MESH AI · 认知训练平台</text>
  </view>
</template>

<style lang="scss" scoped>
// 视觉语言与后台登录页一致：全屏视频 + 深色玻璃卡片 + 白→浅蓝渐变胶囊按钮
// 背景是深色视频，所以卡片内颜色固定，不随亮/暗主题切换

.login-page {
  position: relative;
  height: 100vh;
  min-height: 100vh;
  background: #000011;
  overflow: hidden;
}

// 视频为 540×960（9:16）H.264；机器人位于水平正中、垂直约 21%–57% 处（已裁掉顶部空黑上移，避免被底部卡片压住）。
// 铺满整屏用 absolute + 显式宽高（避免 video 高度回落到默认 225px；原生组件放在 fixed 容器内在部分机型上不渲染）
.bg-stage,
.bg-mask {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

.bg-stage { z-index: 0; }

.bg-poster,
.bg-video {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
}

// 顶部几乎透明，机器人底边附近渐变压暗：
.bg-mask {
  z-index: 1;
  // 渐变跟着机器人底边走（--robot-bottom 由脚本按机型算出，未算出时按 57% 兜底）：
  // 底边上方 220rpx 开始压暗，到底边下方 40rpx 基本压实，既遮住视频里机器人身体底部的硬切边，也托住下面的卡片文字
  background: linear-gradient(
    to bottom,
    rgba(0, 1, 0, 0.08) 0%,
    rgba(0, 1, 0, 0.08) calc(var(--robot-bottom, 57%) - 220rpx),
    rgba(0, 1, 0, 0.88) calc(var(--robot-bottom, 57%) + 40rpx),
    rgba(0, 1, 0, 0.92) 100%
  );
  pointer-events: none;
}

// ── 玻璃卡片 ─────────────────────────────────────────────────
.login-card {
  position: absolute;
  z-index: 2;
  top: 57%;                // 兜底；实际 top 由脚本按机器人底边算出并写入行内样式
  left: $space-4;
  right: $space-4;
  border-radius: 48rpx;
  overflow: hidden;
  background:
    radial-gradient(
      600rpx circle at 50% -20%,
      rgba(94, 141, 249, 0.22),
      rgba(94, 141, 249, 0.05) 40%,
      transparent 65%
    ),
    rgba(12, 14, 18, 0.85);
  border: 1rpx solid rgba(140, 165, 255, 0.28);
  box-shadow:
    0 32rpx 72rpx rgba(0, 0, 0, 0.60),
    0 8rpx 28rpx rgba(0, 0, 0, 0.40),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.08);

  // 定时反光：单次光线扫过后长时间停顿
  &::after {
    content: '';
    position: absolute;
    top: -100%;
    left: -100%;
    width: 300%;
    height: 300%;
    background: linear-gradient(
      125deg,
      transparent 40%,
      rgba(255, 255, 255, 0.05) 48%,
      rgba(255, 255, 255, 0.11) 50%,
      rgba(255, 255, 255, 0.05) 52%,
      transparent 60%
    );
    animation: glass-shine 8s ease-in-out infinite;
    pointer-events: none;
  }
}

@keyframes glass-shine {
  0%   { transform: translate(-40%, -40%); opacity: 0; }
  5%   { opacity: 1; }
  75%  { transform: translate(40%, 40%); opacity: 1; }
  82%  { opacity: 0; }
  100% { transform: translate(40%, 40%); opacity: 0; }
}

.card-body {
  position: relative;
  z-index: 1;
  display: flex;
  flex-direction: column;
  padding: 64rpx 56rpx 48rpx;
}

// 品牌名：白色粗体 + 蓝色外发光
.brand-sys-name {
  font-size: 44rpx;
  font-weight: 900;
  color: #ffffff;
  letter-spacing: 0.04em;
  margin-bottom: 20rpx;
  text-shadow:
    0 0 8rpx rgba(255, 255, 255, 0.85),
    0 0 20rpx rgba(110, 150, 255, 0.95),
    0 0 40rpx rgba(70, 110, 255, 0.80),
    0 0 68rpx rgba(50, 90, 255, 0.60);
}

// 后台是浅蓝渐变文字；小程序里渐变文字在部分机型不显示，用渐变中间色代替
.brand-headline {
  font-size: 26rpx;
  font-weight: 600;
  color: #9fb6d9;
  margin-bottom: 56rpx;
}

// ── 主按钮：白→浅蓝渐变胶囊 ──────────────────────────────
.submit-btn {
  width: 100%;
  height: 96rpx;
  border: none;
  padding: 0;
  border-radius: 9999rpx;
  background: linear-gradient(to right, #cadbf3 0%, #a9beff 100%);
  box-shadow:
    0 8rpx 40rpx rgba(105, 140, 188, 0.35),
    inset 0 1rpx 0 rgba(255, 255, 255, 0.30);

  &::after { border: none; }
  &:active { transform: scale(0.98); }
  &--loading { opacity: 0.65; }
  &[disabled] { background: linear-gradient(to right, #cadbf3 0%, #a9beff 100%); }
}

.btn-inner {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 16rpx;
}

.btn-label {
  font-size: 32rpx;
  font-weight: 600;
  color: #1a2a3a;
  letter-spacing: 0.04em;
}

.spinner {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(26, 42, 58, 0.30);
  border-top-color: #1a2a3a;
  animation: spin 0.7s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.hint-text {
  margin-top: 28rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.45);
  text-align: center;
}

// ── 开发模式快速登录 ──────────────────────────────────────
.dev-login-wrap {
  margin-top: 40rpx;
  display: flex;
  flex-direction: column;
}

.dev-divider {
  display: flex;
  align-items: center;
  margin-bottom: 28rpx;

  &::before,
  &::after {
    content: '';
    flex: 1;
    height: 1rpx;
    background: rgba(255, 255, 255, 0.10);
  }

  &-text {
    margin: 0 20rpx;
    padding: 4rpx 20rpx;
    font-size: 22rpx;
    color: #aabffe;
    border-radius: 9999rpx;
    background: rgba(94, 141, 249, 0.14);
  }
}

// 与后台表单一致：小号浅蓝标签 + 深色半透明输入框
.field-label {
  margin-bottom: 12rpx;
  font-size: 22rpx;
  font-weight: 600;
  color: #aabffe;
  letter-spacing: 0.07em;
}

.dev-input-row {
  display: flex;
  align-items: center;
  gap: 16rpx;
}

.field-wrap {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 16rpx;
  height: 88rpx;
  padding: 0 28rpx;
  border-radius: 20rpx;
  background: rgba(255, 255, 255, 0.06);
  border: 1rpx solid rgba(255, 255, 255, 0.12);
}

.field-input {
  flex: 1;
  min-width: 0;
  height: 88rpx;
  font-size: 28rpx;
  color: rgba(255, 255, 255, 0.90);
}

.dev-btn {
  flex-shrink: 0;
  height: 88rpx;
  line-height: 88rpx;
  padding: 0 40rpx;
  border: none;
  border-radius: 9999rpx;
  background: linear-gradient(to right, #cadbf3 0%, #a9beff 100%);
  color: #1a2a3a;
  font-size: 28rpx;
  font-weight: 600;
  white-space: nowrap;

  &::after { border: none; }
  &:active { transform: scale(0.98); }
}

.dev-hint {
  margin-top: 16rpx;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.35);
  text-align: center;
}

// ── 页脚：卡片外，保持可读 ────────────────────────────────
.page-footer {
  position: absolute;
  left: 0;
  right: 0;
  bottom: calc(40rpx + env(safe-area-inset-bottom));
  z-index: 2;
  text-align: center;
  font-size: 22rpx;
  color: rgba(255, 255, 255, 0.35);
  letter-spacing: 0.06em;
  pointer-events: none;
}
</style>
