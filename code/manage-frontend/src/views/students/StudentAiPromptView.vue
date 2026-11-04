<template>
  <div class="page-root ai-prompt" v-loading="loading">
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="$router.push('/students')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <el-button @click="handleRegenerate" :loading="regenerating">
        <SvgIcon v-if="!regenerating" name="analyse" :size="14" style="margin-right:4px" />
        重新生成学习摘要
      </el-button>
      <button class="btn-pink" type="button" @click="handleSave" :disabled="saving || loading">
        <SvgIcon name="save" :size="13" style="margin-right:4px" />
        保存
      </button>
    </div>

    <div>

      <!-- 📚 学习信息摘要（只读） -->
      <div class="surface section-block learning-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />学习信息摘要</span>
          </div>
          <span class="block-note">训练会话结束后、五力测试完成后异步更新</span>
        </div>
        <div class="summary-text readonly-text learning-text" v-if="summary">{{ summary.learning_summary }}</div>
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
          placeholder="一段概括这位学生特点的文字：兴趣爱好、学习 / 类比偏好、近期状态等。AI 助教聊天累积后会自动更新这段文字，你也可以直接修改，修改后点右上角「保存」；助教聊天时会参考它..."
          style="margin-top:8px"
        />
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

    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studentApi } from '@/api'
import type { StudentDetail, StudentAiPromptSummary } from '@/types'

const route = useRoute()

const loading      = ref(false)
const saving       = ref(false)
const regenerating = ref(false)

const student        = ref<StudentDetail | null>(null)
const summary        = ref<StudentAiPromptSummary | null>(null)

const editableInsight  = ref('')
const promptExpanded   = ref(false)

async function loadAll() {
  loading.value = true
  try {
    const [s, sum] = await Promise.all([
      studentApi.getOne(Number(route.params.id)),
      studentApi.getAiPromptSummary(Number(route.params.id)),
    ])
    student.value        = s
    summary.value        = sum
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

// 只读文本框：与训练题管理详情页的只读文本（stem-display）同样的底色和字色
.readonly-text {
  background: var(--bg-muted);
  border-radius: 4px;
  padding: 14px 16px;

  [data-theme="dark"] & {
    background: #282b31;
    color: #ffffff;
  }
}

// 学习信息摘要：文档式排版，同「训练题管理 → 详情」页的「题目内容」子模块——文字直接排在子模块上，不加灰底文字框
.learning-text {
  font-size: 15px;
  line-height: 1.85;
  background: transparent;
  padding: 4px 0 10px;

  [data-theme="dark"] & { background: transparent; }
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

  [data-theme="dark"] & { background: #282b31; }
}
</style>

<style>
/* 学习信息摘要子模块的云晕：同训练题详情页「题目内容」子模块（左上 + 右下两团，固定大小的椭圆）。
   不加 scoped：选择器要从 html / .content-area 开头，才压得过 style.scss 里的全局玻璃面板规则。
   注意渐变尺寸里不能用 min() / max()（浏览器会判整条 background 无效，云晕不显示）。 */
html[data-theme="dark"] .content-area .page-root.ai-prompt .section-block.learning-block {
  background:
    radial-gradient(ellipse 480px 260px at 6% -6%, rgba(94, 141, 249, 0.22), transparent 72%),
    radial-gradient(ellipse 480px 260px at 104% 106%, rgba(124, 112, 255, 0.15), transparent 72%),
    rgba(14, 17, 22, 0.60) !important;
}
html[data-theme="light"] .content-area .page-root.ai-prompt .section-block.learning-block {
  background:
    radial-gradient(ellipse 480px 260px at 6% -6%, rgba(94, 141, 249, 0.15), transparent 72%),
    radial-gradient(ellipse 480px 260px at 104% 106%, rgba(124, 112, 255, 0.10), transparent 72%),
    rgba(255, 255, 255, 0.74) !important;
}
</style>
