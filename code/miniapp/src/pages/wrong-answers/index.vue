<script setup lang="ts">
/**
 * 错题集：待攻克 / 已攻克 → 单元 → 知识点（只含当前学期）
 *
 * - 每一级都可以点击，直接进入答题：待攻克 / 已攻克这一级从全部题里抽，单元一级只抽该单元的，知识点一级只抽该知识点的
 * - 每一级右侧是对应的题数（题目去重；同一道题无论答对答错几次都只算一道）
 * - 点右侧箭头展开 / 收起下一级（点行本身是进入答题）
 * - 答对归入已攻克、答错归入待攻克（规则在后端）；没有题的单元 / 知识点不展示
 */
import { ref, computed } from 'vue'
import { onLoad, onShow } from '@dcloudio/uni-app'
import { useTheme } from '@/hooks/useTheme'
import { wrongAnswerApi, trainingApi } from '@/api'
import type { WrongOutline, WrongTree } from '@/api/profile'
import { useTrainingStore } from '@/store'
import { PAGES, SUBJECT_LABELS } from '@/constants'
import GradeSemesterDialog from '@/components/training/GradeSemesterDialog.vue'

const { pageStyle, hl } = useTheme()
const trainingStore = useTrainingStore()

type Kind = 'pending' | 'mastered'
const subjects = Object.keys(SUBJECT_LABELS)
const subject = ref('MATH')
const fromTraining = ref(false)    // 从个性化训练进入时已选好科目，不再显示科目切换
const loading = ref(true)
const loadFailed = ref(false)
const outline = ref<WrongOutline | null>(null)
const closed = ref<Record<string, boolean>>({})   // 收起的节点：'pending' / 'pending-39'（默认全部展开）
const creating = ref(false)

const showProfile = ref(false)
const requiredProfile = ref(false)

const sections = computed<Array<{ kind: Kind; title: string; tree: WrongTree }>>(() =>
  outline.value
    ? [
        { kind: 'pending', title: '待攻克', tree: outline.value.pending },
        { kind: 'mastered', title: '已攻克', tree: outline.value.mastered },
      ]
    : [],
)
const gradeSemesterText = computed(() =>
  outline.value?.grade && outline.value?.semester ? `${outline.value.grade.name} · ${outline.value.semester.name}` : '',
)

onLoad((query) => {
  if (query?.subject) {
    subject.value = query.subject as string
    fromTraining.value = true
  }
  load()
})
// 训练结束返回时刷新统计
onShow(() => { if (outline.value) refresh() })

async function load() {
  loading.value = true
  loadFailed.value = false
  try {
    outline.value = await wrongAnswerApi.getOutline(subject.value)
    // 已攻克为 0 时默认不展开（用户手动展开过的不受影响）
    if (outline.value.mastered.count === 0 && closed.value.mastered === undefined) closed.value = { ...closed.value, mastered: true }
    if (outline.value.need_profile) openProfile(true)
  } catch {
    loadFailed.value = true
  } finally {
    loading.value = false
  }
}
async function refresh() {
  try {
    outline.value = await wrongAnswerApi.getOutline(subject.value)
    if (outline.value.mastered.count === 0 && closed.value.mastered === undefined) closed.value = { ...closed.value, mastered: true }
  } catch { /* 静默：保留旧数据 */ }
}
function switchSubject(code: string) {
  if (code === subject.value) return
  subject.value = code
  closed.value = {}
  load()
}

function openProfile(required = false) {
  requiredProfile.value = required
  showProfile.value = true
}
function cancelProfile() {
  showProfile.value = false
  if (requiredProfile.value && fromTraining.value) uni.navigateBack()
}
async function onProfileSaved() {
  showProfile.value = false
  await load()
}

function key(kind: Kind, chapterId?: number) {
  return chapterId ? `${kind}-${chapterId}` : kind
}
function toggle(k: string) {
  closed.value = { ...closed.value, [k]: !closed.value[k] }
}

// 点行 → 按该层级的范围创建错题集训练
async function start(kind: Kind, count: number, scope: { chapter_id?: number; knowledge_point_id?: number } = {}) {
  if (creating.value) return
  if (count <= 0) {
    uni.showToast({ title: kind === 'pending' ? '暂无待攻克题目' : '暂无已攻克题目', icon: 'none' })
    return
  }
  creating.value = true
  try {
    const resp = await trainingApi.createSession({
      training_dimension: 'ERROR_QUESTIONS',
      subject_code: subject.value,
      wrong_status: kind,
      ...scope,
    })
    trainingStore.initSession(resp, subject.value)
    uni.navigateTo({ url: PAGES.TRAINING_SESSION, complete: () => { setTimeout(() => { creating.value = false }, 800) } })
  } catch {
    creating.value = false   // 失败原因已由请求层弹出提示
  }
}
</script>

<template>
  <page-meta :page-style="pageStyle" />
  <view class="wb-page">
    <!-- 顶部：科目 + 当前年级学期 -->
    <view v-if="outline && !outline.need_profile" class="wb-head" :style="hl('wb-head')">
      <view class="wb-head__info">
        <text class="wb-head__title">{{ SUBJECT_LABELS[subject] }} · {{ gradeSemesterText }}</text>
        <text class="wb-head__sub">待攻克 {{ outline.pending.count }} 题 · 已攻克 {{ outline.mastered.count }} 题</text>
      </view>
      <view class="wb-head__edit" @tap="openProfile(false)"><text>修改</text></view>
    </view>

    <!-- 科目切换（从「我的」进入时没有预选科目） -->
    <view v-if="!fromTraining" class="wb-subjects">
      <view
        v-for="c in subjects"
        :key="c"
        class="wb-subject"
        :class="{ 'wb-subject--active': subject === c }"
        @tap="switchSubject(c)"
      ><text>{{ SUBJECT_LABELS[c] }}</text></view>
    </view>

    <view v-if="loading" class="wb-state"><view class="spinner" /></view>
    <view v-else-if="loadFailed" class="wb-state">
      <text class="wb-state__text">加载失败</text>
      <view class="wb-state__btn" @tap="load"><text>重试</text></view>
    </view>

    <template v-else-if="outline && !outline.need_profile">
      <view v-for="sec in sections" :key="sec.kind" class="wb-card" :style="hl('wb-' + sec.kind)">
        <!-- 第一级：待攻克 / 已攻克 -->
        <view class="row row--root" @tap="start(sec.kind, sec.tree.count)">
          <text class="row__name">{{ sec.title }}</text>
          <text class="row__count">{{ sec.tree.count }} 题</text>
          <view class="row__arrow" @tap.stop="toggle(key(sec.kind))">
            <text class="arrow" :class="{ 'arrow--open': !closed[key(sec.kind)] }">›</text>
          </view>
        </view>

        <template v-if="!closed[key(sec.kind)]">
          <!-- 第二级：单元（没有题的不展示） -->
          <template v-for="ch in sec.tree.chapters.filter((c) => c.count > 0)" :key="ch.id">
            <view class="row row--chapter" @tap="start(sec.kind, ch.count, { chapter_id: ch.id })">
              <text class="row__name">{{ ch.name }}</text>
              <text class="row__count">{{ ch.count }} 题</text>
              <view class="row__arrow" @tap.stop="toggle(key(sec.kind, ch.id))">
                <text class="arrow" :class="{ 'arrow--open': !closed[key(sec.kind, ch.id)] }">›</text>
              </view>
            </view>
            <!-- 第三级：知识点 -->
            <template v-if="!closed[key(sec.kind, ch.id)]">
              <view
                v-for="p in ch.points.filter((x) => x.count > 0)"
                :key="p.id"
                class="row row--point"
                @tap="start(sec.kind, p.count, { chapter_id: ch.id, knowledge_point_id: p.id })"
              >
                <text class="row__name">{{ p.name }}</text>
                <text class="row__count">{{ p.count }} 题</text>
                <view class="row__arrow"><text class="arrow arrow--plain">›</text></view>
              </view>
            </template>
          </template>
          <view v-if="sec.tree.count === 0" class="row row--empty">
            <text class="row__count">{{ sec.kind === 'pending' ? '暂无待攻克题目，继续保持' : '暂无已攻克题目' }}</text>
          </view>
        </template>
      </view>
    </template>

    <view v-if="creating" class="mask">
      <view class="mask__inner">
        <view class="spinner" />
        <text class="mask__text">正在准备训练题目...</text>
      </view>
    </view>

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
.wb-page {
  min-height: 100vh;
  background: $bg-page;
  padding: $space-4;
  padding-bottom: 80rpx;
}

.wb-head {
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

.wb-subjects {
  display: flex;
  gap: $space-2;
  margin-bottom: 20rpx;
}
.wb-subject {
  flex: 1;
  height: 72rpx;
  border-radius: $r-pill;
  background: $bg-muted;
  border: 1rpx solid transparent;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: $font-size-sm;
  color: $text-2;
  font-weight: 500;

  &--active { background: $primary-light; border-color: $primary-border; color: $primary; font-weight: 600; }
}

.wb-card {
  @include glass-panel;
  border: 1rpx solid $border;
  padding: 0;
  margin-bottom: 20rpx;
}

.row {
  display: flex;
  align-items: center;
  gap: $space-2;
  padding: 0 0 0 $space-4;
  min-height: 96rpx;
  border-top: 1rpx solid $border;

  &:first-child { border-top: none; }
  &:active { background: $primary-light; }

  &__name { flex: 1; font-size: $font-size-base; color: $text-1; }
  &__count { font-size: $font-size-sm; color: $text-3; }
  // 箭头有独立的点击区域（展开 / 收起），行本身的点击是进入答题
  &__arrow { width: 88rpx; height: 96rpx; display: flex; align-items: center; justify-content: center; }

  &--root &__name { font-weight: 700; font-size: $font-size-lg; }
  &--chapter { padding-left: $space-4; }
  &--chapter &__name { font-weight: 600; }
  &--point { padding-left: calc(#{$space-4} + 28rpx); }
  &--point &__name { font-size: $font-size-sm; color: $text-2; }
  &--empty { padding: $space-3 $space-4; justify-content: center; }
}

.arrow {
  font-size: 36rpx;
  color: $text-3;
  transition: transform 0.2s ease;
  &--open { transform: rotate(90deg); }
  &--plain { font-size: 32rpx; }
}

.wb-state {
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
