<script setup lang="ts">
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { authApi } from '@/api'
import { useAuthStore } from '@/store'
import { PAGES } from '@/constants'

// ── 从页面参数获取 temp_token（getCurrentPages 兼容写法） ─────────────────
const tempToken = ref('')

onMounted(() => {
  const pages = getCurrentPages()
  const current = pages[pages.length - 1]
  const options = (current as any)?.options || {}
  tempToken.value = options.temp_token || ''
})

const authStore = useAuthStore()

// ── 年级选项（G7→初一, G12→高三） ────────────────────────────────────────
const gradeOptions = [
  { label: '初一', value: 'G7' },
  { label: '初二', value: 'G8' },
  { label: '初三', value: 'G9' },
  { label: '高一', value: 'G10' },
  { label: '高二', value: 'G11' },
  { label: '高三', value: 'G12' },
]
const semesterOptions = [
  { label: '上学期', value: 'S1' },
  { label: '下学期', value: 'S2' },
]

// ── 表单状态 ──────────────────────────────────────────────────────────────
const selectedGrade = ref('G10')
const selectedSemester = ref('S1')
const phone = ref('')
const smsCode = ref('')
const submitting = ref(false)
const sendingCode = ref(false)
const countdown = ref(0)
let countdownTimer: ReturnType<typeof setInterval> | null = null

// ── 表单校验 ──────────────────────────────────────────────────────────────
const phoneValid = computed(() => /^1[3-9]\d{9}$/.test(phone.value))
const canSubmit = computed(() => phoneValid.value && smsCode.value.length === 6 && !submitting.value)
const canSendCode = computed(() => phoneValid.value && countdown.value === 0 && !sendingCode.value)

// ── 发送验证码 + 60 秒倒计时 ─────────────────────────────────────────────
async function sendSmsCode() {
  if (!canSendCode.value) return
  sendingCode.value = true
  try {
    await authApi.sendSms(phone.value, 'BIND_PHONE')
    uni.showToast({ title: '验证码已发送', icon: 'success' })
    // 开始倒计时
    countdown.value = 60
    countdownTimer = setInterval(() => {
      countdown.value--
      if (countdown.value <= 0) {
        clearInterval(countdownTimer!)
        countdownTimer = null
      }
    }, 1000)
  } catch {
    uni.showToast({ title: '发送失败，请重试', icon: 'none' })
  } finally {
    sendingCode.value = false
  }
}

// ── 提交绑定 ──────────────────────────────────────────────────────────────
async function handleSubmit() {
  if (!canSubmit.value) return
  submitting.value = true
  try {
    const resp = await authApi.bindPhone(
      {
        phone: phone.value,
        sms_code: smsCode.value,
        grade: selectedGrade.value,
        semester: selectedSemester.value,
      },
      tempToken.value
    )
    // 保存认证信息
    authStore.setAuth({
      access_token: resp.access_token,
      refresh_token: resp.refresh_token,
      user_info: resp.user_info,
    })
    uni.showToast({ title: '绑定成功', icon: 'success' })
    // 新用户没有五力画像，进入测试引导页
    setTimeout(() => {
      uni.reLaunch({ url: PAGES.TEST_HOME })
    }, 800)
  } catch {
    uni.showToast({ title: '绑定失败，请检查验证码', icon: 'none' })
  } finally {
    submitting.value = false
  }
}

onUnmounted(() => {
  if (countdownTimer) clearInterval(countdownTimer)
})
</script>

<template>
  <view class="bind-phone-page">
    <!-- 页头说明 -->
    <view class="page-header">
      <text class="page-title">绑定手机号</text>
      <text class="page-desc">完善信息后即可开始个性化学习之旅</text>
    </view>

    <view class="form-card">
      <!-- 年级选择 -->
      <view class="form-section">
        <text class="form-label">我的年级</text>
        <scroll-view class="grade-scroll" scroll-x>
          <view class="grade-list">
            <view
              v-for="g in gradeOptions"
              :key="g.value"
              class="grade-chip"
              :class="{ 'grade-chip--active': selectedGrade === g.value }"
              @tap="selectedGrade = g.value"
            >
              <text class="grade-chip__text">{{ g.label }}</text>
            </view>
          </view>
        </scroll-view>
      </view>

      <!-- 学期选择 -->
      <view class="form-section">
        <text class="form-label">当前学期</text>
        <view class="semester-row">
          <view
            v-for="s in semesterOptions"
            :key="s.value"
            class="semester-btn"
            :class="{ 'semester-btn--active': selectedSemester === s.value }"
            @tap="selectedSemester = s.value"
          >
            <text class="semester-btn__text">{{ s.label }}</text>
          </view>
        </view>
      </view>

      <!-- 手机号输入 -->
      <view class="form-section">
        <text class="form-label">手机号</text>
        <view class="input-wrap">
          <text class="input-prefix">+86</text>
          <input
            v-model="phone"
            class="form-input"
            type="number"
            maxlength="11"
            placeholder="请输入手机号"
            placeholder-class="input-placeholder"
          />
          <view v-if="phone.length > 0" class="input-status">
            <text class="status-icon">{{ phoneValid ? '✓' : '✗' }}</text>
          </view>
        </view>
      </view>

      <!-- 验证码输入 -->
      <view class="form-section">
        <text class="form-label">验证码</text>
        <view class="input-wrap">
          <input
            v-model="smsCode"
            class="form-input form-input--code"
            type="number"
            maxlength="6"
            placeholder="6位验证码"
            placeholder-class="input-placeholder"
          />
          <button
            class="send-code-btn"
            :class="{ 'send-code-btn--disabled': !canSendCode }"
            :disabled="!canSendCode"
            @tap="sendSmsCode"
          >
            <text class="send-code-text">
              {{ sendingCode ? '发送中...' : countdown > 0 ? `${countdown}s后重发` : '获取验证码' }}
            </text>
          </button>
        </view>
        <text class="hint-text">开发环境验证码固定为 123456</text>
      </view>
    </view>

    <!-- 提交按钮 -->
    <button
      class="submit-btn"
      :class="{ 'submit-btn--disabled': !canSubmit }"
      :disabled="!canSubmit"
      @tap="handleSubmit"
    >
      <view v-if="submitting" class="spinner" />
      <text class="submit-btn__text">{{ submitting ? '提交中...' : '完成绑定，开始学习' }}</text>
    </button>
  </view>
</template>

<style lang="scss" scoped>

.bind-phone-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-5 $space-4 120rpx;
}

.page-header {
  margin-bottom: $space-5;
}

.page-title {
  display: block;
  font-size: $font-size-2xl;
  font-weight: 700;
  color: $text-1;
  margin-bottom: $space-2;
}

.page-desc {
  font-size: $font-size-sm;
  color: $text-2;
}

// 表单卡片
.form-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  box-shadow: $shadow-sm;
  margin-bottom: $space-4;
  display: flex;
  flex-direction: column;
  gap: $space-5;
}

.form-section {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.form-label {
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 500;
}

// 年级选择
.grade-scroll {
  white-space: nowrap;
}

.grade-list {
  display: flex;
  gap: $space-2;
  padding: 4rpx 0;
}

.grade-chip {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  height: 64rpx;
  padding: 0 $space-3;
  border-radius: $r-pill;
  background: $bg-muted;
  border: 2rpx solid transparent;
  transition: $transition-fast;
  flex-shrink: 0;

  &--active {
    background: $primary-light;
    border-color: $primary;
  }

  &__text {
    font-size: $font-size-sm;
    color: $text-2;
    font-weight: 500;

    .grade-chip--active & {
      color: $primary;
      font-weight: 600;
    }
  }
}

// 学期选择
.semester-row {
  display: flex;
  gap: $space-3;
}

.semester-btn {
  flex: 1;
  height: 76rpx;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: $r-lg;
  background: $bg-muted;
  border: 2rpx solid transparent;
  transition: $transition-fast;

  &--active {
    background: $primary-light;
    border-color: $primary;
  }

  &__text {
    font-size: $font-size-base;
    color: $text-2;
    font-weight: 500;

    .semester-btn--active & {
      color: $primary;
      font-weight: 600;
    }
  }
}

// 输入框
.input-wrap {
  display: flex;
  align-items: center;
  gap: $space-2;
  height: 88rpx;
  background: $bg-muted;
  border-radius: $r-md;
  padding: 0 $space-3;
  border: 2rpx solid transparent;

  &:focus-within {
    border-color: $primary;
    background: $bg-surface;
  }
}

.input-prefix {
  font-size: $font-size-base;
  color: $text-2;
  font-weight: 500;
  flex-shrink: 0;
}

.form-input {
  flex: 1;
  font-size: $font-size-base;
  color: $text-1;
  height: 100%;

  &--code {
    letter-spacing: 8rpx;
    font-size: $font-size-lg;
    font-weight: 600;
  }
}

.input-status {
  flex-shrink: 0;
  font-size: $font-size-base;

  .status-icon {
    color: $success;
  }
}

.send-code-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 $space-3;
  background: $primary;
  border-radius: $r-md;
  border: none;
  line-height: 64rpx;

  &::after { border: none; }

  &--disabled {
    background: $bg-muted;
  }

  &-text,
  .send-code-text {
    font-size: $font-size-xs;
    color: #fff;
    font-weight: 500;

    .send-code-btn--disabled & {
      color: $text-3;
    }
  }
}

.hint-text {
  font-size: $font-size-xs;
  color: $text-3;
  margin-top: $space-1;
}

// 提交按钮
.submit-btn {
  width: 100%;
  height: 100rpx;
  border-radius: $r-pill;
  background: $pink;
  border: none;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: $space-2;

  &::after { border: none; }

  &--disabled {
    background: $bg-muted;
  }

  &__text {
    font-size: $font-size-lg;
    color: #fff;
    font-weight: 700;

    .submit-btn--disabled & {
      color: $text-3;
    }
  }
}

.spinner {
  width: 36rpx;
  height: 36rpx;
  border-radius: 50%;
  border: 4rpx solid rgba(255,255,255,0.3);
  border-top-color: #fff;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
