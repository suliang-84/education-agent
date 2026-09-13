<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">题库管理</h1>
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

    <!-- ── 主体：左树右表 ── -->
    <div class="main-layout">

      <!-- ── 左侧：五级知识体系树 ── -->
      <div class="tree-panel surface">
        <div class="tree-panel__title">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 9.776c.112-.017.227-.026.344-.026h15.812c.117 0 .232.009.344.026m-16.5 0a2.25 2.25 0 00-1.883 2.542l.857 6a2.25 2.25 0 002.227 1.932H19.05a2.25 2.25 0 002.227-1.932l.857-6a2.25 2.25 0 00-1.883-2.542m-16.5 0V6A2.25 2.25 0 016 3.75h3.879a1.5 1.5 0 011.06.44l2.122 2.12a1.5 1.5 0 001.06.44H18A2.25 2.25 0 0120.25 9v.776"/>
          </svg>
          知识体系
        </div>

        <!-- 全部节点 -->
        <div
          class="tree-node tree-node--all"
          :class="{ active: !treeFilter.subject }"
          @click="clearTreeFilter"
        >
          全部题目
          <span class="tree-node__count">{{ allCount }}</span>
        </div>

        <!-- 科目树 -->
        <div v-for="subject in knowledgeTree" :key="subject.name">
          <!-- 科目 -->
          <div class="tree-node tree-node--l1" :class="{ active: treeFilter.subject === subject.name && !treeFilter.grade }">
            <span class="tree-toggle" @click="subject.open = !subject.open" :title="subject.open ? '折叠' : '展开'">
              {{ subject.open ? '▼' : '▶' }}
            </span>
            <span class="tree-node__label" @click="selectSubject(subject.name)">{{ subject.name }}</span>
            <span class="tree-node__count">{{ subject.count }}</span>
          </div>

          <!-- 年级 -->
          <template v-if="subject.open">
            <div v-for="grade in subject.grades" :key="grade.name">
              <div class="tree-node tree-node--l2" :class="{ active: treeFilter.subject === subject.name && treeFilter.grade === grade.name && !treeFilter.semester }">
                <span class="tree-toggle" @click="grade.open = !grade.open" :title="grade.open ? '折叠' : '展开'">
                  {{ grade.open ? '▼' : '▶' }}
                </span>
                <span class="tree-node__label" @click="selectGrade(subject.name, grade.name)">{{ grade.name }}</span>
                <span class="tree-node__count">{{ grade.count }}</span>
              </div>

              <!-- 学期 -->
              <template v-if="grade.open">
                <div v-for="sem in grade.semesters" :key="sem.name">
                  <div class="tree-node tree-node--l3" :class="{ active: treeFilter.subject === subject.name && treeFilter.grade === grade.name && treeFilter.semester === sem.name && !treeFilter.chapter }">
                    <span class="tree-toggle" @click="sem.open = !sem.open" :title="sem.open ? '折叠' : '展开'">
                      {{ sem.open ? '▼' : '▶' }}
                    </span>
                    <span class="tree-node__label" @click="selectSemester(subject.name, grade.name, sem.name)">{{ sem.name }}</span>
                    <span class="tree-node__count">{{ sem.count }}</span>
                  </div>

                  <!-- 单元/章节 -->
                  <template v-if="sem.open">
                    <div v-for="ch in sem.chapters" :key="ch.name">
                      <div class="tree-node tree-node--l4" :class="{ active: treeFilter.chapter === ch.name && !treeFilter.knowledge_point }">
                        <span class="tree-toggle" @click="ch.open = !ch.open" :title="ch.open ? '折叠' : '展开'">
                          {{ ch.open ? '▼' : '▶' }}
                        </span>
                        <span class="tree-node__label" @click="selectChapter(subject.name, grade.name, sem.name, ch.name)">{{ ch.name }}</span>
                        <span class="tree-node__count">{{ ch.count }}</span>
                      </div>

                      <!-- 知识点（叶子节点，无展开图标） -->
                      <template v-if="ch.open">
                        <div
                          v-for="kp in ch.knowledge_points" :key="kp.name"
                          class="tree-node tree-node--l5"
                          :class="{ active: treeFilter.knowledge_point === kp.name }"
                          @click="selectKnowledgePoint(subject.name, grade.name, sem.name, ch.name, kp.name)"
                        >
                          <span class="tree-leaf-dot">●</span>
                          <span class="tree-node__label">{{ kp.name }}</span>
                          <span class="tree-node__count">{{ kp.count }}</span>
                        </div>
                      </template>
                    </div>
                  </template>
                </div>
              </template>
            </div>
          </template>
        </div>
      </div>

      <!-- ── 右侧：筛选 + 表格 ── -->
      <div class="table-panel">

        <!-- 状态统计胶囊 -->
        <div class="stat-pills">
          <span
            class="stat-pill"
            :class="{ 'stat-pill--active': filters.status === '' }"
            @click="selectStatus('')"
          >
            全部 <span class="stat-pill__count num">{{ totalCount }}</span>
          </span>
          <span
            v-for="(label, key) in QuestionStatusLabels" :key="key"
            class="stat-pill"
            :class="{ 'stat-pill--active': filters.status === key }"
            @click="selectStatus(key as QuestionStatus)"
          >
            <span class="stat-pill__dot" :class="`status-dot--${key}`" />
            {{ label }}
            <span class="stat-pill__count num">{{ statusCounts[key as QuestionStatus] }}</span>
          </span>
        </div>

        <!-- 筛选栏 -->
        <div class="filter-bar" style="margin-bottom:0;border-radius:0;background:transparent;box-shadow:none;padding:10px 0">
          <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width:100px">
            <el-option v-for="(label, key) in DifficultyLabels" :key="key" :label="label" :value="key" />
          </el-select>
          <el-input v-model="filters.keyword" placeholder="搜索题干..." clearable style="width:200px" @keyup.enter="handleSearch">
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="resetFilters">重置</el-button>
          <span v-if="treeFilter.subject" class="tree-breadcrumb">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"/>
            </svg>
            {{ treeBreadcrumb }}
            <el-button text size="small" @click="clearTreeFilter" style="padding:0 4px;font-size:11px;color:var(--text-3)">✕</el-button>
          </span>
        </div>

        <!-- 题目列表表格 -->
        <div class="surface" style="overflow:hidden">
          <el-table :data="questions" v-loading="loading" style="width:100%">

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
                    <span v-if="row.embedding_status === 'completed'" class="embed-badge embed--ok">向量化 ✓</span>
                    <span v-if="row.embedding_status === 'failed'" class="embed-badge embed--fail">向量化 ✗</span>
                  </div>
                </div>
              </template>
            </el-table-column>

            <!-- 归属：五级体系（科目·年级·学期） -->
            <el-table-column label="归属" width="150">
              <template #default="{ row }">
                <span v-if="row.subject" style="font-size:12.5px;color:var(--text-2);line-height:1.6">
                  {{ row.subject }} · {{ row.grade }}<br>
                  <span style="color:var(--text-3);font-size:11.5px">{{ row.semester }} · {{ row.chapter }}</span>
                </span>
                <span v-else style="font-size:12px;color:var(--text-3)">待分析</span>
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

            <!-- 主五力 -->
            <el-table-column label="主五力" width="90">
              <template #default="{ row }">
                <template v-if="row.five_power_weights">
                  <span class="power-badge" :class="`power-badge--${topPower(row.five_power_weights)}`">
                    {{ FivePowerLabels[topPower(row.five_power_weights) as FivePower] }}
                  </span>
                </template>
                <span v-else style="color:var(--text-3);font-size:12px">—</span>
              </template>
            </el-table-column>

            <!-- 操作 -->
            <el-table-column label="操作" width="175" fixed="right">
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
                  <el-button text size="small" style="color:var(--indigo);font-weight:600" @click="$router.push(`/questions/${row.id}/review`)">审核结果</el-button>
                </template>
                <template v-else-if="row.status === 'published'">
                  <el-button text size="small" style="color:var(--text-2)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
                  <el-button text size="small" style="color:var(--amber)" @click="handleArchive(row)">下架</el-button>
                </template>
                <template v-else>
                  <el-button text size="small" style="color:var(--text-3)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
                </template>
              </template>
            </el-table-column>

          </el-table>

          <div class="paginator">
            <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ total }}</span> 条题目</span>
            <div style="display:flex;gap:6px">
              <el-button size="small" :disabled="cursor === 0" @click="prevPage">上一页</el-button>
              <el-button size="small" :disabled="!hasMore" @click="nextPage">下一页</el-button>
            </div>
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
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi } from '@/api'
import type { Question, QuestionStatus, Difficulty, FivePower } from '@/types'
import { QuestionStatusLabels, DifficultyLabels, FivePowerLabels } from '@/types'

const loading = ref(false)
const importLoading = ref(false)
const questions = ref<Question[]>([])
const allQuestions = ref<Question[]>([])   // 缓存全量，用于树统计
const total = ref(0)
const hasMore = ref(false)
const cursor = ref(0)
const showImport = ref(false)
const batchStems = ref('')

const filters = reactive<{ status: QuestionStatus | ''; difficulty: Difficulty | ''; keyword: string }>({
  status: '', difficulty: '', keyword: '',
})

// ── 左树筛选状态 ─────────────────────────────────────────────
const treeFilter = reactive({
  subject: '',
  grade: '',
  semester: '',
  chapter: '',
  knowledge_point: '',
})

const treeBreadcrumb = computed(() => {
  const parts = [treeFilter.subject, treeFilter.grade, treeFilter.semester, treeFilter.chapter, treeFilter.knowledge_point].filter(Boolean)
  return parts.join(' › ')
})

// ── 左树数据（根据 allQuestions 动态构建）── ─────────────────
const knowledgeTree = computed(() => {
  const subjectMap = new Map<string, { count: number; open: boolean; grades: Map<string, { count: number; open: boolean; semesters: Map<string, { count: number; open: boolean; chapters: Map<string, { count: number; open: boolean; knowledge_points: Map<string, { count: number }> }> }> }> }>()

  for (const q of allQuestions.value) {
    if (!q.subject) continue
    const sub = q.subject, grd = q.grade || '未知年级', sem = q.semester || '未分学期', ch = q.chapter || '未分单元'

    if (!subjectMap.has(sub)) subjectMap.set(sub, { count: 0, open: true, grades: new Map() })
    const subNode = subjectMap.get(sub)!
    subNode.count++

    if (!subNode.grades.has(grd)) subNode.grades.set(grd, { count: 0, open: true, semesters: new Map() })
    const grdNode = subNode.grades.get(grd)!
    grdNode.count++

    if (!grdNode.semesters.has(sem)) grdNode.semesters.set(sem, { count: 0, open: false, chapters: new Map() })
    const semNode = grdNode.semesters.get(sem)!
    semNode.count++

    if (!semNode.chapters.has(ch)) semNode.chapters.set(ch, { count: 0, open: false, knowledge_points: new Map() })
    const chNode = semNode.chapters.get(ch)!
    chNode.count++

    for (const kp of (q.knowledge_points || [])) {
      chNode.knowledge_points.set(kp, { count: (chNode.knowledge_points.get(kp)?.count || 0) + 1 })
    }
  }

  return [...subjectMap.entries()].map(([name, s]) => ({
    name, count: s.count, open: s.open,
    grades: [...s.grades.entries()].map(([gname, g]) => ({
      name: gname, count: g.count, open: g.open,
      semesters: [...g.semesters.entries()].map(([sname, sem]) => ({
        name: sname, count: sem.count, open: sem.open,
        chapters: [...sem.chapters.entries()].map(([cname, ch]) => ({
          name: cname, count: ch.count, open: ch.open,
          knowledge_points: [...ch.knowledge_points.entries()].map(([kname, kp]) => ({ name: kname, count: kp.count })),
        })),
      })),
    })),
  }))
})

// 状态计数（实时统计 allQuestions）
const statusCounts = computed<Record<QuestionStatus, number>>(() => ({
  draft:          allQuestions.value.filter(q => q.status === 'draft').length,
  analyzing:      allQuestions.value.filter(q => q.status === 'analyzing').length,
  pending_review: allQuestions.value.filter(q => q.status === 'pending_review').length,
  published:      allQuestions.value.filter(q => q.status === 'published').length,
  archived:       allQuestions.value.filter(q => q.status === 'archived').length,
}))

const totalCount = computed(() => allQuestions.value.length)
const allCount   = computed(() => totalCount.value)

// ── 树选择操作 ───────────────────────────────────────────────
function clearTreeFilter() {
  Object.assign(treeFilter, { subject: '', grade: '', semester: '', chapter: '', knowledge_point: '' })
  cursor.value = 0; loadData()
}

function selectSubject(s: string) {
  Object.assign(treeFilter, { subject: s, grade: '', semester: '', chapter: '', knowledge_point: '' })
  cursor.value = 0; loadData()
}

function selectGrade(s: string, g: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: '', chapter: '', knowledge_point: '' })
  cursor.value = 0; loadData()
}

function selectSemester(s: string, g: string, sem: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: '', knowledge_point: '' })
  cursor.value = 0; loadData()
}

function selectChapter(s: string, g: string, sem: string, ch: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: ch, knowledge_point: '' })
  cursor.value = 0; loadData()
}

function selectKnowledgePoint(s: string, g: string, sem: string, ch: string, kp: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: ch, knowledge_point: kp })
  cursor.value = 0; loadData()
}

// ── 工具函数 ─────────────────────────────────────────────────
function topPower(weights: Record<string, number>): string {
  return Object.entries(weights).sort((a, b) => b[1] - a[1])[0]?.[0] || 'CONSTRUCT'
}

// ── 数据加载 ─────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { cursor: cursor.value, limit: 20 }
    if (filters.status)              params.status             = filters.status
    if (filters.difficulty)          params.difficulty          = filters.difficulty
    if (filters.keyword)             params.keyword             = filters.keyword
    if (treeFilter.subject)          params.subject             = treeFilter.subject
    if (treeFilter.grade)            params.grade               = treeFilter.grade
    if (treeFilter.semester)         params.semester            = treeFilter.semester
    if (treeFilter.chapter)          params.chapter             = treeFilter.chapter
    if (treeFilter.knowledge_point)  params.knowledge_point     = treeFilter.knowledge_point

    const res = await questionApi.getList(params)
    questions.value = res.list
    total.value = res.total
    hasMore.value = res.has_more
  } finally { loading.value = false }
}

// 初次加载时同时拉全量数据用于树统计
async function loadAll() {
  const res = await questionApi.getList({ limit: 200 })
  allQuestions.value = res.list
}

function selectStatus(s: QuestionStatus | '') {
  filters.status = s; cursor.value = 0; loadData()
}

function handleSearch() { cursor.value = 0; loadData() }
function resetFilters() {
  Object.assign(filters, { status: '', difficulty: '', keyword: '' })
  cursor.value = 0; loadData()
}
function prevPage() { cursor.value = Math.max(0, cursor.value - 20); loadData() }
function nextPage() { cursor.value += 20; loadData() }

async function handleAnalyze(row: Question) {
  await ElMessageBox.confirm(
    `确认对题目 #${row.id} 触发大模型分析？分析约需 10~30 秒，完成后状态变为「待审核」。`,
    '触发模型分析',
    { confirmButtonText: '确认分析', cancelButtonText: '取消', type: 'info' }
  )
  await questionApi.analyze(row.id)
  ElMessage.success('分析任务已提交，请稍后刷新查看结果')
  loadData(); loadAll()
}

async function handleArchive(row: Question) {
  await ElMessageBox.confirm(`确认下架题目 #${row.id}？下架后不再参与训练推荐。`, '确认下架', { type: 'warning' })
  await questionApi.archive(row.id)
  ElMessage.success('题目已下架')
  loadData(); loadAll()
}

async function handleDelete(row: Question) {
  await ElMessageBox.confirm(`确认删除草稿 #${row.id}？此操作不可恢复。`, '确认删除', { type: 'error' })
  await questionApi.delete(row.id)
  ElMessage.success('草稿已删除')
  loadData(); loadAll()
}

function handleFileChange() { ElMessage.info('文件已选择') }
async function handleImport() {
  const stems = batchStems.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (stems.length === 0) { ElMessage.warning('请粘贴题干内容或上传文件'); return }
  importLoading.value = true
  try {
    await questionApi.batchImport(stems)
    ElMessage.success(`已导入 ${stems.length} 条题干，大模型分析任务已提交`)
    showImport.value = false; batchStems.value = ''
    loadData(); loadAll()
  } finally { importLoading.value = false }
}

onMounted(() => { loadData(); loadAll() })
</script>

<style lang="scss" scoped>
// ── 主体布局：左树右表 ───────────────────────────────────────
.main-layout {
  display: flex;
  gap: 16px;
  align-items: flex-start;
}

// ── 左树面板 ─────────────────────────────────────────────────
.tree-panel {
  width: 220px;
  flex-shrink: 0;
  padding: 12px 0;
  overflow: hidden;

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 0 14px 10px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 6px;
  }
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 14px;
  font-size: 13px;
  color: var(--text-2);
  cursor: default;          // 容器不设 pointer，由子元素控制
  border-radius: 0;
  transition: background 0.12s, color 0.12s;
  white-space: nowrap;
  overflow: hidden;

  &:hover { background: var(--bg-muted); }

  &.active {
    background: var(--indigo-light);
    color: var(--indigo);
    font-weight: 600;
  }

  &--all { font-weight: 600; color: var(--text-1); cursor: pointer; }
  &--l1  { padding-left: 14px; font-weight: 600; color: var(--text-1); }
  &--l2  { padding-left: 24px; }
  &--l3  { padding-left: 34px; font-size: 12.5px; color: var(--text-3); }
  &--l4  { padding-left: 44px; font-size: 12px; color: var(--text-3); }
  &--l5  { padding-left: 54px; font-size: 11.5px; color: var(--text-3); cursor: pointer;
            &:hover { color: var(--indigo); } }

  &__label {
    flex: 1;
    overflow: hidden;
    text-overflow: ellipsis;
    cursor: pointer;
    border-radius: 3px;
    padding: 1px 4px;
    margin: 0 -4px;
    transition: color 0.12s, background 0.12s;

    &:hover {
      color: var(--indigo);
      background: rgba(79, 70, 229, 0.06);
    }
  }

  &__count {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    color: var(--text-3);
    background: var(--bg-muted);
    border-radius: 10px;
    padding: 0 6px;
    flex-shrink: 0;
  }
}

.tree-toggle {
  font-size: 8px;
  color: var(--text-3);
  width: 18px;
  height: 18px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 4px;
  flex-shrink: 0;
  cursor: pointer;
  transition: background 0.12s, color 0.12s;

  &:hover {
    background: rgba(79, 70, 229, 0.10);
    color: var(--indigo);
  }
}

.tree-leaf-dot {
  font-size: 8px;
  color: var(--text-3);
  width: 18px;
  text-align: center;
  flex-shrink: 0;
}

// ── 右侧表格区 ───────────────────────────────────────────────
.table-panel {
  flex: 1;
  min-width: 0;
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

.tree-breadcrumb {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12px;
  color: var(--indigo);
  background: var(--indigo-light);
  padding: 4px 10px;
  border-radius: var(--r-pill);
  border: 1px solid var(--indigo-border);
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

.embed-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: var(--r-pill);
  border: 1px solid;

  &.embed--ok   { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &.embed--fail { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }
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
