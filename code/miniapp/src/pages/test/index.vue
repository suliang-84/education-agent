<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { testApi } from '@/api'
import { PAGES } from '@/constants'

// ── 检查是否有未完成的测试（本地存储） ───────────────────────────────────
const hasInProgress = ref(false)
const inProgressSessionId = ref<number | null>(null)
const starting = ref(false)
const resuming = ref(false)

onMounted(() => {
  // 从本地存储检查未完成会话
  const saved = uni.getStorageSync('mesh_test_session')
  if (saved) {
    try {
      const parsed = JSON.parse(saved)
      if (parsed.session_id && parsed.questions?.length) {
        hasInProgress.value = true
        inProgressSessionId.value = parsed.session_id
      }
    } catch {
      uni.removeStorageSync('mesh_test_session')
    }
  }
})

// ── 开始新测试 ────────────────────────────────────────────────────────────
async function startNewTest() {
  if (starting.value) return
  starting.value = true
  try {
    const resp = await testApi.getQuestions()
    // 缓存到本地，以便中断恢复
    uni.setStorageSync('mesh_test_session', JSON.stringify({
      session_id: resp.session_id,
      questions: resp.questions,
      current_index: 0,
      answers: [],
    }))
    uni.navigateTo({
      url: `${PAGES.TEST_QUESTIONS}?session_id=${resp.session_id}`,
    })
  } catch {
    uni.showToast({ title: '获取题目失败，请重试', icon: 'none' })
  } finally {
    starting.value = false
  }
}

// ── 恢复中断的测试 ────────────────────────────────────────────────────────
function resumeTest() {
  if (!inProgressSessionId.value) return
  resuming.value = true
  uni.navigateTo({
    url: `${PAGES.TEST_QUESTIONS}?session_id=${inProgressSessionId.value}&resume=1`,
  })
}

// ── 清除中断记录，重新开始 ────────────────────────────────────────────────
function clearAndStart() {
  uni.showModal({
    title: '重新开始',
    content: '将放弃上次的测试进度，确认重新开始吗？',
    success: (res) => {
      if (res.confirm) {
        uni.removeStorageSync('mesh_test_session')
        hasInProgress.value = false
        startNewTest()
      }
    },
  })
}
</script>

<template>
  <view class="test-index-page">
    <!-- 顶部装饰 -->
    <view class="hero-deco">
      <view class="brain-emoji">🧠</view>
    </view>

    <!-- 标题区 -->
    <view class="hero-content">
      <text class="hero-title">五力认知测试</text>
      <text class="hero-sub">了解你的认知特质，解锁专属学习方案</text>
    </view>

    <!-- 说明卡 -->
    <view class="info-card">
      <view class="info-row">
        <text class="info-icon">⏱️</text>
        <view class="info-text-wrap">
          <text class="info-label">预计用时</text>
          <text class="info-value">15-20 分钟</text>
        </view>
      </view>
      <view class="divider" />
      <view class="info-row">
        <text class="info-icon">📋</text>
        <view class="info-text-wrap">
          <text class="info-label">题目数量</text>
          <text class="info-value">共 20 道选择题</text>
        </view>
      </view>
      <view class="divider" />
      <view class="info-row">
        <text class="info-icon">🎯</text>
        <view class="info-text-wrap">
          <text class="info-label">测试维度</text>
          <text class="info-value">洞察·建构·推演·调适·迁移</text>
        </view>
      </view>
    </view>

    <!-- 五力简介 -->
    <view class="powers-preview">
      <text class="powers-title">测试将评估以下五力</text>
      <view class="powers-list">
        <view
          v-for="(item, idx) in [
            { name: '洞察力', color: '#0D9488', icon: '👁️', desc: '感知题目关键信息' },
            { name: '建构力', color: '#E11D48', icon: '🏗️', desc: '搭建解题框架' },
            { name: '推演力', color: '#4F46E5', icon: '⚙️', desc: '逻辑推导能力' },
            { name: '调适力', color: '#D97706', icon: '🔄', desc: '灵活调整策略' },
            { name: '迁移力', color: '#7C3AED', icon: '🚀', desc: '跨情境应用' },
          ]"
          :key="idx"
          class="power-preview-item"
        >
          <text class="power-preview-icon">{{ item.icon }}</text>
          <view class="power-preview-info">
            <text class="power-preview-name" :style="{ color: item.color }">{{ item.name }}</text>
            <text class="power-preview-desc">{{ item.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 中断恢复提示 -->
    <view v-if="hasInProgress" class="resume-card">
      <text class="resume-icon">⚡</text>
      <view class="resume-info">
        <text class="resume-title">发现未完成的测试</text>
        <text class="resume-desc">是否继续上次的测试进度？</text>
      </view>
      <button class="resume-btn" @tap="resumeTest">
        <text>中断恢复</text>
      </button>
    </view>

    <!-- 操作按钮区 -->
    <view class="action-area">
      <button
        class="start-btn"
        :class="{ 'start-btn--loading': starting }"
        :disabled="starting"
        @tap="hasInProgress ? clearAndStart() : startNewTest()"
      >
        <view v-if="starting" class="spinner" />
        <text class="start-btn__text">
          {{ starting ? '正在准备题目...' : hasInProgress ? '重新测试' : '开始测试' }}
        </text>
      </button>
      <text class="tip-text">测试过程中请确保网络稳定，题目会自动保存进度</text>
    </view>
  </view>
</template>

<style lang="scss" scoped>

.test-index-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-5 $space-4 120rpx;
}

// 顶部装饰
.hero-deco {
  display: flex;
  justify-content: center;
  margin-bottom: $space-3;
}

.brain-emoji {
  font-size: 120rpx;
  filter: drop-shadow(0 8rpx 24rpx rgba(79,70,229,0.2));
}

.hero-content {
  text-align: center;
  margin-bottom: $space-5;
}

.hero-title {
  display: block;
  font-size: $font-size-2xl;
  color: $text-1;
  font-weight: 800;
  margin-bottom: $space-2;
}

.hero-sub {
  font-size: $font-size-base;
  color: $text-2;
}

// 说明卡
.info-card {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-sm;
}

.info-row {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: $space-2 0;
}

.info-icon {
  font-size: 40rpx;
  flex-shrink: 0;
}

.info-text-wrap {
  display: flex;
  align-items: center;
  justify-content: space-between;
  flex: 1;
}

.info-label {
  font-size: $font-size-sm;
  color: $text-2;
}

.info-value {
  font-size: $font-size-sm;
  color: $text-1;
  font-weight: 600;
}

.divider {
  height: 1rpx;
  background: $border;
  margin: 4rpx 0;
}

// 五力预览
.powers-preview {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-4;
  margin-bottom: $space-4;
  box-shadow: $shadow-sm;
}

.powers-title {
  font-size: $font-size-base;
  color: $text-2;
  font-weight: 500;
  display: block;
  margin-bottom: $space-3;
}

.powers-list {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.power-preview-item {
  display: flex;
  align-items: center;
  gap: $space-3;
}

.power-preview-icon {
  font-size: 36rpx;
  flex-shrink: 0;
}

.power-preview-info {
  display: flex;
  align-items: center;
  gap: $space-2;
}

.power-preview-name {
  font-size: $font-size-sm;
  font-weight: 700;
}

.power-preview-desc {
  font-size: $font-size-xs;
  color: $text-3;
}

// 中断恢复卡
.resume-card {
  background: $warning-light;
  border: 2rpx solid $warning;
  border-radius: $r-lg;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  margin-bottom: $space-4;
}

.resume-icon {
  font-size: 36rpx;
  flex-shrink: 0;
}

.resume-info {
  flex: 1;
}

.resume-title {
  display: block;
  font-size: $font-size-sm;
  color: $text-1;
  font-weight: 600;
  margin-bottom: 4rpx;
}

.resume-desc {
  font-size: $font-size-xs;
  color: $text-2;
}

.resume-btn {
  flex-shrink: 0;
  height: 64rpx;
  padding: 0 $space-3;
  background: $warning;
  border: none;
  border-radius: $r-pill;
  font-size: $font-size-xs;
  color: #fff;
  font-weight: 600;

  &::after { border: none; }
}

// 操作区
.action-area {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
}

.start-btn {
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

  &--loading {
    opacity: 0.8;
  }

  &__text {
    font-size: $font-size-lg;
    color: #fff;
    font-weight: 700;
  }
}

.tip-text {
  font-size: $font-size-xs;
  color: $text-3;
  text-align: center;
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
