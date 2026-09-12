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
    <div class="status-board" :class="publishedCount >= 10 ? 'status-board--ok' : 'status-board--warn'">
      <div class="status-board__left">
        <div class="status-icon">
          <svg v-if="publishedCount >= 10" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          <svg v-else width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
          </svg>
        </div>
        <div>
          <div class="status-board__label">测试状态</div>
          <div class="status-board__text" v-if="publishedCount >= 10">● 已发布 <strong>{{ publishedCount }}</strong> 道 — 测试功能已就绪，学生可正常参加测试</div>
          <div class="status-board__text" v-else>● 已发布 <strong>{{ publishedCount }}</strong> 道 — ⚠ 不足10道，测试功能已暂停（至少需发布10道）</div>
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
          <el-input v-model="searchText" placeholder="搜索题干..." clearable size="small" style="width:220px">
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

        <!-- 展开行：题干 + 答案 + 权重 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <!-- 题干 -->
              <p class="expand-stem">{{ row.stem }}</p>
              <!-- 题目描述（管理员元数据） -->
              <p v-if="row.description" class="expand-desc">
                <span class="expand-desc__label">题目描述：</span>{{ row.description }}
              </p>
              <!-- 答案列表 -->
              <div class="expand-answers">
                <div v-for="(answer, idx) in row.answers" :key="idx" class="expand-answer">
                  <div class="expand-answer__header">
                    <span class="expand-key">{{ answer.key || String.fromCharCode(65 + idx) }}</span>
                    <span class="expand-text">{{ answer.text }}</span>
                  </div>
                  <div class="expand-weights">
                    <span v-for="p in powers" :key="p" class="expand-weight-chip">
                      <span class="power-dot-xs" :class="`power-dot-xs--${p}`" />
                      {{ FivePowerLabels[p as FivePower] }}
                      <strong class="num">{{ (answer.force_weights?.[p as FivePower] ?? 0).toFixed(2) }}</strong>
                    </span>
                    <span
                      class="expand-sum num"
                      :class="Math.abs(Object.values(answer.force_weights || {}).reduce((s: number, v: number) => s + v, 0) - 1) < 0.02 ? 'expand-sum--ok' : 'expand-sum--err'"
                    >
                      合计 {{ Object.values(answer.force_weights || {}).reduce((s: number, v: number) => s + v, 0).toFixed(2) }}
                    </span>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 题号 -->
        <el-table-column label="#" prop="question_no" width="60" align="center">
          <template #default="{ row }">
            <span class="num" style="font-weight:600;color:var(--indigo)">{{ row.question_no }}</span>
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

        <!-- 答案数 -->
        <el-table-column label="答案数" width="80" align="center">
          <template #default="{ row }">
            <span class="num" style="color:var(--text-2)">{{ row.answers?.length ?? 0 }}</span>
            <span style="color:var(--text-3);font-size:12px"> 项</span>
          </template>
        </el-table-column>

        <!-- 题干摘要 -->
        <el-table-column label="题干摘要" min-width="360">
          <template #default="{ row }">
            <div>
              <p style="color:var(--text-1);font-size:13.5px;line-height:1.5;margin:0">
                {{ row.stem?.substring(0, 60) }}{{ (row.stem?.length ?? 0) > 60 ? '…' : '' }}
              </p>
              <p v-if="row.description" style="color:var(--text-3);font-size:12px;margin:3px 0 0">
                {{ row.description?.substring(0, 40) }}{{ (row.description?.length ?? 0) > 40 ? '…' : '' }}
              </p>
            </div>
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
        <p>当前已发布：<strong class="num">{{ publishedCount }}</strong> 道，发布后将达：<strong class="num">{{ publishedCount + 1 }}</strong> 道</p>
        <div v-if="publishedCount + 1 === 10" style="margin-top:12px;padding:10px 14px;background:var(--green-dim);border:1px solid var(--green-border);border-radius:var(--r-lg);color:var(--green);font-size:13px">
          🎉 发布后将达到10道，测试功能将自动开启！
        </div>
        <div v-else style="margin-top:12px;padding:10px 14px;background:var(--amber-dim);border:1px solid var(--amber-border);border-radius:var(--r-lg);color:var(--amber);font-size:13px">
          ⚠ 发布后题目内容的修改将立即影响新测试会话的评分计算。
        </div>
      </div>
      <template #footer>
        <el-button @click="publishDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="doPublish">确认发布</el-button>
      </template>
    </el-dialog>

    <!-- ── 下架确认弹窗 ── -->
    <el-dialog v-model="archiveDialogVisible" title="确认下架此题目？" width="440px">
      <div style="line-height:1.8;font-size:14px;color:var(--text-2)">
        <p>下架后该题不再参与新测试组卷。</p>
        <p>当前已发布：<strong class="num">{{ publishedCount }}</strong> 道，下架后将剩：<strong class="num">{{ publishedCount - 1 }}</strong> 道</p>
        <div v-if="publishedCount - 1 < 10" style="margin-top:12px;padding:10px 14px;background:var(--amber-dim);border:1px solid var(--amber-border);border-radius:var(--r-lg);color:var(--amber);font-size:13px">
          ⚠ 下架后已发布题目将不足10道，测试功能将暂停，请尽快补充发布。
        </div>
        <div v-else style="margin-top:12px;padding:10px 14px;background:var(--indigo-light);border:1px solid var(--indigo-border);border-radius:var(--r-lg);color:var(--indigo);font-size:13px">
          下架后仍有 {{ publishedCount - 1 }} 道题目，测试功能保持正常。
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

  // 搜索
  if (searchText.value.trim()) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(q => q.stem?.toLowerCase().includes(kw))
  }

  return list
})

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

.expand-stem {
  font-size: 13.5px;
  color: var(--text-1);
  line-height: 1.65;
  margin: 0 0 10px;
}

.expand-desc {
  font-size: 12px;
  color: var(--text-3);
  margin: 0 0 14px;
  padding: 6px 10px;
  background: rgba(79, 70, 229, 0.04);
  border-radius: var(--r-md);
  border-left: 2px solid var(--indigo-border);

  &__label { font-weight: 600; color: var(--text-2); }
}

.expand-answers {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.expand-answer {
  background: var(--bg-surface);
  border-radius: var(--r-lg);
  border: 1px solid var(--border);
  overflow: hidden;

  &__header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 10px 14px;
    background: var(--bg-surface);
  }
}

.expand-key {
  width: 26px;
  height: 26px;
  border-radius: var(--r-sm);
  background: var(--indigo);
  color: #fff;
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.expand-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-1);
  line-height: 1.5;
}

.expand-time {
  font-size: 12px;
  color: var(--indigo);
  background: var(--indigo-light);
  border: 1px solid var(--indigo-border);
  padding: 2px 9px;
  border-radius: var(--r-pill);
  flex-shrink: 0;
}

.expand-weights {
  display: flex;
  align-items: center;
  gap: 6px;
  flex-wrap: wrap;
  padding: 8px 14px;
  background: #F8F9FD;
  border-top: 1px solid var(--border);
}

.expand-weight-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 11.5px;
  color: var(--text-2);
  background: var(--bg-surface);
  border: 1px solid var(--border);
  border-radius: var(--r-pill);
  padding: 2px 8px;

  strong { color: var(--text-1); }
}

.expand-sum {
  margin-left: auto;
  font-size: 12px;
  font-weight: 700;
  padding: 2px 10px;
  border-radius: var(--r-pill);

  &--ok { background: var(--green-dim); color: var(--green); }
  &--err { background: var(--red-dim);  color: var(--red); }
}

// 五力维度小圆点
.power-dot-xs {
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

// ── 状态 Badge ───────────────────────────────────────────────
.status-badge {
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--draft     { background: var(--bg-muted);  color: var(--text-2); border-color: var(--border-hover); }
  &--published { background: var(--green-dim); color: var(--green);  border-color: var(--green-border); }
  &--archived  { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border); }
}

</style>
