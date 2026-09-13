<template>
  <div class="page-root">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/students')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回用户管理
        </el-button>
        <div>
          <h1 class="page-title">
            <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="vertical-align:middle;margin-right:6px;color:var(--indigo)">
              <path stroke-linecap="round" stroke-linejoin="round" d="M8.625 12a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H8.25m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0H12m4.125 0a.375.375 0 11-.75 0 .375.375 0 01.75 0zm0 0h-.375M21 12c0 4.556-4.03 8.25-9 8.25a9.764 9.764 0 01-2.555-.337A5.972 5.972 0 015.41 20.97a5.969 5.969 0 01-.474-.065 4.48 4.48 0 00.978-2.025c.09-.457-.133-.901-.467-1.226C3.93 16.178 3 14.189 3 12c0-4.556 4.03-8.25 9-8.25s9 3.694 9 8.25z"/>
            </svg>
            {{ student?.nickname || '学生' }}（ID: {{ route.params.id }}）的 AI 助教提示词摘要
          </h1>
          <p class="page-subtitle" v-if="summary">上次更新：{{ formatDate(summary.updated_at) }}</p>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <el-button @click="handleRegenerate" :loading="regenerating">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M16.023 9.348h4.992v-.001M2.985 19.644v-4.992m0 0h4.992m-4.993 0l3.181 3.183a8.25 8.25 0 0013.803-3.7M4.031 9.865a8.25 8.25 0 0113.803-3.7l3.181 3.182m0-4.991v4.99"/>
          </svg>
          重新生成学习摘要
        </el-button>
        <button class="btn-pink" type="button" @click="handleSave" :disabled="saving || loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
          </svg>
          保存
        </button>
      </div>
    </div>

    <div v-loading="loading">

      <!-- 📚 学习信息摘要（只读） -->
      <div class="surface summary-block">
        <div class="block-hd">
          <div class="block-hd__left">
            <span class="block-icon">📚</span>
            <span class="block-title">学习信息摘要</span>
            <span class="block-badge block-badge--auto">系统自动生成</span>
          </div>
          <span class="block-note">训练会话结束后、五力测试完成后异步更新</span>
        </div>
        <div class="summary-text readonly-text" v-if="summary">{{ summary.learning_summary }}</div>
        <div class="empty-tip" v-else>暂无学习信息摘要</div>
      </div>

      <!-- 💬 个人洞察摘要（可编辑） -->
      <div class="surface summary-block">
        <div class="block-hd">
          <div class="block-hd__left">
            <span class="block-icon">💬</span>
            <span class="block-title">个人洞察摘要</span>
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
      <div class="surface summary-block">
        <div class="block-hd">
          <div class="block-hd__left">
            <span class="block-icon">🔗</span>
            <span class="block-title">当前用于 AI 助教的完整 System Prompt 预览</span>
          </div>
          <el-button text size="small" style="color:var(--indigo)" @click="promptExpanded = !promptExpanded">
            {{ promptExpanded ? '收起' : '展开查看' }}
          </el-button>
        </div>
        <div v-if="promptExpanded && summary" class="prompt-preview">{{ summary.full_prompt_preview }}</div>
        <div v-else-if="!promptExpanded" class="prompt-collapsed">点击「展开查看」查看合并后的完整 Prompt 文本（只读）</div>
      </div>

      <!-- 📋 洞察条目历史记录 -->
      <div class="surface summary-block">
        <div class="block-hd">
          <div class="block-hd__left">
            <span class="block-icon">📋</span>
            <span class="block-title">洞察条目历史记录</span>
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

async function handleSave() {
  saving.value = true
  try {
    const updated = await studentApi.updateAiPromptSummary(Number(route.params.id), {
      personal_insight: editableInsight.value,
    })
    summary.value = updated as StudentAiPromptSummary
    ElMessage.success('个人洞察摘要已保存')
  } finally { saving.value = false }
}

async function handleRegenerate() {
  regenerating.value = true
  try {
    await studentApi.regenerateLearningsummary(Number(route.params.id))
    ElMessage.success('学习信息摘要重新生成任务已提交，约 30 秒后完成，请稍后刷新')
  } finally { regenerating.value = false }
}

async function handleAddInsight() {
  if (!newInsightContent.value.trim()) return
  addingInsight.value = true
  try {
    const entry = await studentApi.addInsightEntry(Number(route.params.id), {
      content: newInsightContent.value.trim(),
    })
    insightEntries.value.unshift(entry)
    showAddInsight.value = false
    newInsightContent.value = ''
    ElMessage.success('洞察条目已补充')
  } finally { addingInsight.value = false }
}

onMounted(loadAll)
</script>

<style lang="scss" scoped>
// ── 摘要卡片区块 ─────────────────────────────────────────────
.summary-block {
  padding: 20px 24px;
  margin-bottom: 14px;
}

.block-hd {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 14px;

  &__left {
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.block-icon {
  font-size: 17px;
}

.block-title {
  font-size: 14px;
  font-weight: 700;
  color: var(--text-1);
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
  border-radius: var(--r-lg);
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
  border-radius: var(--r-lg);
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
  border-radius: var(--r-lg);
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
