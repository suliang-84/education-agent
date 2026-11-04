<template>
  <div class="page-root" :class="{ 'is-detail': question && !isEditable }" v-loading="loading">

    <!-- ── 顶部操作栏 ── -->
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="goBack">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <template v-if="question?.status === 'pending_review'">
        <el-button @click="openReject" :loading="saving">
          <SvgIcon v-if="!saving" name="reject_result" :size="14" style="margin-right:4px" />
          驳回结果
        </el-button>
        <el-button @click="handleSaveReview" :loading="saving">
          <SvgIcon v-if="!saving" name="save_result" :size="14" style="margin-right:4px" />
          保存结果
        </el-button>
        <button class="btn-pink" type="button" @click="handlePublish" :disabled="saving">
          <SvgIcon name="deploy" :size="13" style="margin-right:4px" />
          保存并发布上线
        </button>
      </template>
    </div>

    <div v-if="question">

      <!-- ── 题目内容（编辑态结构与训练题管理-编辑页一致）── -->
      <div class="surface section-block stem-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题目内容</span>
        </div>
        <div v-if="!isEditable" class="stem-display">{{ question.stem }}</div>
        <el-input v-else v-model="question.stem" class="stem-input" type="textarea" :rows="7" />
      </div>

      <!-- ── 分析结果（可修改，仅 pending_review 状态）── -->
      <div class="surface section-block detail-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />{{ isEditable ? '大模型分析结果' : '题目详情' }}</span>
          <span v-if="question.status === 'pending_review'" class="edit-hint">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.862 4.487l1.687-1.688a1.875 1.875 0 112.652 2.652L10.582 16.07a4.5 4.5 0 01-1.897 1.13L6 18l.8-2.685a4.5 4.5 0 011.13-1.897l8.932-8.931zm0 0L19.5 7.125M18 14v4.75A2.25 2.25 0 0115.75 21H5.25A2.25 2.25 0 013 18.75V8.25A2.25 2.25 0 015.25 6H10"/>
            </svg>
            所有字段均可修改后再发布
          </span>
        </div>

        <el-form :model="form" label-width="90px">

          <!-- ── 归属体系 ── -->
          <div class="sub-section-title">归属体系</div>
          <div class="section-content">
            <div class="belongs-row">
              <el-form-item label="科目">
                <span v-if="!isEditable" class="plain-value">{{ selectedSubjectName }}</span>
                <el-select v-else v-model="form.subject_id" style="width:100%" @change="onSubjectChange">
                  <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="年级">
                <span v-if="!isEditable" class="plain-value">{{ selectedGradeName }}</span>
                <el-select v-else v-model="form.grade_id" style="width:100%" @change="onGradeChange">
                  <el-option v-for="g in gradeOptions" :key="g.id" :label="g.name" :value="g.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="学期">
                <span v-if="!isEditable" class="plain-value">{{ selectedSemesterName }}</span>
                <el-select v-else v-model="form.semester_id" style="width:100%" @change="onSemesterChange">
                  <el-option v-for="s in semesterOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="章节" style="flex:2" class="chapter-form-item">
                <span v-if="!isEditable" class="plain-value">{{ selectedChapterName }}</span>
                <el-select
                  v-else
                  v-model="form.chapter_id"
                  style="width:100%"
                  clearable
                  :placeholder="chapterOptions.length === 0 ? '请先选择学期' : '请选择章节'"
                  @change="onChapterChange"
                >
                  <el-option v-for="c in chapterOptions" :key="c.id" :label="c.name" :value="c.id" />
                </el-select>
              </el-form-item>
            </div>
            <el-form-item label="知识点">
              <span v-if="!isEditable" class="plain-value">{{ selectedKnowledgePointNames || '—' }}</span>
              <el-select
                v-else
                v-model="form.knowledge_point_ids"
                multiple
                class="select-plain-multi"
                :disabled="knowledgePointOptions.length === 0"
                :placeholder="knowledgePointOptions.length === 0 ? '请先选择章节' : '请选择知识点（可多选）'"
                style="width:100%"
              >
                <el-option v-for="kp in knowledgePointOptions" :key="kp.id" :label="kp.name" :value="kp.id" />
              </el-select>
            </el-form-item>
          </div>

          <!-- ── 题目属性 ── -->
          <div class="sub-section-title">题目属性</div>
          <div class="section-content">
            <el-row :gutter="20" class="attr-row">
              <el-col :span="16">
                <el-form-item label="题目类型">
                  <span v-if="!isEditable" class="plain-value">{{ questionTypeLabel }}</span>
                  <el-radio-group v-else v-model="form.question_type" @change="(val: string) => { saveAnswerCache(prevQuestionType); prevQuestionType = val; onQuestionTypeChange(val) }">
                    <el-radio value="SINGLE_CHOICE">单选题</el-radio>
                    <el-radio value="MULTIPLE_CHOICE">多选题</el-radio>
                    <el-radio value="FILL_BLANK">填空题</el-radio>
                    <el-radio value="TRUE_FALSE">判断题</el-radio>
                    <el-radio value="APPLICATION">应用题</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="难度等级">
                  <span v-if="!isEditable" class="plain-value">{{ difficultyLabel }}</span>
                  <el-radio-group v-else v-model="form.difficulty">
                    <el-radio value="basic">基础</el-radio>
                    <el-radio value="advanced">进阶</el-radio>
                    <el-radio value="challenge">挑战</el-radio>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- ── 题目答案（依题型自动适配）── -->
          <div class="sub-section-title">题目答案</div>

          <!-- 单选题 -->
          <div v-if="form.question_type === 'SINGLE_CHOICE'" class="answer-block">
            <el-form-item label="正确选项">
              <span v-if="!isEditable" class="plain-value">{{ form.answer_single || '—' }}</span>
              <el-radio-group v-else v-model="form.answer_single">
                <el-radio value="A">A</el-radio>
                <el-radio value="B">B</el-radio>
                <el-radio value="C">C</el-radio>
                <el-radio value="D">D</el-radio>
              </el-radio-group>
            </el-form-item>
          </div>

          <!-- 多选题 -->
          <div v-else-if="form.question_type === 'MULTIPLE_CHOICE'" class="answer-block">
            <el-form-item label="正确选项">
              <span v-if="!isEditable" class="plain-value">{{ form.answer_multi.join('、') || '—' }}</span>
              <el-checkbox-group v-else v-model="form.answer_multi">
                <el-checkbox value="A">A</el-checkbox>
                <el-checkbox value="B">B</el-checkbox>
                <el-checkbox value="C">C</el-checkbox>
                <el-checkbox value="D">D</el-checkbox>
              </el-checkbox-group>
            </el-form-item>
          </div>

          <!-- 填空题 -->
          <div v-else-if="form.question_type === 'FILL_BLANK'" class="answer-block">
            <el-form-item label="标准答案">
              <div v-if="!isEditable" class="plain-steps">
                <span v-for="(ans, idx) in form.answer_blanks" :key="idx" class="plain-value" style="margin-bottom:10px">
                  {{ idx + 1 }}. {{ ans || '—' }}
                </span>
              </div>
              <div v-else class="key-steps">
                <el-input
                  v-for="(ans, idx) in form.answer_blanks" :key="idx"
                  v-model="form.answer_blanks[idx]"
                  placeholder="填入标准答案"
                  style="margin-bottom:10px"
                >
                  <template #prefix><span style="margin-right:10px">{{ idx + 1 }}.</span></template>
                  <template #suffix>
                    <SvgIcon
                      name="add" :size="15" color="var(--color-primary)"
                      style="cursor:pointer;margin-right:6px"
                      @click="form.answer_blanks.splice(idx + 1, 0, '')"
                    />
                    <SvgIcon
                      v-if="form.answer_blanks.length > 1"
                      name="delete" :size="15" color="var(--red)"
                      style="cursor:pointer"
                      @click="form.answer_blanks.splice(idx, 1)"
                    />
                  </template>
                </el-input>
              </div>
            </el-form-item>
          </div>

          <!-- 判断题 -->
          <div v-else-if="form.question_type === 'TRUE_FALSE'" class="answer-block">
            <el-form-item label="正确答案">
              <span v-if="!isEditable" class="plain-value">
                {{ form.answer_tf ? '✓ 正确（对）' : '✗ 错误（错）' }}
              </span>
              <el-radio-group v-else v-model="form.answer_tf">
                <el-radio :value="true">✓ 正确（对）</el-radio>
                <el-radio :value="false">✗ 错误（错）</el-radio>
              </el-radio-group>
            </el-form-item>
          </div>

          <!-- 应用题 -->
          <div v-else-if="form.question_type === 'APPLICATION'" class="answer-block">
            <el-form-item label="最终结论">
              <span v-if="!isEditable" class="plain-value">{{ form.answer_final || '—' }}</span>
              <el-input
                v-else
                v-model="form.answer_final"
                placeholder="如：x=33，y=9800（人数33人，总价9800钱）"
              />
            </el-form-item>
            <el-form-item label="关键步骤">
              <div v-if="!isEditable" class="plain-steps">
                <span v-for="(step, idx) in form.answer_steps" :key="idx" class="plain-value" style="margin-bottom:10px">
                  {{ idx + 1 }}. {{ step || '—' }}
                </span>
              </div>
              <div v-else class="key-steps">
                <el-input
                  v-for="(step, idx) in form.answer_steps" :key="idx"
                  v-model="form.answer_steps[idx]"
                  :placeholder="`第 ${idx + 1} 个关键步骤`"
                  style="margin-bottom:10px"
                >
                  <template #prefix><span style="margin-right:10px">{{ idx + 1 }}.</span></template>
                  <template #suffix>
                    <SvgIcon
                      name="add" :size="15" color="var(--color-primary)"
                      style="cursor:pointer;margin-right:6px"
                      @click="form.answer_steps.splice(idx + 1, 0, '')"
                    />
                    <SvgIcon
                      v-if="form.answer_steps.length > 1"
                      name="delete" :size="15" color="var(--red)"
                      style="cursor:pointer"
                      @click="form.answer_steps.splice(idx, 1)"
                    />
                  </template>
                </el-input>
              </div>
            </el-form-item>
          </div>

          <!-- 参考解析 -->
          <div class="sub-section-title">参考解析</div>
          <div class="section-content">
            <el-form-item label="详细推导">
              <span v-if="!isEditable" class="plain-value-area">{{ form.solution || '—' }}</span>
              <el-input v-else v-model="form.solution" type="textarea" :rows="5" placeholder="完整解题推导过程，供 AI 辅导引导和 RAG 检索使用..." />
            </el-form-item>
          </div>

          <!-- 典型错误 -->
          <div class="sub-section-title">典型错误</div>
          <div class="section-content">
            <el-form-item label="典型错误">
              <span v-if="!isEditable" class="plain-value">{{ form.typical_error || '—' }}</span>
              <el-input v-else v-model="form.typical_error" placeholder="学生最常犯的错误..." />
            </el-form-item>
          </div>

          <!-- 五力权重 -->
          <div class="sub-section-title">五力训练权重</div>
          <div class="section-content weights-content">
            <div v-if="!isEditable" ref="radarRef" class="weights-radar" />
            <el-form-item v-else label=" ">
              <div class="power-weights-grid">
                <div v-for="p in powers" :key="p" class="power-weight-item">
                  <div class="power-weight-item__label">
                    <span class="power-dot" :class="`power-dot--${p}`" />
                    {{ FivePowerLabels[p as FivePower] }}
                  </div>
                  <el-input-number
                    v-model="form.five_power_weights[p as FivePower]"
                    :min="0" :max="10" :step="1"
                    :precision="0"
                    controls-position="right"
                    size="small"
                    class="power-weight-val"
                  />
                </div>
              </div>
            </el-form-item>
          </div>

          <!-- 五力训练思路 -->
          <div class="sub-section-title">五力训练思路</div>
          <div class="section-content thoughts-grid">
            <el-form-item
              v-for="p in powers" :key="p"
              :label="FivePowerLabels[p as FivePower]"
            >
              <span v-if="!isEditable" class="plain-value">
                {{ form.five_power_thoughts[p as FivePower] || '—' }}
              </span>
              <el-input
                v-else
                v-model="form.five_power_thoughts[p as FivePower]"
                placeholder="该维度的训练切入点..."
                size="small"
              />
            </el-form-item>
          </div>

          <!-- 迁移方向（已隐藏）-->

        </el-form>
      </div>

    </div>

    <!-- ── 驳回弹窗 ── -->
    <el-dialog v-model="rejectDialogVisible" title="填写驳回意见" width="540px" :close-on-click-modal="false">
      <div style="font-size:13.5px;color:var(--text-2);margin-bottom:14px;line-height:1.6">
        驳回后题目将回到草稿状态，驳回意见会保存。返回列表后手动点击「AI 分析」，驳回意见将自动携带给大模型。
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
          提交驳回
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, onBeforeUnmount, watch, nextTick } from 'vue'
import * as echarts from 'echarts'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi, knowledgeTreeApi, type KnowledgeTreeNode } from '@/api/questions'
import type { QuestionStatus, QuestionType, FivePower, Difficulty } from '@/types'
import { QuestionStatusLabels, FivePowerLabels } from '@/types'

const route  = useRoute()
const router = useRouter()

const loading = ref(false)
const saving  = ref(false)
const question = ref<any>(null)

const rejectDialogVisible = ref(false)
const rejectReason = ref('')

const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 知识体系树（用于下拉选项）────────────────────────────────
const allNodes = ref<KnowledgeTreeNode[]>([])

// 使用树原始结构（有父子关系），不用扁平 map，避免 ID 冲突
const rawTree = ref<KnowledgeTreeNode[]>([])

const subjectOptions = computed(() =>
  rawTree.value.map(n => ({ id: n.id, name: n.name }))
)
const gradeOptions = computed(() => {
  if (!form.subject_id) return []
  const sub = rawTree.value.find(n => n.id === form.subject_id)
  return (sub?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})
const semesterOptions = computed(() => {
  if (!form.grade_id) return []
  const sub = rawTree.value.find(n => n.id === form.subject_id)
  const grade = (sub?.children ?? []).find(n => n.id === form.grade_id)
  return (grade?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})

const chapterOptions = computed(() => {
  if (!form.semester_id) return []
  const sub = rawTree.value.find(n => n.id === form.subject_id)
  const grade = (sub?.children ?? []).find(n => n.id === form.grade_id)
  const sem = (grade?.children ?? []).find(n => n.id === form.semester_id)
  return (sem?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})

// AI 分析返回的知识点列表（含 id+name），用于树查找失败时兜底
const aiKnowledgePoints = ref<{ id: number; name: string }[]>([])

const knowledgePointOptions = computed(() => {
  if (form.chapter_id) {
    const sub = rawTree.value.find(n => n.id === form.subject_id)
    const grade = (sub?.children ?? []).find(n => n.id === form.grade_id)
    const sem = (grade?.children ?? []).find(n => n.id === form.semester_id)
    const ch = (sem?.children ?? []).find(n => n.id === form.chapter_id)
    const treeKPs = (ch?.children ?? []).map(n => ({ id: n.id, name: n.name }))
    if (treeKPs.length > 0) return treeKPs
  }
  // 兜底：树中取不到该章节下的知识点时，使用 AI 返回的知识点列表
  return aiKnowledgePoints.value
})

function onSubjectChange() {
  form.grade_id = null
  form.semester_id = null
  form.chapter_id = null
  form.knowledge_point_ids = []
}
function onGradeChange() {
  form.semester_id = null
  form.chapter_id = null
  form.knowledge_point_ids = []
}
function onSemesterChange() {
  form.chapter_id = null
  form.knowledge_point_ids = []
}
function onChapterChange() {
  form.knowledge_point_ids = []
}

// ── 页面标题 / 可编辑状态 ─────────────────────────────────────
const isEditable = computed(() => question.value?.status === 'pending_review')

const pageTitle = computed(() => {
  const s = question.value?.status
  if (s === 'pending_review') return '审核分析结果'
  if (s === 'published')      return '查看题目详情'
  if (s === 'archived')       return '查看已归档题目'
  return '题目详情'
})

const answerTypeHint = computed(() => {
  const map: Record<QuestionType, string> = {
    SINGLE_CHOICE:   '单选题 — 标注正确选项字母',
    MULTIPLE_CHOICE: '多选题 — 标注所有正确选项字母',
    FILL_BLANK:      '填空题 — 逐空填写标准答案',
    TRUE_FALSE:      '判断题 — 选择「对」或「错」',
    APPLICATION:     '应用题 — 填写最终结论和关键推导步骤',
  }
  return form.question_type ? map[form.question_type as QuestionType] : ''
})

// ── 可编辑表单（使用 ID）────────────────────────────────────
const form = reactive({
  subject_id:           null as number | null,
  grade_id:             null as number | null,
  semester_id:          null as number | null,
  chapter_id:           null as number | null,
  knowledge_point_ids:  [] as number[],
  question_type:        'APPLICATION' as QuestionType,
  difficulty:           'basic' as Difficulty,
  answer_single:        'A' as string,
  answer_multi:         [] as string[],
  answer_blanks:        [''] as string[],
  answer_tf:            true as boolean,
  answer_final:         '' as string,
  answer_steps:         [''] as string[],
  solution:             '' as string,
  typical_error:        '' as string,
  five_power_weights:   { INSIGHT: 2, CONSTRUCT: 5, DEDUCE: 2, ADAPT: 1, MIGRATE: 0 } as Record<FivePower, number>,
  five_power_thoughts:  { INSIGHT: '', CONSTRUCT: '', DEDUCE: '', ADAPT: '', MIGRATE: '' } as Record<FivePower, string>,
  migration_directions: [] as string[],
})

const weightTotal = computed(() => Object.values(form.five_power_weights).reduce((s, v) => s + v, 0))

const selectedKnowledgePointNames = computed(() =>
  form.knowledge_point_ids
    .map(id => knowledgePointOptions.value.find(kp => kp.id === id)?.name ?? '')
    .filter(Boolean)
    .join('、')
)

const selectedSubjectName  = computed(() => subjectOptions.value.find(s => s.id === form.subject_id)?.name  ?? '—')
const selectedGradeName    = computed(() => gradeOptions.value.find(g => g.id === form.grade_id)?.name      ?? '—')
const selectedSemesterName = computed(() => semesterOptions.value.find(s => s.id === form.semester_id)?.name ?? '—')
const selectedChapterName  = computed(() => chapterOptions.value.find(c => c.id === form.chapter_id)?.name  ?? '—')

const questionTypeLabel = computed(() => ({
  SINGLE_CHOICE: '单选题', MULTIPLE_CHOICE: '多选题',
  FILL_BLANK: '填空题', TRUE_FALSE: '判断题', APPLICATION: '应用题',
} as Record<string, string>)[form.question_type] ?? '—')

const difficultyLabel = computed(() => ({
  basic: '基础', advanced: '进阶', challenge: '挑战',
} as Record<string, string>)[form.difficulty] ?? '—')

const migrationDisplayText = computed(() => form.migration_directions.join('、') || '—')

// 记录上一个题型，用于切换前保存缓存
let prevQuestionType = form.question_type

// 各题型答案缓存，切换题型时保存当前答案，切回时恢复
const answerCache: Record<string, {
  answer_single?: string
  answer_multi?: string[]
  answer_blanks?: string[]
  answer_tf?: boolean
  answer_final?: string
  answer_steps?: string[]
}> = {}

function onQuestionTypeChange(newType: string) {
  const cached = answerCache[newType]
  if (cached) {
    if (cached.answer_single !== undefined) form.answer_single = cached.answer_single
    if (cached.answer_multi  !== undefined) form.answer_multi  = [...cached.answer_multi]
    if (cached.answer_blanks !== undefined) form.answer_blanks = [...cached.answer_blanks]
    if (cached.answer_tf     !== undefined) form.answer_tf     = cached.answer_tf
    if (cached.answer_final  !== undefined) form.answer_final  = cached.answer_final
    if (cached.answer_steps  !== undefined) form.answer_steps  = [...cached.answer_steps]
  } else {
    // 第一次切换到该题型，初始化默认值
    form.answer_single = 'A'
    form.answer_multi  = []
    form.answer_blanks = ['']
    form.answer_tf     = true
    form.answer_final  = ''
    form.answer_steps  = ['']
  }
}

// 在题型切换前保存当前答案到缓存
function saveAnswerCache(type: string) {
  answerCache[type] = {
    answer_single: form.answer_single,
    answer_multi:  [...form.answer_multi],
    answer_blanks: [...form.answer_blanks],
    answer_tf:     form.answer_tf,
    answer_final:  form.answer_final,
    answer_steps:  [...form.answer_steps],
  }
}

function deserializeAnswer(answer: any) {
  if (!answer) return
  form.question_type = answer.type as QuestionType
  if (answer.type === 'SINGLE_CHOICE')   form.answer_single = answer.correct
  if (answer.type === 'MULTIPLE_CHOICE') form.answer_multi  = [...(answer.correct ?? [])]
  if (answer.type === 'FILL_BLANK')      form.answer_blanks = answer.correct?.length ? [...answer.correct] : ['']
  if (answer.type === 'TRUE_FALSE')      form.answer_tf     = answer.correct
  if (answer.type === 'APPLICATION') {
    form.answer_final = answer.final_answer ?? ''
    form.answer_steps = answer.key_steps?.length ? [...answer.key_steps] : ['']
  }
}

function serializeAnswer() {
  const t = form.question_type
  if (t === 'SINGLE_CHOICE')   return { type: t, correct: form.answer_single }
  if (t === 'MULTIPLE_CHOICE') return { type: t, correct: [...form.answer_multi] }
  if (t === 'FILL_BLANK')      return { type: t, correct: form.answer_blanks.filter(Boolean), accept_range: null }
  if (t === 'TRUE_FALSE')      return { type: t, correct: form.answer_tf }
  if (t === 'APPLICATION')     return { type: t, final_answer: form.answer_final, key_steps: form.answer_steps.filter(Boolean) }
  return undefined
}


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
// ── 详情态：五力权重雷达图 ──────────────────────────────────
const radarRef = ref<HTMLElement>()
let radarChart: echarts.ECharts | undefined

function renderRadar() {
  if (!radarRef.value) { radarChart?.dispose(); radarChart = undefined; return }
  if (radarChart && radarChart.getDom() !== radarRef.value) { radarChart.dispose(); radarChart = undefined }
  if (!radarChart) radarChart = echarts.init(radarRef.value)
  const values = powers.map(p => form.five_power_weights[p as FivePower] ?? 0)
  const css = getComputedStyle(radarRef.value)
  const primary = css.getPropertyValue('--color-primary').trim() || '#608df8'
  const alpha = (hex: string, a: number) => {
    const m = /^#([0-9a-f]{6})$/i.exec(hex)
    if (!m) return hex
    const n = parseInt(m[1], 16)
    return `rgba(${n >> 16},${(n >> 8) & 255},${n & 255},${a})`
  }
  const dotRich = Object.fromEntries(powers.map(p => [
    `dot_${p}`, { width: 6, height: 6, borderRadius: 3, backgroundColor: css.getPropertyValue(`--power-${p.toLowerCase()}`).trim() || '#608df8' },
  ]))
  radarChart.setOption({
    backgroundColor: 'transparent',
    radar: {
      indicator: powers.map((p, i) => ({ name: `${FivePowerLabels[p as FivePower]}  ${values[i]}`, max: 10, key: p })),
      radius: 80,
      splitNumber: 5,
      axisName: {
        color: primary,
        fontSize: 13,
        formatter: (name: string, indicator: any) => `{dot_${indicator.key}|}  ${name}`,
        rich: dotRich,
      },
      splitLine: { lineStyle: { color: alpha(primary, 0.22) } },
      splitArea: { areaStyle: { color: [alpha(primary, 0.02), alpha(primary, 0.06)] } },
      axisLine: { lineStyle: { color: alpha(primary, 0.3) } },
    },
    series: [{
      type: 'radar',
      symbolSize: 6,
      data: [{ value: values, name: '五力训练权重', itemStyle: { color: primary }, lineStyle: { color: primary, width: 2 }, areaStyle: { color: alpha(primary, 0.25) } }],
    }],
  })
}

watch([radarRef, () => form.five_power_weights], () => nextTick(renderRadar), { deep: true, flush: 'post' })
const onResize = () => radarChart?.resize()
window.addEventListener('resize', onResize)
// 切换亮/暗主题时按新的主题色重绘
const themeObserver = new MutationObserver(() => renderRadar())
themeObserver.observe(document.documentElement, { attributes: true, attributeFilter: ['data-theme'] })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); themeObserver.disconnect(); radarChart?.dispose() })

onMounted(async () => {
  loading.value = true
  try {
    const [raw, treeRes] = await Promise.all([
      questionApi.getOne(Number(route.params.id)),
      knowledgeTreeApi.getTree(),
    ])

    rawTree.value = treeRes.tree
    allNodes.value = flattenTree(treeRes.tree)

    question.value = raw
    const ana = (raw as any).latest_analysis

    // 优先使用 latest_analysis 的 ai_* 字段，回退到题目已确认字段
    // 注意：接口返回的是嵌套对象（ai_subject.id），而非平铺 ID 字段
    form.subject_id          = ana?.ai_subject?.id  ?? ana?.ai_subject_id  ?? (raw as any).subject_id  ?? null
    form.grade_id            = ana?.ai_grade?.id    ?? ana?.ai_grade_id    ?? (raw as any).grade_id    ?? null
    form.semester_id         = ana?.ai_semester?.id ?? ana?.ai_semester_id ?? (raw as any).semester_id ?? null
    form.chapter_id          = ana?.ai_chapter?.id  ?? ana?.ai_chapter_id  ?? (raw as any).chapter_id  ?? null
    form.knowledge_point_ids = [...(ana?.ai_knowledge_point_ids ?? (raw as any).knowledge_point_ids ?? [])].map(Number).filter(Boolean)
    aiKnowledgePoints.value  = (ana?.ai_knowledge_points ?? []).map((kp: any) => ({ id: Number(kp.id), name: kp.name }))
    form.question_type       = (ana?.ai_question_type ?? (raw as any).question_type ?? 'APPLICATION') as QuestionType
    form.difficulty          = (ana?.ai_difficulty   ?? (raw as any).difficulty   ?? 'basic') as Difficulty
    form.solution            = ana?.ai_solution      ?? (raw as any).solution      ?? ''
    form.typical_error       = ana?.ai_common_error  ?? (raw as any).common_error  ?? ''
    form.migration_directions = [...(ana?.ai_transfer_directions ?? (raw as any).transfer_direction ?? [])]

    if (ana?.ai_five_power_weights)
      Object.assign(form.five_power_weights, ana.ai_five_power_weights)
    else if ((raw as any).five_power_weights)
      Object.assign(form.five_power_weights, (raw as any).five_power_weights)

    if (ana?.ai_power_solutions)
      Object.assign(form.five_power_thoughts, ana.ai_power_solutions)
    else if ((raw as any).power_solutions)
      Object.assign(form.five_power_thoughts, (raw as any).power_solutions)

    deserializeAnswer(ana?.ai_answer ?? (raw as any).answer)
  } finally { loading.value = false }
})

function flattenTree(nodes: KnowledgeTreeNode[]): KnowledgeTreeNode[] {
  const result: KnowledgeTreeNode[] = []
  function walk(arr: KnowledgeTreeNode[]) {
    for (const n of arr) {
      result.push(n)
      if (n.children?.length) walk(n.children)
    }
  }
  walk(nodes ?? [])
  return result
}

function buildPayload() {
  return {
    subject_id:          form.subject_id!,
    grade_id:            form.grade_id!,
    semester_id:         form.semester_id!,
    chapter_id:          form.chapter_id ?? undefined as any,
    knowledge_point_ids: [...form.knowledge_point_ids],
    question_type:       form.question_type,
    answer:              serializeAnswer() as any,
    difficulty:          form.difficulty,
    solution:            form.solution,
    common_error:        form.typical_error,
    power_solutions:     { ...form.five_power_thoughts },
    five_power_weights:  { ...form.five_power_weights },
    transfer_directions: [...form.migration_directions],
  }
}

// ── 保存（仅保存当前编辑内容，不改变题目状态）──────────────────
async function handleSaveReview() {
  saving.value = true
  try {
    await questionApi.saveReview(Number(route.params.id), {
      ...buildPayload(),
      stem: question.value?.stem,
    })
    ElMessage.success('保存成功')
    router.push('/questions/entry')
  } finally { saving.value = false }
}

// 返回：待审核题目属于「训练题录入」流程，返回录入列表；已发布/归档的查看页返回训练题管理
function goBack() {
  router.push(question.value?.status === 'pending_review' ? '/questions/entry' : '/questions')
}

// ── 发布 ─────────────────────────────────────────────────────
async function handlePublish() {
  if (weightTotal.value !== 10) {
    const sum = weightTotal.value
    ElMessage.warning(`五力权重合计为 ${sum} 分（需为 10 分），请调整后再发布`)
    return
  }
  if (!form.subject_id || !form.grade_id || !form.semester_id) {
    ElMessage.warning('请选择科目、年级和学期')
    return
  }
  await ElMessageBox.confirm(
    '确认发布此题目？发布后将触发向量化索引，题目将参与学生训练推荐。',
    '确认发布',
    { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'info' }
  )
  saving.value = true
  try {
    const payload = buildPayload()
    // 先保存当前编辑内容，再发布
    await questionApi.saveReview(Number(route.params.id), { ...payload, stem: question.value?.stem })
    await questionApi.publish(Number(route.params.id), payload)
    ElMessage.success('题目已发布')
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
    ElMessage.success('驳回成功，题目已回到草稿状态，请返回列表手动触发重新分析')
    router.push('/questions')
  } finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
// ── 隐藏页面滚动条 ────────────────────────────────────────────
.page-root {
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

// ── 顶部操作栏 ───────────────────────────────────────────────
.form-topbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

// ── 返回按钮 ─────────────────────────────────────────────────
.section-block {
  padding: 5px 15px 15px;
  margin-bottom: 10px;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;

  [data-theme="dark"] & {
    background: #1a1a1a !important;
    border-color: #202020 !important;
  }
}

.stem-display {
  font-size: 14px;
  color: var(--text-1);
  line-height: 1.75;
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 14px 16px;
  white-space: pre-wrap;
  word-break: break-word;

  [data-theme="dark"] & {
    background: #282b31;
    color: #ffffff;
  }
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

.sub-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-2);
  padding: 0;
  margin-bottom: 5px;
  display: flex;
  align-items: center;
  gap: 10px;

  [data-theme="dark"] & { color: #ffffff; }
}

.belongs-row {
  display: flex;
  flex-wrap: nowrap;

  .el-form-item {
    flex: 1;
    margin-bottom: 10px;
  }
}

:deep(.chapter-form-item .el-form-item__content) {
  height: 30px !important;
  line-height: 30px !important;
}

.sub-section-hint {
  font-size: 11.5px;
  font-weight: 400;
  color: var(--text-3);
  text-transform: none;
  letter-spacing: 0;
}

// 统一子模块内容背景容器
.section-content,
.answer-block {
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 10px 10px 10px 0;
  margin-bottom: 12px;

  // 内部表单项间距 10px，最后一项去除 margin 避免与 padding-bottom 叠加
  :deep(.el-form-item) {
    margin-bottom: 10px;
  }
  :deep(.el-form-item:last-child) {
    margin-bottom: 0;
  }
}

.section-content,
.answer-block {
  padding: 15px 15px 15px 0;
}

// 五力训练权重：上内边距为 8px
.section-content.weights-content {
  padding-top: 8px;
}

.answer-hint {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 6px;
}

.fill-blank-answers {
  display: flex;
  flex-direction: column;
  gap: 8px;
}

.fill-blank-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.fill-blank-label {
  font-size: 12.5px;
  color: var(--text-2);
  font-weight: 500;
  white-space: nowrap;
}

.key-steps {
  display: flex;
  flex-direction: column;
  width: 100%;

  // 最后一个输入框去除 margin，避免与容器 padding-bottom 叠加
  :deep(.el-input:last-child) {
    margin-bottom: 0 !important;
  }
}

.key-step-item {
  display: flex;
  align-items: center;
  gap: 10px;
}


.weight-total {
  font-size: 12px;
  font-weight: 600;
  padding: 2px 9px;
  border-radius: var(--r-pill);

  &--ok  { background: var(--green-dim); color: var(--green); }
  &--err { background: var(--red-dim);   color: var(--red); }
}

// 与「测试题管理-答案配置」的五力权重配置（.weights-row / .weight-item）保持一致
.power-weights-grid {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

:deep(.power-weight-item .el-input__inner) {
  text-align: left !important;
}

.power-weight-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;

  &__label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 13px;
    font-weight: 500;
    color: var(--text-2);
    white-space: nowrap;
  }
}

.power-weight-val {
  width: 90px !important;
}

.power-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

.thoughts-grid {
  // background/border-radius/padding 由 .section-content 提供
}

.tag-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}

// ── 纯文本展示（外观与 disabled input 一致）──────────────────
.plain-value {
  display: block;
  width: 100%;
  height: 30px;
  line-height: 28px;
  padding: 0 10px;
  font-size: 13px;
  color: var(--text-1);
  background: var(--bg-surface);
  border: 1px solid rgba(220, 224, 234, 1);
  border-radius: 4px;
  box-sizing: border-box;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;

  [data-theme="dark"] & {
    background: var(--bg-muted);
    border-color: rgba(255, 255, 255, 0.10);
  }
}

// 多行文本展示（textarea 场景）
.plain-value-area {
  display: block;
  width: 100%;
  min-height: 110px;
  padding: 8px 10px;
  font-size: 13px;
  color: var(--text-1);
  background: var(--bg-surface);
  border: 1px solid rgba(220, 224, 234, 1);
  border-radius: 4px;
  box-sizing: border-box;
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.6;

  [data-theme="dark"] & {
    background: var(--bg-muted);
    border-color: rgba(255, 255, 255, 0.10);
  }
}

// 应用题关键步骤只读展示
.plain-steps {
  display: flex;
  flex-direction: column;
  width: 100%;
}

// ── 覆盖 EP CSS 变量 ─────────────────────────────────────────
:deep(.el-form) {
  --el-disabled-text-color: var(--text-1);
  --el-disabled-bg-color: var(--bg-muted);
  --el-disabled-border-color: var(--border);
  --el-color-primary: var(--color-primary);
}

// ── 详情（只读）态：去除 hover 效果，cursor 改为默认箭头 ──────
// 只在详情态生效；编辑态（待审核可修改）的输入框保持正常的悬停 / 光标反馈，与「训练题管理 → 编辑」页一致
// cursor
.is-detail :deep(.el-input__wrapper),
.is-detail :deep(.el-select__wrapper),
.is-detail :deep(.el-textarea__inner),
.is-detail :deep(.el-input-number) {
  cursor: default !important;
  * { cursor: default !important; }
}

// input/select hover（亮主题）：维持基础边框色，不变蓝
.is-detail :deep(.el-input__wrapper:hover:not(.is-focus)) {
  border-color: rgba(220, 224, 234, 1) !important;
  box-shadow: none !important;
}
.is-detail :deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  box-shadow: 0 0 0 1px rgba(220, 224, 234, 1) inset !important;
}
.is-detail :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(220, 224, 234, 1) inset !important;
  border-color: rgba(220, 224, 234, 1) !important;
}
// textarea hover（亮主题）
.is-detail :deep(.el-textarea__inner:hover) {
  border-color: rgba(220, 224, 234, 1) !important;
}

// input/select hover（暗主题）：维持暗主题基础边框色
[data-theme="dark"] .page-root.is-detail :deep(.el-input__wrapper:hover:not(.is-focus)) {
  border-color: rgba(255, 255, 255, 0.10) !important;
}
[data-theme="dark"] .page-root.is-detail :deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.10) inset !important;
}
[data-theme="dark"] .page-root.is-detail :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.10) inset !important;
  border-color: rgba(255, 255, 255, 0.10) !important;
}
// textarea hover（暗主题）
[data-theme="dark"] .page-root.is-detail :deep(.el-textarea__inner:hover) {
  border-color: rgba(255, 255, 255, 0.10) !important;
}

// ── disabled：文字颜色（textarea / input）────────────────────
:deep(.el-textarea.is-disabled .el-textarea__inner) {
  color: var(--text-1) !important;
  -webkit-text-fill-color: var(--text-1) !important;
}
:deep(.el-input.is-disabled .el-input__inner),
:deep(.el-input-number.is-disabled .el-input__inner) {
  -webkit-text-fill-color: var(--text-1) !important;
}

// ── disabled radio/checkbox cursor ──────────────────────────────
:deep(.el-radio.is-disabled .el-radio__input),
:deep(.el-checkbox.is-disabled .el-checkbox__input) {
  cursor: default !important;
}
:deep(.el-radio.is-disabled),
:deep(.el-checkbox.is-disabled) {
  cursor: default !important;
}

// ── 知识点 select disabled：去除 tag 盒子样式 ────────────────
:deep(.el-select.is-disabled .el-tag) {
  background: transparent !important;
  border-color: transparent !important;
  color: var(--text-1) !important;
  padding: 0 2px !important;
  height: 22px !important;
  line-height: 22px !important;
  .el-tag__content { color: var(--text-1) !important; }
  .el-tag__close { display: none !important; }
}

// ── 详情（只读）模式：文档式排版，与编辑态的输入框外观明确区分 ──
.is-detail {
  // 子模块沿用全局玻璃面板：云晕底 + 随机位置的边框高亮（每次渲染各子模块各自随机，见 utils/edgeHighlight.ts）。
  // 原先这里有一条固定在左侧的 3px 主色边框，会让高亮位置固定，已去掉
  .section-block {
    position: relative;
  }

  // 题目内容：与后台学生「摘要」页的「学习信息摘要」文本框同样式——深色底、等宽字体、白字
  .stem-display {
    background: #1E2030;
    border-radius: 4px;
    padding: 16px 18px;
    font-family: var(--font-mono);
    font-size: 12.5px;
    line-height: 1.7;
    color: #ffffff;
    white-space: pre-wrap;
    word-break: break-word;
    // 暗色主题与摘要页「学习信息摘要」文本框完全一致（#1E2030 + 白字，不单独换底色）；
    // 亮色主题改为浅灰底 + 深色字，不再是深色块
    [data-theme="light"] & {
      background: var(--bg-muted);
      color: var(--text-1);
    }
  }

  // 子模块纵向节奏统一为 10px：
  // 子标题 → 子内容 → 分割线 → 下一个子标题；子内容内各项之间同为 10px
  // 文字框尽量贴合文字：标题 / 标签 / 只读值统一 22px 行高，
  // 这样「10px」就是文字与文字之间的实际视觉间距，而不是各自 20/30px 框之间的间距
  .sub-section-title {
    margin: 0 0 10px;
    height: 22px;
    line-height: 22px;
  }

  :deep(.el-form-item__label),
  :deep(.el-form-item__content) {
    height: auto !important;
    min-height: 22px;
    line-height: 22px !important;
  }

  // 虚线置于每个子模块内容的底部（最后一个子模块除外）
  .section-content,
  .answer-block {
    background: transparent;
    padding: 0 0 10px;
    margin: 0 0 10px;
    border-bottom: 1px dashed rgba(94, 141, 249, 0.40);
    [data-theme="dark"] & { border-bottom-color: rgba(255, 255, 255, 0.20); }

    &:last-child { border-bottom: none; padding-bottom: 0; margin-bottom: 0; }
  }

  // 去掉输入框外观，只保留文字
  .plain-value,
  .plain-value-area {
    height: auto;
    min-height: 0;
    line-height: 1.7;
    padding: 0;
    background: transparent;
    border: none;
    font-weight: 500;
    white-space: normal;
    overflow: visible;
    [data-theme="dark"] & { background: transparent; border: none; }
  }

  :deep(.el-form-item__label) { color: var(--text-3); font-weight: 400; }
  .weights-radar { width: 420px; max-width: 100%; height: 216px; margin-right: auto; }
  .belongs-row { margin-bottom: 10px; .el-form-item { margin-bottom: 0; } }

  // 步骤逐条之间 10px（行内 margin-bottom），最后一条不留，避免与子内容底部 10px 叠加成 20px
  .plain-steps .plain-value:last-child { margin-bottom: 0 !important; }

  // 题目属性与「归属体系」同一栅格：每列 20%（科目:年级:学期:章节 = 1:1:1:2），
  // 使「难度等级」与上方「年级」在 x 轴方向对齐
  .attr-row {
    flex-wrap: nowrap;
    margin: 0 !important;
    .el-col {
      flex: 0 0 20%;
      max-width: 20%;
      padding: 0 !important;
    }
  }
}
</style>

<style>
/* （已去掉对所有子模块的统一云晕：「题目内容」等子模块沿用全局玻璃面板的背景，与摘要页「学习信息摘要」一致；下面只保留「题目详情」子模块的云晕）
   详情页子模块的云晕：全局玻璃面板的云晕是固定像素大小（约 360~420px）的两团光，一个子模块很高（如「题目详情」）时
   只有左上和右下两个角有光，中间一大片是平的。云晕用固定大小的椭圆（480px × 260px）：宽而矮的子模块（如「题目内容」）不会被拉成一条很长的光带，
   高的子模块也只在角上有光。注意不能在渐变尺寸里用 min() / max()：浏览器会判整条 background 无效，云晕整个不显示。
   不加 scoped：选择器要从 html / .content-area 开头，才压得过 style.scss 里的全局规则。 */

/* 「题目详情」子模块（详情态）：右上角再加一团云晕；暗色下恢复定时反光（二级页面默认去掉了反光，这里单独打开） */
html[data-theme="dark"] .content-area .page-root.is-detail .section-block.detail-block {
  background:
    radial-gradient(ellipse 480px 260px at 100% 0%, rgba(94, 141, 249, 0.26), transparent 72%),
    radial-gradient(ellipse 480px 260px at 104% 106%, rgba(124, 112, 255, 0.15), transparent 72%),
    rgba(14, 17, 22, 0.60) !important;
}
html[data-theme="light"] .content-area .page-root.is-detail .section-block.detail-block {
  background:
    radial-gradient(ellipse 480px 260px at 100% 0%, rgba(94, 141, 249, 0.17), transparent 72%),
    radial-gradient(ellipse 480px 260px at 104% 106%, rgba(124, 112, 255, 0.10), transparent 72%),
    rgba(255, 255, 255, 0.74) !important;
}
@media (prefers-reduced-motion: no-preference) {
  html[data-theme="dark"] .content-area.no-shine .page-root.is-detail .section-block.detail-block::after {
    animation: panel-shine 9s ease-in-out infinite;
    opacity: 1;
  }
}
</style>
