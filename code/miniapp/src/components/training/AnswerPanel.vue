<script setup lang="ts">
/**
 * 训练答题作答区（按题型切换组件）
 *   单选 → 单选组件 A.xxx    多选 → 复选框 A.xxx    判断 → 单选组件 对 / 错
 *   填空 → 按空数逐行 1.____  应用题 → 解题过程 + 最终答案    其它 → 多行文本框
 * 见产品设计说明书 §4.4.1 / 接口设计说明书 §5.2。
 */
import { computed, getCurrentInstance, nextTick, onMounted, reactive, ref, watch } from 'vue'
import type { TrainingQuestion } from '@/api/training'
import { MATH_SYMBOLS, TF_OPTIONS, answerMode, type AnswerState } from '@/utils/answer'
import { useThemeStore } from '@/store/theme'

const props = defineProps<{
  question: TrainingQuestion
  modelValue: AnswerState
  readonly?: boolean
  /** 页面里底部操作栏顶部的 y（px，已扣除作答区下方留白）；文本框模式据此铺满剩余高度 */
  limitBottom?: number
}>()
const emit = defineEmits<{ (e: 'update:modelValue', v: AnswerState): void }>()

const instance = getCurrentInstance()
const theme = useThemeStore()
const mode = computed(() => answerMode(props.question))
const qType = computed(() => String(props.question.question_type || '').toUpperCase())
const options = computed(() => props.question.options ?? [])
const blankCount = computed(() => props.modelValue.blanks.length)

function patch(p: Partial<AnswerState>) {
  emit('update:modelValue', { ...props.modelValue, ...p })
}

// ── 选择类：单选 / 多选 / 判断 ───────────────────────────────────────────
const isChecked = (key: string) => props.modelValue.selected.includes(key)

function pick(key: string) {
  if (props.readonly) return
  if (mode.value === 'multi') {
    const set = new Set(props.modelValue.selected)
    set.has(key) ? set.delete(key) : set.add(key)
    patch({ selected: [...set] })
  } else {
    patch({ selected: [key] })   // 单选：点另一项即切换；再点已选项保持选中
  }
}

// ── 输入类：字段读写 + 光标 + 符号快捷条 ──────────────────────────────────
// 字段 key：'text'（文本框 / 应用题解题过程）、'final'（应用题最终答案）、'blank-N'（第 N+1 个空）
const focusKey = ref('')              // 绑定到各输入框的 :focus
const lastKey = ref('')               // 最近编辑的字段，符号快捷条把符号插到这里
const cursors = reactive<Record<string, number>>({})

function valueOf(key: string): string {
  if (key === 'text') return props.modelValue.text
  if (key === 'final') return props.modelValue.final
  return props.modelValue.blanks[Number(key.split('-')[1])] ?? ''
}
function setValue(key: string, v: string) {
  if (key === 'text') patch({ text: v })
  else if (key === 'final') patch({ final: v })
  else {
    const i = Number(key.split('-')[1])
    patch({ blanks: props.modelValue.blanks.map((b, k) => (k === i ? v : b)) })
  }
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onInput(key: string, e: any) {
  const d = e?.detail ?? {}
  const v: string = d.value ?? ''
  setValue(key, v)
  cursors[key] = typeof d.cursor === 'number' ? d.cursor : v.length
  lastKey.value = key
}
function onFocus(key: string) {
  lastKey.value = key
  focusKey.value = key
}
// eslint-disable-next-line @typescript-eslint/no-explicit-any
function onBlur(key: string, e: any) {
  const c = e?.detail?.cursor
  if (typeof c === 'number') cursors[key] = c
  if (focusKey.value === key) focusKey.value = ''
}

const firstKey = computed(() => {
  if (mode.value === 'fill') return 'blank-0'
  if (mode.value === 'application' || mode.value === 'text') return 'text'
  return ''
})

function focusField(key: string) {
  if (!key || props.readonly) return
  focusKey.value = ''                           // 先置空再设置，保证重复触发时 :focus 能重新生效
  nextTick(() => { focusKey.value = key })
}
/** 页面点击答题区时调用：聚焦第一个输入框（选择类题型没有输入框，什么也不做） */
function focusFirst() {
  if (focusKey.value) return   // 已经有输入框获得焦点（比如用户刚点了第 2 个空）：不要抢回第一个
  focusField(firstKey.value)
}

function insertSymbol(sym: string) {
  if (props.readonly) return
  const key = lastKey.value || firstKey.value
  if (!key) return
  const v = valueOf(key)
  const c = Math.min(cursors[key] ?? v.length, v.length)
  setValue(key, v.slice(0, c) + sym + v.slice(c))
  cursors[key] = c + sym.length
  lastKey.value = key
  focusField(key)
}

const showSymbols = computed(() => {
  if (props.readonly) return false
  if (mode.value === 'fill' || mode.value === 'application') return true
  return mode.value === 'text' && !['SINGLE_CHOICE', 'MULTIPLE_CHOICE'].includes(qType.value)
})

// ── 文本框模式：占位符、字数、铺满剩余高度 ─────────────────────────────────
const placeholder = computed(() => {
  switch (qType.value) {
    case 'SINGLE_CHOICE': return '请输入你选择的选项字母，例如：B'
    case 'MULTIPLE_CHOICE': return '请输入所有正确选项的字母，例如：AC（顺序不限）'
    case 'FILL_BLANK': return '如果有多个空，请按顺序作答，空与空之间用逗号或分号分隔'
    default: return '在此输入你的解题过程和答案...'
  }
})

const textMinH = ref(0)
function refit() {
  if (mode.value !== 'text' || !props.limitBottom || props.readonly) return
  uni.createSelectorQuery()
    .in(instance?.proxy)
    .select('.ap-text-wrap')
    .boundingClientRect((r) => {
      const rect = r as { top: number } | null
      if (!rect) return
      // 字数统计行约 44rpx
      textMinH.value = Math.max(uni.upx2px(120), Math.floor(props.limitBottom! - rect.top - uni.upx2px(44)))
    })
    .exec()
}
watch(
  () => [props.limitBottom, mode.value, props.question.question_id, props.readonly],
  () => nextTick(() => setTimeout(refit, 50)),
)
onMounted(() => setTimeout(refit, 300))

defineExpose({ focusFirst, refit })
</script>

<template>
  <view class="ap">
    <!-- ── 单选 / 多选 / 判断：选项行 ─────────────────────────── -->
    <view v-if="mode === 'single' || mode === 'multi'" class="ap-opts">
      <view
        v-for="o in options"
        :key="o.key"
        class="ap-opt"
        :class="{ 'ap-opt--on': isChecked(o.key), 'ap-opt--ro': readonly }"
        @tap.stop="pick(o.key)"
      >
        <view class="ap-ctl" :class="[mode === 'multi' ? 'ap-ctl--box' : 'ap-ctl--radio', { 'ap-ctl--on': isChecked(o.key) }]">
          <text v-if="mode === 'multi' && isChecked(o.key)" class="ap-ctl__tick">✓</text>
          <view v-else-if="mode === 'single' && isChecked(o.key)" class="ap-ctl__dot" />
        </view>
        <text class="ap-opt__key">{{ o.key }}.</text>
        <text class="ap-opt__text">{{ o.text }}</text>
      </view>
    </view>

    <view v-else-if="mode === 'tf'" class="ap-opts">
      <view
        v-for="t in TF_OPTIONS"
        :key="t"
        class="ap-opt"
        :class="{ 'ap-opt--on': isChecked(t), 'ap-opt--ro': readonly }"
        @tap.stop="pick(t)"
      >
        <view class="ap-ctl ap-ctl--radio" :class="{ 'ap-ctl--on': isChecked(t) }">
          <view v-if="isChecked(t)" class="ap-ctl__dot" />
        </view>
        <text class="ap-opt__text">{{ t }}</text>
      </view>
    </view>

    <!-- ── 填空：按空数逐行 1.____ ───────────────────────────── -->
    <view v-else-if="mode === 'fill'" class="ap-blanks">
      <view v-for="(b, i) in modelValue.blanks" :key="i" class="ap-blank">
        <text class="ap-blank__no">{{ i + 1 }}.</text>
        <text v-if="readonly" class="ap-blank__ro">{{ b || '（未作答）' }}</text>
        <input
          v-else
          class="ap-blank__input"
          :value="b"
          :focus="focusKey === `blank-${i}`"
          :cursor="cursors[`blank-${i}`] ?? -1"
          :placeholder="blankCount > 1 ? `第 ${i + 1} 个空` : '请输入答案'"
          placeholder-style="color: rgba(148, 163, 184, 0.85)"
          :maxlength="100"
          :hold-keyboard="true"
          confirm-type="next"
          @input="onInput(`blank-${i}`, $event)"
          @focus="onFocus(`blank-${i}`)"
          @blur="onBlur(`blank-${i}`, $event)"
        />
      </view>
    </view>

    <!-- ── 应用题：解题过程（选填）+ 最终答案 ─────────────────── -->
    <view v-else-if="mode === 'application'" class="ap-app">
      <view class="ap-block">
        <text class="ap-label">解题过程<text class="ap-label__opt">（选填）</text></text>
        <text v-if="readonly" class="ap-ro">{{ modelValue.text.trim() || '（未填写）' }}</text>
        <textarea
          v-else
          class="ap-textarea"
          :value="modelValue.text"
          :focus="focusKey === 'text'"
          :cursor="cursors['text'] ?? -1"
          placeholder="写出你的解题思路和步骤..."
          placeholder-style="color: rgba(148, 163, 184, 0.85)"
          :maxlength="2000"
          :show-confirm-bar="false"
          :hold-keyboard="true"
          disable-default-padding
          auto-height
          @input="onInput('text', $event)"
          @focus="onFocus('text')"
          @blur="onBlur('text', $event)"
        />
      </view>
      <view class="ap-block">
        <text class="ap-label">最终答案</text>
        <text v-if="readonly" class="ap-ro">{{ modelValue.final.trim() || '（未作答）' }}</text>
        <input
          v-else
          class="ap-final"
          :value="modelValue.final"
          :focus="focusKey === 'final'"
          :cursor="cursors['final'] ?? -1"
          placeholder="例如：35人，10600元（请带上单位）"
          placeholder-style="color: rgba(148, 163, 184, 0.85)"
          :maxlength="100"
          :hold-keyboard="true"
          @input="onInput('final', $event)"
          @focus="onFocus('final')"
          @blur="onBlur('final', $event)"
        />
      </view>
    </view>

    <!-- ── 其它：多行文本框 ───────────────────────────────────── -->
    <view v-else class="ap-text-wrap">
      <text v-if="readonly" class="ap-ro">{{ modelValue.text.trim() || '（未作答）' }}</text>
      <template v-else>
        <textarea
          class="ap-textarea"
          :style="textMinH ? { minHeight: textMinH + 'px' } : {}"
          :value="modelValue.text"
          :focus="focusKey === 'text'"
          :cursor="cursors['text'] ?? -1"
          :placeholder="placeholder"
          placeholder-style="color: rgba(148, 163, 184, 0.85)"
          :maxlength="2000"
          :show-confirm-bar="false"
          :hold-keyboard="true"
          disable-default-padding
          auto-height
          @input="onInput('text', $event)"
          @focus="onFocus('text')"
          @blur="onBlur('text', $event)"
        />
        <text class="ap-count" :class="{ 'ap-count--warn': modelValue.text.length >= 1900 }">
          {{ modelValue.text.length }} / 2000
        </text>
      </template>
    </view>

    <!-- 选择类题型未作答（只读态）的提示 -->
    <text v-if="readonly && (mode === 'single' || mode === 'multi' || mode === 'tf') && !modelValue.selected.length" class="ap-ro ap-ro--tip">（未作答）</text>

    <!-- ── 数学符号快捷条（手机键盘很难输入 × ² ° 等）─────────── -->
    <scroll-view v-if="showSymbols" class="ap-sym" scroll-x :show-scrollbar="false">
      <view class="ap-sym__list">
        <view v-for="s in MATH_SYMBOLS" :key="s" class="ap-sym__chip" @tap.stop="insertSymbol(s)">
          <text class="ap-sym__text" :class="{ 'ap-sym__text--dark': theme.isDark }">{{ s }}</text>
        </view>
      </view>
    </scroll-view>
  </view>
</template>

<style lang="scss" scoped>
.ap {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

// ── 选项行（单选 / 多选 / 判断）──────────────────────────────────────
.ap-opts {
  display: flex;
  flex-direction: column;
  gap: $space-2;
}

.ap-opt {
  display: flex;
  align-items: center;
  gap: $space-2;
  // 选中底色比内容区向左右各多伸出 16rpx（负外边距）、再用同样大小的内边距补回，所以选项文字 / 圆圈的位置不变，
  // 只是选中效果离内容更远，不再紧贴文字
  margin: 0 -16rpx;
  padding: 22rpx 32rpx;
  border-radius: 16rpx;   // 8px
  transition: $transition-fast;

  &:active { background: $primary-light; }

  // 选中：同后台下拉框选中项——蓝色横向渐变底 + 文字变色，字重不加粗
  &--on,
  &--on:active { background: var(--option-on-bg); }
  &--ro { pointer-events: none; }

  &__key {
    flex-shrink: 0;
    font-size: $font-size-base;
    font-weight: 400;
    color: $text-2;

    .ap-opt--on & { color: var(--option-on-text); }
  }

  &__text {
    flex: 1;
    min-width: 0;
    font-size: $font-size-base;
    font-weight: 400;
    color: $text-1;
    line-height: 1.6;

    .ap-opt--on & { color: var(--option-on-text); }
  }
}

// 单选圆圈 / 复选方框
.ap-ctl {
  flex-shrink: 0;
  width: 36rpx;
  height: 36rpx;
  border: 2rpx solid $border-hover;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: $transition-fast;

  &--radio { border-radius: 50%; }
  &--box { border-radius: 10rpx; }

  &--on {
    border-color: $primary;
  }
  &--box.ap-ctl--on { background: $primary; }

  &__dot {
    width: 18rpx;
    height: 18rpx;
    border-radius: 50%;
    background: $primary;
  }

  &__tick {
    font-size: 24rpx;
    line-height: 1;
    font-weight: 700;
    color: $on-primary;
  }
}

// ── 填空 ──────────────────────────────────────────────────────────────
.ap-blanks {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.ap-blank {
  display: flex;
  align-items: flex-end;
  gap: $space-2;

  &__no {
    flex-shrink: 0;
    font-size: $font-size-base;
    font-weight: 700;
    color: $text-2;
    line-height: 72rpx;
  }

  // 下划线样式：只有底边，无边框无背景；聚焦时不换色
  &__input,
  &__ro {
    flex: 1;
    min-width: 0;
    height: 72rpx;
    line-height: 72rpx;
    font-size: $font-size-base;
    color: $text-1;
    border-bottom: 2rpx solid $border-hover;
    background: transparent;
  }
}

// ── 应用题 ────────────────────────────────────────────────────────────
.ap-app {
  display: flex;
  flex-direction: column;
  gap: $space-3;
}

.ap-block {
  display: flex;
  flex-direction: column;
  gap: $space-1;
}

.ap-label {
  font-size: $font-size-xs;
  font-weight: 600;
  color: $text-2;

  &__opt { font-weight: 400; color: $text-3; }
}

.ap-textarea {
  width: 100%;
  min-height: 160rpx;
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.7;
}

.ap-final {
  height: 72rpx;
  line-height: 72rpx;
  font-size: $font-size-base;
  color: $text-1;
  border-bottom: 2rpx solid $border-hover;
  background: transparent;
}

// ── 文本框模式 ─────────────────────────────────────────────────────────
.ap-text-wrap {
  display: flex;
  flex-direction: column;
}

.ap-count {
  align-self: flex-end;
  margin-top: $space-1;
  font-size: $font-size-xs;
  line-height: 1.4;
  color: $text-3;

  &--warn { color: $warning; }
}

// ── 只读展示 ───────────────────────────────────────────────────────────
.ap-ro {
  font-size: $font-size-base;
  color: $text-1;
  line-height: 1.7;

  &--tip { color: $text-3; padding-left: $space-2; }
}

// ── 数学符号快捷条 ─────────────────────────────────────────────────────
.ap-sym {
  white-space: nowrap;
  margin-top: $space-1;

  &__list {
    display: inline-flex;
    gap: $space-2;
    padding: 4rpx 0;
  }

  // 每个符号都是正方形
  &__chip {
    flex-shrink: 0;
    width: 64rpx;
    height: 64rpx;
    padding: 0;
    border-radius: $r-sm;
    background: $bg-muted;
    display: flex;
    align-items: center;
    justify-content: center;

    &:active { background: $primary-light; }
  }

  &__text {
    font-size: $font-size-base;
    color: $text-2;
    line-height: 1;

    // 暗色下符号用白色
    &--dark { color: #ffffff; }
  }
}
</style>
