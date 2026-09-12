<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">五力测试题库管理</h1>
        <p class="page-subtitle">管理用于生成学生五力认知画像的测试题目</p>
      </div>
      <el-button type="primary" @click="router.push('/cognitive-test/create')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        新增题目
      </el-button>
    </div>

    <!-- ── 测试状态看板 ── -->
    <div class="status-board" :class="publishedCount === 20 ? 'status-board--ok' : 'status-board--warn'">
      <div class="status-board__left">
        <div class="status-icon">
          <svg v-if="publishedCount === 20" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
          </svg>
        </div>
        <div>
          <div class="status-board__label">测试状态</div>
          <div class="status-board__text" v-if="publishedCount === 20">● 已发布 <strong>{{ publishedCount }}/20</strong> 道 — 测试功能已就绪，学生可正常参加测试</div>
          <div class="status-board__text" v-else>● 已发布 <strong>{{ publishedCount }}/20</strong> 道 — ⚠ 未达20道，测试功能已暂停</div>
        </div>
      </div>
      <div class="status-board__counts">
        <span class="count-chip count-chip--draft" @click="activeTab = 'draft'">草稿 {{ draftCount }}</span>
        <span class="count-chip count-chip--published" @click="activeTab = 'published'">已发布 {{ publishedCount }}</span>
        <span class="count-chip count-chip--archived" @click="activeTab = 'archived'">已下架 {{ archivedCount }}</span>
      </div>
    </div>

    <!-- ── 标签页 + 筛选栏 ── -->
    <div class="surface" style="padding:0;overflow:hidden" v-loading="loading">
      <div class="tab-filter-bar">
        <div class="tab-group">
          <button class="tab-item" :class="{ active: activeTab === 'all' }" @click="activeTab = 'all'">
            全部 ({{ allQuestions.length }})
          </button>
          <button class="tab-item" :class="{ active: activeTab === 'draft' }" @click="activeTab = 'draft'">
            草稿 ({{ draftCount }})
          </button>
          <button class="tab-item" :class="{ active: activeTab === 'published' }" @click="activeTab = 'published'">
            已发布 ({{ publishedCount }})
          </button>
          <button class="tab-item" :class="{ active: activeTab === 'archived' }" @click="activeTab = 'archived'">
            已下架 ({{ archivedCount }})
          </button>
        </div>
        <div class="filter-group">
          <el-select v-model="filterPower" placeholder="目标维度" clearable size="small" style="width:120px">
            <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key" />
          </el-select>
          <el-select v-model="filterType" placeholder="题目类型" clearable size="small" style="width:120px">
            <el-option label="标准题" value="STANDARD" />
            <el-option label="开放题" value="OPEN" />
          </el-select>
          <el-input v-model="searchText" placeholder="搜索题干..." clearable size="small" style="width:180px">
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
        </div>
      </div>

      <!-- ── 列表表格 ── -->
      <el-table :data="filteredQuestions" row-key="id" style="width:100%">

        <!-- 展开行 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <p style="font-size:13.5px;color:var(--text-1);line-height:1.6;margin-bottom:14px">{{ row.stem }}</p>
              <div class="score-pills">
                <span v-for="opt in ['A','B','C','D']" :key="opt"
                  class="score-pill" :class="{ 'score-pill--max': isMaxScore(row, opt) }">
                  <span class="score-pill__opt">{{ opt }}</span>
                  <span class="score-pill__val num">{{ row.option_scores?.[opt] ?? 0 }}</span>
                  <span class="score-pill__unit">分</span>
                </span>
                <span class="ref-time-pill">⏱ {{ row.reference_time_sec }} 秒</span>
              </div>
              <div v-if="row.question_type === 'OPEN' && row.option_force_weights" style="margin-top:14px">
                <p style="font-size:12px;font-weight:600;color:var(--text-3);margin-bottom:8px;text-transform:uppercase;letter-spacing:0.05em">五力权重分布</p>
                <el-table :data="['A','B','C','D'].map(o => ({ opt: o }))" border size="small" style="max-width:560px">
                  <el-table-column label="选项" prop="opt" width="58" align="center">
                    <template #default="{ row: wr }">
                      <span style="font-weight:700;color:var(--indigo)">{{ wr.opt }}</span>
                    </template>
                  </el-table-column>
                  <el-table-column v-for="p in powers" :key="p" :label="FivePowerLabels[p as FivePower]" width="84" align="center">
                    <template #default="{ row: wr }">
                      <span class="num" style="font-size:12px;color:var(--text-2)">{{ row.option_force_weights?.[wr.opt]?.[p as FivePower]?.toFixed(2) }}</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 题号 -->
        <el-table-column label="#" prop="order_num" width="60" align="center">
          <template #default="{ row }">
            <span class="num" style="font-weight:600;color:var(--indigo)">{{ row.order_num }}</span>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status-badge" :class="`status-badge--${row.status}`">
              {{ CognitiveQuestionStatusLabels[row.status as CognitiveQuestionStatus] }}
            </span>
          </template>
        </el-table-column>

        <!-- 类型 -->
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <span class="type-badge" :class="row.question_type === 'OPEN' ? 'type--open' : 'type--std'">
              {{ row.question_type === 'OPEN' ? '开放题' : '标准题' }}
            </span>
          </template>
        </el-table-column>

        <!-- 题干摘要 -->
        <el-table-column label="题干摘要" min-width="320">
          <template #default="{ row }">
            <span style="color:var(--text-1);font-size:13.5px;line-height:1.5">
              {{ row.stem?.substring(0, 55) }}{{ row.stem?.length > 55 ? '…' : '' }}
            </span>
          </template>
        </el-table-column>

        <!-- 目标维度 -->
        <el-table-column label="目标维度" width="100">
          <template #default="{ row }">
            <span class="power-badge" :class="`power-badge--${row.target_power}`">
              {{ FivePowerLabels[row.target_power as FivePower] }}
            </span>
          </template>
        </el-table-column>

        <!-- 参考时间 -->
        <el-table-column label="参考时间" width="100" align="center">
          <template #default="{ row }">
            <span class="num" style="color:var(--text-2)">{{ row.reference_time_sec }}</span>
            <span style="color:var(--text-3);font-size:12px">秒</span>
          </template>
        </el-table-column>

        <!-- 操作 -->
        <el-table-column label="操作" width="160" align="center">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;justify-content:center;gap:4px">
              <!-- 草稿 -->
              <template v-if="row.status === 'draft'">
                <el-button text size="small" style="color:var(--indigo)" @click="router.push(`/cognitive-test/${row.id}/edit`)">编辑</el-button>
                <el-button text size="small" style="color:var(--green)" @click="confirmPublish(row)">发布</el-button>
                <el-button text size="small" style="color:var(--red)" @click="confirmDelete(row)">删除</el-button>
              </template>
              <!-- 已发布 -->
              <template v-else-if="row.status === 'published'">
                <el-button text size="small" style="color:var(--indigo)" @click="router.push(`/cognitive-test/${row.id}/edit`)">编辑</el-button>
                <el-button text size="small" style="color:var(--amber)" @click="confirmArchive(row)">下架</el-button>
              </template>
              <!-- 已下架 -->
              <template v-else>
                <el-button text size="small" style="color:var(--text-2)" @click="router.push(`/cognitive-test/${row.id}/edit`)">查看</el-button>
                <el-button text size="small" style="color:var(--indigo)" @click="confirmRepublish(row)">重新发布</el-button>
              </template>
            </div>
          </template>
        </el-table-column>

      </el-table>
    </div>

    <!-- ── 发布确认弹窗 ── -->
    <el-dialog v-model="publishDialogVisible" title="确认发布此题目？" width="440px">
      <div style="line-height:1.8;font-size:14px;color:var(--text-2)">
        <p>发布后该题将加入测试题池。</p>
        <p>当前已发布：<strong class="num">{{ publishedCount }}</strong> / 20 道</p>
        <p>发布后将达：<strong class="num">{{ publishedCount + 1 }}</strong> / 20 道</p>
        <div v-if="publishedCount + 1 === 20" style="margin-top:12px;padding:10px 14px;background:var(--green-dim);border:1px solid var(--green-border);border-radius:var(--r-lg);color:var(--green);font-size:13px">
          🎉 发布后题目数将达到20道，测试功能将自动开启！
        </div>
        <div v-else-if="publishedCount >= 20" style="margin-top:12px;padding:10px 14px;background:var(--red-dim);border:1px solid var(--red-border);border-radius:var(--r-lg);color:var(--red);font-size:13px">
          ⚠ 已发布题目数已达20道，请先下架一道题后再发布新题。
        </div>
        <div v-else style="margin-top:12px;padding:10px 14px;background:var(--amber-dim);border:1px solid var(--amber-border);border-radius:var(--r-lg);color:var(--amber);font-size:13px">
          ⚠ 发布后题目内容的修改将立即影响新测试会话的评分计算。
        </div>
      </div>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :disabled="publishedCount >= 20" :loading="saving" @click="doPublish">确认发布</el-button>
      </template>
    </el-dialog>

    <!-- ── 下架确认弹窗 ── -->
    <el-dialog v-model="archiveDialogVisible" title="确认下架此题目？" width="440px">
      <div style="line-height:1.8;font-size:14px;color:var(--text-2)">
        <p>下架后该题不再参与新测试组卷。</p>
        <p>当前已发布：<strong class="num">{{ publishedCount }}</strong> / 20 道</p>
        <p>下架后将剩：<strong class="num">{{ publishedCount - 1 }}</strong> / 20 道</p>
        <div style="margin-top:12px;padding:10px 14px;background:var(--amber-dim);border:1px solid var(--amber-border);border-radius:var(--r-lg);color:var(--amber);font-size:13px">
          ⚠ 下架后测试功能将暂停，请尽快补充新题目并发布至20道。
        </div>
      </div>
      <template #footer>
        <el-button @click="archiveDialogVisible = false">取消</el-button>
        <el-button type="warning" :loading="saving" @click="doArchive">确认下架</el-button>
      </template>
    </el-dialog>

    <!-- ── 删除确认弹窗 ── -->
    <el-dialog v-model="deleteDialogVisible" title="确认删除此草稿题目？" width="400px">
      <div style="line-height:1.8;font-size:14px;color:var(--text-2)">
        <p>此操作不可撤销，草稿题目将被永久删除。</p>
        <p style="color:var(--text-3);font-size:13px">已发布或已下架的题目不可删除。</p>
      </div>
      <template #footer>
        <el-button @click="deleteDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="saving" @click="doDelete">确认删除</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { cognitiveApi } from '@/api'
import type { CognitiveQuestion, FivePower, CognitiveQuestionStatus } from '@/types'
import { FivePowerLabels, CognitiveQuestionStatusLabels } from '@/types'

const router = useRouter()

// ── 常量 ──────────────────────────────────────────────────────
const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 状态 ──────────────────────────────────────────────────────
const loading = ref(false)
const saving = ref(false)
const allQuestions = ref<CognitiveQuestion[]>([])

// 筛选
const activeTab = ref<'all' | 'draft' | 'published' | 'archived'>('all')
const filterPower = ref('')
const filterType = ref('')
const searchText = ref('')

// 操作确认弹窗
const publishDialogVisible = ref(false)
const archiveDialogVisible = ref(false)
const deleteDialogVisible = ref(false)
const actionTarget = ref<CognitiveQuestion | null>(null)

// ── 计算属性 ──────────────────────────────────────────────────
const publishedCount = computed(() => allQuestions.value.filter(q => q.status === 'published').length)
const draftCount = computed(() => allQuestions.value.filter(q => q.status === 'draft').length)
const archivedCount = computed(() => allQuestions.value.filter(q => q.status === 'archived').length)

const filteredQuestions = computed(() => {
  let list = allQuestions.value

  // 标签页筛选
  if (activeTab.value !== 'all') {
    list = list.filter(q => q.status === activeTab.value)
  }

  // 维度筛选
  if (filterPower.value) {
    list = list.filter(q => q.target_power === filterPower.value)
  }

  // 类型筛选
  if (filterType.value) {
    list = list.filter(q => q.question_type === filterType.value)
  }

  // 搜索
  if (searchText.value.trim()) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(q => q.stem?.toLowerCase().includes(kw))
  }

  return list
})

// ── 工具函数 ──────────────────────────────────────────────────
function isMaxScore(row: CognitiveQuestion, opt: string) {
  if (!row.option_scores) return false
  const max = Math.max(...Object.values(row.option_scores))
  return row.option_scores[opt] === max
}

// ── 初始化 ────────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    allQuestions.value = await cognitiveApi.getList()
  } finally {
    loading.value = false
  }
})

// ── 发布操作 ──────────────────────────────────────────────────
function confirmPublish(row: CognitiveQuestion) {
  actionTarget.value = row
  publishDialogVisible.value = true
}

async function doPublish() {
  if (!actionTarget.value) return
  saving.value = true
  try {
    await cognitiveApi.publish(actionTarget.value.id)
    actionTarget.value.status = 'published'
    publishDialogVisible.value = false
    ElMessage.success('题目已发布至测试池')
  } finally {
    saving.value = false
  }
}

// ── 下架操作 ──────────────────────────────────────────────────
function confirmArchive(row: CognitiveQuestion) {
  actionTarget.value = row
  archiveDialogVisible.value = true
}

async function doArchive() {
  if (!actionTarget.value) return
  saving.value = true
  try {
    await cognitiveApi.archive(actionTarget.value.id)
    actionTarget.value.status = 'archived'
    archiveDialogVisible.value = false
    ElMessage.success('题目已下架')
  } finally {
    saving.value = false
  }
}

// ── 重新发布 ──────────────────────────────────────────────────
function confirmRepublish(row: CognitiveQuestion) {
  if (publishedCount.value >= 20) {
    ElMessage.error('已发布题目数已达20道，请先下架一道题后再重新发布')
    return
  }
  actionTarget.value = row
  publishDialogVisible.value = true
}

// ── 删除草稿 ──────────────────────────────────────────────────
function confirmDelete(row: CognitiveQuestion) {
  actionTarget.value = row
  deleteDialogVisible.value = true
}

async function doDelete() {
  if (!actionTarget.value) return
  saving.value = true
  try {
    await cognitiveApi.delete(actionTarget.value.id)
    const idx = allQuestions.value.findIndex(q => q.id === actionTarget.value!.id)
    if (idx !== -1) allQuestions.value.splice(idx, 1)
    deleteDialogVisible.value = false
    ElMessage.success('草稿已删除')
  } finally {
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
// ── 测试状态看板 ─────────────────────────────────────────────
.status-board {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  padding: 14px 20px;
  border-radius: var(--r-xl);
  border: 1.5px solid;
  flex-wrap: wrap;

  &--ok {
    background: var(--green-dim);
    border-color: var(--green-border);
    color: var(--green);

    .status-icon { background: rgba(16,185,129,0.12); }
  }

  &--warn {
    background: var(--amber-dim);
    border-color: var(--amber-border);
    color: var(--amber);

    .status-icon { background: rgba(217,119,6,0.12); }
  }

  &__left {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  &__label {
    font-size: 11px;
    font-weight: 600;
    letter-spacing: 0.06em;
    text-transform: uppercase;
    opacity: 0.7;
    margin-bottom: 2px;
  }

  &__text {
    font-size: 13.5px;
    font-weight: 500;

    strong { font-family: var(--font-mono); font-weight: 700; }
  }

  &__counts {
    display: flex;
    gap: 8px;
    flex-wrap: wrap;
  }
}

.status-icon {
  width: 36px;
  height: 36px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.count-chip {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 12px;
  border-radius: var(--r-pill);
  border: 1px solid;
  cursor: pointer;
  transition: opacity 0.15s;

  &:hover { opacity: 0.75; }

  &--draft     { background: var(--bg-muted);   color: var(--text-2); border-color: var(--border-hover); }
  &--published { background: var(--green-dim);  color: var(--green);  border-color: var(--green-border); }
  &--archived  { background: var(--bg-muted);   color: var(--text-3); border-color: var(--border); }
}

// ── 标签页 + 筛选栏 ──────────────────────────────────────────
.tab-filter-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 0 16px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.tab-group {
  display: flex;
  gap: 0;
}

.tab-item {
  padding: 12px 16px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;

  &:hover { color: var(--text-1); }

  &.active {
    color: var(--indigo);
    border-bottom-color: var(--indigo);
    font-weight: 600;
  }
}

.filter-group {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 10px 0;
  flex-wrap: wrap;
}

// ── 展开面板 ─────────────────────────────────────────────────
.expand-panel {
  padding: 16px 20px;
  background: var(--bg-muted);
  border-top: 1px solid var(--border);
}

.score-pills { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }

.score-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--r-pill);
  background: var(--bg-surface);
  border: 1.5px solid var(--border);
  font-size: 13px;

  &--max {
    background: var(--green-dim);
    border-color: var(--green-border);

    .score-pill__val { color: var(--green); }
  }

  &__opt  { font-weight: 700; color: var(--text-2); }
  &__val  { font-weight: 700; color: var(--text-1); margin-left: 2px; }
  &__unit { font-size: 11px; color: var(--text-3); }
}

.ref-time-pill {
  padding: 5px 12px;
  border-radius: var(--r-pill);
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1.5px solid var(--indigo-border);
  font-size: 13px;
  font-weight: 500;
}

// ── 状态 Badge ───────────────────────────────────────────────
.status-badge {
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--draft     { background: var(--bg-muted);   color: var(--text-2); border-color: var(--border-hover); }
  &--published { background: var(--green-dim);  color: var(--green);  border-color: var(--green-border); }
  &--archived  { background: var(--bg-muted);   color: var(--text-3); border-color: var(--border); }
}

// ── 类型 Badge ───────────────────────────────────────────────
.type-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &.type--open { background: var(--amber-dim);   color: var(--amber);  border-color: var(--amber-border); }
  &.type--std  { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); }
}

</style>
