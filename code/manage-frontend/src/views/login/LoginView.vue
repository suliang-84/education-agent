<template>
  <div class="login-root">

    <!-- ── 背景视频 ── -->
    <video class="bg-video" autoplay muted playsinline loop >
      <source src="@/assets/login-background.mp4" type="video/mp4" />
    </video>
    <div class="bg-overlay" />

    <!-- ── 居中登录卡片 ── -->
    <div class="login-stage">
      <div
        class="login-card"
        ref="cardRef"
        @mousemove="handleCardMouseMove"
        @mouseenter="isHovering = true"
        @mouseleave="handleMouseLeave"
        :style="cardTransform"
      >

        <!-- 整体：品牌 + 表单 -->
        <div class="card-body">
          <p class="brand-sys-name">MESH · 后台管理系统</p>
          <div class="brand-headline">智能教学数据尽在掌握</div>

          <form class="form-body" @submit.prevent="handleLogin">
            <div class="field">
              <label class="field-label">账号</label>
              <div class="field-wrap">
                <svg class="field-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
                </svg>
                <input v-model="form.username" class="field-input" placeholder="管理员账号" autocomplete="username" required />
              </div>
            </div>
            <div class="field">
              <label class="field-label">密码</label>
              <div class="field-wrap">
                <svg class="field-icon" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 10.5V6.75a4.5 4.5 0 10-9 0v3.75m-.75 11.25h10.5a2.25 2.25 0 002.25-2.25v-6.75a2.25 2.25 0 00-2.25-2.25H6.75a2.25 2.25 0 00-2.25 2.25v6.75a2.25 2.25 0 002.25 2.25z"/>
                </svg>
                <input v-model="form.password" :type="showPwd ? 'text' : 'password'" class="field-input" placeholder="••••••••" autocomplete="current-password" required />
                <button type="button" class="eye-btn" @click="showPwd = !showPwd" tabindex="-1">
                  <svg v-if="!showPwd" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M2.036 12.322a1.012 1.012 0 010-.639C3.423 7.51 7.36 4.5 12 4.5c4.638 0 8.573 3.007 9.963 7.178.07.207.07.431 0 .639C20.577 16.49 16.64 19.5 12 19.5c-4.638 0-8.573-3.007-9.963-7.178z"/>
                    <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M3.98 8.223A10.477 10.477 0 001.934 12C3.226 16.338 7.244 19.5 12 19.5c.993 0 1.953-.138 2.863-.395M6.228 6.228A10.45 10.45 0 0112 4.5c4.756 0 8.773 3.162 10.065 7.498a10.523 10.523 0 01-4.293 5.774M6.228 6.228L3 3m3.228 3.228l3.65 3.65m7.894 7.894L21 21m-3.228-3.228l-3.65-3.65m0 0a3 3 0 10-4.243-4.243m4.242 4.242L9.88 9.88"/>
                  </svg>
                </button>
              </div>
            </div>
            <button type="submit" class="submit-btn" :class="{ loading }">
              <span v-if="!loading">登录</span>
              <span v-else class="spinner" />
            </button>
          </form>
        </div>

      </div>
    </div>

    <div class="page-footer">MESH AI · 认知训练平台管理系统</div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed } from 'vue'
import { useRouter } from 'vue-router'
import { authApi } from '@/api'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const loading = ref(false)
const showPwd = ref(false)
const isHovering = ref(false)
const cardRef = ref<HTMLElement | null>(null)
const tiltX = ref(0)
const tiltY = ref(0)
const mouseX = ref(50)
const mouseY = ref(50)

const form = reactive({ username: '', password: '' })

const cardTransform = computed(() => ({
  transform: `perspective(1000px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg) scale3d(${isHovering.value ? 1.012 : 1}, ${isHovering.value ? 1.012 : 1}, 1)`,
  transition: isHovering.value
    ? 'transform 0.12s cubic-bezier(0.16,1,0.3,1)'
    : 'transform 0.65s cubic-bezier(0.16,1,0.3,1)',
  '--mouse-x': `${mouseX.value}%`,
  '--mouse-y': `${mouseY.value}%`,
  '--hovering': isHovering.value ? '1' : '0',
}))

function handleCardMouseMove(e: MouseEvent) {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  tiltY.value = ((e.clientX - cx) / (rect.width / 2)) * 7
  tiltX.value = -((e.clientY - cy) / (rect.height / 2)) * 7
  mouseX.value = ((e.clientX - rect.left) / rect.width) * 100
  mouseY.value = ((e.clientY - rect.top) / rect.height) * 100
}

function handleMouseLeave() {
  isHovering.value = false
  tiltX.value = 0
  tiltY.value = 0
  mouseX.value = 50
  mouseY.value = 50
}

async function handleLogin() {
  loading.value = true
  try {
    const res = await authApi.login(form)
    authStore.setAuth(res.access_token, res.admin)
    router.push('/')
  } catch { /* interceptor handles */ } finally { loading.value = false }
}
</script>

<style lang="scss" scoped>
// ── 根容器 ───────────────────────────────────────────────────
.login-root {
  display: flex;
  align-items: center;
  justify-content: flex-end;
  min-height: 100dvh;
  overflow: hidden;
  font-family: var(--font-sans);
  position: relative;
}

// ── 背景视频 ─────────────────────────────────────────────────
.bg-video {
  position: absolute;
  inset: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  z-index: 0;
  pointer-events: none;
}

// 轻压暗：让白色磨砂玻璃的反差更明显
.bg-overlay {
  position: absolute;
  inset: 0;
  z-index: 1;
  pointer-events: none;
}

// ── 登录舞台 ─────────────────────────────────────────────────
.login-stage {
  position: relative;
  z-index: 2;
  padding-right: 80px;
}

// ── 卡片外壳：玻璃质感 + 定时反光 + 鼠标跟随高亮边框 ─────────
.login-card {
  width: 400px;
  border-radius: 24px;
  overflow: hidden;
  will-change: transform;
  transform-style: preserve-3d;
  position: relative;

  // 玻璃质感：深色半透明 + 鼠标位置内部光晕
  background:
    radial-gradient(
      400px circle at var(--mouse-x, 50%) var(--mouse-y, -20%),
      rgba(94, 141, 249, 0.18),
      rgba(94, 141, 249, 0.04) 40%,
      transparent 65%
    ),
    rgba(12, 14, 18, 0.85);
  border: 1px solid rgba(12, 14, 18, 0.75);

  // 阴影
  box-shadow:
    0 32px 72px rgba(0, 0, 0, 0.60),
    0 8px 28px rgba(0, 0, 0, 0.40),
    inset 0 1px 0 rgba(255, 255, 255, 0.06);

  // 动态高亮边框（鼠标跟随）
  &::before {
    content: '';
    position: absolute;
    inset: 0;
    border-radius: 24px;
    padding: 1px;
    background: radial-gradient(
      280px circle at var(--mouse-x, 50%) var(--mouse-y, 0%),
      rgba(94, 141, 249, 0.85),
      rgba(255, 255, 255, 0.20) 40%,
      rgba(255, 255, 255, 0.05) 70%
    );
    -webkit-mask:
      linear-gradient(#fff 0 0) content-box,
      linear-gradient(#fff 0 0);
    -webkit-mask-composite: xor;
    mask-composite: exclude;
    pointer-events: none;
    z-index: 2;
  }

  // 定时反光：单次光线扫过后长时间停顿
  &::after {
    content: '';
    position: absolute;
    inset: -100%;
    border-radius: 24px;
    background: linear-gradient(
      125deg,
      transparent 40%,
      rgba(255, 255, 255, 0.06) 48%,
      rgba(255, 255, 255, 0.13) 50%,
      rgba(255, 255, 255, 0.06) 52%,
      transparent 60%
    );
    animation: glass-shine 8s ease-in-out infinite;
    pointer-events: none;
    z-index: 1;
  }
}

@keyframes glass-shine {
  0%   { transform: translateX(-120%) translateY(-120%); opacity: 0; }
  5%   { opacity: 1; }
  75%  { transform: translateX(120%) translateY(120%); opacity: 1; }
  82%  { opacity: 0; }
  100% { transform: translateX(120%) translateY(120%); opacity: 0; }
}

// ── 卡片内容区（整体统一）────────────────────────────────────
.card-body {
  padding: 38px 32px 32px;
  position: relative;
  z-index: 1;
}

.brand-sys-name {
  font-size: 18px;
  font-weight: 700;
  color: #ffffff;
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 14px;
  opacity: 0.70;
}

.brand-headline {
  font-size: 12px;
  font-weight: 600;
  background: linear-gradient(to right, #cadbf3, #698cbc);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  background-clip: text;
  line-height: 1.22;
  letter-spacing: -0.025em;
  margin-bottom: 50px;
}

.brand-pills {
  display: flex;
  flex-wrap: wrap;
  gap: 7px;
}

.brand-pill {
  font-size: 11px;
  font-weight: 500;
  padding: 4px 11px;
  border-radius: 9999px;
  background: rgba(79, 70, 229, 0.08);
  color: var(--indigo);
  border: 1px solid rgba(79, 70, 229, 0.18);
  letter-spacing: 0.02em;
}


// 分割线正中的靛蓝微光，增加光学层次
.glass-shimmer {
  position: absolute;
  top: 0;
  left: 15%;
  right: 15%;
  height: 1px;
  background: linear-gradient(
    90deg,
    transparent,
    rgba(79, 70, 229, 0.22) 40%,
    rgba(79, 70, 229, 0.22) 60%,
    transparent
  );
  pointer-events: none;
}

// ── 表单 ─────────────────────────────────────────────────────
.form-body {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.field-label {
  font-size: 11px;
  font-weight: 600;
  color: var(--text-2);
  letter-spacing: 0.07em;
  text-transform: uppercase;
}

.field-label-hint {
  font-size: 11px;
  font-weight: 400;
  color: var(--text-3);
  text-transform: none;
  letter-spacing: 0;
}

.field-wrap {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 14px;
  border-radius: 10px;
  background: rgba(255, 255, 255, 0.06);
  border: 1px solid rgba(255, 255, 255, 0.12);
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;

  &:focus-within {
    background: rgba(255, 255, 255, 0.10);
    border-color: rgba(94, 141, 249, 0.50);
    box-shadow: 0 0 0 3px rgba(94, 141, 249, 0.08);
  }
}

.field-icon {
  color: var(--text-3);
  flex-shrink: 0;
}

.field-input {
  flex: 1;
  min-width: 0;
  font-family: inherit;
  font-size: 14px;
  color: rgba(255, 255, 255, 0.90);
  background: transparent !important;
  background-color: transparent !important;
  border: none;
  outline: none;
  padding: 11px 0;
  -webkit-appearance: none;
  appearance: none;
  box-shadow: none !important;

  // 覆盖浏览器 autofill 白色背景
  &:-webkit-autofill,
  &:-webkit-autofill:hover,
  &:-webkit-autofill:focus {
    -webkit-box-shadow: 0 0 0 1000px rgba(30, 34, 40, 0.01) inset !important;
    -webkit-text-fill-color: rgba(255, 255, 255, 0.90) !important;
    background-color: transparent !important;
    transition: background-color 99999s ease-in-out 0s;
  }

  &::placeholder { color: rgba(255, 255, 255, 0.35); }
}

.eye-btn {
  background: none;
  border: none;
  color: var(--text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 0;
  transition: color 0.12s;

  &:hover { color: var(--text-1); }
}

// ── 提交按钮：白到蓝渐变，鼠标移入登录框时蓝色从右铺满 ────────
.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  // 背景宽度 200%：左半为白→蓝，右半为纯蓝
  // 默认显示左半（position 0%），hover 显示右半（position 100%）
  background: linear-gradient(to right, #cadbf3 0%, #698cbc 50%, #698cbc 100%);
  background-size: 200% 100%;
  background-position: 0% 0%;
  color: #1a2a3a;
  border: none;
  border-radius: 9999px;
  font-size: 14px;
  font-weight: 600;
  font-family: inherit;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  letter-spacing: 0.02em;
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.30);
  transition: background-position 0.8s ease, color 0.4s ease, box-shadow 0.3s ease;

  &:active  { transform: scale(0.98); }
  &.loading { opacity: 0.65; pointer-events: none; }
}

// 鼠标移入登录框时，蓝色从右线性铺满
.login-card:hover .submit-btn {
  background-position: 100% 0%;
  color: #ffffff;
  box-shadow:
    0 4px 20px rgba(105, 140, 188, 0.45),
    inset 0 1px 0 rgba(255, 255, 255, 0.20);
}

.spinner {
  width: 16px;
  height: 16px;
  border: 2px solid rgba(255, 255, 255, 0.35);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

// ── 版权（卡片外，保持白色可读）─────────────────────────────
.page-footer {
  position: absolute;
  bottom: 20px;
  left: 0;
  right: 0;
  text-align: center;
  font-size: 11.5px;
  color: rgba(255, 255, 255, 0.35);
  pointer-events: none;
  z-index: 2;
  letter-spacing: 0.06em;
}

// ── 响应式 ───────────────────────────────────────────────────
@media (max-width: 520px) {
  .login-stage    { padding-right: 0; padding: 0 16px; }
  .login-card     { width: 100%; }
  .card-brand     { padding: 28px 24px 20px; }
  .card-glass     { padding: 20px 24px 28px; }
  .brand-headline { font-size: 24px; }
}
</style>

<style>
/* 登录页输入框透明背景（不加 scoped 确保覆盖浏览器默认样式） */
.login-root input.field-input {
  background: transparent !important;
  background-color: transparent !important;
}
</style>
