<template>
  <div class="page-root" v-loading="loading">

    <!-- ── 各训练方式的出题参数 ── -->
    <div v-for="f in forms" :key="f.dimension" class="surface section-block">
      <div class="section-hd">
        <span class="section-title">
          <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />{{ f.label }}
        </span>
        <div class="hd-actions">
          <el-button v-if="f.smart" size="small" text title="只恢复页面上的数值，点「保存」后才生效" style="color:var(--color-primary)" @click="resetSmart(f)">
            <SvgIcon name="reset_default" :size="16" color="var(--color-primary)" style="margin-right:4px" />恢复算法默认值
          </el-button>
          <el-button size="small" text :loading="f.saving" style="color:var(--color-primary)" @click="saveDimension(f)">
            <SvgIcon v-if="!f.saving" name="save" :size="16" color="var(--color-primary)" style="margin-right:4px" />保存
          </el-button>
        </div>
      </div>

      <el-form label-width="150px" class="cfg-form" @submit.prevent>
        <el-form-item label="每次抽取题数">
          <el-input-number v-model="f.questions_per_session" :min="1" :max="100" :step="1" />
          <span class="hint">1 ~ 100 题，默认 5</span>
        </el-form-item>
        <el-form-item label="避开最近做过的题">
          <el-input-number v-model="f.dedup_window_size" :min="0" :max="500" :step="5" />
          <span class="hint">抽题时尽量避开最近做过的 N 道题；题库不够时仍会出题，0 表示不避开</span>
        </el-form-item>

        <template v-if="f.dimension !== 'SMART'">
          <el-form-item label="题型比例" class="title-row" />
          <el-form-item label=" ">
            <div class="ratio-row">
              <div v-for="t in cfg.question_types" :key="t" class="ratio-item">
                <div class="ratio-item__label"><SvgIcon :name="QT_ICONS[t] ?? 'qt_application'" :size="14" class="type-icon" :class="`type-icon--${t}`" />{{ typeLabel(t) }}</div>
                <el-input-number v-model="f.typeR[t]" :min="0" :max="100" :step="5" :precision="0" controls-position="right" size="small" class="ratio-val" />
              </div>
              <span class="ratio-total" :class="{ bad: sumOf(f.typeR) !== 100 }">合计 {{ sumOf(f.typeR) }}%</span>
            </div>
          </el-form-item>

          <el-form-item label="难度比例" class="title-row" />
          <el-form-item label=" ">
            <div class="ratio-row">
              <div v-for="d in cfg.difficulties" :key="d" class="ratio-item">
                <div class="ratio-item__label"><span class="diff-dot" :class="`diff-dot--${d}`" />{{ diffLabel(d) }}</div>
                <el-input-number v-model="f.diffR[d]" :min="0" :max="100" :step="5" :precision="0" controls-position="right" size="small" class="ratio-val" />
              </div>
              <span class="ratio-total" :class="{ bad: sumOf(f.diffR) !== 100 }">合计 {{ sumOf(f.diffR) }}%</span>
            </div>
          </el-form-item>
        </template>
      </el-form>

      <!-- 智能训练：算法参数 -->
      <template v-if="f.dimension === 'SMART' && f.smart">
        <el-form label-width="150px" class="cfg-form" @submit.prevent>
          <el-form-item label="槽位配比" class="title-row" />
          <el-form-item label=" ">
            <div class="ratio-row">
              <div v-for="s in SLOTS" :key="s.key" class="ratio-item">
                <div class="ratio-item__label"><SvgIcon :name="s.icon" :size="14" class="slot-icon" :class="`slot-icon--${s.key}`" />{{ s.label }}</div>
                <el-input-number v-model="f.smart.slots[s.key]" :min="0" :max="100" :step="5" :precision="0" controls-position="right" size="small" class="ratio-val" />
              </div>
              <span class="ratio-total" :class="{ bad: sumOf(f.smart.slots) !== 100 }">合计 {{ sumOf(f.smart.slots) }}%</span>
            </div>
          </el-form-item>
          <el-form-item label="近期困惑保底题数">
            <el-input-number v-model="f.smart.intent_min_slots" :min="0" :max="5" />
            <span class="hint">学生在 AI 助教里提到的困惑知识点，至少出几道题</span>
          </el-form-item>
        </el-form>

        <el-form label-width="150px" class="cfg-form" @submit.prevent>
          <el-form-item label="打分权重" class="title-row" />
          <el-form-item label=" ">
            <div class="ratio-row">
              <div v-for="w in WEIGHTS" :key="w.key" class="ratio-item">
                <div class="ratio-item__label">{{ w.label }}</div>
                <el-input-number v-model="f.smart.weights[w.key]" :min="0" :max="5" :step="0.1" :precision="2" controls-position="right" size="small" class="ratio-val" />
              </div>
              <span class="ratio-total">数值越大越优先</span>
            </div>
          </el-form-item>
        </el-form>

        <div class="sub-title"><span class="sub-title__text">时间衰减与随机性</span></div>
        <el-form label-width="150px" class="cfg-form cfg-form--lv3" @submit.prevent>
          <div class="list-col">
            <el-form-item label="做题历史半衰期（天）">
              <el-input-number v-model="f.smart.half_life_days" :min="1" :max="365" size="small" controls-position="right" />
              <span class="hint">学生的做题记录每过这么多天，对「薄弱度」判断的影响减半；越小越看重最近的表现，默认 14</span>
            </el-form-item>
            <el-form-item label="聊天困惑半衰期（天）">
              <el-input-number v-model="f.smart.intent_half_life_days" :min="1" :max="365" size="small" controls-position="right" />
              <span class="hint">学生在助教里提过的困惑，每过这么多天影响减半；越小越只关注最近聊的，默认 7</span>
            </el-form-item>
            <el-form-item label="平滑先验（错）">
              <el-input-number v-model="f.smart.prior[0]" :min="0.1" :max="20" :step="0.5" :precision="1" size="small" controls-position="right" />
              <span class="hint">做题很少时，假装多错了这么多道，避免「做 1 错 1 就判成 100% 错」；与「对」一起决定初始错误率，默认 1</span>
            </el-form-item>
            <el-form-item label="平滑先验（对）">
              <el-input-number v-model="f.smart.prior[1]" :min="0.1" :max="20" :step="0.5" :precision="1" size="small" controls-position="right" />
              <span class="hint">做题很少时，假装多做对了这么多道；默认 错 1 : 对 2，即没有记录时错误率按 1/3 算，默认 2</span>
            </el-form-item>
            <el-form-item label="最近做过的题扣分">
              <el-input-number v-model="f.smart.recent_penalty" :min="0" :max="5" :step="0.1" :precision="2" size="small" controls-position="right" />
              <span class="hint">最近做过的题得分减去这个值，越大越避免重复出同一道题，默认 0.8</span>
            </el-form-item>
            <el-form-item label="抽取随机程度">
              <el-input-number v-model="f.smart.temperature" :min="0.05" :max="2" :step="0.05" :precision="2" size="small" controls-position="right" />
              <span class="hint">越小越只选得分最高的题，越大越随机，默认 0.35</span>
            </el-form-item>
            <el-form-item label="同题型降权倍数">
              <el-input-number v-model="f.smart.diversity_type" :min="0.1" :max="1" :step="0.1" :precision="2" size="small" controls-position="right" />
              <span class="hint">同一张卷里，同题型每多出现一道，下一道同题型的得分乘这个值；越小越分散，1 表示不限制，默认 0.5</span>
            </el-form-item>
            <el-form-item label="同知识点降权倍数">
              <el-input-number v-model="f.smart.diversity_kp" :min="0.1" :max="1" :step="0.1" :precision="2" size="small" controls-position="right" />
              <span class="hint">同一张卷里，同知识点每多出现一道，下一道同知识点的得分乘这个值；越小越分散，1 表示不限制，默认 0.7</span>
            </el-form-item>
          </div>
          <el-form-item label="已攻克题复习间隔">
            <el-input-number v-model="f.smart.review_interval_days" :min="1" :max="365" :step="1" size="small" controls-position="right" />
            <span class="hint">已攻克的题每隔多少天复习一次，默认 7 天</span>
          </el-form-item>
        </el-form>
      </template>
    </div>

    <!-- ── 题目分析（大模型）── -->
    <div class="surface section-block">
      <div class="section-hd">
        <span class="section-title">
          <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题目分析（大模型）
        </span>
        <div class="hd-actions">
          <el-button size="small" text :loading="analysisSaving" style="color:var(--color-primary)" @click="saveAnalysis">
            <SvgIcon v-if="!analysisSaving" name="save" :size="16" color="var(--color-primary)" style="margin-right:4px" />保存
          </el-button>
        </div>
      </div>
      <el-form label-width="150px" class="cfg-form" @submit.prevent>
        <el-form-item label="批量分析并发数">
          <el-input-number v-model="analysis.question_analysis_concurrency" :min="1" :max="10" />
          <span class="hint">批量分析时同时调用大模型的题数，其余排队；大模型繁忙时调小更稳</span>
        </el-form-item>
        <el-form-item label="单题分析超时（秒）">
          <el-input-number v-model="analysis.question_analysis_timeout_sec" :min="30" :max="600" :step="30" />
          <span class="hint">超过后该题退回草稿，可重新分析；排队时间不计入</span>
        </el-form-item>
      </el-form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trainingConfigApi } from '@/api'
import { QuestionTypeLabels } from '@/types'
import type { DimensionConfig, SmartParams, TrainingConfigList, AnalysisConfig } from '@/types'

interface Form {
  dimension: string
  label: string
  questions_per_session: number
  dedup_window_size: number
  typeR: Record<string, number>
  diffR: Record<string, number>
  smart: SmartParams | null
  saving: boolean
}

const SLOTS = [
  { key: 'weak', label: '弱项强化', icon: 'slot_weak' },
  { key: 'strong', label: '强项拓展', icon: 'slot_strong' },
  { key: 'review', label: '复习探索', icon: 'slot_review' },
] as const
const WEIGHTS = [
  { key: 'kp_weak', label: '知识点薄弱度' },
  { key: 'pending', label: '在待攻克里' },
  { key: 'type_weak', label: '题型薄弱度' },
  { key: 'power_fit', label: '五力匹配' },
  { key: 'intent', label: '近期困惑' },
  { key: 'fav', label: '收藏' },
  { key: 'novelty', label: '没做过的新题' },
] as const
// 题目类型图标（与训练题管理列表「题目类型」列一致）
const QT_ICONS: Record<string, string> = {
  SINGLE_CHOICE: 'qt_single', MULTIPLE_CHOICE: 'qt_multi', TRUE_FALSE: 'qt_judge', FILL_BLANK: 'qt_fill', APPLICATION: 'qt_application',
}
const DIFF_LABELS: Record<string, string> = { basic: '基础', advanced: '进阶', challenge: '挑战' }

const loading = ref(false)
const cfg = reactive<TrainingConfigList>({
  list: [], question_types: [], difficulties: [], default_difficulty_ratio: {},
  default_smart_params: null as unknown as SmartParams,
  analysis: { question_analysis_concurrency: 3, question_analysis_timeout_sec: 180 },
})
const forms = ref<Form[]>([])
const analysis = reactive<AnalysisConfig>({ question_analysis_concurrency: 3, question_analysis_timeout_sec: 180 })
const analysisSaving = ref(false)

const typeLabel = (t: string) => QuestionTypeLabels[t as keyof typeof QuestionTypeLabels] ?? t
const diffLabel = (d: string) => DIFF_LABELS[d] ?? d
const clone = <T,>(v: T): T => JSON.parse(JSON.stringify(v))

/** 把比例换算成合计 100 的整数百分比（没配置时平均分；尾差补到最大的一项） */
function toPercent(r: Record<string, number> | null | undefined, keys: string[]): Record<string, number> {
  const w = keys.map((k) => (r ? Number(r[k]) || 0 : 1))
  const total = w.reduce((a, b) => a + b, 0) || keys.length
  const vals = (w.some((x) => x > 0) ? w : keys.map(() => 1)).map((x) => Math.round((x / total) * 100))
  const diff = 100 - vals.reduce((a, b) => a + b, 0)
  vals[vals.indexOf(Math.max(...vals))] += diff
  return Object.fromEntries(keys.map((k, i) => [k, vals[i]]))
}

/** 槽位配比库里存的是小数（0.6 / 0.2 / 0.2），页面按百分比（60 / 20 / 20）填写 */
function slotsToPercent(sp: SmartParams): SmartParams {
  const p = toPercent(sp.slots as unknown as Record<string, number>, ['weak', 'strong', 'review'])
  sp.slots = { weak: p.weak, strong: p.strong, review: p.review }
  return sp
}

function toForm(c: DimensionConfig): Form {
  const typeR: Record<string, number> = {}
  const tp = toPercent(c.type_ratio, cfg.question_types)
  cfg.question_types.forEach((t) => { typeR[t] = tp[t] })
  const diffR: Record<string, number> = {}
  const dp = toPercent(c.difficulty_ratio ?? cfg.default_difficulty_ratio, cfg.difficulties)
  cfg.difficulties.forEach((d) => { diffR[d] = dp[d] })
  const smart = c.smart_params ? slotsToPercent(clone(c.smart_params)) : null
  return {
    dimension: c.dimension, label: c.label,
    questions_per_session: c.questions_per_session,
    dedup_window_size: c.dedup_window_size,
    typeR, diffR,
    smart,
    saving: false,
  }
}

async function load() {
  loading.value = true
  try {
    Object.assign(cfg, await trainingConfigApi.getAll())
    forms.value = cfg.list.map(toForm)
    Object.assign(analysis, cfg.analysis)
  } finally { loading.value = false }
}

function resetSmart(f: Form) {
  f.smart = slotsToPercent(clone(cfg.default_smart_params))
}

function sumOf(r: object) { return (Object.values(r) as number[]).reduce((a, b) => a + (Number(b) || 0), 0) }

async function saveDimension(f: Form) {
  if (f.saving) return
  // 点击后校验并提示（不做按钮置灰）
  if (sumOf(f.typeR) !== 100) { ElMessage.warning(`题型比例合计需为 100%，当前为 ${sumOf(f.typeR)}%`); return }
  if (sumOf(f.diffR) !== 100) { ElMessage.warning(`难度比例合计需为 100%，当前为 ${sumOf(f.diffR)}%`); return }
  const payload: Partial<DimensionConfig> = {
    questions_per_session: f.questions_per_session,
    dedup_window_size: f.dedup_window_size,
    type_ratio: { ...f.typeR },
    difficulty_ratio: { ...f.diffR },
  }
  if (f.smart) {
    if (sumOf(f.smart.slots) !== 100) { ElMessage.warning(`槽位配比合计需为 100%，当前为 ${sumOf(f.smart.slots)}%`); return }
    const sp = clone(f.smart)
    sp.slots = { weak: sp.slots.weak / 100, strong: sp.slots.strong / 100, review: sp.slots.review / 100 }
    payload.smart_params = sp
  }
  f.saving = true
  try {
    const saved = await trainingConfigApi.save(f.dimension, payload)
    Object.assign(f, toForm(saved))
    ElMessage.success(`「${f.label}」已保存，学生下一次开始训练时生效`)
  } finally { f.saving = false }
}

async function saveAnalysis() {
  if (analysisSaving.value) return
  analysisSaving.value = true
  try {
    Object.assign(analysis, await trainingConfigApi.saveAnalysis({ ...analysis }))
    ElMessage.success('已保存，新触发的分析按新设置执行')
  } finally { analysisSaving.value = false }
}

onMounted(load)
</script>

<style lang="scss" scoped>
.page-root {
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.section-block {
  padding: 5px 15px 15px;
  margin-bottom: 0;
  flex-shrink: 0;          // 页面是纵向 flex 布局，不加这个卡片会被压扁、内容被裁掉
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;
}

.cfg-form {
  :deep(.el-form-item) { margin-bottom: 10px; }
  :deep(.el-form-item__label) { font-size: 13px; color: var(--text-1) !important; }
}

.hd-actions {
  display: flex;
  align-items: center;
  gap: 15px;
  // 文字按钮去掉自带的内边距，按钮之间 / 保存与卡片右边框的距离才是 15px；悬停时不变底色
  :deep(.el-button) {
    margin-left: 0 !important;
    padding: 0 !important;
    height: auto !important;
    background: transparent !important;
    border-color: transparent !important;
    &:hover, &:focus, &:active { background: transparent !important; border-color: transparent !important; }
  }
}
.cfg-form--lv3 :deep(.el-form-item__label) { color: var(--text-2) !important; }   // 三级标题：同难度比例的小标题色

.list-col { display: block; }

.grid {
  display: grid;
  grid-template-columns: repeat(2, minmax(0, 1fr));
  column-gap: 24px;
  @media (max-width: 1100px) { grid-template-columns: 1fr; }
}

.hint {
  margin-left: 12px;
  font-size: 12px;
  color: var(--text-3);
}

.sub-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  margin: 10px 0 8px;
  display: flex;
  align-items: center;

  // 与表单项标题同一列：宽 150px、右对齐、右侧留 12px（同 el-form-item__label）
  &__text {
    width: 150px;
    padding-right: 12px;
    box-sizing: border-box;
    text-align: right;
    flex-shrink: 0;
  }
  .hint { margin-left: 0; font-weight: 400; }
}

// 比例类配置：标题独占一行（右对齐，位置不变），配置条件在下一行（起点不变）
.cfg-form :deep(.title-row) { margin-bottom: 0; }

// 与训练题管理编辑页「五力训练权重」一致：标签在上、居中，输入框 90px 宽、增减按钮在右侧
.ratio-row {
  display: flex;
  align-items: flex-end;
  gap: 10px;
  flex-wrap: wrap;
}
.ratio-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;

  // 三级标题：与「五力训练权重」各项标签同色（--text-2）；题型前面的圆点颜色同训练题管理列表「题目类型」列
  &__label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
    line-height: 20px;       // 继承自表单项的 32px 行高会把标题和输入框撑开
    color: var(--text-2);
    white-space: nowrap;
  }
}
.type-icon {
  flex-shrink: 0;
  color: var(--text-3);

  &--SINGLE_CHOICE   { color: var(--qt-single); }
  &--MULTIPLE_CHOICE { color: var(--qt-multi); }
  &--FILL_BLANK      { color: var(--qt-fill); }
  &--TRUE_FALSE      { color: var(--qt-judge); }
  &--APPLICATION     { color: var(--qt-application); }
}
.diff-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;
  background: var(--text-3);

  // 颜色同训练题管理列表「难度」列标签的背景色
  &--basic     { background: #E8F5D0; }
  &--advanced  { background: #FFF0D6; }
  &--challenge { background: #FFE0E0; }
}
.slot-icon {
  flex-shrink: 0;
  // 弱项强化：琥珀（向上箭头 + 底线）／强项拓展：绿（向外扩张箭头）／复习探索：青（循环箭头）
  &--weak   { color: var(--amber); }
  &--strong { color: var(--green); }
  &--review { color: var(--teal); }
}
.ratio-val { width: 90px !important; }
:deep(.ratio-val .el-input__inner) { text-align: left !important; }
.ratio-total {
  font-size: 12px;
  color: var(--text-3);
  align-self: flex-end;      // 与输入框同一行底对齐，行高 = 输入框高度，文字就垂直居中
  height: 30px;              // size=small 的输入框实际高 30px
  line-height: 30px;
  &.bad { color: var(--red); font-weight: 600; }
}
</style>
