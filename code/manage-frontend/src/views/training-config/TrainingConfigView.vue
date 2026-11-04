<template>
  <div class="page-root" v-loading="loading">

    <!-- ── 各训练方式的出题参数 ── -->
    <div v-for="f in forms" :key="f.dimension" class="surface section-block">
      <div class="section-hd">
        <span class="section-title">
          <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />{{ f.label }}
        </span>
        <el-button size="small" :loading="f.saving" @click="saveDimension(f)">
          <SvgIcon v-if="!f.saving" name="save" :size="14" style="margin-right:4px" />保存
        </el-button>
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
        <div v-else class="hint smart-tip">智能训练按下方「槽位配比」组卷，不使用题型比例和难度比例。</div>
      </el-form>

      <!-- 智能训练：算法参数 -->
      <template v-if="f.dimension === 'SMART' && f.smart">
        <div class="sub-title">槽位配比（弱项强化 / 强项拓展 / 复习探索）</div>
        <el-form label-width="150px" class="cfg-form" @submit.prevent>
          <el-form-item label="槽位配比" class="title-row" />
          <el-form-item label=" ">
            <div class="ratio-row">
              <div v-for="s in SLOTS" :key="s.key" class="ratio-item">
                <div class="ratio-item__label">{{ s.label }}（{{ pct(f.smart.slots, s.key) }}）</div>
                <el-input-number v-model="f.smart.slots[s.key]" :min="0" :max="100" :step="0.1" :precision="2" controls-position="right" size="small" class="ratio-val" />
              </div>
            </div>
          </el-form-item>
          <el-form-item label="近期困惑保底题数">
            <el-input-number v-model="f.smart.intent_min_slots" :min="0" :max="5" />
            <span class="hint">学生在 AI 助教里提到的困惑知识点，至少出几道题</span>
          </el-form-item>
        </el-form>

        <div class="sub-title">打分权重（越大越优先）</div>
        <el-form label-width="150px" class="cfg-form" @submit.prevent>
          <div class="grid">
            <el-form-item v-for="w in WEIGHTS" :key="w.key" :label="w.label">
              <el-input-number v-model="f.smart.weights[w.key]" :min="0" :max="5" :step="0.1" :precision="2" size="small" controls-position="right" />
            </el-form-item>
          </div>
        </el-form>

        <div class="sub-title">时间衰减与随机性</div>
        <el-form label-width="150px" class="cfg-form" @submit.prevent>
          <div class="grid">
            <el-form-item label="做题历史半衰期（天）">
              <el-input-number v-model="f.smart.half_life_days" :min="1" :max="365" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="聊天困惑半衰期（天）">
              <el-input-number v-model="f.smart.intent_half_life_days" :min="1" :max="365" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="平滑先验（错）">
              <el-input-number v-model="f.smart.prior[0]" :min="0.1" :max="20" :step="0.5" :precision="1" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="平滑先验（对）">
              <el-input-number v-model="f.smart.prior[1]" :min="0.1" :max="20" :step="0.5" :precision="1" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="最近做过的题扣分">
              <el-input-number v-model="f.smart.recent_penalty" :min="0" :max="5" :step="0.1" :precision="2" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="抽取随机程度">
              <el-input-number v-model="f.smart.temperature" :min="0.05" :max="2" :step="0.05" :precision="2" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="同题型降权倍数">
              <el-input-number v-model="f.smart.diversity_type" :min="0.1" :max="1" :step="0.1" :precision="2" size="small" controls-position="right" />
            </el-form-item>
            <el-form-item label="同知识点降权倍数">
              <el-input-number v-model="f.smart.diversity_kp" :min="0.1" :max="1" :step="0.1" :precision="2" size="small" controls-position="right" />
            </el-form-item>
          </div>
          <el-form-item label="已攻克题复习间隔">
            <el-input v-model="f.reviewText" placeholder="如 1,3,7,14" style="max-width:260px" />
            <span class="hint">单位：天，逗号分隔，最多 8 个</span>
          </el-form-item>
          <el-form-item>
            <el-button size="small" @click="resetSmart(f)">恢复算法默认值</el-button>
            <span class="hint">只恢复页面上的数值，点右上角「保存」后才生效</span>
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
        <el-button size="small" :loading="analysisSaving" @click="saveAnalysis">
          <SvgIcon v-if="!analysisSaving" name="save" :size="14" style="margin-right:4px" />保存
        </el-button>
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
  reviewText: string
  saving: boolean
}

const SLOTS = [
  { key: 'weak', label: '弱项强化' },
  { key: 'strong', label: '强项拓展' },
  { key: 'review', label: '复习探索' },
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

function pct(r: Record<string, number>, key: string) {
  const sum = Object.values(r).reduce((a, b) => a + (Number(b) || 0), 0)
  return sum > 0 ? `${Math.round(((Number(r[key]) || 0) / sum) * 100)}%` : '—'
}

/** 把比例换算成合计 100 的整数百分比（没配置时平均分；尾差补到最大的一项） */
function toPercent(r: Record<string, number> | null | undefined, keys: string[]): Record<string, number> {
  const w = keys.map((k) => (r ? Number(r[k]) || 0 : 1))
  const total = w.reduce((a, b) => a + b, 0) || keys.length
  const vals = (w.some((x) => x > 0) ? w : keys.map(() => 1)).map((x) => Math.round((x / total) * 100))
  const diff = 100 - vals.reduce((a, b) => a + b, 0)
  vals[vals.indexOf(Math.max(...vals))] += diff
  return Object.fromEntries(keys.map((k, i) => [k, vals[i]]))
}

function toForm(c: DimensionConfig): Form {
  const typeR: Record<string, number> = {}
  const tp = toPercent(c.type_ratio, cfg.question_types)
  cfg.question_types.forEach((t) => { typeR[t] = tp[t] })
  const diffR: Record<string, number> = {}
  const dp = toPercent(c.difficulty_ratio ?? cfg.default_difficulty_ratio, cfg.difficulties)
  cfg.difficulties.forEach((d) => { diffR[d] = dp[d] })
  const smart = c.smart_params ? clone(c.smart_params) : null
  return {
    dimension: c.dimension, label: c.label,
    questions_per_session: c.questions_per_session,
    dedup_window_size: c.dedup_window_size,
    typeR, diffR,
    smart, reviewText: smart ? smart.review_intervals_days.join(',') : '',
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
  f.smart = clone(cfg.default_smart_params)
  f.reviewText = f.smart.review_intervals_days.join(',')
}

function sumOf(r: Record<string, number>) { return Object.values(r).reduce((a, b) => a + (Number(b) || 0), 0) }

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
    if (sumOf(f.smart.slots as unknown as Record<string, number>) <= 0) { ElMessage.warning('槽位配比至少要有一项大于 0'); return }
    const days = f.reviewText.split(/[,，\s]+/).filter(Boolean).map(Number)
    if (!days.length || days.length > 8 || days.some((d) => !Number.isInteger(d) || d < 1 || d > 365)) {
      ElMessage.warning('复习间隔需填 1~8 个 1~365 的整数天数，如 1,3,7,14'); return
    }
    payload.smart_params = { ...clone(f.smart), review_intervals_days: days }
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
.smart-tip { margin: 0 0 10px 150px; }

.sub-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  margin: 10px 0 8px;
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
