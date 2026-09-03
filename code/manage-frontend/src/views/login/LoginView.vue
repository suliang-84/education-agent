<template>
  <div class="login-page">
    <!-- Floating math symbols — teaching atmosphere -->
    <div class="math-bg" aria-hidden="true">
      <span
        v-for="s in mathSymbols"
        :key="s.id"
        class="math-sym"
        :style="{
          left:              s.x + '%',
          animationDuration: s.dur + 's',
          animationDelay:    s.delay + 's',
          fontSize:          s.size + 'px',
          opacity:           s.alpha,
        }"
      >{{ s.char }}</span>
    </div>

    <!-- Blueprint grid overlay -->
    <div class="grid-overlay" aria-hidden="true"></div>

    <!-- Login card -->
    <div class="login-card">
      <!-- Logo -->
      <div class="login-logo">
        <div class="logo-mark">
          <span>M</span>
        </div>
        <h1 class="product-name">MESH 管理平台</h1>
        <p class="product-slogan">AI 认知训练系统后台管理</p>
      </div>

      <!-- Step 1: 账号密码 -->
      <div v-if="step === 1" class="step-body">
        <h2 class="step-title">管理员登录</h2>
        <el-form ref="loginFormRef" :model="loginForm" :rules="loginRules" @submit.prevent="handleLogin">
          <el-form-item prop="username">
            <el-input
              v-model="loginForm.username"
              placeholder="请输入用户名"
              size="large"
              :prefix-icon="User"
            />
          </el-form-item>
          <el-form-item prop="password">
            <el-input
              v-model="loginForm.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password
              :prefix-icon="Lock"
              @keyup.enter="handleLogin"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleLogin"
          >
            验证密码
          </el-button>
        </el-form>
        <p class="demo-hint">
          演示账号：<strong>admin001</strong> / 密码：<strong>admin123</strong>
        </p>
      </div>

      <!-- Step 2: 短信2FA -->
      <div v-if="step === 2" class="step-body">
        <div class="back-btn" @click="step = 1">
          <el-icon><ArrowLeft /></el-icon> 返回
        </div>
        <h2 class="step-title">短信验证</h2>
        <p class="phone-hint">验证码已发送至 <strong>{{ phoneMasked }}</strong></p>

        <el-form ref="twoFaFormRef" :model="twoFaForm" :rules="twoFaRules">
          <el-form-item prop="smsCode">
            <el-input
              v-model="twoFaForm.smsCode"
              placeholder="请输入6位短信验证码"
              size="large"
              maxlength="6"
              :prefix-icon="Key"
              @keyup.enter="handleVerify2FA"
            />
          </el-form-item>
          <el-button
            type="primary"
            size="large"
            :loading="loading"
            class="login-btn"
            @click="handleVerify2FA"
          >
            验证登录
          </el-button>
        </el-form>
        <p class="demo-hint">
          演示验证码：任意 <strong>6位数字</strong>（如 123456）
        </p>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { User, Lock, Key, ArrowLeft } from '@element-plus/icons-vue'
import { authApi } from '../../api'
import { useAuthStore } from '../../stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const step = ref(1)
const loading = ref(false)
const phoneMasked = ref('')
const sessionToken = ref('')

const loginFormRef = ref()
const twoFaFormRef = ref()

const loginForm = reactive({ username: 'admin001', password: 'admin123' })
const twoFaForm = reactive({ smsCode: '' })

// Teaching atmosphere — math & logic symbols floating upward
const mathSymbols = [
  { id:  1, char: '∑', x:  4, dur: 14, delay:  0,   size: 28, alpha: 0.13 },
  { id:  2, char: 'π', x: 12, dur: 10, delay:  2.5, size: 22, alpha: 0.10 },
  { id:  3, char: '∆', x: 21, dur: 17, delay:  5,   size: 32, alpha: 0.08 },
  { id:  4, char: '∞', x: 33, dur: 12, delay:  1,   size: 24, alpha: 0.11 },
  { id:  5, char: '∇', x: 46, dur: 19, delay:  7,   size: 20, alpha: 0.09 },
  { id:  6, char: 'λ', x: 58, dur: 11, delay:  3,   size: 26, alpha: 0.12 },
  { id:  7, char: '∫', x: 68, dur: 15, delay:  6,   size: 30, alpha: 0.08 },
  { id:  8, char: 'θ', x: 78, dur: 13, delay:  1.5, size: 22, alpha: 0.10 },
  { id:  9, char: 'φ', x: 88, dur: 18, delay:  4.5, size: 28, alpha: 0.09 },
  { id: 10, char: '√', x: 17, dur:  9, delay:  8,   size: 18, alpha: 0.08 },
  { id: 11, char: 'γ', x: 53, dur: 21, delay:  2,   size: 24, alpha: 0.10 },
  { id: 12, char: 'Σ', x: 76, dur: 13, delay:  9,   size: 20, alpha: 0.12 },
  { id: 13, char: 'ε', x: 38, dur: 16, delay: 10,   size: 20, alpha: 0.09 },
  { id: 14, char: 'μ', x: 93, dur: 14, delay:  3.5, size: 18, alpha: 0.08 },
]

const loginRules = {
  username: [{ required: true, message: '请输入用户名', trigger: 'blur' }],
  password: [{ required: true, message: '请输入密码', trigger: 'blur' }],
}
const twoFaRules = {
  smsCode: [
    { required: true, message: '请输入验证码', trigger: 'blur' },
    { len: 6, message: '验证码为6位数字', trigger: 'blur' },
  ],
}

async function handleLogin() {
  if (!loginFormRef.value) return
  const valid = await loginFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await authApi.login(loginForm.username, loginForm.password)
    if (res.status === 'success') {
      phoneMasked.value = res.data.phone_masked
      sessionToken.value = res.data.session_token
      step.value = 2
      ElMessage.success(res.msg)
    } else {
      ElMessage.error(res.msg)
    }
  } finally {
    loading.value = false
  }
}

async function handleVerify2FA() {
  if (!twoFaFormRef.value) return
  const valid = await twoFaFormRef.value.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    const res = await authApi.verify2fa(twoFaForm.smsCode, sessionToken.value)
    if (res.status === 'success') {
      authStore.setAuth(res.data.access_token, res.data.admin_info)
      ElMessage.success('登录成功')
      router.push('/dashboard')
    } else {
      ElMessage.error(res.msg)
    }
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
/* ── Login page — Synaptic Academy ── */
.login-page {
  min-height: 100vh;
  background:
    linear-gradient(145deg, #EEF2FF 0%, #F0F9FF 40%, #EDE9FE 70%, #F0F4FF 100%);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 24px;
  position: relative;
  overflow: hidden;
}

/* Blueprint dot grid */
.grid-overlay {
  position: absolute;
  inset: 0;
  background-image: radial-gradient(rgba(67, 97, 238, 0.12) 1px, transparent 1px);
  background-size: 32px 32px;
  pointer-events: none;
}

/* ── Floating math symbols ── */
.math-bg {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}

.math-sym {
  position: absolute;
  bottom: -8%;
  font-family: 'JetBrains Mono', 'Courier New', monospace;
  color: #4361EE;
  user-select: none;
  line-height: 1;
  animation: floatSymbol linear infinite;
}

@keyframes floatSymbol {
  0%   { transform: translateY(0) rotate(0deg);       opacity: 0; }
  8%   { opacity: 1; }
  92%  { opacity: 1; }
  100% { transform: translateY(-110vh) rotate(12deg);  opacity: 0; }
}

/* ── Login card ── */
.login-card {
  background: rgba(255, 255, 255, 0.88);
  backdrop-filter: blur(28px);
  -webkit-backdrop-filter: blur(28px);
  border-radius: 20px;
  padding: 48px 40px;
  width: 100%;
  max-width: 420px;
  border: 1px solid rgba(67, 97, 238, 0.12);
  box-shadow:
    0 24px 64px rgba(67, 97, 238, 0.13),
    0 0 0 1px rgba(67, 97, 238, 0.06),
    0 0 80px rgba(123, 47, 190, 0.07);
  position: relative;
  z-index: 1;
  animation: cardRise 0.65s cubic-bezier(0.16, 1, 0.3, 1) both;
}

@keyframes cardRise {
  from { opacity: 0; transform: translateY(28px) scale(0.97); }
  to   { opacity: 1; transform: translateY(0)    scale(1); }
}

/* ── Logo ── */
.login-logo {
  text-align: center;
  margin-bottom: 36px;
}

.logo-mark {
  width: 64px;
  height: 64px;
  background: linear-gradient(135deg, #4361EE 0%, #7B2FBE 100%);
  border-radius: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  margin: 0 auto 18px;
  animation: logoBreathe 3.5s ease-in-out infinite;
}

.logo-mark span {
  font-family: 'Outfit', sans-serif;
  font-size: 28px;
  font-weight: 900;
  color: #FFFFFF;
  letter-spacing: -1px;
}

@keyframes logoBreathe {
  0%, 100% { box-shadow: 0 6px 24px rgba(67, 97, 238, 0.35); }
  50%       { box-shadow: 0 8px 40px rgba(67, 97, 238, 0.55), 0 0 0 6px rgba(67, 97, 238, 0.08); }
}

.product-name {
  font-family: 'Outfit', sans-serif;
  font-size: 22px;
  font-weight: 700;
  color: #0F172A;
  margin: 0 0 8px;
  letter-spacing: -0.5px;
}

.product-slogan {
  font-size: 13px;
  color: #64748B;
  margin: 0;
  letter-spacing: 0.3px;
}

/* ── Step body ── */
.step-body { animation: fadeInUp 0.3s cubic-bezier(0.16, 1, 0.3, 1) both; }

@keyframes fadeInUp {
  from { opacity: 0; transform: translateY(10px); }
  to   { opacity: 1; transform: translateY(0); }
}

.step-title {
  font-family: 'Outfit', sans-serif;
  font-size: 18px;
  font-weight: 600;
  color: #0F172A;
  margin: 0 0 24px;
  text-align: center;
  letter-spacing: -0.3px;
}

/* Input fields */
:deep(.el-input__wrapper) {
  border-radius: 10px !important;
  background: rgba(67, 97, 238, 0.03) !important;
  border: 1px solid rgba(67, 97, 238, 0.14) !important;
  box-shadow: none !important;
  transition: border-color 0.2s, box-shadow 0.2s !important;
}
:deep(.el-input__wrapper:hover) {
  border-color: rgba(67, 97, 238, 0.3) !important;
}
:deep(.el-input__wrapper.is-focus) {
  border-color: rgba(67, 97, 238, 0.6) !important;
  box-shadow: 0 0 0 3px rgba(67, 97, 238, 0.08) !important;
}
:deep(.el-input__inner) {
  color: #0F172A !important;
  background: transparent !important;
  font-family: 'DM Sans', sans-serif !important;
}
:deep(.el-input__prefix-icon) { color: #94A3B8 !important; }

/* Login button */
.login-btn {
  width: 100%;
  height: 48px;
  font-family: 'Outfit', sans-serif !important;
  font-size: 15px !important;
  font-weight: 700 !important;
  background: linear-gradient(135deg, #4361EE 0%, #7B2FBE 100%) !important;
  border: none !important;
  border-radius: 10px !important;
  color: #FFFFFF !important;
  margin-top: 8px;
  letter-spacing: 0.3px;
  box-shadow: 0 4px 20px rgba(67, 97, 238, 0.35) !important;
  transition: all 0.2s ease !important;
}
.login-btn:hover {
  background: linear-gradient(135deg, #3451CA 0%, #6A27A5 100%) !important;
  box-shadow: 0 6px 28px rgba(67, 97, 238, 0.5) !important;
  transform: translateY(-1px);
}
.login-btn:active { transform: translateY(0) !important; }

/* Hints */
.demo-hint {
  text-align: center;
  font-size: 12px;
  color: #94A3B8;
  margin-top: 18px;
}
.demo-hint strong { color: #64748B; }

.phone-hint {
  text-align: center;
  font-size: 14px;
  color: #64748B;
  margin-bottom: 24px;
}

.back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  color: #4361EE;
  font-size: 14px;
  cursor: pointer;
  margin-bottom: 20px;
  opacity: 0.7;
  transition: opacity 0.2s;
}
.back-btn:hover { opacity: 1; }
</style>
