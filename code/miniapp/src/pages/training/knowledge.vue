<script setup lang="ts">
/**
 * 按知识点训练 · 选择知识点
 *
 * 流程：先按学生资料里的年级 / 学期取当前学期的单元与知识点；缺年级或学期时弹窗让学生补充；
 * 知识点按单元分组（默认全部展开，点单元标题可收起 / 展开）；点某个知识点才创建训练并进入答题页，
 * 题目由服务端从该知识点下「已启用」的题目里按题型 / 难度比例随机抽取。
 */
import { ref, computed } from 'vue'
import { onLoad } from '@dcloudio/uni-app'
import { useTheme } from '@/hooks/useTheme'
import { knowledgeApi, trainingApi, profileApi } from '@/api'
import type { Outline, OutlinePoint } from '@/api/knowledge'
import { useTrainingStore, useAuthStore } from '@/store'
import { PAGES, SUBJECT_LABELS } from '@/constants'

const { pageStyle, hl } = useTheme()
const trainingStore = useTrainingStore()
const authStore = useAuthStore()

const subject = ref('MATH')
const loading = ref(true)
const loadFailed = ref(false)
const outline = ref<Outline | null>(null)
const collapsed = ref<Record<number, boolean>>({})   // 章节 id → 是否收起（默认全部展开）
const creating = ref(false)

// 年级 / 学期补充弹窗
const showProfile = ref(false)
const pickGrade = ref('')
const pickSemester = ref('')
const profileError = ref('')
const saving = ref(false)

const subjectLabel = computed(() => SUBJECT_LABELS[subject.value] || '')
const gradeSemesterText = computed(() =>
  outline.value?.grade && outline.value?.semester
    ? `${outline.value.grade.name} · ${outline.value.semester.name}`
    : '',
)
const pointTotal = computed(() => (outline.value?.chapters ?? []).reduce((n, c) => n + c.points.length, 0))

onLoad((query) => {
  subject.value = (query?.subject as string) || 'MATH'
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
function openProfile(required = false) {
  pickGrade.value = outline.value?.grade?.code ?? ''
  pickSemester.value = outline.value?.semester?.code ?? ''
  profileError.value = ''
  showProfile.value = true
  requiredProfile.value = required
}
const requiredProfile = ref(false)

function cancelProfile() {
  showProfile.value = false
  if (requiredProfile.value) uni.navigateBack()   // 没有年级学期就无法列出知识点，取消即返回
}

async function saveProfile() {
  if (saving.value) return
  if (!pickGrade.value || !pickSemester.value) {
    profileError.value = !pickGrade.value ? '请选择年级' : '请选择学期'
    return
  }
  saving.value = true
  try {
    await profileApi.updateMe({ grade: pickGrade.value, semester: pickSemester.value })
    authStore.updateUserInfo({ grade: pickGrade.value, semester: pickSemester.value } as never)
    showProfile.value = false
    await load()
  } catch {
    profileError.value = '保存失败，请重试'
  } finally {
    saving.value = false
  }
}

// ── 单元展开 / 收起 ───────────────────────────────────────────────────────
function toggle(id: number) {
  collapsed.value = { ...collapsed.value, [id]: !collapsed.value[id] }
}

// ── 选定知识点，创建训练 ──────────────────────────────────────────────────
async function startPoint(p: OutlinePoint) {
  if (creating.value) return
  if (p.question_count <= 0) {
    uni.showToast({ title: '该知识点暂无题目', icon: 'none' })
    return
  }
  creating.value = true
  try {
    const resp = await trainingApi.createSession({
      training_dimension: 'KNOWLEDGE_POINT',
      knowledge_point_id: p.id,
      subject_code: subject.value,
    })
    trainingStore.initSession(resp, subject.value)
    uni.navigateTo({ url: PAGES.TRAINING_SESSION, complete: () => { setTimeout(() => { creating.value = false }, 800) } })
  } catch {
    creating.value = false
    uni.showToast({ title: '创建训练失败，请重试', icon: 'none' })
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
        <text class="kp-head__sub">共 {{ outline.chapters.length }} 个单元 · {{ pointTotal }} 个知识点</text>
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

    <!-- 单元 + 知识点 -->
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
    <view v-if="showProfile" class="mask mask--dialog">
      <view class="dialog">
        <text class="dialog__title">{{ requiredProfile ? '请先补充年级和学期' : '修改年级和学期' }}</text>
        <text class="dialog__desc">按你当前所在的年级和学期，为你列出对应的知识点</text>

        <text class="dialog__label">年级</text>
        <view class="chips">
          <view
            v-for="g in outline?.grade_options"
            :key="g.code"
            class="chip"
            :class="{ 'chip--active': pickGrade === g.code }"
            @tap="pickGrade = g.code; profileError = ''"
          ><text class="chip__text">{{ g.name }}</text></view>
        </view>

        <text class="dialog__label">学期</text>
        <view class="chips">
          <view
            v-for="s in outline?.semester_options"
            :key="s.code"
            class="chip chip--half"
            :class="{ 'chip--active': pickSemester === s.code }"
            @tap="pickSemester = s.code; profileError = ''"
          ><text class="chip__text">{{ s.name }}</text></view>
        </view>

        <text v-if="profileError" class="dialog__error">{{ profileError }}</text>

        <view class="dialog__btns">
          <button class="dlg-btn dlg-btn--cancel" @tap="cancelProfile">{{ requiredProfile ? '返回' : '取消' }}</button>
          <button class="dlg-btn dlg-btn--ok" @tap="saveProfile">确定</button>
        </view>
      </view>
    </view>
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

  &--dialog { padding: $space-6; z-index: 1000; }
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

.dialog {
  background: $bg-surface;
  border-radius: $r-xl;
  padding: $space-5;
  width: 100%;
  border: 1rpx solid $border;
  box-shadow: $shadow-md;
  display: flex;
  flex-direction: column;
  gap: $space-2;

  &__title { font-size: $font-size-lg; color: $text-1; font-weight: 700; text-align: center; }
  &__desc { font-size: $font-size-sm; color: $text-3; text-align: center; margin-bottom: $space-2; }
  &__label { font-size: $font-size-sm; color: $text-2; font-weight: 600; margin-top: $space-2; }
  &__error { font-size: $font-size-sm; color: $danger; margin-top: $space-1; }
  &__btns { display: flex; gap: $space-2; margin-top: $space-3; }
}

.chips { display: flex; flex-wrap: wrap; gap: $space-2; }
.chip {
  height: 68rpx;
  padding: 0 $space-4;
  border-radius: $r-pill;
  background: $bg-muted;
  border: 1rpx solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;

  &--half { flex: 1; }
  &--active { background: $primary-light; border-color: $primary-border; }
  &__text { font-size: $font-size-sm; color: $text-2; font-weight: 500; }
  &--active &__text { color: $primary; font-weight: 600; }
}

.dlg-btn {
  flex: 1;
  height: 88rpx;
  line-height: 88rpx;
  border-radius: $r-pill;
  font-size: $font-size-base;
  font-weight: 600;
  border: none;
  padding: 0;
  &::after { border: none; }

  &--cancel { background: $bg-muted; color: $text-2; }
  &--ok { background: $cta-gradient; color: $on-primary; box-shadow: $shadow-cta; }
}
</style>
