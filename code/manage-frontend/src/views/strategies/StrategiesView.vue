<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { strategyApi } from '../../api'
import type { Strategy } from '../../types'

const loading = ref(false)
const strategies = ref<Strategy[]>([])
const editDialog = ref(false)
const editForm = reactive({ strategy_id: '', default_priority: 1, description: '', is_active: true })

const powerLabelMap: Record<string, string> = {
  INSIGHT: '洞察力', STRUCTURE: '建构力', INFERENCE: '推演力',
  ADAPTATION: '调适力', TRANSFER: '迁移力',
}

async function load() {
  loading.value = true
  try {
    const res = await strategyApi.list()
    strategies.value = res.data?.list || []
  } finally { loading.value = false }
}

function openEdit(row: Strategy) {
  Object.assign(editForm, { strategy_id: row.strategy_id, default_priority: row.default_priority, description: row.description, is_active: row.is_active })
  editDialog.value = true
}

async function handleSave() {
  await strategyApi.update(editForm.strategy_id, { default_priority: editForm.default_priority, description: editForm.description, is_active: editForm.is_active })
  ElMessage.success('策略配置已更新')
  editDialog.value = false
  load()
}

async function toggleActive(row: Strategy) {
  await strategyApi.update(row.strategy_id, { is_active: !row.is_active })
  ElMessage.success(row.is_active ? '策略已禁用' : '策略已启用')
  load()
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>启发策略管理</h2>
      <el-text type="info">共 {{ strategies.length }} 种策略，已启用 {{ strategies.filter(s=>s.is_active).length }} 种</el-text>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="strategies" v-loading="loading" stripe>
        <el-table-column prop="default_priority" label="优先级" width="70" align="center">
          <template #default="{ row }">
            <el-tag type="info" size="small">{{ row.default_priority }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="strategy_id" label="策略ID" width="180">
          <template #default="{ row }">
            <code style="font-size:12px;color:#1D4ED8;background:#EFF6FF;padding:2px 6px;border-radius:4px">{{ row.strategy_id }}</code>
          </template>
        </el-table-column>
        <el-table-column prop="strategy_name" label="策略名称" width="130" />
        <el-table-column label="适用五力" min-width="200">
          <template #default="{ row }">
            <span v-for="p in row.applicable_powers" :key="p"
              class="power-tag" :class="p" style="margin-right:4px">
              {{ powerLabelMap[p] }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="策略描述" min-width="200">
          <template #default="{ row }">
            <span style="font-size:13px;color:#374151">{{ row.description }}</span>
          </template>
        </el-table-column>
        <el-table-column label="示例话术" min-width="200">
          <template #default="{ row }">
            <el-tooltip :content="row.example_phrase" placement="top">
              <span style="font-size:12px;color:#6B7280;cursor:default">{{ row.example_phrase?.slice(0, 30) }}...</span>
            </el-tooltip>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="80" align="center">
          <template #default="{ row }">
            <el-switch :model-value="row.is_active" @change="toggleActive(row)" size="small" />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog v-model="editDialog" title="编辑策略配置" width="480px">
      <el-form :model="editForm" label-position="top">
        <el-form-item label="策略ID">
          <el-input :value="editForm.strategy_id" disabled />
        </el-form-item>
        <el-form-item label="默认优先级（数字越小优先级越高）">
          <el-input-number v-model="editForm.default_priority" :min="1" :max="20" />
        </el-form-item>
        <el-form-item label="策略描述（≤50字，会注入AI上下文）">
          <el-input v-model="editForm.description" type="textarea" :rows="3" :maxlength="50" show-word-limit />
        </el-form-item>
        <el-form-item label="启用状态">
          <el-switch v-model="editForm.is_active" active-text="启用" inactive-text="禁用" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
