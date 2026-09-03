<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemConfigApi } from '../../api'
import type { SystemConfig } from '../../types'

const loading = ref(false)
const configs = ref<SystemConfig[]>([])
const editDialog = ref(false)
const editItem = ref<SystemConfig | null>(null)
const editValue = ref('')

async function load() {
  loading.value = true
  try {
    const res = await systemConfigApi.getList()
    configs.value = res.data?.configs || []
  } finally { loading.value = false }
}

function openEdit(row: SystemConfig) {
  editItem.value = { ...row }
  editValue.value = row.value
  editDialog.value = true
}

async function handleSave() {
  if (!editItem.value) return
  try {
    await systemConfigApi.update(editItem.value.key, editValue.value)
    ElMessage.success(`参数已更新，立即生效（无需重启）`)
    editDialog.value = false
    load()
  } catch {}
}

const categoryMap: Record<string, string> = {
  active_llm_provider: 'LLM配置',
  active_embedding_provider: 'LLM配置',
  embedding_model: 'LLM配置',
  embedding_dimensions: 'LLM配置',
  chat_max_rounds: 'AI对话',
  proactive_max_count: 'AI对话',
  strategy_switch_threshold: 'AI对话',
  session_max_token_budget: 'AI对话',
  rag_timeout_sec: 'RAG配置',
  rag_topk_questions: 'RAG配置',
  rag_topk_strategies: 'RAG配置',
  rag_similarity_threshold: 'RAG配置',
}

function getCategory(key: string) { return categoryMap[key] || '其他' }

import { computed } from 'vue'
const grouped = computed(() => {
  const g: Record<string, SystemConfig[]> = {}
  configs.value.forEach(c => {
    const cat = getCategory(c.key)
    if (!g[cat]) g[cat] = []
    g[cat].push(c)
  })
  return g
})

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>系统参数配置</h2>
      <el-tag type="success">所有修改立即生效（无需重启）</el-tag>
    </div>

    <div v-loading="loading">
      <div v-for="(items, cat) in grouped" :key="cat" class="card" style="margin-bottom:16px">
        <h3 style="font-size:14px;color:#6B7280;margin-bottom:12px;border-bottom:1px solid #F3F4F6;padding-bottom:8px">{{ cat }}</h3>
        <el-table :data="items" stripe :show-header="false">
          <el-table-column prop="key" label="参数键" width="280">
            <template #default="{ row }">
              <code style="font-size:13px;color:#1D4ED8;background:#EFF6FF;padding:2px 6px;border-radius:4px">{{ row.key }}</code>
            </template>
          </el-table-column>
          <el-table-column prop="value" label="当前值" width="160">
            <template #default="{ row }">
              <span style="font-weight:600;color:#111827">{{ row.value }}</span>
            </template>
          </el-table-column>
          <el-table-column prop="description" label="说明" />
          <el-table-column label="操作" width="80" fixed="right">
            <template #default="{ row }">
              <el-button size="small" @click="openEdit(row)">修改</el-button>
            </template>
          </el-table-column>
        </el-table>
      </div>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialog" title="修改系统参数" width="480px">
      <el-descriptions :column="1" border v-if="editItem">
        <el-descriptions-item label="参数键">
          <code style="color:#1D4ED8">{{ editItem.key }}</code>
        </el-descriptions-item>
        <el-descriptions-item label="当前值">{{ editItem.value }}</el-descriptions-item>
        <el-descriptions-item label="说明">{{ editItem.description }}</el-descriptions-item>
      </el-descriptions>
      <el-form style="margin-top:16px">
        <el-form-item label="新值">
          <el-input v-model="editValue" placeholder="输入新的参数值..." />
        </el-form-item>
      </el-form>
      <el-alert type="warning" :closable="false" title="修改后立即对新请求生效，旧缓存5分钟内自动清除" style="margin-top:8px" />
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>
