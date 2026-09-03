<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { auditApi } from '../../api'
import type { AuditLog } from '../../types'

const loading = ref(false)
const logs = ref<AuditLog[]>([])
const total = ref(0)
const page = reactive({ current: 1, size: 20 })
const filter = reactive({ action: '', keyword: '' })
const detailDialog = ref(false)
const currentLog = ref<AuditLog | null>(null)

const actionOptions = [
  'CONFIRM_ANNOTATION', 'PUBLISH_QUESTION', 'DELETE_QUESTION',
  'CREATE_TRAINING_CONFIG', 'UPDATE_SYSTEM_CONFIG', 'LOGIN',
  'BIND_PARENT', 'UPDATE_STRATEGY',
]

async function load() {
  loading.value = true
  try {
    const res = await auditApi.list(filter.action, page.current, page.size)
    logs.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function showDetail(row: AuditLog) {
  currentLog.value = row
  detailDialog.value = true
}

const actionTagType = (action: string): '' | 'success' | 'warning' | 'info' | 'danger' => {
  if (action.includes('DELETE') || action.includes('DISABLE')) return 'danger'
  if (action.includes('UPDATE') || action.includes('RESET')) return 'warning'
  if (action.includes('CREATE') || action.includes('PUBLISH') || action.includes('CONFIRM')) return 'success'
  return 'info'
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>审计日志</h2>
      <el-text type="info">记录所有管理员操作，不可篡改</el-text>
    </div>

    <div class="filter-bar">
      <el-form inline>
        <el-form-item label="操作类型">
          <el-select v-model="filter.action" placeholder="全部" clearable style="width:200px">
            <el-option v-for="a in actionOptions" :key="a" :label="a" :value="a" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="load">查询</el-button>
          <el-button @click="filter.action = ''; load()">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="logs" v-loading="loading" stripe>
        <el-table-column prop="log_id" label="ID" width="80" />
        <el-table-column label="操作时间" width="160">
          <template #default="{ row }">
            <span style="font-size:13px;color:#374151">{{ row.created_at?.replace('T',' ').slice(0,19) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作人" width="140">
          <template #default="{ row }">
            <div style="font-size:13px">
              <div style="color:#111827;font-weight:500">{{ row.admin_name }}</div>
              <div style="color:#9CA3AF;font-size:11px">{{ row.ip_address }}</div>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="操作类型" width="200">
          <template #default="{ row }">
            <el-tag :type="actionTagType(row.action)" size="small">{{ row.action }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作对象" width="120">
          <template #default="{ row }">
            <span style="font-size:13px;color:#6B7280">
              {{ row.target_type }}
              <span v-if="row.target_id" style="margin-left:4px;color:#1D4ED8">#{{ row.target_id }}</span>
            </span>
          </template>
        </el-table-column>
        <el-table-column label="操作详情" min-width="200">
          <template #default="{ row }">
            <el-text line-clamp="1" style="font-size:12px;color:#374151">
              {{ JSON.stringify(row.detail).slice(0, 60) }}...
            </el-text>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
          </template>
        </el-table-column>
      </el-table>
      <div class="pagination-wrap" style="padding:16px">
        <el-pagination v-model:current-page="page.current" v-model:page-size="page.size"
          :total="total" layout="total, prev, pager, next" @change="load" />
      </div>
    </div>

    <!-- 详情弹窗 -->
    <el-dialog v-model="detailDialog" title="操作详情" width="560px" v-if="currentLog">
      <el-descriptions :column="2" border>
        <el-descriptions-item label="日志ID">{{ currentLog.log_id }}</el-descriptions-item>
        <el-descriptions-item label="操作时间">{{ currentLog.created_at?.replace('T',' ').slice(0,19) }}</el-descriptions-item>
        <el-descriptions-item label="操作人">{{ currentLog.admin_name }}</el-descriptions-item>
        <el-descriptions-item label="IP地址">{{ currentLog.ip_address }}</el-descriptions-item>
        <el-descriptions-item label="操作类型" :span="2">
          <el-tag :type="actionTagType(currentLog.action)">{{ currentLog.action }}</el-tag>
        </el-descriptions-item>
        <el-descriptions-item label="目标类型">{{ currentLog.target_type }}</el-descriptions-item>
        <el-descriptions-item label="目标ID">{{ currentLog.target_id || '—' }}</el-descriptions-item>
      </el-descriptions>
      <div style="margin-top:16px">
        <div style="font-size:13px;color:#6B7280;margin-bottom:8px">变更内容（JSON）</div>
        <pre style="background:#F9FAFB;border-radius:6px;padding:12px;font-size:12px;overflow:auto;max-height:200px;color:#374151">{{ JSON.stringify(currentLog.detail, null, 2) }}</pre>
      </div>
    </el-dialog>
  </div>
</template>
