<template>
  <div class="login-root">

    <!-- ── 背景光斑 ── -->
    <div class="glow glow--indigo" />
    <div class="glow glow--pink" />
    <div class="glow glow--teal" />

    <!-- ── 左侧品牌区 ── -->
    <div class="brand-side">
      <div class="brand-logo">
        <div class="brand-icon">
          <svg width="24" height="24" viewBox="0 0 256 256" fill="none">
            <path fill="#fff" d="M 160 88 L 194 34 L 216 0 L 256 0 L 256 40 L 221.5 93.5 L 200 128 L 256 128 L 256 256 L 96 256 L 96 168 L 64.246 220 L 40 256 L 0 256 L 0 216 L 34 162 L 56 128 L 0 128 L 0 0 L 160 0 Z"/>
          </svg>
        </div>
        <span class="brand-name">MESH Admin</span>
      </div>
      <h2 class="brand-headline">智能教学数据<br>尽在掌握</h2>
      <p class="brand-desc">AI 驱动的五力认知训练平台<br>后台管理系统</p>
      <div class="brand-pills">
        <span class="brand-pill" style="background:rgba(79,70,229,0.10);color:#4F46E5">五力认知诊断</span>
        <span class="brand-pill" style="background:rgba(13,148,136,0.10);color:#0D9488">个性化训练</span>
        <span class="brand-pill" style="background:rgba(244,63,126,0.10);color:#F43F7E">AI 智能助教</span>
      </div>
    </div>

    <!-- ── 右侧登录卡片 ── -->
    <div class="card-side">
      <div
        class="glass-card"
        ref="cardRef"
        @mousemove="handleCardMouseMove"
        @mouseenter="isHovering = true"
        @mouseleave="handleMouseLeave"
        :style="cardTransform"
      >
        <!-- 顶部折射高光线 -->
        <div class="glass-shimmer" />

        <!-- Logo -->
        <div class="logo-wrap">
          <div class="logo-icon">
            <svg width="20" height="20" viewBox="0 0 256 256" fill="none">
              <path fill="#fff" d="M 160 88 L 194 34 L 216 0 L 256 0 L 256 40 L 221.5 93.5 L 200 128 L 256 128 L 256 256 L 96 256 L 96 168 L 64.246 220 L 40 256 L 0 256 L 0 216 L 34 162 L 56 128 L 0 128 L 0 0 L 160 0 Z"/>
            </svg>
          </div>
          <span class="logo-name">MESH Admin</span>
        </div>

        <h1 class="card-title">管理员登录</h1>
        <p class="card-sub">完成双因素验证后进入系统</p>

        <transition name="fade-slide" mode="out-in">

          <!-- Step 1: 账号密码 -->
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

          <!-- Step 2: 短信验证码 -->
          <form v-else key="s2" class="form-body" @submit.prevent="handleVerify">
            <div class="sms-tip">
              <div class="sms-tip__icon">
                <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="#4F46E5" stroke-width="1.8">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 1.5H8.25A2.25 2.25 0 006 3.75v16.5a2.25 2.25 0 002.25 2.25h7.5A2.25 2.25 0 0018 20.25V3.75a2.25 2.25 0 00-2.25-2.25H13.5m-3 0V3h3V1.5m-3 0h3"/>
                </svg>
              </div>
              <div>
                <div class="sms-tip__title">验证码已发送</div>
                <div class="sms-tip__sub">请查看绑定手机号的短信</div>
              </div>
            </div>
            <div class="field">
              <label class="field-label">验证码 <span style="color:#94A3B8;font-weight:400;font-size:12px">（演示: 123456）</span></label>
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

    <!-- 底部版权 -->
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
  transform: `perspective(900px) rotateX(${tiltX.value}deg) rotateY(${tiltY.value}deg) scale3d(${isHovering.value ? 1.015 : 1}, ${isHovering.value ? 1.015 : 1}, 1)`,
  transition: isHovering.value
    ? 'transform 0.12s cubic-bezier(0.16,1,0.3,1)'
    : 'transform 0.65s cubic-bezier(0.16,1,0.3,1)',
}))

function handleCardMouseMove(e: MouseEvent) {
  if (!cardRef.value) return
  const rect = cardRef.value.getBoundingClientRect()
  const cx = rect.left + rect.width / 2
  const cy = rect.top + rect.height / 2
  tiltY.value = ((e.clientX - cx) / (rect.width / 2)) * 10
  tiltX.value = -((e.clientY - cy) / (rect.height / 2)) * 10
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

<style scoped>
/* ── Root: split layout ─────────────────────────────────────── */
.login-root {
  display: flex;
  min-height: 100dvh;
  background: #E8ECF8;
  overflow: hidden;
  font-family: 'Inter', 'PingFang SC', system-ui, sans-serif;
  position: relative;
}

/* ── Background glows ───────────────────────────────────────── */
.glow {
  position: absolute;
  border-radius: 50%;
  filter: blur(90px);
  animation: glow-drift 14s ease-in-out infinite alternate;
  pointer-events: none;
  z-index: 0;
}
.glow--indigo { width: 520px; height: 520px; background: #818CF8; top: -12%; left: -10%; opacity: 0.38; animation-duration: 16s; }
.glow--pink   { width: 400px; height: 400px; background: #F9A8D4; bottom: -8%; left: 22%;  opacity: 0.30; animation-duration: 12s; animation-delay: -5s; }
.glow--teal   { width: 340px; height: 340px; background: #5EEAD4; top: 15%;   left: 35%;  opacity: 0.26; animation-duration: 10s; animation-delay: -8s; }

@keyframes glow-drift {
  0%   { transform: translate(0, 0) scale(1); }
  100% { transform: translate(28px, -22px) scale(1.1); }
}

/* ── Left: brand area ───────────────────────────────────────── */
.brand-side {
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  padding: 60px 64px;
  position: relative;
  z-index: 1;
}

.brand-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-bottom: 48px;
}

.brand-icon {
  width: 38px; height: 38px;
  background: #4F46E5;
  border-radius: 11px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 14px rgba(79,70,229,0.38);
}

.brand-name {
  font-size: 16px; font-weight: 700;
  color: #1E293B; letter-spacing: -0.02em;
}

.brand-headline {
  font-size: 40px; font-weight: 800;
  color: #1E293B;
  line-height: 1.18;
  letter-spacing: -0.03em;
  margin-bottom: 16px;
}

.brand-desc {
  font-size: 15px; color: #64748B;
  line-height: 1.7; margin-bottom: 36px;
}

.brand-pills {
  display: flex; flex-wrap: wrap; gap: 10px;
}

.brand-pill {
  font-size: 12.5px; font-weight: 500;
  padding: 6px 14px;
  border-radius: 9999px;
}

/* ── Right: card area ───────────────────────────────────────── */
.card-side {
  width: 460px;
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 48px;
  position: relative;
  z-index: 10;
}

/* ── Glass card ─────────────────────────────────────────────── */
.glass-card {
  width: 100%;
  padding: 32px 30px 28px;
  border-radius: 24px;
  position: relative;
  /* Glassmorphism */
  background: transparent;
  backdrop-filter: blur(28px) saturate(160%);
  -webkit-backdrop-filter: blur(28px) saturate(160%);
  border: 1px solid rgba(255, 255, 255, 0.40);
  box-shadow:
    inset 0 1.5px 0 rgba(255, 255, 255, 0.75),
    inset 1px 0 0 rgba(255, 255, 255, 0.18),
    0 24px 64px rgba(79, 70, 229, 0.18),
    0 8px 24px rgba(79, 70, 229, 0.10),
    0 2px 8px rgba(0, 0, 0, 0.06);
  will-change: transform;
  transform-style: preserve-3d;
}

.glass-shimmer {
  position: absolute;
  top: 0; left: 0; right: 0;
  height: 1px;
  background: linear-gradient(90deg, transparent, rgba(255,255,255,0.9) 30%, rgba(255,255,255,0.9) 70%, transparent);
  border-radius: 24px 24px 0 0;
  pointer-events: none;
}

/* ── Logo ── */
.logo-wrap {
  display: flex; align-items: center; gap: 10px;
  margin-bottom: 24px;
}
.logo-icon {
  width: 34px; height: 34px;
  background: #4F46E5;
  border-radius: 10px;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 3px 10px rgba(79,70,229,0.35);
}
.logo-name { font-size: 15px; font-weight: 700; color: #1E293B; letter-spacing: -0.02em; }

/* ── Title ── */
.card-title {
  font-size: 22px; font-weight: 700;
  color: #1E293B; letter-spacing: -0.03em;
  line-height: 1.2; margin-bottom: 5px;
}
.card-sub { font-size: 13px; color: #64748B; margin-bottom: 22px; }

/* ── Form ── */
.form-body { display: flex; flex-direction: column; gap: 14px; }
.field { display: flex; flex-direction: column; gap: 5px; }
.field-label { font-size: 12.5px; font-weight: 600; color: #334155; }

.field-wrap {
  display: flex; align-items: center;
  background: rgba(255, 255, 255, 0.72);
  border: 1.5px solid rgba(255, 255, 255, 0.65);
  border-radius: 10px;
  padding: 0 12px;
  gap: 8px;
  transition: all 0.15s;
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 1px 4px rgba(79,70,229,0.06);
}
.field-wrap:focus-within {
  border-color: rgba(79,70,229,0.55);
  background: rgba(255,255,255,0.88);
  box-shadow: inset 0 1px 0 rgba(255,255,255,0.9), 0 0 0 3px rgba(79,70,229,0.14);
}
.field-icon { color: #94A3B8; flex-shrink: 0; }
.field-input {
  flex: 1; min-width: 0;
  font-family: inherit; font-size: 14px; color: #1E293B;
  background: transparent; border: none; outline: none;
  padding: 10px 0;
}
.field-input::placeholder { color: #94A3B8; }
.field-input--code {
  font-family: 'JetBrains Mono', 'SF Mono', monospace;
  font-size: 20px; letter-spacing: 0.22em; text-align: center;
  padding: 12px 0;
}

.eye-btn {
  background: none; border: none; color: #94A3B8;
  cursor: pointer; display: flex; align-items: center;
  padding: 0; transition: color 0.12s;
}
.eye-btn:hover { color: #4F46E5; }

.submit-btn {
  width: 100%; height: 46px;
  background: linear-gradient(135deg, #F43F7E, #E11D63);
  color: #fff; border: none; border-radius: 9999px;
  font-size: 14.5px; font-weight: 700; font-family: inherit;
  cursor: pointer;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 4px 16px rgba(244,63,126,0.38);
  transition: all 0.15s cubic-bezier(0.16,1,0.3,1);
  margin-top: 4px;
}
.submit-btn:hover {
  background: linear-gradient(135deg, #EC4899, #DB1E6A);
  box-shadow: 0 6px 22px rgba(244,63,126,0.50);
  transform: translateY(-1px);
}
.submit-btn:active { transform: scale(0.97) translateY(0); }
.submit-btn.loading { opacity: 0.75; pointer-events: none; }

.spinner {
  width: 16px; height: 16px;
  border: 2px solid rgba(255,255,255,0.4);
  border-top-color: #fff;
  border-radius: 50%;
  animation: spin 0.65s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.hint-text { font-size: 12px; color: #64748B; text-align: center; margin-top: -4px; }

/* ── SMS tip ── */
.sms-tip {
  display: flex; align-items: center; gap: 10px;
  background: rgba(79,70,229,0.07);
  border: 1.5px solid rgba(79,70,229,0.15);
  border-radius: 10px; padding: 11px 14px;
}
.sms-tip__icon {
  width: 30px; height: 30px;
  background: rgba(79,70,229,0.10);
  border-radius: 8px;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.sms-tip__title { font-size: 13px; font-weight: 600; color: #1E293B; }
.sms-tip__sub   { font-size: 11.5px; color: #94A3B8; margin-top: 1px; }

.back-link {
  display: inline-flex; align-items: center; gap: 5px;
  background: none; border: none;
  font-size: 13px; font-weight: 500; color: #94A3B8;
  cursor: pointer; font-family: inherit;
  text-align: center; width: 100%;
  justify-content: center;
  padding: 4px; transition: color 0.12s;
}
.back-link:hover { color: #4F46E5; }

/* ── Footer ─────────────────────────────────────────────────── */
.page-footer {
  position: absolute;
  bottom: 20px; left: 0; right: 0;
  text-align: center;
  font-size: 12px; color: rgba(79,70,229,0.45);
  pointer-events: none; z-index: 5;
}

/* ── Step transition ── */
.fade-slide-enter-active,
.fade-slide-leave-active { transition: all 0.22s cubic-bezier(0.16,1,0.3,1); }
.fade-slide-enter-from { opacity: 0; transform: translateX(10px); }
.fade-slide-leave-to  { opacity: 0; transform: translateX(-10px); }

/* ── Responsive ── */
@media (max-width: 768px) {
  .login-root { flex-direction: column; }
  .brand-side { padding: 40px 28px 24px; }
  .brand-headline { font-size: 28px; }
  .card-side { width: 100%; padding: 0 20px 40px; }
}
</style>
