<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { annotationApi } from '../../api'
import type { Annotation } from '../../types'

const loading = ref(false)
const annotations = ref<Annotation[]>([])
const total = ref(0)
const selectedIds = ref<number[]>([])
const page = reactive({ current: 1, size: 15 })
const filter = reactive({ status: 'pending', min_conf: 0, max_conf: 1 })

import { reactive } from 'vue'

const powerLabelMap: Record<string, string> = {
  INSIGHT: '洞察力', STRUCTURE: '建构力', INFERENCE: '推演力',
  ADAPTATION: '调适力', TRANSFER: '迁移力',
}

async function load() {
  loading.value = true
  try {
    const res = await annotationApi.list(filter.status, filter.min_conf, filter.max_conf, page.current, page.size)
    annotations.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

async function handleConfirm(row: Annotation) {
  await annotationApi.confirm(row.annotation_id, row.ai_annotation.primary_power, row.ai_annotation.primary_power)
  ElMessage.success('标注已确认')
  load()
}

async function handleBatchConfirm() {
  if (!selectedIds.value.length) { ElMessage.warning('请先选择题目'); return }
  try {
    await ElMessageBox.confirm(`确认批量确认 ${selectedIds.value.length} 条标注？`, '提示', { type: 'warning' })
    await annotationApi.batchConfirm(selectedIds.value, 0.85)
    ElMessage.success('批量确认成功')
    selectedIds.value = []
    load()
  } catch {}
}

function handleSelect(rows: Annotation[]) {
  selectedIds.value = rows.filter(r => r.ai_annotation.confidence >= 0.85).map(r => r.annotation_id)
}

function confidenceColor(v: number) {
  if (v >= 0.85) return '#22C55E'
  if (v >= 0.6) return '#F59E0B'
  return '#EF4444'
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>AI 标注审核</h2>
      <el-button type="primary" @click="handleBatchConfirm" :disabled="!selectedIds.length">
        批量确认置信度≥0.85（已选 {{ selectedIds.length }} 条）
      </el-button>
    </div>

    <div class="filter-bar">
      <el-form inline>
        <el-form-item label="标注状态">
          <el-select v-model="filter.status" style="width:120px" @change="load">
            <el-option label="待审核" value="pending" />
            <el-option label="已确认" value="confirmed" />
            <el-option label="失败" value="failed" />
          </el-select>
        </el-form-item>
        <el-form-item label="置信度范围">
          <el-input-number v-model="filter.min_conf" :min="0" :max="1" :step="0.05" :precision="2" style="width:100px" />
          <span style="margin:0 8px">~</span>
          <el-input-number v-model="filter.max_conf" :min="0" :max="1" :step="0.05" :precision="2" style="width:100px" />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="annotations" v-loading="loading" @selection-change="handleSelect" stripe>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="annotation_id" label="ID" width="80" />
        <el-table-column label="题干摘要" min-width="260">
          <template #default="{ row }">
            <span style="font-size:13px;color:#374151">{{ row.stem.slice(0, 80) }}...</span>
          </template>
        </el-table-column>
        <el-table-column label="AI标注五力" width="110">
          <template #default="{ row }">
            <span class="power-tag" :class="row.ai_annotation.primary_power">{{ powerLabelMap[row.ai_annotation.primary_power] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="置信度" width="120" align="center">
          <template #default="{ row }">
            <el-progress :percentage="Math.round(row.ai_annotation.confidence * 100)"
              :color="confidenceColor(row.ai_annotation.confidence)" :stroke-width="8" style="width:80px;display:inline-block" />
            <span style="font-size:12px;color:#6B7280;margin-left:4px">{{ (row.ai_annotation.confidence * 100).toFixed(0) }}%</span>
          </template>
        </el-table-column>
        <el-table-column label="标注状态" width="100">
          <template #default="{ row }">
            <el-tag :type="row.annotation_status === 'confirmed' ? 'success' : row.annotation_status === 'failed' ? 'danger' : 'warning'" size="small">
              {{ row.annotation_status === 'confirmed' ? '已确认' : row.annotation_status === 'failed' ? '失败' : '待审核' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="160" fixed="right">
          <template #default="{ row }">
            <template v-if="row.annotation_status === 'pending'">
              <el-button size="small" type="success" @click="handleConfirm(row)">确认</el-button>
              <el-button size="small" type="warning">修改</el-button>
            </template>
            <el-tag v-else type="info" size="small">已处理</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" style="padding:16px">
        <el-pagination v-model:current-page="page.current" v-model:page-size="page.size"
          :total="total" layout="total, prev, pager, next" @change="load" />
      </div>
    </div>
  </div>
</template>
