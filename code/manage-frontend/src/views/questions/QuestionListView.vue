<template>
  <div class="page-root">

    <!-- ── 主体：左树右表 ── -->
    <div class="main-layout">

      <!-- ── 左侧：五级知识体系树 ── -->
      <div class="tree-panel surface">
        <!-- 树搜索框 -->
        <div class="tree-search">
          <el-input
            v-model="treeKeyword"
            placeholder="搜索知识体系..."
            clearable
            size="small"
          >
            <template #prefix>
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
        </div>

        <div class="tree-scroll">
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
        <div v-for="subject in filteredTree" :key="subject.id">
          <!-- 科目 -->
          <div class="tree-node tree-node--l1" :class="{ active: treeFilter.subject_id === subject.id && !treeFilter.grade_id }">
            <span class="tree-toggle" @click="subject.open = !subject.open" :title="subject.open ? '折叠' : '展开'">
              {{ subject.open ? '▼' : '▶' }}
            </span>
            <SvgIcon v-if="subjectIcon(subject.name)" :name="subjectIcon(subject.name)" :size="20" color="var(--color-primary)" style="flex-shrink:0;margin-right:2px;vertical-align:middle" />
            <span class="tree-node__label" @click="selectSubject(subject)">{{ subject.name }}</span>
            <span v-if="subject.published_count > 0" class="tree-node__count">{{ subject.published_count }}</span>
          </div>

          <!-- 年级 -->
          <template v-if="subject.open">
            <div v-for="grade in subject.children" :key="grade.id">
              <div class="tree-node tree-node--l2" :class="{ active: treeFilter.grade_id === grade.id && !treeFilter.semester_id }">
                <span class="tree-toggle" @click="grade.open = !grade.open" :title="grade.open ? '折叠' : '展开'">
                  {{ grade.open ? '▼' : '▶' }}
                </span>
                <span class="tree-node__label" @click="selectGrade(subject, grade)">{{ grade.name }}</span>
                <span v-if="grade.published_count > 0" class="tree-node__count">{{ grade.published_count }}</span>
              </div>

              <!-- 学期 -->
              <template v-if="grade.open">
                <div v-for="sem in grade.children" :key="sem.id">
                  <div class="tree-node tree-node--l3" :class="{ active: treeFilter.semester_id === sem.id && !treeFilter.chapter_id }">
                    <span class="tree-toggle" @click="sem.open = !sem.open" :title="sem.open ? '折叠' : '展开'">
                      {{ sem.open ? '▼' : '▶' }}
                    </span>
                    <span class="tree-node__label" @click="selectSemester(subject, grade, sem)">{{ sem.name }}</span>
                    <span v-if="sem.published_count > 0" class="tree-node__count">{{ sem.published_count }}</span>
                  </div>

                  <!-- 单元/章节 -->
                  <template v-if="sem.open">
                    <div v-for="ch in sem.children" :key="ch.id">
                      <div class="tree-node tree-node--l4" :class="{ active: treeFilter.chapter_id === ch.id && !treeFilter.knowledge_point_id }">
                        <span class="tree-toggle" @click="ch.open = !ch.open" :title="ch.open ? '折叠' : '展开'">
                          {{ ch.open ? '▼' : '▶' }}
                        </span>
                        <span class="tree-node__label" @click="selectChapter(subject, grade, sem, ch)">{{ ch.name }}</span>
                        <span v-if="ch.published_count > 0" class="tree-node__count">{{ ch.published_count }}</span>
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
                          <span v-if="kp.published_count > 0" class="tree-node__count">{{ kp.published_count }}</span>
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
      </div>

      <!-- ── 右侧：筛选 + 表格 ── -->
      <div class="table-panel">

        <!-- 筛选栏 -->
        <div class="inner-toolbar">
          <el-input v-model="filters.keyword" placeholder="搜索题干..." clearable>
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
          <el-select v-model="filters.is_active" placeholder="启用状态" clearable style="width:110px" @change="handleSearch">
            <el-option label="已启用" :value="true" />
            <el-option label="未启用" :value="false" />
          </el-select>
          <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width:90px" @change="handleSearch">
            <el-option v-for="(label, key) in DifficultyLabels" :key="key" :label="label" :value="key" />
          </el-select>
          <div style="flex:1" />
          <el-button class="btn-import" style="color:var(--green);padding:0 8px !important" :loading="batchActivating" @click="handleBatchSetActive(true)">
            <SvgIcon v-if="!batchActivating" name="play" :size="15" style="margin-right:5px" />
            批量启用
          </el-button>
          <el-button class="btn-import" style="color:var(--red);padding:0 8px !important" :loading="batchDeactivating" @click="handleBatchSetActive(false)">
            <SvgIcon v-if="!batchDeactivating" name="pause" :size="15" style="margin-right:5px" />
            批量停用
          </el-button>
        </div>

        <!-- 题目列表表格 -->
        <div class="surface surface--table">
          <el-table
            :data="questions"
            v-loading="loading"
            style="width:100%"
            @selection-change="(rows: Question[]) => selected = rows"
          >
            <el-table-column type="selection" width="46" />
            <el-table-column label="序号" width="60" align="center">
              <template #default="{ $index }">
                <span class="num" style="color:var(--text-3);font-size:12px">{{ (page - 1) * pageSize + $index + 1 }}</span>
              </template>
            </el-table-column>

            <el-table-column label="题干" min-width="300">
              <template #default="{ row }">
                <el-tooltip :content="row.stem" placement="top-start" :show-after="300" effect="light">
                  <span class="stem-text">{{ row.stem }}</span>
                </el-tooltip>
              </template>
            </el-table-column>

            <!-- 启用状态（is_active 独立于 status）-->
            <el-table-column label="启用状态" width="100" align="center">
              <template #default="{ row }">
                <span class="active-flag" :class="row.is_active === false ? 'active-flag--off' : 'active-flag--on'">
                  <SvgIcon :name="row.is_active === false ? 'close_circle' : 'check_circle'" :size="16" />
                  {{ row.is_active === false ? '未启用' : '已启用' }}
                </span>
              </template>
            </el-table-column>

            <!-- 归属：五级体系（科目·年级·学期） -->
            <el-table-column label="归属" width="140">
              <template #default="{ row }">
                <span v-if="row.subject_id" style="font-size:12.5px;color:var(--text-2)">
                  {{ subjectName(row.subject_id) }} · {{ gradeName(row.grade_id) }} · {{ semesterName(row.semester_id) }}
                </span>
                <span v-else style="font-size:12px;color:var(--text-3)">—</span>
              </template>
            </el-table-column>

            <!-- 难度 -->
            <el-table-column label="难度" width="80" align="center">
              <template #default="{ row }">
                <span v-if="row.difficulty" class="diff-badge" :class="`diff--${row.difficulty}`">
                  {{ DifficultyLabels[row.difficulty as Difficulty] }}
                </span>
                <span v-else style="color:var(--text-3);font-size:12px">—</span>
              </template>
            </el-table-column>

            <!-- 主五力 -->
            <el-table-column label="主五力" width="90" align="center">
              <template #default="{ row }">
                <span v-if="row.five_power_weights" class="power-dot-label" :class="`power-dot-label--${topPower(row.five_power_weights)}`">
                  <span class="power-dot-label__dot" />
                  {{ FivePowerLabels[topPower(row.five_power_weights) as FivePower] }}
                </span>
                <span v-else style="color:var(--text-3);font-size:12px">—</span>
              </template>
            </el-table-column>

            <!-- 操作 -->
            <el-table-column label="操作" width="110" fixed="right">
              <template #default="{ row }">
                <el-button text size="small" style="color:#f3c601" @click="$router.push(`/questions/${row.id}/review`)">
                  <SvgIcon name="detail" :size="18" color="#f3c601" title="查看" />
                </el-button>
                <el-button v-if="row.is_active !== false" text size="small" class="btn-no-hover" style="color:var(--red)" @click="handleDeactivate(row)">
                  <SvgIcon name="pause" :size="18" color="var(--red)" title="停用" />
                </el-button>
                <template v-else>
                  <el-button text size="small" style="color:var(--color-primary)" @click="$router.push(`/questions/${row.id}/archived-edit`)">
                    <SvgIcon name="edit" :size="18" color="var(--color-primary)" title="编辑" />
                  </el-button>
                  <el-button text size="small" class="btn-no-hover" style="color:var(--green)" @click="handleActivate(row)">
                    <SvgIcon name="play" :size="18" color="var(--green)" title="启用" />
                  </el-button>
                </template>
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
import type { KnowledgeTreeNode, BatchResult } from '@/api/questions'
import type { Question, Difficulty, FivePower } from '@/types'
import { DifficultyLabels, FivePowerLabels } from '@/types'

const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const totalAll = ref(0)
const page = ref(1)
const totalPages = ref(1)
const pageSize = ref(50)
const PAGE_SIZE = pageSize

const filters = reactive<{ difficulty: Difficulty | ''; keyword: string; is_active: boolean | '' }>({
  difficulty: '', keyword: '', is_active: '',
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
const treeKeyword = ref('')

// 树节点名称匹配关键词（递归检查子节点）
function nodeMatches(node: KnowledgeTreeNode, kw: string): boolean {
  if (node.name.includes(kw)) return true
  return (node.children ?? []).some(c => nodeMatches(c, kw))
}

const filteredTree = computed(() => {
  const kw = treeKeyword.value.trim()
  if (!kw) return knowledgeTree.value
  return knowledgeTree.value.filter(subject => nodeMatches(subject, kw))
})

async function loadKnowledgeTree() {
  try {
    const res = await knowledgeTreeApi.getTree()
    knowledgeTree.value = res.tree
  } catch { /* ignore */ }
}

const allCount = computed(() => totalAll.value)

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

const SUBJECT_ICONS: Record<string, string> = {
  '数学': 'math',
  '物理': 'physics',
  '化学': 'chemistry',
}
function subjectIcon(name: string): string {
  return SUBJECT_ICONS[name] ?? ''
}

// ── 工具函数 ─────────────────────────────────────────────────

function topPower(weights: Record<string, number>): string {
  return Object.entries(weights).sort((a, b) => b[1] - a[1])[0]?.[0] || 'CONSTRUCT'
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
    if (typeof filters.is_active === 'boolean') params.is_active = filters.is_active   // true 已启用 / false 未启用
    if (filters.keyword)               params.keyword             = filters.keyword
    if (treeFilter.subject_id)         params.subject_id          = treeFilter.subject_id
    if (treeFilter.grade_id)           params.grade_id            = treeFilter.grade_id
    if (treeFilter.semester_id)        params.semester_id         = treeFilter.semester_id
    if (treeFilter.chapter_id)         params.chapter_id          = treeFilter.chapter_id
    if (treeFilter.knowledge_point_id) params.knowledge_point_id  = treeFilter.knowledge_point_id

    const res = await questionApi.getList(params)
    questions.value = res.list
    selected.value = []   // 翻页 / 筛选后清空勾选，范围仅限当前页
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

// ── 批量启用 / 停用（后端批量接口，一次请求）──────────────────
const selected = ref<Question[]>([])
const batchActivating = ref(false)
const batchDeactivating = ref(false)
const BATCH_MAX = 200   // 与后端 QBATCH-002 一致：单次最多 200 条

function notifyBatchResult(res: BatchResult, doneText: string) {
  if (res.skipped_count === 0 && res.failed_count === 0) {
    ElMessage.success(`${doneText} ${res.success_count} 道题目`)
    return
  }
  const notes = [
    res.skipped_count > 0 ? `${res.skipped_count} 道已处于目标状态或状态不符，已跳过` : '',
    res.failed_count > 0 ? `${res.failed_count} 道处理失败，请稍后重试` : '',
  ].filter(Boolean)
  ElMessage.warning(`${doneText} ${res.success_count} 道题目；${notes.join('；')}`)
}

async function handleBatchSetActive(toActive: boolean) {
  const verb = toActive ? '启用' : '停用'
  if (selected.value.length === 0) {
    ElMessage.warning(`请先勾选需要${verb}的题目`)
    return
  }
  if (selected.value.length > BATCH_MAX) {
    ElMessage.warning(`单次最多${verb} ${BATCH_MAX} 道题目，当前已勾选 ${selected.value.length} 道，请减少勾选后重试`)
    return
  }
  // 前端预校验仅为交互优化，最终以后端校验为准
  const targets = selected.value.filter(q => (q.is_active !== false) !== toActive)
  const skipped = selected.value.length - targets.length
  if (targets.length === 0) {
    ElMessage.warning(`所选题目均已处于${verb}状态，无需${verb}`)
    return
  }
  const effect = toActive
    ? '启用后将重新加入小程序端练习抽题'
    : '停用后将从小程序端练习抽题中移除，直到重新启用为止，题目发布状态不受影响'
  const msg = skipped > 0
    ? `已勾选 ${selected.value.length} 道题目，其中 ${targets.length} 道将被${verb}；其余 ${skipped} 道已处于${verb}状态，会被跳过。${effect}，是否继续？`
    : `已勾选 ${targets.length} 道题目，将全部${verb}。${effect}，是否继续？`
  const confirmed = await ElMessageBox.confirm(msg, `批量${verb}确认`, {
    confirmButtonText: `确认${verb}`, cancelButtonText: '取消', type: toActive ? 'info' : 'warning',
  }).then(() => true, () => false)
  if (!confirmed) return

  const flag = toActive ? batchActivating : batchDeactivating
  flag.value = true
  try {
    const ids = selected.value.map(q => q.id)
    const res = toActive ? await questionApi.batchActivate(ids) : await questionApi.batchDeactivate(ids)
    notifyBatchResult(res, `已${verb}`)
    loadData()
  } finally { flag.value = false }
}

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

async function loadTotalAll() {
  const res = await questionApi.getList({ page: 1, limit: 1, status: 'published' })
  totalAll.value = res.total
}

onMounted(() => { loadData(); loadKnowledgeTree(); loadTotalAll() })
</script>

<style lang="scss" scoped>
// ── 主体布局：左树右表 ───────────────────────────────────────
.main-layout {
  flex: 1;
  min-height: 0;
  display: flex;
  gap: 10px;
  align-items: stretch;   // 左树与右表等高
}

// ── 左树面板 ─────────────────────────────────────────────────
.tree-panel {
  width: 220px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  border-radius: 4px !important;
  background: #ffffff !important;

  [data-theme="dark"] & {
    background: #1a1a1a !important;
  }

  &__title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 12px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    padding: 12px 14px 10px;
    border-bottom: 1px solid var(--border);
    flex-shrink: 0;
  }
}


.tree-search {
  flex-shrink: 0;
  border-bottom: 1px solid var(--border);

  :deep(.el-input__wrapper) {
    border: none !important;
    box-shadow: none !important;
    background: transparent !important;
    &:hover, &.is-focus { border: none !important; box-shadow: none !important; }
  }
}

.tree-scroll {
  flex: 1;
  min-height: 0;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 6px 0;
}

.tree-node {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 6px;
  margin: 1px 8px;
  font-size: 13px;
  color: var(--text-2);
  cursor: default;
  border-radius: 6px;
  transition: background 0.12s, color 0.12s, box-shadow 0.12s;
  white-space: nowrap;
  overflow: hidden;

  &:hover { color: var(--color-primary); }

  // 同侧栏选中项：蓝色渐变底
  &.active {
    background: linear-gradient(90deg, rgba(94, 141, 249, 0.20), rgba(94, 141, 249, 0.05));
    color: var(--color-primary);
    font-weight: 600;
  }

  &--all { font-weight: 600; color: var(--text-1); cursor: pointer; }
  &--l1  { padding-left: 6px; color: var(--text-1); }
  &--l2  { padding-left: 16px; color: var(--text-2); }
  &--l3  { padding-left: 26px; font-size: 12.5px; color: var(--text-2); }
  &--l4  { padding-left: 36px; font-size: 12px; color: var(--text-2); }
  &--l5  { padding-left: 46px; font-size: 11.5px; color: var(--text-2); cursor: pointer;
            &:hover { color: var(--color-primary); } }

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
      color: var(--color-primary);
    }
  }

  &__count {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    color: var(--color-primary);
    background: var(--color-primary-light);
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
    background: var(--color-primary-light);
    color: var(--color-primary);
  }
}

.tree-leaf-dot {
  font-size: 8px;
  color: var(--text-3);
  width: 18px;
  text-align: center;
  flex-shrink: 0;
  transition: color 0.12s;

  .tree-node.active &,
  .tree-node:hover & { color: var(--color-primary); }
}

// ── 右侧表格区 ───────────────────────────────────────────────
.table-panel {
  flex: 1;
  min-width: 0;
  min-height: 0;
  display: flex;
  flex-direction: column;
  gap: 10px;
}

// ── 题干列 ───────────────────────────────────────────────────
.stem-cell { display: flex; align-items: center; gap: 8px; }
.stem-text {
  font-size: 13.5px; color: var(--text-1);
  white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
  flex: 1; min-width: 0;
}
.stem-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }

// ── 主五力：圆点 + 文字（参考录入页状态列）────────────────────
.power-dot-label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 13.5px;
  font-weight: 400;

  &__dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &--INSIGHT   { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-insight); } }
  &--CONSTRUCT { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-construct); } }
  &--DEDUCE    { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-deduce); } }
  &--ADAPT     { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-adapt); } }
  &--MIGRATE   { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-migrate); } }
}

// 启用状态：圆环对勾 / 圆环叉图标 + 文字，无底色无圆点，与「状态」列的圆点样式区分；图标色走主题变量
.active-flag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  white-space: nowrap;

  // 文字与图标同色：SvgIcon 默认 fill: currentColor，随文字色变化
  &--on  { color: var(--green); }
  &--off { color: var(--red); }
}

.diff-badge {
  font-size: 12px;
  font-weight: 500;
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 60px;
  height: 22px;
  border-radius: 11px;
  border: none;

  &.diff--basic     { background: #E8F5D0; color: #4A7C10; }
  &.diff--advanced  { background: #FFF0D6; color: #B45309; }
  &.diff--challenge { background: #FFE0E0; color: #DC2626; }
}


:deep(.btn-no-hover:hover) {
  background: transparent !important;
  border-color: transparent !important;
}
</style>
