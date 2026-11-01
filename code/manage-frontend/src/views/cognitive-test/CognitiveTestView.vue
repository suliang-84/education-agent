<template>
  <div class="page-root">


    <!-- ── 测试状态看板 ── -->
    <!-- ── 筛选栏 ── -->
    <div class="inner-toolbar">
      <el-input v-model="searchText" placeholder="搜索题目..." clearable size="small" style="flex:1;min-width:130px;max-width:260px">
        <template #prefix>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
          </svg>
        </template>
      </el-input>
      <el-select v-model="filterActive" placeholder="状态" clearable size="small" style="width:120px">
        <el-option label="已启用" value="on" />
        <el-option label="已停用" value="off" />
      </el-select>
      <div style="flex:1" />
      <el-button class="btn-import" style="color:var(--green);padding:0 8px !important" :loading="batchActivating" @click="handleBatchSetStatus(true)">
        <SvgIcon v-if="!batchActivating" name="play" :size="15" style="margin-right:5px" />
        批量启用
      </el-button>
      <el-button class="btn-import" style="color:var(--red);padding:0 8px !important" :loading="batchDeactivating" @click="handleBatchSetStatus(false)">
        <SvgIcon v-if="!batchDeactivating" name="pause" :size="15" style="margin-right:5px" />
        批量停用
      </el-button>
      <el-button type="primary" @click="router.push('/cognitive-test/create')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        新增题目
      </el-button>
    </div>

    <div class="surface surface--table cognitive-surface" style="padding:0" v-loading="loading">

      <!-- ── 列表表格 ── -->
      <el-table
        ref="tableRef"
        :data="filteredQuestions"
        row-key="id"
        style="width:100%"
        @selection-change="(rows: CognitiveQuestion[]) => selected = rows"
      >
        <el-table-column type="selection" width="46" />

        <!-- 展开行：题目 + 答案 + 权重 -->
        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <!-- 题目 -->
              <div class="expand-section">
                <div class="expand-section__title">
                  <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题目内容
                </div>
                <div class="expand-stem">{{ row.stem }}</div>
              </div>

              <!-- 题目描述 -->
              <div v-if="row.description" class="expand-section">
                <div class="expand-section__title">
                  <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />题目描述
                </div>
                <div class="expand-desc">{{ row.description }}</div>
              </div>

              <!-- 答案列表 -->
              <div class="expand-section">
                <div class="expand-section__title">
                  <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />答案配置
                </div>
                <div class="expand-answers">
                  <div v-for="(answer, idx) in row.answers" :key="idx" class="expand-answer">
                    <div class="expand-answer__header">
                      <span class="expand-key">{{ answer.key || String.fromCharCode(65 + idx) }}</span>
                      <span class="expand-text">{{ answer.text }}</span>
                    </div>
                    <div class="expand-weights">
                      <span v-for="p in powers" :key="p" class="expand-weight-chip">
                        <span class="power-dot-xs" :class="`power-dot-xs--${p}`" />
                        {{ FivePowerLabels[p as FivePower] }}({{ answer.force_weights?.[p as FivePower] ?? 0 }})
                      </span>
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </template>
        </el-table-column>

        <!-- 序号 -->
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            <span class="num" style="color:var(--text-3);font-size:12px">{{ $index + 1 }}</span>
          </template>
        </el-table-column>

        <!-- 题目 -->
        <el-table-column label="题目" min-width="360">
          <template #default="{ row }">
            <el-tooltip :content="row.stem" placement="top-start" :show-after="300" effect="light">
              <span class="stem-text">{{ row.stem }}</span>
            </el-tooltip>
          </template>
        </el-table-column>

        <!-- 状态 -->
        <el-table-column label="状态" width="100" align="center">
          <template #default="{ row }">
            <span class="active-flag" :class="row.status === 'published' ? 'active-flag--on' : 'active-flag--off'">
              <SvgIcon :name="row.status === 'published' ? 'check_circle' : 'close_circle'" :size="16" />
              {{ CognitiveQuestionStatusLabels[row.status as CognitiveQuestionStatus] }}
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
        <el-table-column label="操作" width="120" fixed="right">
          <template #default="{ row }">
            <!-- 已启用 -->
            <template v-if="row.status === 'published'">
              <el-button text size="small" style="color:var(--amber)" @click="confirmArchive(row)">
                <SvgIcon name="pause" :size="18" color="var(--amber)" title="停用" />
              </el-button>
            </template>
            <!-- 已停用 -->
            <template v-else>
              <el-button text size="small" style="color:var(--color-primary)" @click="router.push(`/cognitive-test/${row.id}/edit`)">
                <SvgIcon name="edit" :size="18" color="var(--color-primary)" title="编辑" />
              </el-button>
              <el-button text size="small" style="color:var(--green)" @click="confirmRepublish(row)">
                <SvgIcon name="play" :size="18" color="var(--green)" title="启用" />
              </el-button>
              <el-button text size="small" style="color:var(--red)" @click="confirmDelete(row)">
                <SvgIcon name="delete" :size="18" color="var(--red)" title="删除" />
              </el-button>
            </template>
          </template>
        </el-table-column>

      </el-table>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cognitiveApi } from '@/api'
import type { CognitiveBatchResult } from '@/api/cognitive'
import type { CognitiveQuestion, FivePower, CognitiveQuestionStatus } from '@/types'
import { FivePowerLabels, CognitiveQuestionStatusLabels } from '@/types'

const router = useRouter()
const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 状态 ──────────────────────────────────────────────────────
const loading = ref(false)
const allQuestions = ref<CognitiveQuestion[]>([])

// 筛选
// 启用状态筛选：on 已启用 = published；off 已停用 = archived（测试题只有这两态）
const filterActive = ref<'' | 'on' | 'off'>('')
const searchText = ref('')


// ── 计算属性 ──────────────────────────────────────────────────
const publishedCount = computed(() => allQuestions.value.filter(q => q.status === 'published').length)
const archivedCount = computed(() => allQuestions.value.filter(q => q.status === 'archived').length)

const filteredQuestions = computed(() => {
  let list = allQuestions.value

  // 启用状态筛选
  if (filterActive.value) {
    const target = filterActive.value === 'on' ? 'published' : 'archived'
    list = list.filter(q => q.status === target)
  }

  // 搜索
  if (searchText.value.trim()) {
    const kw = searchText.value.toLowerCase()
    list = list.filter(q => q.stem?.toLowerCase().includes(kw))
  }

  return list
})

// ── 初始化 ────────────────────────────────────────────────────
async function loadData() {
  loading.value = true
  try {
    const res = await cognitiveApi.getList()
    allQuestions.value = res.list
  } finally {
    loading.value = false
  }
}
onMounted(loadData)

// ── 批量启用 / 停用（后端批量接口，一次请求）──────────────────
// 测试题只有两态：启用 = archived → published；停用 = published → archived
const tableRef = ref<{ clearSelection: () => void } | null>(null)
const selected = ref<CognitiveQuestion[]>([])
const batchActivating = ref(false)
const batchDeactivating = ref(false)
const BATCH_MAX = 200          // 与后端 CBATCH-002 一致：单次最多 200 条
const PUBLISH_LIMIT = 20       // 与后端一致：已启用上限
const TEST_MIN_PUBLISHED = 10  // 已启用 ≥ 10 道测试功能可用

function notifyBatchResult(res: CognitiveBatchResult, doneText: string) {
  const byCode = (code: string) => res.items.filter(i => i.reason_code === code).length
  const limited = byCode('PUBLISH_LIMIT_REACHED')
  const skipped = res.skipped_count - limited
  const notes = [
    limited > 0 ? `${limited} 道因已启用题目达到上限（${PUBLISH_LIMIT}/${PUBLISH_LIMIT}）未启用` : '',
    skipped > 0 ? `${skipped} 道状态不符或已处于目标状态，已跳过` : '',
    res.failed_count > 0 ? `${res.failed_count} 道处理失败，请稍后重试` : '',
    !res.test_available ? `已启用不足 ${TEST_MIN_PUBLISHED} 道，测试功能已暂停` : '',
  ].filter(Boolean)
  if (res.skipped_count === 0 && res.failed_count === 0 && res.test_available) {
    ElMessage.success(`${doneText} ${res.success_count} 道题目`)
  } else {
    ElMessage.warning(`${doneText} ${res.success_count} 道题目${notes.length ? '；' + notes.join('；') : ''}`)
  }
}

async function handleBatchSetStatus(toActive: boolean) {
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
  const sourceStatus = toActive ? 'archived' : 'published'
  const targets = selected.value.filter(q => q.status === sourceStatus)
  const skipped = selected.value.length - targets.length
  if (targets.length === 0) {
    ElMessage.warning(toActive
      ? '所选题目中不包含已停用的题目，仅已停用题目可以启用'
      : '所选题目中不包含已启用的题目，仅已启用题目可以停用')
    return
  }
  let slotNote = ''
  if (toActive) {
    const slots = PUBLISH_LIMIT - publishedCount.value
    if (slots <= 0) {
      ElMessage.warning(`已启用题目已达上限（${PUBLISH_LIMIT}/${PUBLISH_LIMIT}），请先停用部分题目`)
      return
    }
    if (targets.length > slots) slotNote = `当前剩余启用名额 ${slots} 个，将按勾选顺序启用前 ${slots} 道，其余将被跳过。`
  } else {
    const after = publishedCount.value - targets.length
    if (after < TEST_MIN_PUBLISHED) slotNote = `停用后已启用题目将不足 ${TEST_MIN_PUBLISHED} 道，学生测试功能会暂停。`
  }
  const msg = (skipped > 0
    ? `已勾选 ${selected.value.length} 道题目，其中 ${targets.length} 道将被${verb}；其余 ${skipped} 道状态不符，会被跳过。`
    : `已勾选 ${targets.length} 道题目，将全部${verb}。`)
    + slotNote + '是否继续？'
  const confirmed = await ElMessageBox.confirm(msg, `批量${verb}确认`, {
    confirmButtonText: `确认${verb}`, cancelButtonText: '取消', type: toActive ? 'info' : 'warning',
  }).then(() => true, () => false)
  if (!confirmed) return

  const flag = toActive ? batchActivating : batchDeactivating
  flag.value = true
  try {
    // 提交勾选的全部 ID，资格校验与状态变更由后端完成
    const ids = selected.value.map(q => q.id)
    const res = toActive ? await cognitiveApi.batchActivate(ids) : await cognitiveApi.batchDeactivate(ids)
    notifyBatchResult(res, `已${verb}`)
    tableRef.value?.clearSelection()
    await loadData()
  } finally { flag.value = false }
}

// ── 启用 / 停用 / 删除（确认弹窗样式与训练题录入「发布」确认一致）──────────
async function confirmRepublish(row: CognitiveQuestion) {
  const after = publishedCount.value + 1
  await ElMessageBox.confirm(
    `确认启用题目 #${row.id}？启用后该题将加入测试题池，当前已启用 ${publishedCount.value} 道，启用后将达 ${after} 道。\n\n` +
    (after === 10 ? '启用后将达到 10 道，测试功能将自动开启。' : '启用后题目内容的修改将立即影响新测试会话的评分计算。'),
    '确认启用',
    { confirmButtonText: '确认启用', cancelButtonText: '取消', type: 'info' }
  )
  await cognitiveApi.publish(row.id)
  row.status = 'published'
  ElMessage.success('题目已启用，已加入测试题池')
}

async function confirmArchive(row: CognitiveQuestion) {
  const left = publishedCount.value - 1
  await ElMessageBox.confirm(
    `确认停用题目 #${row.id}？停用后该题不再参与新测试组卷，当前已启用 ${publishedCount.value} 道，停用后将剩 ${left} 道。\n\n` +
    (left < 10 ? '停用后已启用题目将不足 10 道，测试功能将暂停，请尽快启用更多题目。' : `停用后仍有 ${left} 道题目，测试功能保持正常。`),
    '确认停用',
    { confirmButtonText: '确认停用', cancelButtonText: '取消', type: 'warning' }
  )
  await cognitiveApi.archive(row.id)
  row.status = 'archived'
  ElMessage.success('题目已停用')
}

async function confirmDelete(row: CognitiveQuestion) {
  await ElMessageBox.confirm(
    `确认删除题目 #${row.id}？删除后该题目将从列表中移除，且无法恢复，历史测试成绩不受影响。`,
    '确认删除',
    { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error' }
  )
  await cognitiveApi.delete(row.id)
  const idx = allQuestions.value.findIndex(q => q.id === row.id)
  if (idx !== -1) allQuestions.value.splice(idx, 1)
  ElMessage.success('题目已删除')
}
</script>

<style lang="scss" scoped>
// ── 主卡片：flex column，table body 内部滚动 ─────────────────
.cognitive-surface {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;

  // el-table 撑满剩余高度
  :deep(.el-table) {
    flex: 1;
    min-height: 0;
    overflow: hidden;
  }
  :deep(.el-table__inner-wrapper) {
    display: flex;
    flex-direction: column;
    height: 100%;
  }
  :deep(.el-table__header-wrapper) { flex-shrink: 0; }
  :deep(.el-table__body-wrapper) {
    flex: 1;
    min-height: 0;
    overflow-y: auto;
  }
}

// ── 题目列 ───────────────────────────────────────────────────
.stem-text {
  font-size: 13.5px;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  display: block;
  max-width: 100%;
}

// ── 展开面板 ─────────────────────────────────────────────────
.expand-panel {
  padding-bottom: 10px;
  background: var(--bg-surface);
  display: flex;
  flex-direction: column;
}

// 展开行不跟随表格行 hover 变色
:deep(.el-table__expanded-cell) {
  background: var(--bg-surface) !important;
}

.expand-section {
  background: var(--bg-surface);

  &__title {
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 700;
    color: var(--color-primary);
    padding: 8px 0;
  }
}

.expand-stem {
  font-size: 13px;
  color: var(--text-1);
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-word;
}

.expand-desc {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 6px;
}

.expand-answers {
  display: flex;
  flex-direction: column;
  gap: 10px;
}

.expand-answer {
  border: none;
  border-radius: var(--r-xs);
  overflow: hidden;

  &__header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 12px 14px 8px;
    background: transparent;
  }
}

// 背景同 .preview-item（QuestionFormView）：蓝色渐变（按约 90px 走完后保持末端色），无边框、无外发光
[data-theme="light"] .expand-answer {
  background: linear-gradient(90deg, rgba(94, 141, 249, 0.20) 0, rgba(94, 141, 249, 0.05) 90px, rgba(94, 141, 249, 0.05)), #ffffff;
}

[data-theme="dark"] .expand-answer {
  background: linear-gradient(90deg, rgba(94, 141, 249, 0.24) 0, rgba(94, 141, 249, 0.07) 90px, rgba(94, 141, 249, 0.07));
}

.expand-key {
  width: 26px;
  height: 26px;
  border-radius: 4px;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

[data-theme="dark"] .expand-key { color: #0D0D0D; }

.expand-text {
  flex: 1;
  font-size: 13px;
  color: var(--text-1);
  line-height: 1.5;
}

.expand-weights {
  display: flex;
  flex-direction: row;
  gap: 40px;
  flex-wrap: wrap;
  padding: 4px 14px 12px;
  background: transparent;
}

.expand-weight-chip {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 12.5px;
  color: var(--text-2);
  white-space: nowrap;
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

// 深色主题：indigo 变为亮黄绿，答案 key 徽标文字需改为深色
:global([data-theme="dark"]) .expand-key {
  color: #0D0D0D;
}
</style>
