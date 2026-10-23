<template>
  <div class="page-root" v-loading="loading">

    <!-- ── 顶部操作栏 ── -->
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="$router.push('/questions')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <template v-if="question?.status === 'pending_review'">
        <el-button @click="openReject" :loading="saving">驳回</el-button>
        <button class="btn-pink" type="button" @click="handlePublish" :disabled="saving">
          <SvgIcon name="deploy" :size="13" style="margin-right:4px" />
          发布上线
        </button>
      </template>
    </div>

    <div v-if="question">

      <!-- ── 题干内容（只读）── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题干内容</span>
        </div>
        <el-input v-model="question.stem" type="textarea" :rows="7" :disabled="!isEditable" />
      </div>

      <!-- ── 分析结果（可修改，仅 pending_review 状态）── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />大模型分析结果</span>
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
            <el-row :gutter="20">
              <el-col :span="16">
                <el-form-item label="题目类型">
                  <span v-if="!isEditable" class="plain-value">{{ questionTypeLabel }}</span>
                  <el-radio-group v-else v-model="form.question_type" @change="onQuestionTypeChange">
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
          <div class="section-content">
            <el-form-item label=" ">
              <div class="power-weights-grid">
                <div v-for="p in powers" :key="p" class="power-weight-item">
                  <div class="power-weight-item__label">
                    <span class="power-dot" :class="`power-dot--${p}`" />
                    {{ FivePowerLabels[p as FivePower] }}
                  </div>
                  <span v-if="!isEditable" class="plain-value power-weight-val">
                    {{ form.five_power_weights[p as FivePower] }}
                  </span>
                  <el-input-number
                    v-else
                    v-model="form.five_power_weights[p as FivePower]"
                    :min="0" :max="10" :step="1"
                    controls-position="right"
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
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
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
  // 兜底：树中无对应章节（该章节已发布题数为0，未含在树内），使用 AI 返回的知识点列表
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

function onQuestionTypeChange() {
  form.answer_single = 'A'
  form.answer_multi  = []
  form.answer_blanks = ['']
  form.answer_tf     = true
  form.answer_final  = ''
  form.answer_steps  = ['']
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
    form.subject_id          = ana?.ai_subject?.id  ?? (raw as any).subject_id  ?? null
    form.grade_id            = ana?.ai_grade?.id    ?? (raw as any).grade_id    ?? null
    form.semester_id         = ana?.ai_semester?.id ?? (raw as any).semester_id ?? null
    form.chapter_id          = ana?.ai_chapter?.id  ?? (raw as any).chapter_id  ?? null
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

// ── 发布 ─────────────────────────────────────────────────────
async function handlePublish() {
  if (weightTotal.value !== 10) {
    ElMessage.warning('五力权重合计必须等于10分，请调整后再发布')
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
    await questionApi.publish(Number(route.params.id), {
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
    })
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
[data-theme="light"] .btn-back.el-button {
  background-color: #ffffff;
  color: #9ca2af;
  border-color: #ffffff;
  &:hover { color: var(--color-primary); border-color: var(--color-primary); }
}
[data-theme="dark"] .btn-back.el-button {
  background-color: #242424;
  color: #9ca2af;
  border-color: #242424;
  &:hover { color: var(--color-primary); border-color: var(--color-primary); }
}

.section-block {
  padding: 5px 15px 15px;
  margin-bottom: 15px;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;

  [data-theme="dark"] & {
    background: #242424 !important;
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

.power-weights-grid {
  display: flex;
  flex-direction: row;
  gap: 16px;
  flex-wrap: nowrap;
  align-items: flex-start;
}

.power-weight-item {
  display: flex;
  flex-direction: column;
  align-items: flex-start;

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
  width: 120px !important;
  text-align: center;
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

// ── 全页面表单组件：去除 hover 效果，cursor 改为默认箭头 ──────
// cursor
:deep(.el-input__wrapper),
:deep(.el-select__wrapper),
:deep(.el-textarea__inner),
:deep(.el-input-number) {
  cursor: default !important;
  * { cursor: default !important; }
}

// input/select hover（亮主题）：维持基础边框色，不变蓝
:deep(.el-input__wrapper:hover:not(.is-focus)) {
  border-color: rgba(220, 224, 234, 1) !important;
  box-shadow: none !important;
}
:deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  box-shadow: 0 0 0 1px rgba(220, 224, 234, 1) inset !important;
}
:deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(220, 224, 234, 1) inset !important;
  border-color: rgba(220, 224, 234, 1) !important;
}
// textarea hover（亮主题）
:deep(.el-textarea__inner:hover) {
  border-color: rgba(220, 224, 234, 1) !important;
}

// input/select hover（暗主题）：维持暗主题基础边框色
[data-theme="dark"] .page-root :deep(.el-input__wrapper:hover:not(.is-focus)) {
  border-color: rgba(255, 255, 255, 0.10) !important;
}
[data-theme="dark"] .page-root :deep(.el-select__wrapper.is-hovering:not(.is-focused)) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.10) inset !important;
}
[data-theme="dark"] .page-root :deep(.el-select .el-input__wrapper:hover) {
  box-shadow: 0 0 0 1px rgba(255, 255, 255, 0.10) inset !important;
  border-color: rgba(255, 255, 255, 0.10) !important;
}
// textarea hover（暗主题）
[data-theme="dark"] .page-root :deep(.el-textarea__inner:hover) {
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
</style>
