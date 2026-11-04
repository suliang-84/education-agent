<template>
  <div class="page-root" v-loading="loading">
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="$router.push('/students')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <el-button @click="handleSave" :loading="saving">
        <SvgIcon v-if="!saving" name="save" :size="14" style="margin-right:4px" />
        保存信息
      </el-button>
    </div>

    <div>

      <!-- 💬 个人洞察摘要（可编辑） -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />个人洞察摘要</span>
          </div>
        </div>
        <el-input
          v-model="editableInsight"
          type="textarea"
          :rows="6"
          placeholder="一段概括这位学生特点的文字：兴趣爱好、学习 / 类比偏好、近期状态等。AI 助教聊天累积后会自动更新这段文字，你也可以直接修改，修改后点右上角「保存」；助教聊天时会参考它..."
        />
      </div>

      <!-- 📚 学习信息摘要（只读） -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />学习信息摘要</span>
          </div>
          <span class="block-note">训练会话结束后、五力测试完成后异步更新</span>
        </div>
        <div class="prompt-preview" v-if="summary">{{ summary.learning_summary }}</div>
        <div class="empty-tip" v-else>暂无学习信息摘要</div>
      </div>

      <!-- 🔗 完整 Prompt 预览 -->
      <div class="surface section-block">
        <div class="section-hd">
          <div class="block-hd__left">
            <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />当前用于 AI 助教的完整 System Prompt 预览</span>
          </div>
        </div>
        <div v-if="summary" class="prompt-preview">{{ summary.full_prompt_preview }}</div>
        <div v-else class="empty-tip">暂无 Prompt 内容</div>
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

const student        = ref<StudentDetail | null>(null)
const summary        = ref<StudentAiPromptSummary | null>(null)

const editableInsight  = ref('')

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
  if (saving.value || loading.value) return
  saving.value = true
  try {
    await studentApi.updateAiPromptSummary(Number(route.params.id), {
      personal_insight: editableInsight.value,
    })
    await loadSummary()
    ElMessage.success('个人洞察摘要已保存')
  } finally { saving.value = false }
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

  // 亮色主题：浅灰底 + 深色字（同其它页面的只读文本框），不再是深色块
  [data-theme="light"] & {
    background: var(--bg-muted);
    color: var(--text-1);
  }
}
</style>
