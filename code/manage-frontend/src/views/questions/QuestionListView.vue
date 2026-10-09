<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">训练题管理</h1>
        <p class="page-subtitle">管理已发布至训练池的题目，可停用或查看题目详情</p>
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
        <div v-for="subject in knowledgeTree" :key="subject.id">
          <!-- 科目 -->
          <div class="tree-node tree-node--l1" :class="{ active: treeFilter.subject === subject.name && !treeFilter.grade }">
            <span class="tree-toggle" @click="subject.open = !subject.open" :title="subject.open ? '折叠' : '展开'">
              {{ subject.open ? '▼' : '▶' }}
            </span>
            <span class="tree-node__label" @click="selectSubject(subject.name)">{{ subject.name }}</span>
            <span class="tree-node__count">{{ subject.published_count }}</span>
          </div>

          <!-- 年级 -->
          <template v-if="subject.open">
            <div v-for="grade in subject.children" :key="grade.id">
              <div class="tree-node tree-node--l2" :class="{ active: treeFilter.subject === subject.name && treeFilter.grade === grade.name && !treeFilter.semester }">
                <span class="tree-toggle" @click="grade.open = !grade.open" :title="grade.open ? '折叠' : '展开'">
                  {{ grade.open ? '▼' : '▶' }}
                </span>
                <span class="tree-node__label" @click="selectGrade(subject.name, grade.name)">{{ grade.name }}</span>
                <span class="tree-node__count">{{ grade.published_count }}</span>
              </div>

              <!-- 学期 -->
              <template v-if="grade.open">
                <div v-for="sem in grade.children" :key="sem.id">
                  <div class="tree-node tree-node--l3" :class="{ active: treeFilter.subject === subject.name && treeFilter.grade === grade.name && treeFilter.semester === sem.name && !treeFilter.chapter }">
                    <span class="tree-toggle" @click="sem.open = !sem.open" :title="sem.open ? '折叠' : '展开'">
                      {{ sem.open ? '▼' : '▶' }}
                    </span>
                    <span class="tree-node__label" @click="selectSemester(subject.name, grade.name, sem.name)">{{ sem.name }}</span>
                    <span class="tree-node__count">{{ sem.published_count }}</span>
                  </div>

                  <!-- 单元/章节 -->
                  <template v-if="sem.open">
                    <div v-for="ch in sem.children" :key="ch.id">
                      <div class="tree-node tree-node--l4" :class="{ active: treeFilter.chapter === ch.name && !treeFilter.knowledge_point }">
                        <span class="tree-toggle" @click="ch.open = !ch.open" :title="ch.open ? '折叠' : '展开'">
                          {{ ch.open ? '▼' : '▶' }}
                        </span>
                        <span class="tree-node__label" @click="selectChapter(subject.name, grade.name, sem.name, ch.name)">{{ ch.name }}</span>
                        <span class="tree-node__count">{{ ch.published_count }}</span>
                      </div>

                      <!-- 知识点（叶子节点，无展开图标） -->
                      <template v-if="ch.open">
                        <div
                          v-for="kp in ch.children" :key="kp.id"
                          class="tree-node tree-node--l5"
                          :class="{ active: treeFilter.knowledge_point === kp.name }"
                          @click="selectKnowledgePoint(subject.name, grade.name, sem.name, ch.name, kp.name)"
                        >
                          <span class="tree-leaf-dot">●</span>
                          <span class="tree-node__label">{{ kp.name }}</span>
                          <span class="tree-node__count">{{ kp.published_count }}</span>
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
            :class="{ 'stat-pill--active': filters.status === 'published' }"
            @click="selectStatus('published')"
          >
            <span class="stat-pill__dot status-dot--published" />
            已发布
            <span class="stat-pill__count num">{{ statusCounts.published }}</span>
          </span>
          <span
            class="stat-pill"
            :class="{ 'stat-pill--active': filters.status === 'archived' }"
            @click="selectStatus('archived')"
          >
            <span class="stat-pill__dot status-dot--archived" />
            已停用
            <span class="stat-pill__count num">{{ statusCounts.archived }}</span>
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
          <el-table
            :data="questions"
            v-loading="loading"
            style="width:100%"
          >
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
                      {{ row.status === 'archived' ? '已停用' : QuestionStatusLabels[row.status as QuestionStatus] }}
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
                <span v-if="row.subject_id" style="font-size:12.5px;color:var(--text-2);line-height:1.6">
                  {{ subjectName(row.subject_id) }} · {{ gradeName(row.grade_id) }}<br>
                  <span style="color:var(--text-3);font-size:11.5px">{{ semesterName(row.semester_id) }}</span>
                </span>
                <span v-else style="font-size:12px;color:var(--text-3)">—</span>
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

            <!-- 创建时间 -->
            <el-table-column label="创建时间" width="140">
              <template #default="{ row }">
                <span style="font-size:12px;color:var(--text-3)">{{ formatDate(row.created_at) }}</span>
              </template>
            </el-table-column>

            <!-- 操作 -->
            <el-table-column label="操作" width="130" fixed="right">
              <template #default="{ row }">
                <template v-if="row.status === 'published'">
                  <el-button text size="small" style="color:var(--text-2)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
                  <el-button text size="small" style="color:var(--amber)" @click="handleArchive(row)">停用</el-button>
                </template>
                <template v-else>
                  <el-button text size="small" style="color:var(--text-3)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
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
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi, knowledgeTreeApi } from '@/api'
import type { KnowledgeTreeNode } from '@/api/questions'
import type { Question, QuestionStatus, Difficulty, FivePower } from '@/types'
import { QuestionStatusLabels, DifficultyLabels, FivePowerLabels } from '@/types'

const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const totalPages = ref(1)
const PAGE_SIZE = 20

// 状态统计（来自后端）
const statusCounts = ref<Record<string, number>>({
  draft: 0, analyzing: 0, pending_review: 0, published: 0, archived: 0,
})

const filters = reactive<{ status: QuestionStatus | ''; difficulty: Difficulty | ''; keyword: string }>({
  status: 'published', difficulty: '', keyword: '',
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

// ── 左树数据（来自后端知识体系树接口）── ─────────────────────
const knowledgeTree = ref<KnowledgeTreeNode[]>([])

async function loadKnowledgeTree() {
  try {
    const res = await knowledgeTreeApi.getTree()
    knowledgeTree.value = res.tree
  } catch { /* ignore */ }
}

const allCount = computed(() => total.value)

// ── 知识体系 ID → 名称映射 ────────────────────────────────────
const nodeNameByTypeId = computed<Record<string, string>>(() => {
  const map: Record<string, string> = {}
  function walk(nodes: KnowledgeTreeNode[]) {
    for (const n of nodes) {
      map[`${n.type}_${n.id}`] = n.name
      if (n.children?.length) walk(n.children)
    }
  }
  walk(knowledgeTree.value)
  return map
})
function subjectName(id: number | null | undefined) { return id ? (nodeNameByTypeId.value[`subject_${id}`] ?? '') : '' }
function gradeName(id: number | null | undefined)   { return id ? (nodeNameByTypeId.value[`grade_${id}`]   ?? '') : '' }
function semesterName(id: number | null | undefined){ return id ? (nodeNameByTypeId.value[`semester_${id}`]?? '') : '' }

// ── 树选择操作 ───────────────────────────────────────────────
function clearTreeFilter() {
  Object.assign(treeFilter, { subject: '', grade: '', semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectSubject(s: string) {
  Object.assign(treeFilter, { subject: s, grade: '', semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectGrade(s: string, g: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectSemester(s: string, g: string, sem: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectChapter(s: string, g: string, sem: string, ch: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: ch, knowledge_point: '' })
  page.value = 1; loadData()
}

function selectKnowledgePoint(s: string, g: string, sem: string, ch: string, kp: string) {
  Object.assign(treeFilter, { subject: s, grade: g, semester: sem, chapter: ch, knowledge_point: kp })
  page.value = 1; loadData()
}

// ── 工具函数 ─────────────────────────────────────────────────
function topPower(weights: Record<string, number>): string {
  return Object.entries(weights).sort((a, b) => b[1] - a[1])[0]?.[0] || 'CONSTRUCT'
}

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
    if (filters.status)             params.status     = filters.status
    if (filters.difficulty)         params.difficulty  = filters.difficulty
    if (filters.keyword)            params.keyword     = filters.keyword
    if (treeFilter.subject)         params.subject     = treeFilter.subject
    if (treeFilter.grade)           params.grade       = treeFilter.grade
    if (treeFilter.semester)        params.semester    = treeFilter.semester
    if (treeFilter.chapter)         params.chapter     = treeFilter.chapter
    if (treeFilter.knowledge_point) params.knowledge_point = treeFilter.knowledge_point

    const res = await questionApi.getList(params)
    questions.value = res.list
    total.value = res.total
    totalPages.value = res.total_pages ?? 1
  } finally { loading.value = false }
}

async function loadStats() {
  try {
    const res = await questionApi.getStats()
    Object.assign(statusCounts.value, res)
  } catch { /* ignore */ }
}

function selectStatus(s: QuestionStatus) {
  filters.status = s; page.value = 1; loadData()
}

function handleSearch() { page.value = 1; loadData() }
function resetFilters() {
  Object.assign(filters, { status: 'published', difficulty: '', keyword: '' })
  page.value = 1; loadData()
}
function prevPage() { if (page.value > 1) { page.value--; loadData() } }
function nextPage() { if (page.value < totalPages.value) { page.value++; loadData() } }

async function handleArchive(row: Question) {
  await ElMessageBox.confirm(`确认停用题目 #${row.id}？停用后不再参与训练推荐。`, '确认停用', { type: 'warning' })
  await questionApi.archive(row.id)
  ElMessage.success('题目已停用')
  loadData(); loadStats()
}

onMounted(() => { loadData(); loadStats(); loadKnowledgeTree() })
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
  cursor: default;
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
  &--published { background: var(--green); }
  &--archived  { background: var(--text-3); }
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

  &--published { background: var(--green-dim);  color: var(--green);  border-color: var(--green-border);  .status-badge__dot { background: var(--green); } }
  &--archived  { background: var(--bg-muted);   color: var(--text-3); border-color: var(--border-hover);  .status-badge__dot { background: var(--text-3); } }
}

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
</style>
