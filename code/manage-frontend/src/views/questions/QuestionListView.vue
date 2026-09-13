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

    <!-- ── 状态统计栏 ── -->
    <div class="stat-pills">
      <span
        v-for="(label, key) in QuestionStatusLabels" :key="key"
        class="stat-pill"
        :class="{ 'stat-pill--active': filters.status === key }"
        @click="selectStatus(key as QuestionStatus)"
      >
        <span class="stat-pill__dot" :class="`status-dot--${key}`" />
        {{ label }}
        <span class="stat-pill__count num">{{ statusCounts[key as QuestionStatus] ?? 0 }}</span>
      </span>
      <span
        class="stat-pill"
        :class="{ 'stat-pill--active': filters.status === '' }"
        @click="selectStatus('')"
      >
        全部
        <span class="stat-pill__count num">{{ questions.length }}</span>
      </span>
    </div>

    <!-- ── 筛选栏 ── -->
    <div class="filter-bar">
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
    </div>

    <!-- ── 题目列表表格 ── -->
    <div class="surface" style="overflow:hidden">
      <el-table :data="questions" v-loading="loading" style="width:100%">

        <!-- ID -->
        <el-table-column label="ID" width="90">
          <template #default="{ row }">
            <span class="id-chip">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <!-- 题干 + 状态 -->
        <el-table-column label="题干" min-width="340">
          <template #default="{ row }">
            <div class="stem-cell">
              <div class="stem-text">
                {{ row.stem.substring(0, 65) }}{{ row.stem.length > 65 ? '…' : '' }}
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

        <!-- 归属（AI 分析后才有） -->
        <el-table-column label="科目 / 年级" width="120">
          <template #default="{ row }">
            <span v-if="row.subject" style="font-size:13px;color:var(--text-2)">
              {{ row.subject }} · {{ row.grade }}
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

        <!-- 主五力权重 Top -->
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
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <!-- 草稿：触发分析 + 删除 -->
            <template v-if="row.status === 'draft'">
              <el-button text size="small" style="color:var(--indigo)" @click="$router.push(`/questions/${row.id}/edit`)">编辑</el-button>
              <el-button text size="small" style="color:var(--green)" @click="handleAnalyze(row)">模型分析</el-button>
              <el-button text size="small" style="color:var(--red)" @click="handleDelete(row)">删除</el-button>
            </template>
            <!-- 分析中：不可操作 -->
            <template v-else-if="row.status === 'analyzing'">
              <span style="font-size:12px;color:var(--text-3)">分析中…</span>
            </template>
            <!-- 待审核：审核入口 -->
            <template v-else-if="row.status === 'pending_review'">
              <el-button text size="small" style="color:var(--indigo);font-weight:600" @click="$router.push(`/questions/${row.id}/review`)">审核结果</el-button>
            </template>
            <!-- 已发布：下架 -->
            <template v-else-if="row.status === 'published'">
              <el-button text size="small" style="color:var(--text-2)" @click="$router.push(`/questions/${row.id}/review`)">查看</el-button>
              <el-button text size="small" style="color:var(--amber)" @click="handleArchive(row)">下架</el-button>
            </template>
            <!-- 已归档：查看 -->
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

    <!-- ── 批量导入弹窗 ── -->
    <el-dialog v-model="showImport" title="批量导入题干" width="560px">
      <div class="import-hint">
        <p>每行一道题目的题干文本，导入后系统将<strong>自动触发大模型逐条分析</strong>，无需手动操作。</p>
        <p style="margin-top:8px">或上传 <code class="inline-code">.txt</code> / <code class="inline-code">.json</code> 格式文件（JSON 格式每条仅需包含 <code class="inline-code">stem</code> 字段）。</p>
      </div>
      <el-input
        v-model="batchStems"
        type="textarea"
        :rows="8"
        placeholder="每行粘贴一道题干..."
        style="margin-top:16px"
      />
      <el-upload
        drag accept=".txt,.json" :auto-upload="false"
        :on-change="handleFileChange"
        style="margin-top:12px"
      >
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
const total = ref(0)
const hasMore = ref(false)
const cursor = ref(0)
const showImport = ref(false)
const batchStems = ref('')

const filters = reactive<{ status: QuestionStatus | ''; difficulty: Difficulty | ''; keyword: string }>({
  status: '', difficulty: '', keyword: '',
})

// 各状态计数
const statusCounts = computed(() => {
  const counts: Partial<Record<QuestionStatus, number>> = {}
  // 实际场景应由 API 返回总数，这里以当前页数据近似
  return counts
})

// 找权重最高的维度
function topPower(weights: Record<string, number>): string {
  return Object.entries(weights).sort((a, b) => b[1] - a[1])[0]?.[0] || 'CONSTRUCT'
}

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { cursor: cursor.value, limit: 20 }
    if (filters.status)    params.status    = filters.status
    if (filters.difficulty) params.difficulty = filters.difficulty
    if (filters.keyword)   params.keyword   = filters.keyword
    const res = await questionApi.getList(params)
    questions.value = res.list
    total.value = res.total
    hasMore.value = res.has_more
  } finally { loading.value = false }
}

function selectStatus(s: QuestionStatus | '') {
  filters.status = s
  cursor.value = 0
  loadData()
}

function handleSearch() { cursor.value = 0; loadData() }
function resetFilters() {
  Object.assign(filters, { status: '', difficulty: '', keyword: '' })
  cursor.value = 0; loadData()
}
function prevPage() { cursor.value = Math.max(0, cursor.value - 20); loadData() }
function nextPage() { cursor.value += 20; loadData() }

// 触发大模型分析
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

// 下架
async function handleArchive(row: Question) {
  await ElMessageBox.confirm(`确认下架题目 #${row.id}？下架后不再参与训练推荐。`, '确认下架', { type: 'warning' })
  await questionApi.archive(row.id)
  ElMessage.success('题目已下架')
  loadData()
}

// 软删除草稿
async function handleDelete(row: Question) {
  await ElMessageBox.confirm(`确认删除草稿 #${row.id}？此操作不可恢复。`, '确认删除', { type: 'error' })
  await questionApi.delete(row.id)
  ElMessage.success('草稿已删除')
  loadData()
}

// 批量导入
function handleFileChange() { ElMessage.info('文件已选择') }
async function handleImport() {
  const stems = batchStems.value.split('\n').map(s => s.trim()).filter(Boolean)
  if (stems.length === 0) { ElMessage.warning('请粘贴题干内容或上传文件'); return }
  importLoading.value = true
  try {
    await questionApi.batchImport(stems)
    ElMessage.success(`已导入 ${stems.length} 条题干，大模型分析任务已提交`)
    showImport.value = false
    batchStems.value = ''
    loadData()
  } finally { importLoading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
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

  &__count {
    font-weight: 700;
    color: var(--text-1);
  }
}

// 状态点颜色
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

// ── 状态徽章 ─────────────────────────────────────────────────
.status-badge {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &__dot {
    width: 6px;
    height: 6px;
    border-radius: 50%;
  }

  &--draft          { background: var(--amber-dim);   color: var(--amber);  border-color: var(--amber-border);
                      .status-badge__dot { background: var(--amber); } }
  &--analyzing      { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border);
                      .status-badge__dot { background: var(--indigo); } }
  &--pending_review { background: var(--purple-dim);  color: var(--purple); border-color: var(--purple-border);
                      .status-badge__dot { background: var(--purple); } }
  &--published      { background: var(--green-dim);   color: var(--green);  border-color: var(--green-border);
                      .status-badge__dot { background: var(--green); } }
  &--archived       { background: var(--bg-muted);    color: var(--text-3); border-color: var(--border-hover);
                      .status-badge__dot { background: var(--text-3); } }
}

.round-tag {
  font-size: 10px;
  font-weight: 500;
  padding: 0 5px;
  border-radius: 4px;
  background: rgba(124, 58, 237, 0.15);
}

// 分析中动效
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

// ── 难度徽章 ─────────────────────────────────────────────────
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

// ── 向量化状态 ───────────────────────────────────────────────
.embed-badge {
  font-size: 11px;
  font-weight: 500;
  padding: 2px 7px;
  border-radius: var(--r-pill);
  border: 1px solid;

  &.embed--ok   { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &.embed--fail { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }
}

// ── 批量导入提示 ─────────────────────────────────────────────
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
