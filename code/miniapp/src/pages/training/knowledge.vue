<script setup lang="ts">
/**
 * 按知识点 / 按单元训练 · 选择知识点或单元（mode=point | unit）
 *
 * 按单元与按知识点共用本页：范围判断、补充年级学期弹窗、创建中遮罩都一样，
 * 区别只在于：按单元只列出当前学期的单元（不展开知识点），点单元直接创建训练，从该单元下所有知识点的已启用题目里抽题。
 *
 * 流程：先按学生资料里的年级 / 学期取当前学期的单元与知识点；缺年级或学期时弹窗让学生补充；
 * 知识点按单元分组（默认全部展开，点单元标题可收起 / 展开）；点某个知识点才创建训练并进入答题页，
 * 题目由服务端从该知识点下「已启用」的题目里按题型 / 难度比例随机抽取。
 */
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/hooks/useTheme'
import { knowledgeApi, trainingApi } from '@/api'
import GradeSemesterDialog from '@/components/training/GradeSemesterDialog.vue'
import type { Outline, OutlinePoint, OutlineChapter } from '@/api/knowledge'
import { useTrainingStore } from '@/store'
import { PAGES, SUBJECT_LABELS } from '@/constants'

const { pageStyle, hl } = useTheme()
const trainingStore = useTrainingStore()

const subject = ref('MATH')
const unitMode = ref(false)   // true：按单元训练，只选单元
const loading = ref(true)
const loadFailed = ref(false)
const outline = ref<Outline | null>(null)
const collapsed = ref<Record<number, boolean>>({})   // 章节 id → 是否收起（默认全部展开）
const creating = ref(false)


const subjectLabel = computed(() => SUBJECT_LABELS[subject.value] || '')
const gradeSemesterText = computed(() =>
  outline.value?.grade && outline.value?.semester
    ? `${outline.value.grade.name} · ${outline.value.semester.name}`
    : '',
)
const pointTotal = computed(() => (outline.value?.chapters ?? []).reduce((n, c) => n + c.points.length, 0))

onLoad((query) => {
  subject.value = (query?.subject as string) || 'MATH'
  unitMode.value = query?.mode === 'unit'
  uni.setNavigationBarTitle({ title: unitMode.value ? '选择单元' : '选择知识点' })
  load()
})

async function load() {
  loading.value = true
  loadFailed.value = false
  try {
    outline.value = await knowledgeApi.getOutline(subject.value)
    if (outline.value.need_profile) openProfile(true)
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}

// ── 补充 / 修改年级学期 ───────────────────────────────────────────────────
const showProfile = ref(false)
const requiredProfile = ref(false)
function openProfile(required = false) {
  requiredProfile.value = required
  showProfile.value = true
}
function cancelProfile() {
  showProfile.value = false
  if (requiredProfile.value) uni.navigateBack()   // 没有年级学期就无法列出内容，取消即返回
}
async function onProfileSaved() {
  showProfile.value = false
  await load()
}

// ── 单元展开 / 收起 ───────────────────────────────────────────────────────
function toggle(id: number) {
  collapsed.value = { ...collapsed.value, [id]: !collapsed.value[id] }
}

// ── 选定知识点 / 单元，创建训练 ───────────────────────────────────────────
function startPoint(p: OutlinePoint) {
  start(p.question_count, '该知识点暂无题目', { training_dimension: 'KNOWLEDGE_POINT', knowledge_point_id: p.id })
}
function startChapter(ch: OutlineChapter) {
  start(ch.question_count, '该单元暂无题目', { training_dimension: 'UNIT', chapter_id: ch.id })
}
async function start(count: number, emptyTip: string, scope: { training_dimension: 'KNOWLEDGE_POINT' | 'UNIT'; knowledge_point_id?: number; chapter_id?: number }) {
  if (creating.value) return
  if (count <= 0) {
    uni.showToast({ title: emptyTip, icon: 'none' })
    return
  }
  creating.value = true
  try {
    const resp = await trainingApi.createSession({ ...scope, subject_code: subject.value })
    trainingStore.initSession(resp, subject.value)
    uni.navigateTo({ url: PAGES.TRAINING_SESSION, complete: () => { setTimeout(() => { creating.value = false }, 800) } })
  } catch {
    creating.value = false   // 失败原因已由请求层弹出提示
  }
}
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="kp-page">
    <!-- 顶部：当前年级学期 -->
    <view v-if="outline && !outline.need_profile" class="kp-head" :style="hl('kp-head')">
      <view class="kp-head__info">
        <text class="kp-head__title">{{ subjectLabel }} · {{ gradeSemesterText }}</text>
        <text class="kp-head__sub">共 {{ outline.chapters.length }} 个单元{{ unitMode ? '' : ' · ' + pointTotal + ' 个知识点' }}</text>
      </view>
      <view class="kp-head__edit" @tap="openProfile(false)"><text>修改</text></view>
    </view>

    <view v-if="loading" class="kp-state"><view class="spinner" /></view>

    <view v-else-if="loadFailed" class="kp-state">
      <text class="kp-state__text">加载失败</text>
      <view class="kp-state__btn" @tap="load"><text>重试</text></view>
    </view>

    <view v-else-if="outline && !outline.need_profile && outline.chapters.length === 0" class="kp-state">
      <text class="kp-state__text">{{ gradeSemesterText }}暂无{{ subjectLabel }}知识点</text>
      <view class="kp-state__btn" @tap="openProfile(false)"><text>修改年级学期</text></view>
    </view>

    <!-- 按单元：只列单元，点单元直接开始 -->
    <template v-else-if="outline && !outline.need_profile && unitMode">
      <view v-for="ch in outline.chapters" :key="ch.id" class="chapter" :style="hl('ch-' + ch.id)">
        <view class="chapter__head" @tap="startChapter(ch)">
          <view class="chapter__info">
            <text class="chapter__name" :class="{ 'point__name--empty': ch.question_count <= 0 }">{{ ch.name }}</text>
            <text class="chapter__count">{{ ch.points.length }} 个知识点 · {{ ch.question_count > 0 ? ch.question_count + ' 题' : '暂无题目' }}</text>
          </view>
          <text class="point__arrow">›</text>
        </view>
      </view>
    </template>

    <!-- 按知识点：单元 + 知识点 -->
    <template v-else-if="outline && !outline.need_profile">
      <view v-for="ch in outline.chapters" :key="ch.id" class="chapter" :style="hl('ch-' + ch.id)">
        <view class="chapter__head" @tap="toggle(ch.id)">
          <text class="chapter__name">{{ ch.name }}</text>
          <text class="chapter__count">{{ ch.points.length }} 个知识点</text>
          <text class="chapter__arrow" :class="{ 'chapter__arrow--open': !collapsed[ch.id] }">›</text>
        </view>
        <view v-if="!collapsed[ch.id]" class="chapter__body">
          <view
            v-for="p in ch.points"
            :key="p.id"
            class="point"
            @tap="startPoint(p)"
          >
            <text class="point__name" :class="{ 'point__name--empty': p.question_count <= 0 }">{{ p.name }}</text>
            <text class="point__count">{{ p.question_count > 0 ? p.question_count + ' 题' : '暂无题目' }}</text>
            <text class="point__arrow">›</text>
          </view>
          <view v-if="ch.points.length === 0" class="point"><text class="point__count">该单元暂无知识点</text></view>
        </view>
      </view>
    </template>

    <!-- 创建中遮罩 -->
    <view v-if="creating" class="mask">
      <view class="mask__inner">
        <view class="spinner" />
        <text class="mask__text">正在准备训练题目...</text>
      </view>
    </view>

    <!-- 补充 / 修改年级学期弹窗 -->
    <GradeSemesterDialog
      :show="showProfile"
      :required="requiredProfile"
      :grade-options="outline?.grade_options ?? []"
      :semester-options="outline?.semester_options ?? []"
      :grade="outline?.grade?.code"
      :semester="outline?.semester?.code"
      @saved="onProfileSaved"
      @cancel="cancelProfile"
    />
  </view>
</template>

<style lang="scss" scoped>
.kp-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 80rpx;
}

.kp-head {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: $space-3 $space-4;
  margin-bottom: 20rpx;
  display: flex;
  align-items: center;
  gap: $space-3;

  &__info { flex: 1; display: flex; flex-direction: column; gap: 4rpx; }
  &__title { font-size: $font-size-lg; font-weight: 700; color: $text-1; }
  &__sub { font-size: $font-size-xs; color: $text-3; }
  &__edit {
    padding: 10rpx 24rpx;
    border-radius: $r-pill;
    background: $primary-light;
    font-size: $font-size-sm;
    color: $primary;
    font-weight: 600;
  }
}

.chapter {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: 0;
  margin-bottom: 20rpx;

  &__head {
    display: flex;
    align-items: center;
    gap: $space-2;
    padding: $space-3 $space-4;
  }
  &__info { flex: 1; display: flex; flex-direction: column; gap: 6rpx; }
  &__name { flex: 1; font-size: $font-size-base; font-weight: 700; color: $text-1; }
  &__count { font-size: $font-size-xs; color: $text-3; }
  &__arrow {
    font-size: 36rpx;
    color: $text-3;
    transition: transform 0.2s ease;
    &--open { transform: rotate(90deg); }
  }
}

.point {
  display: flex;
  align-items: center;
  gap: $space-2;
  padding: $space-3 $space-4;
  border-top: 1rpx solid $border;

  &:active { background: $primary-light; }
  &__name { flex: 1; font-size: $font-size-base; color: $text-1; &--empty { color: $text-3; } }
  &__count { font-size: $font-size-xs; color: $text-3; }
  &__arrow { font-size: 32rpx; color: $text-3; }
}

.kp-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: $space-3;
  padding-top: 200rpx;

  &__text { font-size: $font-size-base; color: $text-3; }
  &__btn {
    padding: 14rpx 36rpx;
    border-radius: $r-pill;
    background: $primary-light;
    font-size: $font-size-sm;
    color: $primary;
    font-weight: 600;
  }
}

.spinner {
  width: 60rpx;
  height: 60rpx;
  border-radius: 50%;
  border: 6rpx solid $bg-muted;
  border-top-color: $primary;
  animation: spin 0.7s linear infinite;
}
@keyframes spin { to { transform: rotate(360deg); } }

.mask {
  position: fixed;
  inset: 0;
  background: $mask;
  backdrop-filter: blur(6px);
  display: flex;
  align-items: center;
  justify-content: center;
  z-index: 999;

  &__inner {
    background: $bg-surface;
    border-radius: $r-xl;
    padding: $space-5;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: $space-3;
  }
  &__text { font-size: $font-size-base; color: $text-2; }
}
</style>
