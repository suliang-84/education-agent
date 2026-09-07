<template>
  <div class="login-root">

    <!-- ── 背景视频 ── -->
    <video class="bg-video" autoplay muted playsinline loop>
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

        <!-- 上半：品牌区（透明，文字叠在视频上） -->
        <div class="card-brand">
          <p class="brand-sys-name">MESH · 五力认知训练平台</p>
          <h1 class="brand-headline">智能教学数据<br>尽在掌握</h1>
          <div class="brand-pills">
            <span class="brand-pill">五力认知诊断</span>
            <span class="brand-pill">个性化训练</span>
            <span class="brand-pill">AI 智能助教</span>
          </div>
        </div>

        <!-- 下半：毛玻璃磨砂表单区 -->
        <div class="card-glass">
          <div class="glass-shimmer" />

          <transition name="fade-slide" mode="out-in">

            <!-- Step 1 -->
            <form v-if="step === 1" key="s1" class="form-body" @submit.prevent="handleLogin">
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
                <span v-if="!loading">继续</span>
                <span v-else class="spinner" />
              </button>
              <p class="hint-text">账号密码验证通过后，将发送短信验证码</p>
            </form>

            <!-- Step 2 -->
            <form v-else key="s2" class="form-body" @submit.prevent="handleVerify">
              <div class="sms-tip">
                <div class="sms-tip__icon">
                  <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3"/>
                  </svg>
                </div>
                <div>
                  <div class="sms-tip__title">验证码已发送</div>
                  <div class="sms-tip__sub">请查看绑定手机号的短信</div>
                </div>
              </div>
              <div class="field">
                <label class="field-label">
                  验证码
                  <span class="field-label-hint">（演示: 123456）</span>
                </label>
                <div class="field-wrap">
                  <input v-model="codeForm.code" class="field-input field-input--code" placeholder="000000" maxlength="6" inputmode="numeric" autocomplete="one-time-code" required />
                </div>
              </div>
              <button type="submit" class="submit-btn" :class="{ loading }">
                <span v-if="!loading">登录</span>
                <span v-else class="spinner" />
              </button>
              <button type="button" class="back-link" @click="step = 1">
                <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
                </svg>
                返回上一步
              </button>
            </form>

          </transition>
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

const step = ref(1)
const loading = ref(false)
const showPwd = ref(false)
const sessionToken = ref('')
const isHovering = ref(false)
const cardRef = ref<HTMLElement | null>(null)
const tiltX = ref(0)
const tiltY = ref(0)

const form = reactive({ username: 'admin001', password: 'password123' })
const codeForm = reactive({ code: '123456' })

const cardTransform = computed(() => ({
  transform: `perspective(1000px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg) scale3d(${isHovering.value ? 1.012 : 1}, ${isHovering.value ? 1.012 : 1}, 1)`,
  transition: isHovering.value
    ? 'transform 0.12s cubic-bezier(0.16,1,0.3,1)'
    : 'transform 0.65s cubic-bezier(0.16,1,0.3,1)',
}))

function handleCardMouseMove(e: MouseEvent) {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  tiltY.value = ((e.clientX - cx) / (rect.width / 2)) * 7
  tiltX.value = -((e.clientY - cy) / (rect.height / 2)) * 7
}

function handleMouseLeave() {
  isHovering.value = false
  tiltX.value = 0
  tiltY.value = 0
}

async function handleLogin() {
  loading.value = true
  try {
    const res = await authApi.login(form)
    sessionToken.value = res.session_token
    step.value = 2
  } catch { /* interceptor handles */ } finally { loading.value = false }
}

async function handleVerify() {
  loading.value = true
  try {
    const res = await authApi.verify2fa({ session_token: sessionToken.value, code: codeForm.code })
    authStore.setAuth(res.access_token, res.admin as { id: number; username: string; role: string })
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

// ── 卡片外壳：白色磨砂玻璃（0.4 opacity）────────────────────
.login-card {
  width: 400px;
  border-radius: 24px;
  overflow: hidden;
  will-change: transform;
  transform-style: preserve-3d;
  position: relative;
  background-color: #ffffff;

  // 白色磨砂玻璃核心
  backdrop-filter: blur(28px) saturate(180%);
  -webkit-backdrop-filter: blur(28px) saturate(180%);

  // 阴影：靛蓝色调，与品牌系统一致
  box-shadow:
    0 32px 72px rgba(79, 70, 229, 0.22),
    0 8px 28px rgba(79, 70, 229, 0.14),
    0 2px 6px rgba(0, 0, 0, 0.10);
}

// ── 上半：品牌区（继承卡片白色磨砂，深色文字）───────────────
.card-brand {
  padding: 38px 32px 26px;
  background: transparent;
}

.brand-sys-name {
  font-size: 10.5px;
  font-weight: 700;
  color: var(--indigo);
  letter-spacing: 0.14em;
  text-transform: uppercase;
  margin-bottom: 14px;
  opacity: 0.70;
}

.brand-headline {
  font-size: 28px;
  font-weight: 700;
  color: var(--text-1);
  line-height: 1.22;
  letter-spacing: -0.025em;
  margin-bottom: 20px;
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

// ── 下半：表单区（略深于品牌区，靛蓝细分割线）───────────────
.card-glass {
  position: relative;
  padding: 24px 32px 32px;
  background: rgba(255, 255, 255, 0.22);
  border-top: 1px solid rgba(79, 70, 229, 0.10);
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
  background: rgba(255, 255, 255, 0.58);
  border: 1.5px solid rgba(79, 70, 229, 0.14);
  transition: background 0.15s, border-color 0.15s, box-shadow 0.15s;

  &:focus-within {
    background: rgba(255, 255, 255, 0.88);
    border-color: rgba(79, 70, 229, 0.45);
    box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.10);
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
  color: var(--text-1);
  background: transparent;
  border: none;
  outline: none;
  padding: 11px 0;

  &::placeholder { color: var(--text-3); }
}

.field-input--code {
  font-family: var(--font-mono);
  font-size: 22px;
  letter-spacing: 0.24em;
  text-align: center;
  padding: 12px 0;
  color: var(--indigo);
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

// ── 提交按钮：热粉色胶囊 CTA（设计规范主行动色）─────────────
.submit-btn {
  width: 100%;
  height: 48px;
  margin-top: 4px;
  background: linear-gradient(135deg, #F43F7E 0%, #EC4899 100%);
  color: #fff;
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
  box-shadow:
    0 4px 16px rgba(244, 63, 126, 0.40),
    inset 0 1px 0 rgba(255, 255, 255, 0.20);
  transition: all 0.16s cubic-bezier(0.16, 1, 0.3, 1);

  &:hover {
    background: linear-gradient(135deg, #E11D63 0%, #DB2777 100%);
    box-shadow:
      0 6px 24px rgba(244, 63, 126, 0.54),
      inset 0 1px 0 rgba(255, 255, 255, 0.20);
    transform: translateY(-1px);
  }

  &:active  { transform: scale(0.98) translateY(0); }
  &.loading { opacity: 0.65; pointer-events: none; }
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

.hint-text {
  font-size: 11.5px;
  color: var(--text-3);
  text-align: center;
  margin-top: -2px;
}

// ── SMS 提示 ─────────────────────────────────────────────────
.sms-tip {
  display: flex;
  align-items: center;
  gap: 12px;
  background: rgba(79, 70, 229, 0.06);
  border: 1px solid rgba(79, 70, 229, 0.16);
  border-radius: 10px;
  padding: 12px 14px;

  &__icon {
    width: 30px;
    height: 30px;
    background: rgba(79, 70, 229, 0.12);
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    color: var(--indigo);
  }

  &__title { font-size: 13px; font-weight: 600; color: var(--text-1); }
  &__sub   { font-size: 11.5px; color: var(--text-3); margin-top: 2px; }
}

// ── 返回链接 ─────────────────────────────────────────────────
.back-link {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  gap: 5px;
  background: none;
  border: none;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-3);
  cursor: pointer;
  font-family: inherit;
  width: 100%;
  padding: 4px;
  transition: color 0.12s;

  &:hover { color: var(--text-1); }
}

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

// ── 步骤过渡 ─────────────────────────────────────────────────
.fade-slide-enter-active,
.fade-slide-leave-active { transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1); }
.fade-slide-enter-from   { opacity: 0; transform: translateX(10px); }
.fade-slide-leave-to     { opacity: 0; transform: translateX(-10px); }

// ── 响应式 ───────────────────────────────────────────────────
@media (max-width: 520px) {
  .login-stage    { padding-right: 0; padding: 0 16px; }
  .login-card     { width: 100%; }
  .card-brand     { padding: 28px 24px 20px; }
  .card-glass     { padding: 20px 24px 28px; }
  .brand-headline { font-size: 24px; }
}
</style>
