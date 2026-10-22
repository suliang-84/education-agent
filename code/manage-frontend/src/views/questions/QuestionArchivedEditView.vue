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
      <el-button @click="handleSave" :loading="saving">
        <SvgIcon v-if="!saving" name="save" :size="14" style="margin-right:4px" />
        保存
      </el-button>
      <button class="btn-pink" type="button" @click="handleSaveAndActivate" :disabled="saving">
        <SvgIcon name="play" :size="13" style="margin-right:4px" />
        保存并启用
      </button>
    </div>

    <div v-if="question">

      <!-- ── 题干内容 ── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题干内容</span>
        </div>
        <el-input v-model="question.stem" type="textarea" :rows="7" />
      </div>

      <!-- ── 编辑内容 ── -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题目详情</span>
        </div>

        <el-form :model="form" label-width="90px">

          <!-- ── 归属体系 ── -->
          <div class="sub-section-title">归属体系</div>
          <div class="section-content">
            <div class="belongs-row">
              <el-form-item label="科目">
                <el-select v-model="form.subject_id" style="width:100%" @change="onSubjectChange">
                  <el-option v-for="s in subjectOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="年级">
                <el-select v-model="form.grade_id" style="width:100%" @change="onGradeChange">
                  <el-option v-for="g in gradeOptions" :key="g.id" :label="g.name" :value="g.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="学期">
                <el-select v-model="form.semester_id" style="width:100%" @change="onSemesterChange">
                  <el-option v-for="s in semesterOptions" :key="s.id" :label="s.name" :value="s.id" />
                </el-select>
              </el-form-item>
              <el-form-item label="章节" style="flex:2">
                <el-select
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
              <el-select
                v-model="form.knowledge_point_ids"
                multiple
                collapse-tags
                collapse-tags-tooltip
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
                  <el-radio-group v-model="form.question_type" @change="onQuestionTypeChange">
                    <el-radio-button value="SINGLE_CHOICE">单选题</el-radio-button>
                    <el-radio-button value="MULTIPLE_CHOICE">多选题</el-radio-button>
                    <el-radio-button value="FILL_BLANK">填空题</el-radio-button>
                    <el-radio-button value="TRUE_FALSE">判断题</el-radio-button>
                    <el-radio-button value="APPLICATION">应用题</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
              <el-col :span="8">
                <el-form-item label="难度等级">
                  <el-radio-group v-model="form.difficulty">
                    <el-radio-button value="basic">基础</el-radio-button>
                    <el-radio-button value="advanced">进阶</el-radio-button>
                    <el-radio-button value="challenge">挑战</el-radio-button>
                  </el-radio-group>
                </el-form-item>
              </el-col>
            </el-row>
          </div>

          <!-- ── 题目答案 ── -->
          <div class="sub-section-title">题目答案</div>

          <!-- 单选题 -->
          <div v-if="form.question_type === 'SINGLE_CHOICE'" class="answer-block">
            <el-form-item label="正确选项">
              <el-radio-group v-model="form.answer_single">
                <el-radio-button value="A">A</el-radio-button>
                <el-radio-button value="B">B</el-radio-button>
                <el-radio-button value="C">C</el-radio-button>
                <el-radio-button value="D">D</el-radio-button>
              </el-radio-group>
              <div class="answer-hint">标注题干中正确选项对应的字母</div>
            </el-form-item>
          </div>

          <!-- 多选题 -->
          <div v-else-if="form.question_type === 'MULTIPLE_CHOICE'" class="answer-block">
            <el-form-item label="正确选项">
              <el-checkbox-group v-model="form.answer_multi">
                <el-checkbox-button value="A">A</el-checkbox-button>
                <el-checkbox-button value="B">B</el-checkbox-button>
                <el-checkbox-button value="C">C</el-checkbox-button>
                <el-checkbox-button value="D">D</el-checkbox-button>
              </el-checkbox-group>
              <div class="answer-hint">可选多个正确选项</div>
            </el-form-item>
          </div>

          <!-- 填空题 -->
          <div v-else-if="form.question_type === 'FILL_BLANK'" class="answer-block">
            <el-form-item label="标准答案">
              <div class="fill-blank-answers">
                <div v-for="(ans, idx) in form.answer_blanks" :key="idx" class="fill-blank-item">
                  <span class="fill-blank-label">第 {{ idx + 1 }} 空</span>
                  <el-input
                    v-model="form.answer_blanks[idx]"
                    placeholder="填入标准答案"
                    style="width:180px"
                    size="small"
                  />
                  <el-button
                    v-if="form.answer_blanks.length > 1"
                    text size="small" style="color:var(--red)"
                    @click="form.answer_blanks.splice(idx, 1)"
                  >删除</el-button>
                </div>
                <el-button size="small" @click="form.answer_blanks.push('')">+ 添加空</el-button>
              </div>
              <div class="answer-hint">多空题目请逐空填写标准答案</div>
            </el-form-item>
          </div>

          <!-- 判断题 -->
          <div v-else-if="form.question_type === 'TRUE_FALSE'" class="answer-block">
            <el-form-item label="正确答案">
              <el-radio-group v-model="form.answer_tf">
                <el-radio-button :value="true">✓ 正确（对）</el-radio-button>
                <el-radio-button :value="false">✗ 错误（错）</el-radio-button>
              </el-radio-group>
            </el-form-item>
          </div>

          <!-- 应用题 -->
          <div v-else-if="form.question_type === 'APPLICATION'" class="answer-block">
            <el-form-item label="最终结论">
              <el-input v-model="form.answer_final" placeholder="如：x=33，y=9800（人数33人，总价9800钱）" />
            </el-form-item>
            <el-form-item label="关键步骤">
              <div class="key-steps">
                <div v-for="(step, idx) in form.answer_steps" :key="idx" class="key-step-item">
                  <el-input
                    v-model="form.answer_steps[idx]"
                    :placeholder="`第 ${idx + 1} 个关键步骤`"
                    size="small"
                    style="flex:1"
                  >
                    <template #prefix>{{ idx + 1 }}.</template>
                  </el-input>
                  <el-button
                    v-if="form.answer_steps.length > 1"
                    text size="small" style="color:var(--red)"
                    @click="form.answer_steps.splice(idx, 1)"
                  >删除</el-button>
                </div>
                <el-button size="small" @click="form.answer_steps.push('')">+ 添加步骤</el-button>
              </div>
              <div class="answer-hint">列出解题的关键推导步骤，无需完整，突出思路节点即可</div>
            </el-form-item>
          </div>

          <!-- 参考解析 -->
          <div class="sub-section-title">参考解析</div>
          <div class="section-content">
            <el-form-item label="详细推导">
              <el-input v-model="form.solution" type="textarea" :rows="5" placeholder="完整解题推导过程，供 AI 辅导引导和 RAG 检索使用..." />
            </el-form-item>
          </div>

          <!-- 典型错误 -->
          <div class="sub-section-title">典型错误</div>
          <div class="section-content">
            <el-form-item label="典型错误">
              <el-input v-model="form.typical_error" placeholder="学生最常犯的错误..." />
            </el-form-item>
          </div>

          <!-- 五力权重 -->
          <div class="sub-section-title">
            五力训练权重
            <span class="weight-total" :class="weightTotal === 10 ? 'weight-total--ok' : 'weight-total--err'">
              合计: {{ weightTotal }} / 10
              <span v-if="weightTotal === 10"> ✓</span>
            </span>
          </div>
          <div class="section-content">
            <el-form-item label=" ">
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
              style="margin-bottom:10px"
            >
              <el-input
                v-model="form.five_power_thoughts[p as FivePower]"
                placeholder="该维度的训练切入点..."
                size="small"
              />
            </el-form-item>
          </div>

          <!-- 迁移方向 -->
          <div class="sub-section-title">迁移方向</div>
          <div class="section-content">
            <el-form-item label="迁移方向">
              <div class="tag-area">
                <el-tag
                  v-for="(d, i) in form.migration_directions" :key="i"
                  type="success" closable
                  :disable-transitions="false"
                  @close="form.migration_directions.splice(i, 1)"
                  style="margin-right:6px;margin-bottom:4px"
                >{{ d }}</el-tag>
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
              </div>
            </el-form-item>
          </div>

        </el-form>
      </div>

    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { questionApi, knowledgeTreeApi, type KnowledgeTreeNode } from '@/api/questions'
import type { QuestionType, FivePower, Difficulty } from '@/types'
import { FivePowerLabels } from '@/types'

const route  = useRoute()
const router = useRouter()

const loading = ref(false)
const saving  = ref(false)
const question = ref<any>(null)

const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 知识体系树 ────────────────────────────────────────────────
const rawTree = ref<KnowledgeTreeNode[]>([])

const subjectOptions = computed(() => rawTree.value.map(n => ({ id: n.id, name: n.name })))
const gradeOptions = computed(() => {
  if (!form.subject_id) return []
  return (rawTree.value.find(n => n.id === form.subject_id)?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})
const semesterOptions = computed(() => {
  if (!form.grade_id) return []
  const sub = rawTree.value.find(n => n.id === form.subject_id)
  return ((sub?.children ?? []).find(n => n.id === form.grade_id)?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})
const chapterOptions = computed(() => {
  if (!form.semester_id) return []
  const sub = rawTree.value.find(n => n.id === form.subject_id)
  const grade = (sub?.children ?? []).find(n => n.id === form.grade_id)
  return ((grade?.children ?? []).find(n => n.id === form.semester_id)?.children ?? []).map(n => ({ id: n.id, name: n.name }))
})

const aiKnowledgePoints = ref<{ id: number; name: string }[]>([])
const knowledgePointOptions = computed(() => {
  if (form.chapter_id) {
    const sub = rawTree.value.find(n => n.id === form.subject_id)
    const grade = (sub?.children ?? []).find(n => n.id === form.grade_id)
    const sem = (grade?.children ?? []).find(n => n.id === form.semester_id)
    const ch = (sem?.children ?? []).find(n => n.id === form.chapter_id)
    const kps = (ch?.children ?? []).map(n => ({ id: n.id, name: n.name }))
    if (kps.length > 0) return kps
  }
  return aiKnowledgePoints.value
})

function onSubjectChange()  { form.grade_id = null; form.semester_id = null; form.chapter_id = null; form.knowledge_point_ids = [] }
function onGradeChange()    { form.semester_id = null; form.chapter_id = null; form.knowledge_point_ids = [] }
function onSemesterChange() { form.chapter_id = null; form.knowledge_point_ids = [] }
function onChapterChange()  { form.knowledge_point_ids = [] }

// ── 表单 ─────────────────────────────────────────────────────
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

function onQuestionTypeChange() {
  form.answer_single = 'A'; form.answer_multi = []; form.answer_blanks = ['']
  form.answer_tf = true; form.answer_final = ''; form.answer_steps = ['']
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
    question.value = raw

    form.subject_id          = (raw as any).subject_id  ?? null
    form.grade_id            = (raw as any).grade_id    ?? null
    form.semester_id         = (raw as any).semester_id ?? null
    form.chapter_id          = (raw as any).chapter_id  ?? null
    form.knowledge_point_ids = [...((raw as any).knowledge_point_ids ?? [])].map(Number).filter(Boolean)
    aiKnowledgePoints.value  = ((raw as any).knowledge_points ?? []).map((kp: any) => ({ id: Number(kp.id), name: kp.name }))
    form.difficulty          = ((raw as any).difficulty ?? 'basic') as Difficulty
    form.solution            = (raw as any).solution      ?? ''
    form.typical_error       = (raw as any).common_error  ?? ''
    form.migration_directions = [...((raw as any).transfer_direction ?? [])]
    if ((raw as any).five_power_weights) Object.assign(form.five_power_weights, (raw as any).five_power_weights)
    if ((raw as any).power_solutions)    Object.assign(form.five_power_thoughts, (raw as any).power_solutions)
    deserializeAnswer((raw as any).answer)
  } finally { loading.value = false }
})

// ── 构建 payload ─────────────────────────────────────────────
function buildPayload() {
  return {
    stem:                form.solution !== undefined ? question.value?.stem : undefined,
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

// ── 保存（不改变状态）────────────────────────────────────────
async function handleSave() {
  if (!form.subject_id || !form.grade_id || !form.semester_id) {
    ElMessage.warning('请选择科目、年级和学期')
    return
  }
  saving.value = true
  try {
    await questionApi.updateFull(Number(route.params.id), {
      ...buildPayload(),
      stem: question.value?.stem,
    })
    ElMessage.success('保存成功')
    router.push('/questions')
  } finally { saving.value = false }
}

// ── 保存并启用 ────────────────────────────────────────────────
async function handleSaveAndActivate() {
  if (!form.subject_id || !form.grade_id || !form.semester_id) {
    ElMessage.warning('请选择科目、年级和学期')
    return
  }
  if (weightTotal.value !== 10) {
    ElMessage.warning('五力权重合计必须等于10分，请调整后再启用')
    return
  }
  saving.value = true
  try {
    await questionApi.updateFull(Number(route.params.id), {
      ...buildPayload(),
      stem: question.value?.stem,
    })
    await questionApi.activate(Number(route.params.id))
    ElMessage.success('保存成功，题目已启用')
    router.push('/questions')
  } finally { saving.value = false }
}
</script>

<style lang="scss" scoped>
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

.sub-section-title {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-2);
  padding: 12px 0 10px;
  display: flex;
  align-items: center;
  gap: 10px;

  [data-theme="dark"] & { color: #ffffff; }
}

.belongs-row {
  display: flex;
  gap: 16px;
  flex-wrap: nowrap;

  .el-form-item {
    flex: 1;
    margin-bottom: 16px;
  }
}

// 统一子模块内容背景容器
.section-content,
.answer-block {
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 16px 0 4px;
  margin-bottom: 12px;
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
  gap: 8px;
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
  align-items: center;
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

.power-weight-val {
  width: 70px !important;
  text-align: center;
}

.power-dot {
  width: 4px;
  height: 4px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

.thoughts-grid {
  // background/padding 由 .section-content 提供
}

.tag-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 6px;
  min-height: 32px;
}
</style>
