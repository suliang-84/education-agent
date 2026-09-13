<template>
  <div class="page-root" v-loading="loading">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/questions')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回列表
        </el-button>
        <div>
          <h1 class="page-title">{{ pageTitle }}</h1>
          <p class="page-subtitle">
            <span class="id-chip">#{{ question?.id }}</span>
            <span v-if="question?.analysis_round" style="margin-left:8px;font-size:13px;color:var(--text-3)">
              第 {{ question.analysis_round }} 次分析结果
            </span>
          </p>
        </div>
      </div>
      <!-- 操作按钮：仅待审核状态可发布/驳回 -->
      <div v-if="question?.status === 'pending_review'" style="display:flex;gap:10px">
        <el-button @click="openReject" :loading="saving">驳回</el-button>
        <button class="btn-pink" type="button" @click="handlePublish" :disabled="saving">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          发布上线
        </button>
      </div>
    </div>

    <div v-if="question">

      <!-- ── 原始题干（只读）── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title">原始题干</span>
          <span class="status-badge" :class="`status-badge--${question.status}`">
            {{ QuestionStatusLabels[question.status as QuestionStatus] }}
          </span>
        </div>
        <div class="stem-display">{{ question.stem }}</div>
      </div>

      <!-- ── 分析结果（可修改，仅 pending_review 状态）── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title">大模型分析结果</span>
          <span v-if="question.status === 'pending_review'" class="edit-hint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>
            </svg>
            所有字段均可修改后再发布
          </span>
        </div>

        <el-form :model="form" label-width="100px">

          <!-- 归属体系 -->
          <div class="sub-section-title">归属体系</div>
          <el-row :gutter="20">
            <el-col :span="6">
              <el-form-item label="科目">
                <el-select v-model="form.subject" :disabled="!isEditable" style="width:100%">
                  <el-option label="数学" value="数学" />
                  <el-option label="物理" value="物理" />
                  <el-option label="化学" value="化学" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="6">
              <el-form-item label="年级">
                <el-select v-model="form.grade" :disabled="!isEditable" style="width:100%">
                  <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="章节">
                <el-input v-model="form.chapter" :disabled="!isEditable" placeholder="如：第三章 方程与方程组" />
              </el-form-item>
            </el-col>
          </el-row>

          <el-form-item label="知识点">
            <div class="tag-area">
              <el-tag
                v-for="(kp, i) in form.knowledge_points" :key="i"
                closable
                :disable-transitions="false"
                @close="removeKnowledgePoint(i)"
                style="margin-right:6px;margin-bottom:4px"
              >{{ kp }}</el-tag>
              <template v-if="isEditable">
                <el-input
                  v-if="kpInputVisible"
                  ref="kpInputRef"
                  v-model="kpInput"
                  size="small"
                  style="width:130px"
                  @keyup.enter="addKnowledgePoint"
                  @blur="addKnowledgePoint"
                />
                <el-button v-else size="small" @click="showKpInput">+ 添加知识点</el-button>
              </template>
            </div>
          </el-form-item>

          <!-- 难度 -->
          <div class="sub-section-title">难度</div>
          <el-form-item label="难度等级">
            <el-radio-group v-model="form.difficulty" :disabled="!isEditable">
              <el-radio-button value="basic">基础</el-radio-button>
              <el-radio-button value="advanced">进阶</el-radio-button>
              <el-radio-button value="challenge">挑战</el-radio-button>
            </el-radio-group>
          </el-form-item>

          <!-- 参考解析 -->
          <div class="sub-section-title">参考解析</div>
          <el-form-item label="解析内容">
            <el-input v-model="form.solution" type="textarea" :rows="5" :disabled="!isEditable" placeholder="完整解题过程..." />
          </el-form-item>

          <!-- 典型错误 -->
          <div class="sub-section-title">典型错误</div>
          <el-form-item label="典型错误">
            <el-input v-model="form.typical_error" :disabled="!isEditable" placeholder="学生最常犯的错误..." />
          </el-form-item>

          <!-- 五力权重 -->
          <div class="sub-section-title">
            五力训练权重
            <span class="weight-total" :class="weightTotal === 10 ? 'weight-total--ok' : 'weight-total--err'">
              合计: {{ weightTotal }} / 10
              <span v-if="weightTotal === 10"> ✓</span>
            </span>
          </div>
          <div class="power-weights-grid">
            <div v-for="p in powers" :key="p" class="power-weight-item">
              <div class="power-weight-item__label">
                <span class="power-dot" :class="`power-dot--${p}`" />
                {{ FivePowerLabels[p as FivePower] }}
              </div>
              <el-input-number
                v-model="form.five_power_weights[p as FivePower]"
                :min="0" :max="10" :step="1"
                controls-position="right"
                size="small"
                :disabled="!isEditable"
                style="width:90px"
              />
            </div>
          </div>

          <!-- 五力训练思路 -->
          <div class="sub-section-title">五力训练思路</div>
          <div class="thoughts-grid">
            <el-form-item
              v-for="p in powers" :key="p"
              :label="FivePowerLabels[p as FivePower]"
              label-width="60px"
              style="margin-bottom:10px"
            >
              <el-input
                v-model="form.five_power_thoughts[p as FivePower]"
                :disabled="!isEditable"
                placeholder="该维度的训练切入点..."
                size="small"
              />
            </el-form-item>
          </div>

          <!-- 迁移方向 -->
          <div class="sub-section-title">迁移方向</div>
          <el-form-item label="迁移方向">
            <div class="tag-area">
              <el-tag
                v-for="(d, i) in form.migration_directions" :key="i"
                type="success" closable
                :disable-transitions="false"
                @close="form.migration_directions.splice(i, 1)"
                style="margin-right:6px;margin-bottom:4px"
              >{{ d }}</el-tag>
              <template v-if="isEditable">
                <el-input
                  v-if="mdInputVisible"
                  ref="mdInputRef"
                  v-model="mdInput"
                  size="small"
                  style="width:130px"
                  @keyup.enter="addMigrationDir"
                  @blur="addMigrationDir"
                />
                <el-button v-else size="small" @click="showMdInput">+ 添加方向</el-button>
              </template>
            </div>
          </el-form-item>

          <!-- 保存修改按钮（仅 pending_review 状态） -->
          <div v-if="isEditable" style="display:flex;justify-content:flex-end;padding-top:8px">
            <el-button type="primary" :loading="saving" @click="handleSaveAnalysis">保存修改</el-button>
          </div>

        </el-form>
      </div>

    </div>

    <!-- ── 驳回弹窗 ── -->
    <el-dialog v-model="rejectDialogVisible" title="填写驳回意见" width="540px" :close-on-click-modal="false">
      <div style="font-size:13.5px;color:var(--text-2);margin-bottom:14px;line-height:1.6">
        驳回意见将连同原始题干一起提交给大模型，系统将自动触发第 {{ (question?.analysis_round || 1) + 1 }} 次分析。
      </div>
      <el-input
        v-model="rejectReason"
        type="textarea"
        :rows="5"
        placeholder="请描述分析结果中的问题，例如：五力权重分配不合理，推演力权重偏低，该题主要考查推演力，应将推演力权重提升至5分以上..."
      />
      <template #footer>
        <el-button @click="rejectDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" :disabled="!rejectReason.trim()" @click="handleReject">
          提交驳回并重新分析
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi } from '@/api'
import type { Question, QuestionStatus, FivePower, Difficulty } from '@/types'
import { QuestionStatusLabels, FivePowerLabels } from '@/types'

const route  = useRoute()
const router = useRouter()

const loading = ref(false)
const saving  = ref(false)
const question = ref<Question | null>(null)

const rejectDialogVisible = ref(false)
const rejectReason = ref('')

const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const
const grades = ['七年级', '八年级', '九年级', '高一', '高二', '高三']

// 仅待审核状态可编辑
const isEditable = computed(() => question.value?.status === 'pending_review')

const pageTitle = computed(() => {
  const s = question.value?.status
  if (s === 'pending_review') return '审核分析结果'
  if (s === 'published')      return '查看题目详情'
  if (s === 'archived')       return '查看已归档题目'
  return '题目详情'
})

// ── 可编辑表单 ───────────────────────────────────────────────
const form = reactive({
  subject: '' as string,
  grade: '' as string,
  chapter: '' as string,
  knowledge_points: [] as string[],
  difficulty: 'basic' as Difficulty,
  solution: '' as string,
  typical_error: '' as string,
  five_power_weights: { INSIGHT: 2, CONSTRUCT: 5, DEDUCE: 2, ADAPT: 1, MIGRATE: 0 } as Record<FivePower, number>,
  five_power_thoughts: { INSIGHT: '', CONSTRUCT: '', DEDUCE: '', ADAPT: '', MIGRATE: '' } as Record<FivePower, string>,
  migration_directions: [] as string[],
})

const weightTotal = computed(() => Object.values(form.five_power_weights).reduce((s, v) => s + v, 0))

// 知识点 tag 输入
const kpInputVisible = ref(false)
const kpInput = ref('')
const kpInputRef = ref<HTMLInputElement>()
function showKpInput() { kpInputVisible.value = true; nextTick(() => kpInputRef.value?.focus()) }
function addKnowledgePoint() {
  if (kpInput.value.trim()) form.knowledge_points.push(kpInput.value.trim())
  kpInputVisible.value = false; kpInput.value = ''
}
function removeKnowledgePoint(i: number) { form.knowledge_points.splice(i, 1) }

// 迁移方向 tag 输入
const mdInputVisible = ref(false)
const mdInput = ref('')
const mdInputRef = ref<HTMLInputElement>()
function showMdInput() { mdInputVisible.value = true; nextTick(() => mdInputRef.value?.focus()) }
function addMigrationDir() {
  if (mdInput.value.trim()) form.migration_directions.push(mdInput.value.trim())
  mdInputVisible.value = false; mdInput.value = ''
}

// ── 初始化 ───────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    const q = await questionApi.getOne(Number(route.params.id))
    question.value = q
    // 填充表单
    form.subject            = q.subject ?? ''
    form.grade              = q.grade ?? ''
    form.chapter            = q.chapter ?? ''
    form.knowledge_points   = q.knowledge_points ? [...q.knowledge_points] : []
    form.difficulty         = q.difficulty ?? 'basic'
    form.solution           = q.solution ?? ''
    form.typical_error      = q.typical_error ?? ''
    form.migration_directions = q.migration_directions ? [...q.migration_directions] : []
    if (q.five_power_weights) Object.assign(form.five_power_weights, q.five_power_weights)
    if (q.five_power_thoughts) Object.assign(form.five_power_thoughts, q.five_power_thoughts)
  } finally { loading.value = false }
})

// ── 保存修改 ─────────────────────────────────────────────────
async function handleSaveAnalysis() {
  saving.value = true
  try {
    await questionApi.update(Number(route.params.id), {
      subject:            form.subject,
      grade:              form.grade,
      chapter:            form.chapter,
      knowledge_points:   [...form.knowledge_points],
      difficulty:         form.difficulty,
      solution:           form.solution,
      typical_error:      form.typical_error,
      five_power_weights: { ...form.five_power_weights },
      five_power_thoughts: { ...form.five_power_thoughts },
      migration_directions: [...form.migration_directions],
    })
    ElMessage.success('修改已保存')
  } finally { saving.value = false }
}

// ── 发布 ─────────────────────────────────────────────────────
async function handlePublish() {
  if (weightTotal.value !== 10) {
    ElMessage.warning('五力权重合计必须等于10分，请调整后再发布')
    return
  }
  await ElMessageBox.confirm(
    '确认发布此题目？发布后将触发向量化索引，题目将参与学生训练推荐。',
    '确认发布',
    { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'info' }
  )
  saving.value = true
  try {
    // 先保存修改，再发布
    await questionApi.update(Number(route.params.id), {
      subject: form.subject, grade: form.grade, chapter: form.chapter,
      knowledge_points: [...form.knowledge_points], difficulty: form.difficulty,
      solution: form.solution, typical_error: form.typical_error,
      five_power_weights: { ...form.five_power_weights },
      five_power_thoughts: { ...form.five_power_thoughts },
      migration_directions: [...form.migration_directions],
    })
    await questionApi.publish(Number(route.params.id))
    ElMessage.success('题目已发布，向量化任务已提交')
    router.push('/questions')
  } finally { saving.value = false }
}

// ── 驳回 ─────────────────────────────────────────────────────
function openReject() {
  rejectReason.value = ''
  rejectDialogVisible.value = true
}

async function handleReject() {
  if (!rejectReason.value.trim()) return
  saving.value = true
  try {
    await questionApi.reject(Number(route.params.id), { rejection_reason: rejectReason.value })
    rejectDialogVisible.value = false
    ElMessage.success('驳回成功，大模型重新分析任务已提交')
    router.push('/questions')
  } finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
.section-block {
  padding: 22px 24px;
  margin-bottom: 16px;
}

.stem-display {
  font-size: 14px;
  color: var(--text-1);
  line-height: 1.75;
  background: var(--bg-muted);
  border-radius: var(--r-lg);
  padding: 14px 16px;
  white-space: pre-wrap;
  word-break: break-word;
}

.edit-hint {
  display: flex;
  align-items: center;
  gap: 5px;
  font-size: 12.5px;
  color: var(--indigo);
  font-weight: 400;
}

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--draft          { background: var(--amber-dim);   color: var(--amber);  border-color: var(--amber-border); }
  &--analyzing      { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); }
  &--pending_review { background: var(--purple-dim);  color: var(--purple); border-color: var(--purple-border); }
  &--published      { background: var(--green-dim);   color: var(--green);  border-color: var(--green-border); }
  &--archived       { background: var(--bg-muted);    color: var(--text-3); border-color: var(--border-hover); }
}

// 小节标题
.sub-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 14px 0 12px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 16px;
  display: flex;
  align-items: center;
  gap: 10px;
}

// 五力权重合计
.weight-total {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: var(--r-pill);

  &--ok  { background: var(--green-dim); color: var(--green); }
  &--err { background: var(--red-dim);   color: var(--red); }
}

// 五力权重输入网格
.power-weights-grid {
  display: flex;
  gap: 16px;
  flex-wrap: wrap;
  margin-bottom: 4px;
}

.power-weight-item {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 6px;

  &__label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 12px;
    font-weight: 500;
    color: var(--text-2);
    white-space: nowrap;
  }
}

// 五力维度彩色圆点
.power-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

// 五力思路输入
.thoughts-grid {
  background: var(--bg-muted);
  border-radius: var(--r-lg);
  padding: 14px 16px 4px;
  margin-bottom: 4px;
}

// Tag 区域
.tag-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}
</style>
