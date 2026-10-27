<template>
  <div class="page-root">
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="$router.push('/students')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <el-button @click="handleRegenerate" :loading="regenerating">重新生成学习摘要</el-button>
      <button class="btn-pink" type="button" @click="handleSave" :disabled="saving || loading">
        <SvgIcon name="save" :size="13" style="margin-right:4px" />
        保存
      </button>
    </div>

    <div v-loading="loading">

      <!-- 📚 学习信息摘要（只读） -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />学习信息摘要</span>
            <span class="block-badge block-badge--auto">系统自动生成</span>
          </div>
          <span class="block-note">训练会话结束后、五力测试完成后异步更新</span>
        </div>
        <div class="summary-text readonly-text" v-if="summary">{{ summary.learning_summary }}</div>
        <div class="empty-tip" v-else>暂无学习信息摘要</div>
      </div>

      <!-- 💬 个人洞察摘要（可编辑） -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />个人洞察摘要</span>
            <span class="block-badge block-badge--editable">AI 提取 · 管理员可编辑</span>
          </div>
        </div>
        <el-input
          v-model="editableInsight"
          type="textarea"
          :rows="6"
          placeholder="AI 从对话中自动提取并更新，管理员也可手动补充或修正..."
          style="margin-top:8px"
        />
        <el-button
          size="small"
          style="margin-top:10px"
          @click="showAddInsight = true"
        >
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
          手动补充信息
        </el-button>
      </div>

      <!-- 🔗 完整 Prompt 预览 -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />当前用于 AI 助教的完整 System Prompt 预览</span>
          </div>
          <el-button text size="small" style="color:var(--indigo)" @click="promptExpanded = !promptExpanded">
            {{ promptExpanded ? '收起' : '展开查看' }}
          </el-button>
        </div>
        <div v-if="promptExpanded && summary" class="prompt-preview">{{ summary.full_prompt_preview }}</div>
        <div v-else-if="!promptExpanded" class="prompt-collapsed">点击「展开查看」查看合并后的完整 Prompt 文本（只读）</div>
      </div>

      <!-- 📋 洞察条目历史记录 -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />洞察条目历史记录</span>
          </div>
        </div>
        <div class="insight-list">
          <div v-for="entry in insightEntries" :key="entry.id" class="insight-entry">
            <div class="insight-entry__meta">
              <span class="insight-date">{{ formatDate(entry.created_at) }}</span>
              <span class="insight-source" :class="entry.source === 'AI' ? 'source--ai' : 'source--admin'">
                {{ entry.source === 'AI' ? 'AI提取' : '管理员' }}
              </span>
            </div>
            <div class="insight-entry__content">{{ entry.content }}</div>
          </div>
          <div class="empty-tip" v-if="insightEntries.length === 0">暂无洞察记录</div>
        </div>
      </div>

    </div>

    <!-- 手动补充洞察弹窗 -->
    <el-dialog v-model="showAddInsight" title="手动补充洞察信息" width="480px" :close-on-click-modal="false">
      <div style="font-size:13.5px;color:var(--text-2);margin-bottom:14px;line-height:1.6">
        新增一条洞察条目，来源将标记为「管理员」，写入历史记录并纳入个人洞察摘要。
      </div>
      <el-input
        v-model="newInsightContent"
        type="textarea"
        :rows="4"
        placeholder="如：学生提到近期有升学压力，建议AI助教适度减少学业强度，多给正向鼓励..."
      />
      <template #footer>
        <el-button @click="showAddInsight = false">取消</el-button>
        <el-button type="primary" :disabled="!newInsightContent.trim()" :loading="addingInsight" @click="handleAddInsight">
          确认补充
        </el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studentApi } from '@/api'
import type { StudentDetail, StudentAiPromptSummary, PromptInsightEntry } from '@/types'
import { formatDate } from '@/utils/format'

const route = useRoute()

const loading      = ref(false)
const saving       = ref(false)
const regenerating = ref(false)
const addingInsight = ref(false)

const student        = ref<StudentDetail | null>(null)
const summary        = ref<StudentAiPromptSummary | null>(null)
const insightEntries = ref<PromptInsightEntry[]>([])

const editableInsight  = ref('')
const promptExpanded   = ref(false)
const showAddInsight   = ref(false)
const newInsightContent = ref('')

async function loadAll() {
  loading.value = true
  try {
    const [s, sum, entries] = await Promise.all([
      studentApi.getOne(Number(route.params.id)),
      studentApi.getAiPromptSummary(Number(route.params.id)),
      studentApi.getInsightEntries(Number(route.params.id)),
    ])
    student.value        = s
    summary.value        = sum
    insightEntries.value = entries
    editableInsight.value = sum.personal_insight
  } finally { loading.value = false }
}

async function loadSummary() {
  const sum = await studentApi.getAiPromptSummary(Number(route.params.id))
  summary.value = sum
  editableInsight.value = sum.personal_insight
}

async function handleSave() {
  saving.value = true
  try {
    await studentApi.updateAiPromptSummary(Number(route.params.id), {
      personal_insight: editableInsight.value,
    })
    await loadSummary()
    ElMessage.success('个人洞察摘要已保存')
  } finally { saving.value = false }
}

async function handleRegenerate() {
  regenerating.value = true
  try {
    await studentApi.regenerateLearningsummary(Number(route.params.id))
    await loadSummary()
    ElMessage.success('学习信息摘要已重新生成')
  } finally { regenerating.value = false }
}

async function handleAddInsight() {
  if (!newInsightContent.value.trim()) return
  addingInsight.value = true
  try {
    await studentApi.addInsightEntry(Number(route.params.id), {
      content: newInsightContent.value.trim(),
      insight_type: 'other',
    })
    insightEntries.value = await studentApi.getInsightEntries(Number(route.params.id))
    showAddInsight.value = false
    newInsightContent.value = ''
    ElMessage.success('洞察条目已补充')
  } finally { addingInsight.value = false }
}

onMounted(loadAll)
</script>

<style lang="scss" scoped>
// ── 顶部操作栏（与训练题审核页一致）────────────────────────
.page-root {
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

.form-topbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

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

// ── 摘要卡片区块 ─────────────────────────────────────────────
.section-block {
  padding: 5px 15px 15px;
  margin-bottom: 10px;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;

  [data-theme="dark"] & {
    background: #1a1a1a !important;
    border-color: #202020 !important;
  }
}

.block-hd__left {
  display: flex;
  align-items: center;
  gap: 8px;
}

.block-badge {
  font-size: 11.5px;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: var(--r-pill);
  border: 1px solid;

  &--auto     { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); }
  &--editable { background: var(--green-dim);    color: var(--green);  border-color: var(--green-border); }
}

.block-note {
  font-size: 12px;
  color: var(--text-3);
}

// ── 摘要文本区域 ─────────────────────────────────────────────
.summary-text {
  font-size: 13.5px;
  color: var(--text-1);
  line-height: 1.75;
  white-space: pre-wrap;
  word-break: break-word;
}

.readonly-text {
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 14px 16px;
}

.empty-tip {
  font-size: 13px;
  color: var(--text-3);
  padding: 12px 0;
}

// ── Prompt 预览 ───────────────────────────────────────────────
.prompt-preview {
  background: #1E2030;
  border-radius: 4px;
  padding: 16px 18px;
  font-family: var(--font-mono);
  font-size: 12.5px;
  color: #A9B1D6;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
  max-height: 360px;
  overflow-y: auto;
  margin-top: 8px;
}

.prompt-collapsed {
  font-size: 13px;
  color: var(--text-3);
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 14px 16px;
  cursor: default;
}

// ── 洞察条目历史 ─────────────────────────────────────────────
.insight-list {
  display: flex;
  flex-direction: column;
  gap: 1px;
}

.insight-entry {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 12px 0;
  border-bottom: 1px solid var(--border);

  &:last-child { border-bottom: none; }

  &__meta {
    display: flex;
    flex-direction: column;
    align-items: flex-start;
    gap: 4px;
    flex-shrink: 0;
    min-width: 130px;
  }

  &__content {
    font-size: 13.5px;
    color: var(--text-1);
    line-height: 1.6;
    flex: 1;
  }
}

.insight-date {
  font-size: 12px;
  color: var(--text-3);
  font-family: var(--font-mono);
}

.insight-source {
  font-size: 11px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: 4px;
  border: 1px solid;

  &.source--ai    { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); }
  &.source--admin { background: var(--purple-dim);   color: var(--purple); border-color: var(--purple-border); }
}
</style>
