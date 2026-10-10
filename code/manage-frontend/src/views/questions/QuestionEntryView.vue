<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">训练题录入</h1>
        <p class="page-subtitle">录入题干后由大模型自动分析，审核后发布至训练池</p>
      </div>
      <div style="display:flex;gap:10px">
        <el-button @click="showImport = true">批量导入</el-button>
        <button class="btn-pink" @click="$router.push('/questions/create')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
          录入题干
        </button>
      </div>
    </div>

    <!-- ── 表格区 ── -->
    <div class="table-panel">

      <!-- 筛选栏 -->
      <div class="inner-toolbar">
        <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width:90px">
          <el-option v-for="(label, key) in DifficultyLabels" :key="key" :label="label" :value="key" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="搜索题干..." clearable @keyup.enter="handleSearch">
          <template #prefix>
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
            </svg>
          </template>
        </el-input>
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>

      <!-- 批量操作栏 -->
      <div v-if="selected.length > 0" class="batch-bar">
        <span class="batch-bar__info">已选 <b>{{ selected.length }}</b> 条</span>
        <el-button size="small" type="primary" :loading="batchAnalyzing" @click="handleBatchAnalyze">
          批量模型分析
        </el-button>
        <el-button size="small" type="danger" :loading="batchDeleting" @click="handleBatchDelete">
          批量删除
        </el-button>
        <el-button size="small" text @click="selected = []">取消选择</el-button>
      </div>

      <!-- 题目列表表格 -->
      <div class="surface" style="overflow:hidden">
        <el-table
          :data="questions"
          v-loading="loading"
          style="width:100%"
          @selection-change="(rows: Question[]) => selected = rows"
        >
          <el-table-column type="selection" width="46" />

          <el-table-column label="ID" width="90">
            <template #default="{ row }">
              <span class="id-chip">#{{ row.id }}</span>
            </template>
          </el-table-column>

          <el-table-column label="题干" min-width="300">
            <template #default="{ row }">
              <div class="stem-cell">
                <div class="stem-text">
                  {{ row.stem.substring(0, 60) }}{{ row.stem.length > 60 ? '…' : '' }}
                </div>
                <div class="stem-meta">
                  <span class="status-badge" :class="`status-badge--${row.status}`">
                    <span class="status-badge__dot" />
                    {{ QuestionStatusLabels[row.status as QuestionStatus] }}
                    <span v-if="row.status === 'pending_review' && row.analysis_round > 1" class="round-tag">第{{ row.analysis_round }}次</span>
                  </span>
                  <span v-if="row.status === 'analyzing'" class="analyzing-tip">
                    <span class="analyzing-spinner" />约 10~30 秒
                  </span>
                </div>
              </div>
            </template>
          </el-table-column>

          <!-- 难度 -->
          <el-table-column label="难度" width="80">
            <template #default="{ row }">
              <span v-if="row.difficulty" class="diff-badge" :class="`diff--${row.difficulty}`">
                {{ DifficultyLabels[row.difficulty as Difficulty] }}
              </span>
              <span v-else style="color:var(--text-3);font-size:12px">—</span>
            </template>
          </el-table-column>

          <!-- 创建时间 -->
          <el-table-column label="创建时间" width="140">
            <template #default="{ row }">
              <span style="font-size:12px;color:var(--text-3)">{{ formatDate(row.created_at) }}</span>
            </template>
          </el-table-column>

          <!-- 操作 -->
          <el-table-column label="操作" width="210" fixed="right">
            <template #default="{ row }">
              <template v-if="row.status === 'draft'">
                <el-button text size="small" style="color:var(--indigo)" @click="$router.push(`/questions/${row.id}/edit`)">编辑</el-button>
                <el-button text size="small" style="color:var(--green)" @click="handleAnalyze(row)">模型分析</el-button>
                <el-button text size="small" style="color:var(--red)" @click="handleDelete(row)">删除</el-button>
              </template>
              <template v-else-if="row.status === 'analyzing'">
                <span style="font-size:12px;color:var(--text-3)">分析中…</span>
              </template>
              <template v-else-if="row.status === 'pending_review'">
                <el-button text size="small" style="color:var(--indigo)" @click="$router.push(`/questions/${row.id}/review`)">审核结果</el-button>
                <el-button text size="small" style="color:var(--green);font-weight:600" :loading="publishingId === row.id" @click="handlePublish(row)">发布</el-button>
              </template>
            </template>
          </el-table-column>

        </el-table>

        <div class="paginator">
          <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ total }}</span> 条题目</span>
          <div style="display:flex;align-items:center;gap:6px">
            <el-button size="small" :disabled="page <= 1" @click="prevPage">上一页</el-button>
            <span style="font-size:13px;color:var(--text-3);padding:0 4px">{{ page }} / {{ totalPages }}</span>
            <el-button size="small" :disabled="page >= totalPages" @click="nextPage">下一页</el-button>
          </div>
        </div>
      </div>
    </div>

    <!-- ── 批量导入弹窗 ── -->
    <el-dialog v-model="showImport" title="批量导入题干" width="560px">
      <div class="import-hint">
        <p>每行一道题目的题干文本，导入后系统将<strong>自动触发大模型逐条分析</strong>，无需手动操作。</p>
        <p style="margin-top:8px">或上传 <code class="inline-code">.txt</code> / <code class="inline-code">.json</code> 格式文件（JSON 格式每条仅需包含 <code class="inline-code">stem</code> 字段）。</p>
      </div>
      <el-input v-model="batchStems" type="textarea" :rows="8" placeholder="每行粘贴一道题干..." style="margin-top:16px" />
      <el-upload drag accept=".txt,.json" :auto-upload="false" :on-change="handleFileChange" style="margin-top:12px">
        <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="var(--indigo)" stroke-width="1.5" style="margin-bottom:6px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M3 16.5v2.25A2.25 2.25 0 005.25 21h13.5A2.25 2.25 0 0021 18.75V16.5m-13.5-9L12 3m0 0l4.5 4.5M12 3v13.5"/>
        </svg>
        <div style="font-size:13.5px;color:var(--text-2)">拖拽文件至此处，或<em style="color:var(--indigo)">点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" :loading="importLoading" @click="handleImport">开始导入并分析</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, onUnmounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi } from '@/api'
import type { Question, QuestionStatus, Difficulty } from '@/types'
import { QuestionStatusLabels, DifficultyLabels } from '@/types'

const loading = ref(false)
const importLoading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const totalPages = ref(1)
const PAGE_SIZE = 20
const showImport = ref(false)
const batchStems = ref('')

// 批量操作
const selected = ref<Question[]>([])
const batchAnalyzing = ref(false)
const batchDeleting = ref(false)
const publishingId = ref<number | null>(null)

const filters = reactive<{ difficulty: Difficulty | ''; keyword: string }>({
  difficulty: '', keyword: '',
})

// ── 日期格式化 ───────────────────────────────────────────────
function formatDate(dt: string) {
  if (!dt) return '—'
  const d = new Date(dt)
  const p = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${p(d.getMonth()+1)}-${p(d.getDate())} ${p(d.getHours())}:${p(d.getMinutes())}`
}

// ── 数据加载 ─────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: PAGE_SIZE, order_by: 'created_at_desc' }
    if (filters.difficulty) params.difficulty = filters.difficulty
    if (filters.keyword)    params.keyword    = filters.keyword

    const res = await questionApi.getList(params)
    // 录入列表只展示未发布的三个状态，已发布/已停用题目归属训练题管理
    questions.value = res.list.filter((q: Question) => ['draft', 'analyzing', 'pending_review'].includes(q.status))
    total.value = res.total
    totalPages.value = res.total_pages ?? 1
    if (res.list.some((q: Question) => q.status === 'analyzing')) startPolling()
  } finally { loading.value = false }
}


function handleSearch() { page.value = 1; loadData() }
function resetFilters() {
  Object.assign(filters, { difficulty: '', keyword: '' })
  page.value = 1; loadData()
}
function prevPage() { if (page.value > 1) { page.value--; loadData() } }
function nextPage() { if (page.value < totalPages.value) { page.value++; loadData() } }

async function handleAnalyze(row: Question) {
  await ElMessageBox.confirm(
    `确认对题目 #${row.id} 触发大模型分析？分析约需 10~30 秒，完成后状态变为「待审核」。`,
    '触发模型分析',
    { confirmButtonText: '确认分析', cancelButtonText: '取消', type: 'info' }
  )
  await questionApi.analyze(row.id)
  ElMessage.success('分析任务已提交，请稍后刷新查看结果')
  loadData()
}

async function handlePublish(row: Question) {
  await ElMessageBox.confirm(
    `确认发布题目 #${row.id}？将直接使用大模型分析结果发布，发布后题目将参与训练推荐。`,
    '确认发布',
    { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'info' }
  )
  publishingId.value = row.id
  try {
    const detail = await questionApi.getOne(row.id)
    const ana = (detail as any).latest_analysis
    if (!ana?.ai_subject?.id) {
      ElMessage.warning('分析数据不完整，请进入「审核结果」页面手动补充后再发布')
      return
    }
    await questionApi.publish(row.id, {
      subject_id:          ana.ai_subject.id,
      grade_id:            ana.ai_grade.id,
      semester_id:         ana.ai_semester?.id,
      chapter_id:          ana.ai_chapter?.id,
      knowledge_point_ids: (ana.ai_knowledge_point_ids ?? []).map(Number),
      difficulty:          ana.ai_difficulty ?? 'basic',
      solution:            ana.ai_solution ?? '',
      common_error:        ana.ai_common_error,
      power_solutions:     ana.ai_power_solutions,
      five_power_weights:  ana.ai_five_power_weights ?? { INSIGHT: 2, CONSTRUCT: 5, DEDUCE: 2, ADAPT: 1, MIGRATE: 0 },
      transfer_directions: ana.ai_transfer_directions ?? [],
      question_type:       ana.ai_question_type,
      answer:              ana.ai_answer,
    })
    ElMessage.success('题目已发布，可在「训练题管理」中查看')
    loadData()
  } finally {
    publishingId.value = null
  }
}

async function handleDelete(row: Question) {
  await ElMessageBox.confirm(`确认删除草稿 #${row.id}？此操作不可恢复。`, '确认删除', { type: 'error' })
  await questionApi.delete(row.id)
  ElMessage.success('草稿已删除')
  loadData()
}

// ── 批量模型分析 ──────────────────────────────────────────────
async function handleBatchAnalyze() {
  const targets = selected.value.filter(q => q.status === 'draft')
  const skipped = selected.value.length - targets.length
  if (targets.length === 0) {
    ElMessage.warning('所选题目中无草稿状态题目，无法触发分析')
    return
  }
  const msg = skipped > 0
    ? `选中 ${selected.value.length} 条，其中 ${targets.length} 条草稿将触发分析，${skipped} 条因状态不符跳过。确认继续？`
    : `将对 ${targets.length} 条草稿题目串行触发模型分析，确认继续？`
  await ElMessageBox.confirm(msg, '批量模型分析', { confirmButtonText: '确认分析', cancelButtonText: '取消', type: 'info' })
  batchAnalyzing.value = true
  let successCount = 0
  try {
    for (const q of targets) {
      try { await questionApi.analyze(q.id); successCount++ } catch { /* 单条失败跳过 */ }
    }
    ElMessage.success(`已提交 ${successCount} 条分析任务，请稍后查看结果`)
    selected.value = []
    loadData()
  } finally { batchAnalyzing.value = false }
}

// ── 批量删除 ──────────────────────────────────────────────────
async function handleBatchDelete() {
  const targets = selected.value.filter(q => q.status === 'draft')
  const skipped = selected.value.length - targets.length
  if (targets.length === 0) {
    ElMessage.warning('所选题目中无草稿状态题目，无法删除')
    return
  }
  const msg = skipped > 0
    ? `选中 ${selected.value.length} 条，其中 ${targets.length} 条草稿将被删除，${skipped} 条因状态不符跳过。此操作不可恢复，确认继续？`
    : `将删除 ${targets.length} 条草稿题目，此操作不可恢复，确认继续？`
  await ElMessageBox.confirm(msg, '批量删除', { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error' })
  batchDeleting.value = true
  let successCount = 0
  try {
    for (const q of targets) {
      try { await questionApi.delete(q.id); successCount++ } catch { /* 单条失败跳过 */ }
    }
    ElMessage.success(`已删除 ${successCount} 条草稿题目`)
    selected.value = []
    loadData()
  } finally { batchDeleting.value = false }
}

function handleFileChange() { ElMessage.info('文件已选择') }
async function handleImport() {
  const stems = batchStems.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (stems.length === 0) { ElMessage.warning('请粘贴题干内容或上传文件'); return }
  importLoading.value = true
  try {
    await questionApi.batchImportStems(stems)
    ElMessage.success(`已导入 ${stems.length} 条题干，大模型分析任务已提交`)
    showImport.value = false; batchStems.value = ''
    loadData()
  } finally { importLoading.value = false }
}

// 轮询：有 analyzing 状态题目时每 5 秒刷新一次
let pollTimer: ReturnType<typeof setInterval> | null = null

function startPolling() {
  if (pollTimer) return
  pollTimer = setInterval(() => {
    const hasAnalyzing = questions.value.some(q => q.status === 'analyzing')
    if (hasAnalyzing) { loadData() }
    else { stopPolling() }
  }, 5000)
}

function stopPolling() {
  if (pollTimer) { clearInterval(pollTimer); pollTimer = null }
}

onMounted(() => { loadData() })
onUnmounted(() => stopPolling())
</script>

<style lang="scss" scoped>
// ── 批量操作栏 ────────────────────────────────────────────────
.batch-bar {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 8px 14px;
  background: var(--indigo-light);
  border: 1.5px solid var(--indigo-border);
  border-radius: var(--r-lg);
  margin-bottom: 10px;

  &__info {
    font-size: 13px;
    color: var(--indigo);
    font-weight: 500;
    flex-shrink: 0;
  }
}

// ── 表格区 ───────────────────────────────────────────────────
.table-panel {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

// ── 状态统计胶囊 ─────────────────────────────────────────────
.stat-pills {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}

.stat-pill {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: var(--r-pill);
  border: 1.5px solid var(--border-hover);
  background: var(--bg-surface);
  font-size: 13px;
  color: var(--text-2);
  cursor: pointer;
  transition: all 0.15s;
  user-select: none;

  &:hover { border-color: var(--indigo); color: var(--indigo); background: var(--indigo-light); }

  &--active {
    background: var(--indigo-light);
    border-color: var(--indigo);
    color: var(--indigo);
    font-weight: 600;
  }

  &__dot {
    width: 7px;
    height: 7px;
    border-radius: 50%;
  }

  &__count { font-weight: 700; color: var(--text-1); }
}

.status-dot {
  &--draft          { background: var(--amber); }
  &--analyzing      { background: var(--indigo); }
  &--pending_review { background: var(--purple); }
  &--published      { background: var(--green); }
  &--archived       { background: var(--text-3); }
}

// ── 题干列 ───────────────────────────────────────────────────
.stem-cell { display: flex; flex-direction: column; gap: 6px; padding: 3px 0; }
.stem-text { font-size: 13.5px; color: var(--text-1); line-height: 1.55; }
.stem-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &__dot { width: 6px; height: 6px; border-radius: 50%; }

  &--draft          { background: var(--amber-dim);   color: var(--amber);  border-color: var(--amber-border);  .status-badge__dot { background: var(--amber); } }
  &--analyzing      { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); .status-badge__dot { background: var(--indigo); } }
  &--pending_review { background: var(--purple-dim);  color: var(--purple); border-color: var(--purple-border); .status-badge__dot { background: var(--purple); } }
  &--published      { background: var(--green-dim);   color: var(--green);  border-color: var(--green-border);  .status-badge__dot { background: var(--green); } }
  &--archived       { background: var(--bg-muted);    color: var(--text-3); border-color: var(--border-hover);  .status-badge__dot { background: var(--text-3); } }
}

.round-tag {
  font-size: 10px;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(124, 58, 237, 0.15);
}

.analyzing-tip {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 12px;
  color: var(--text-3);
}

.analyzing-spinner {
  width: 10px;
  height: 10px;
  border: 1.5px solid var(--border-hover);
  border-top-color: var(--indigo);
  border-radius: 50%;
  animation: spin 0.8s linear infinite;
}

@keyframes spin { to { transform: rotate(360deg); } }

.diff-badge {
  font-size: 11.5px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &.diff--basic     { background: var(--teal-dim);  color: var(--teal);  border-color: var(--teal-border); }
  &.diff--advanced  { background: var(--amber-dim); color: var(--amber); border-color: var(--amber-border); }
  &.diff--challenge { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }
}

.import-hint {
  font-size: 13.5px;
  color: var(--text-2);
  line-height: 1.7;
  background: var(--indigo-light);
  border-radius: var(--r-lg);
  padding: 12px 16px;

  strong { color: var(--indigo); font-weight: 600; }
}

.inline-code {
  font-family: var(--font-mono);
  font-size: 12.5px;
  background: var(--bg-muted);
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--indigo);
}
</style>
