<template>
  <div class="page-root">

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
          :class="{ active: !treeFilter.subject_id }"
          @click="clearTreeFilter"
        >
          全部题目
          <span class="tree-node__count">{{ allCount }}</span>
        </div>

        <!-- 科目树 -->
        <div v-for="subject in knowledgeTree" :key="subject.id">
          <!-- 科目 -->
          <div class="tree-node tree-node--l1" :class="{ active: treeFilter.subject_id === subject.id && !treeFilter.grade_id }">
            <span class="tree-toggle" @click="subject.open = !subject.open" :title="subject.open ? '折叠' : '展开'">
              {{ subject.open ? '▼' : '▶' }}
            </span>
            <span class="tree-node__label" @click="selectSubject(subject)">{{ subject.name }}</span>
            <span class="tree-node__count">{{ subject.published_count }}</span>
          </div>

          <!-- 年级 -->
          <template v-if="subject.open">
            <div v-for="grade in subject.children" :key="grade.id">
              <div class="tree-node tree-node--l2" :class="{ active: treeFilter.grade_id === grade.id && !treeFilter.semester_id }">
                <span class="tree-toggle" @click="grade.open = !grade.open" :title="grade.open ? '折叠' : '展开'">
                  {{ grade.open ? '▼' : '▶' }}
                </span>
                <span class="tree-node__label" @click="selectGrade(subject, grade)">{{ grade.name }}</span>
                <span class="tree-node__count">{{ grade.published_count }}</span>
              </div>

              <!-- 学期 -->
              <template v-if="grade.open">
                <div v-for="sem in grade.children" :key="sem.id">
                  <div class="tree-node tree-node--l3" :class="{ active: treeFilter.semester_id === sem.id && !treeFilter.chapter_id }">
                    <span class="tree-toggle" @click="sem.open = !sem.open" :title="sem.open ? '折叠' : '展开'">
                      {{ sem.open ? '▼' : '▶' }}
                    </span>
                    <span class="tree-node__label" @click="selectSemester(subject, grade, sem)">{{ sem.name }}</span>
                    <span class="tree-node__count">{{ sem.published_count }}</span>
                  </div>

                  <!-- 单元/章节 -->
                  <template v-if="sem.open">
                    <div v-for="ch in sem.children" :key="ch.id">
                      <div class="tree-node tree-node--l4" :class="{ active: treeFilter.chapter_id === ch.id && !treeFilter.knowledge_point_id }">
                        <span class="tree-toggle" @click="ch.open = !ch.open" :title="ch.open ? '折叠' : '展开'">
                          {{ ch.open ? '▼' : '▶' }}
                        </span>
                        <span class="tree-node__label" @click="selectChapter(subject, grade, sem, ch)">{{ ch.name }}</span>
                        <span class="tree-node__count">{{ ch.published_count }}</span>
                      </div>

                      <!-- 知识点（叶子节点，无展开图标） -->
                      <template v-if="ch.open">
                        <div
                          v-for="kp in ch.children" :key="kp.id"
                          class="tree-node tree-node--l5"
                          :class="{ active: treeFilter.knowledge_point_id === kp.id }"
                          @click="selectKnowledgePoint(subject, grade, sem, ch, kp)"
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

        <!-- 筛选栏 -->
        <div class="inner-toolbar">
          <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width:90px" @change="handleSearch">
            <el-option v-for="(label, key) in DifficultyLabels" :key="key" :label="label" :value="key" />
          </el-select>
          <el-input v-model="filters.keyword" placeholder="搜索题干..." clearable>
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
          <span v-if="treeFilter.subject_id" class="tree-breadcrumb">
            <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9 6.75V15m6-6v8.25m.503 3.498l4.875-2.437c.381-.19.622-.58.622-1.006V4.82c0-.836-.88-1.38-1.628-1.006l-3.869 1.934c-.317.159-.69.159-1.006 0L9.503 3.252a1.125 1.125 0 00-1.006 0L3.622 5.689C3.24 5.88 3 6.27 3 6.695V19.18c0 .836.88 1.38 1.628 1.006l3.869-1.934c.317-.159.69-.159 1.006 0l4.994 2.497c.317.158.69.158 1.006 0z"/>
            </svg>
            {{ treeBreadcrumb }}
            <el-button text size="small" @click="clearTreeFilter" style="padding:0 4px;font-size:11px;color:var(--text-3)">✕</el-button>
          </span>
        </div>

        <!-- 题目列表表格 -->
        <div class="surface surface--table">
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
                <el-tooltip :content="row.stem" placement="top-start" :show-after="300" effect="light">
                  <span class="stem-text">{{ row.stem }}</span>
                </el-tooltip>
              </template>
            </el-table-column>

            <!-- 归属：五级体系（科目·年级·学期） -->
            <el-table-column label="归属" width="180">
              <template #default="{ row }">
                <span v-if="row.subject_id" style="font-size:12.5px;color:var(--text-2)">
                  {{ subjectName(row.subject_id) }} · {{ gradeName(row.grade_id) }} · {{ semesterName(row.semester_id) }}
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
            <el-table-column label="操作" width="150" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" style="color:var(--text-2)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
                <el-button
                  v-if="row.is_active !== false"
                  text size="small" style="color:var(--amber)"
                  @click="handleDeactivate(row)"
                >停用</el-button>
                <el-button
                  v-else
                  text size="small" style="color:var(--green)"
                  @click="handleActivate(row)"
                >启用</el-button>
              </template>
            </el-table-column>

          </el-table>

          <div class="paginator">
            <el-pagination
              v-model:current-page="page"
              v-model:page-size="pageSize"
              :page-sizes="[10, 20, 50, 100, 200]"
              :total="total"
              background
              size="small"
              layout="total, ->, prev, pager, next, sizes"
              @current-change="loadData"
              @size-change="onSizeChange"
            />
          </div>
        </div>
      </div>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, watch } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi, knowledgeTreeApi } from '@/api'
import type { KnowledgeTreeNode } from '@/api/questions'
import type { Question, Difficulty, FivePower } from '@/types'
import { DifficultyLabels, FivePowerLabels } from '@/types'

const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const page = ref(1)
const totalPages = ref(1)
const pageSize = ref(50)
const PAGE_SIZE = pageSize

const filters = reactive<{ difficulty: Difficulty | ''; keyword: string }>({
  difficulty: '', keyword: '',
})

// ── 左树筛选状态（存 ID）────────────────────────────────────
const treeFilter = reactive({
  subject_id:         null as number | null,
  grade_id:           null as number | null,
  semester_id:        null as number | null,
  chapter_id:         null as number | null,
  knowledge_point_id: null as number | null,
})

// 面包屑展示用名称（与 treeFilter 同步更新）
const treeFilterNames = reactive({
  subject: '', grade: '', semester: '', chapter: '', knowledge_point: '',
})

const treeBreadcrumb = computed(() => {
  return [treeFilterNames.subject, treeFilterNames.grade, treeFilterNames.semester, treeFilterNames.chapter, treeFilterNames.knowledge_point].filter(Boolean).join(' › ')
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

// ── 树选择操作（传 node 对象，记录 id 和 name）───────────────
function clearTreeFilter() {
  Object.assign(treeFilter, { subject_id: null, grade_id: null, semester_id: null, chapter_id: null, knowledge_point_id: null })
  Object.assign(treeFilterNames, { subject: '', grade: '', semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectSubject(node: KnowledgeTreeNode) {
  Object.assign(treeFilter, { subject_id: node.id, grade_id: null, semester_id: null, chapter_id: null, knowledge_point_id: null })
  Object.assign(treeFilterNames, { subject: node.name, grade: '', semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectGrade(subject: KnowledgeTreeNode, node: KnowledgeTreeNode) {
  Object.assign(treeFilter, { subject_id: subject.id, grade_id: node.id, semester_id: null, chapter_id: null, knowledge_point_id: null })
  Object.assign(treeFilterNames, { subject: subject.name, grade: node.name, semester: '', chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectSemester(subject: KnowledgeTreeNode, grade: KnowledgeTreeNode, node: KnowledgeTreeNode) {
  Object.assign(treeFilter, { subject_id: subject.id, grade_id: grade.id, semester_id: node.id, chapter_id: null, knowledge_point_id: null })
  Object.assign(treeFilterNames, { subject: subject.name, grade: grade.name, semester: node.name, chapter: '', knowledge_point: '' })
  page.value = 1; loadData()
}

function selectChapter(subject: KnowledgeTreeNode, grade: KnowledgeTreeNode, sem: KnowledgeTreeNode, node: KnowledgeTreeNode) {
  Object.assign(treeFilter, { subject_id: subject.id, grade_id: grade.id, semester_id: sem.id, chapter_id: node.id, knowledge_point_id: null })
  Object.assign(treeFilterNames, { subject: subject.name, grade: grade.name, semester: sem.name, chapter: node.name, knowledge_point: '' })
  page.value = 1; loadData()
}

function selectKnowledgePoint(subject: KnowledgeTreeNode, grade: KnowledgeTreeNode, sem: KnowledgeTreeNode, ch: KnowledgeTreeNode, node: KnowledgeTreeNode) {
  Object.assign(treeFilter, { subject_id: subject.id, grade_id: grade.id, semester_id: sem.id, chapter_id: ch.id, knowledge_point_id: node.id })
  Object.assign(treeFilterNames, { subject: subject.name, grade: grade.name, semester: sem.name, chapter: ch.name, knowledge_point: node.name })
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
    // 管理页只展示已发布题目，is_active 独立控制启用/停用，不影响 status
    const params: Record<string, unknown> = {
      page: page.value,
      limit: pageSize.value,
      order_by: 'created_at_desc',
      status: 'published',
    }
    if (filters.difficulty)            params.difficulty          = filters.difficulty
    if (filters.keyword)               params.keyword             = filters.keyword
    if (treeFilter.subject_id)         params.subject_id          = treeFilter.subject_id
    if (treeFilter.grade_id)           params.grade_id            = treeFilter.grade_id
    if (treeFilter.semester_id)        params.semester_id         = treeFilter.semester_id
    if (treeFilter.chapter_id)         params.chapter_id          = treeFilter.chapter_id
    if (treeFilter.knowledge_point_id) params.knowledge_point_id  = treeFilter.knowledge_point_id

    const res = await questionApi.getList(params)
    questions.value = res.list
    total.value = res.total
    totalPages.value = res.total_pages ?? 1
  } finally { loading.value = false }
}

function handleSearch() { page.value = 1; loadData() }
function onSizeChange() { page.value = 1; loadData() }
function prevPage() { if (page.value > 1) { page.value--; loadData() } }

// 防抖搜索（输入框专用）
let _searchTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (_searchTimer) clearTimeout(_searchTimer)
  _searchTimer = setTimeout(handleSearch, 1000)
}
watch(() => filters.keyword, debouncedSearch)
function nextPage() { if (page.value < totalPages.value) { page.value++; loadData() } }

async function handleDeactivate(row: Question) {
  if (row.is_active === false) return
  await ElMessageBox.confirm(
    `确认停用题目 #${row.id}？\n\n停用后该题目将从小程序端练习抽题中移除，学生无法被抽取到该题目，直到重新启用为止。题目发布状态不受影响。`,
    '确认停用',
    { confirmButtonText: '确认停用', cancelButtonText: '取消', type: 'warning' }
  )
  await questionApi.deactivate(row.id)
  ElMessage.success('题目已停用，将不再参与学生练习抽题')
  loadData()
}

async function handleActivate(row: Question) {
  if (row.is_active !== false) return
  await ElMessageBox.confirm(
    `确认启用题目 #${row.id}？\n\n启用后该题目将重新加入小程序端练习抽题，学生可被抽取到该题目进行练习。`,
    '确认启用',
    { confirmButtonText: '确认启用', cancelButtonText: '取消', type: 'info' }
  )
  await questionApi.activate(row.id)
  ElMessage.success('题目已启用，将重新参与学生练习抽题')
  loadData()
}

onMounted(() => { loadData(); loadKnowledgeTree() })
</script>

<style lang="scss" scoped>
// ── 主体布局：左树右表 ───────────────────────────────────────
.main-layout {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 16px;
  align-items: stretch;   // 左树与右表等高
}

// ── 左树面板 ─────────────────────────────────────────────────
.tree-panel {
  width: 220px;
  flex-shrink: 0;
  padding: 12px 0;
  overflow-y: auto;    // 树节点过多时内部滚动
  overflow-x: hidden;

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
  min-height: 0;
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
.stem-cell { display: flex; align-items: center; gap: 8px; }
.stem-text {
  font-size: 13.5px; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  flex: 1; min-width: 0;
}
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

// ── 启用状态徽标 ─────────────────────────────────────────────
.active-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &__dot { width: 6px; height: 6px; border-radius: 50%; }

  &--on  { background: var(--green-dim);  color: var(--green);  border-color: var(--green-border);  .active-badge__dot { background: var(--green); } }
  &--off { background: var(--amber-dim);  color: var(--amber);  border-color: var(--amber-border);  .active-badge__dot { background: var(--amber); } }
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
