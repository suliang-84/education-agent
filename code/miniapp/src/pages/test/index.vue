<script setup lang="ts">
import { useTheme } from '@/hooks/useTheme'
import type { FivePower } from '@/constants'
import { ref, onMounted } from 'vue'
import { testApi } from '@/api'
import { PAGES } from '@/constants'
import SvgIcon from '@/components/SvgIcon.vue'


const { pageStyle, hl, isDark, powerColors } = useTheme()
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
  <page-meta :page-style="pageStyle" />
  <view class="test-index-page">
    <!-- 顶部装饰 -->
    <view class="hero-deco">
      <view class="brain-emoji"><SvgIcon name="brain" :size="72" /></view>
    </view>

    <!-- 标题区 -->
    <view class="hero-content">
      <text class="hero-title">五力认知测试</text>
      <text class="hero-sub">了解你的认知特质，解锁专属学习方案</text>
    </view>

    <!-- 说明卡 -->
    <view class="info-card" :style="hl('info')">
      <view class="info-row">
        <view class="info-icon"><SvgIcon name="calendar" :size="36" /></view>
        <view class="info-text-wrap">
          <text class="info-label">预计用时</text>
          <text class="info-value">15-20 分钟</text>
        </view>
      </view>
      <view class="divider" />
      <view class="info-row">
        <view class="info-icon"><SvgIcon name="book" :size="36" /></view>
        <view class="info-text-wrap">
          <text class="info-label">题目数量</text>
          <text class="info-value">共 20 道选择题</text>
        </view>
      </view>
      <view class="divider" />
      <view class="info-row">
        <view class="info-icon"><SvgIcon name="target" :size="36" /></view>
        <view class="info-text-wrap">
          <text class="info-label">测试维度</text>
          <text class="info-value">洞察·建构·推演·调适·迁移</text>
        </view>
      </view>
    </view>

    <!-- 五力简介 -->
    <view class="powers-preview" :style="hl('powers')">
      <text class="powers-title">测试将评估以下五力</text>
      <view class="powers-list">
        <view
          v-for="(item, idx) in [
            { key: 'INSIGHT', name: '洞察力', icon: 'target', desc: '感知题目关键信息' },
            { key: 'CONSTRUCT', name: '建构力', icon: 'ruler', desc: '搭建解题框架' },
            { key: 'DEDUCE', name: '推演力', icon: 'branch', desc: '逻辑推导能力' },
            { key: 'ADAPT', name: '调适力', icon: 'repeat', desc: '灵活调整策略' },
            { key: 'MIGRATE', name: '迁移力', icon: 'rocket', desc: '跨情境应用' },
          ]"
          :key="idx"
          class="power-preview-item"
        >
          <view class="power-preview-icon" :style="{ background: powerColors[item.key as FivePower] + '1A' }"><SvgIcon :name="item.icon" :size="32" :color="powerColors[item.key as FivePower]" /></view>
          <view class="power-preview-info">
            <text class="power-preview-name" :style="{ color: powerColors[item.key as FivePower] }">{{ item.name }}</text>
            <text class="power-preview-desc" :class="{ 'power-preview-desc--dark': isDark }">{{ item.desc }}</text>
          </view>
        </view>
      </view>
    </view>

    <!-- 中断恢复提示 -->
    <view v-if="hasInProgress" class="resume-card">
      <view class="resume-icon"><SvgIcon name="sparkles" :size="36" color="#F59E0B" /></view>
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
  width: 144rpx;
  height: 144rpx;
  border-radius: $r-xl;
  background: $primary-light;
  border: 1rpx solid $primary-border;
  box-shadow: $shadow-md;
  display: flex;
  align-items: center;
  justify-content: center;
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
  @include glass-panel;
  padding: 0;
  margin-bottom: $space-4;
  border: 1rpx solid $border;
}

.info-row {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: 28rpx 20rpx;   // 左右 10px；面板自身无内边距，上下留 28rpx 与下方五力模块的行高一致
}

.info-icon {
  width: 64rpx;
  height: 64rpx;
  border-radius: $r-md;
  background: $primary-light;
  display: flex;
  align-items: center;
  justify-content: center;
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
  margin: 0;
}

// 五力预览：面板自身不留内边距，标题行 / 每个维度行各自带内边距，行与行之间用通栏分割线分隔
.powers-preview {
  @include glass-panel;
  padding: 0;
  margin-bottom: $space-4;
  border: 1rpx solid $border;
}

.powers-title {
  display: block;
  padding: $space-4;
  font-size: $font-size-base;
  color: $primary;
  font-weight: 600;
  border-bottom: 1rpx solid $border;
}

.powers-list {
  display: flex;
  flex-direction: column;
}

.power-preview-item {
  display: flex;
  align-items: center;
  gap: $space-3;
  padding: 28rpx $space-4;

  & + & {
    border-top: 1rpx solid $border;
  }
}

.power-preview-icon {
  width: 56rpx;
  height: 56rpx;
  border-radius: $r-md;
  display: flex;
  align-items: center;
  justify-content: center;
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

  // 暗色下用白色，亮色保持原来的浅灰
  &--dark { color: #ffffff; }
}

// 中断恢复卡
.resume-card {
  background: $warning-light;
  border: 1rpx solid rgba(245, 158, 11, 0.35);
  border-radius: $r-lg;
  box-shadow: $shadow-sm;
  padding: $space-3 $space-4;
  display: flex;
  align-items: center;
  gap: $space-3;
  margin-bottom: $space-4;
}

.resume-icon {
  display: flex;
  align-items: center;
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
  color: $on-primary;
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
  background: $cta-gradient;
  box-shadow: $shadow-cta;
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
    color: $on-primary;
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
  border: 4rpx solid $on-primary-line;
  border-top-color: $on-primary;
  animation: spin 0.7s linear infinite;
}

@keyframes spin {
  to { transform: rotate(360deg); }
}
</style>
