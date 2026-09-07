<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">审计日志</h1>
        <p class="page-subtitle">记录所有管理员操作，支持追溯变更内容</p>
      </div>
    </div>

    <div class="filter-bar">
      <el-input v-model="filters.admin_username" placeholder="管理员账号" clearable style="width:150px" @keyup.enter="handleSearch" />
      <el-select v-model="filters.action_type" placeholder="操作类型" clearable style="width:180px">
        <el-option v-for="t in actionTypes" :key="t.value" :label="t.label" :value="t.value" />
      </el-select>
      <el-date-picker
        v-model="filters.date_range" type="daterange"
        range-separator="–" start-placeholder="开始日期" end-placeholder="结束日期"
        format="YYYY-MM-DD" value-format="YYYY-MM-DD"
        style="width:240px"
      />
      <div style="margin-left:auto;display:flex;gap:8px">
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div class="surface" style="overflow:hidden">
      <el-table :data="logs" v-loading="loading" style="width:100%">
        <el-table-column label="时间" width="155">
          <template #default="{ row }">
            <span class="mono" style="color:var(--text-2);font-size:13px">{{ formatDate(row.created_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作人" width="150">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <div class="admin-avatar">{{ row.admin_username[0].toUpperCase() }}</div>
              <span style="font-weight:500;color:var(--text-1)">{{ row.admin_username }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="操作类型" width="180">
          <template #default="{ row }">
            <span class="action-badge" :class="getActionClass(row.action_type)">{{ getActionLabel(row.action_type) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作对象" min-width="200">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <span class="table-code">{{ row.target_table }}</span>
              <span class="id-chip">#{{ row.target_id }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="IP 地址" width="130">
          <template #default="{ row }">
            <span class="mono" style="color:var(--text-3);font-size:12.5px">{{ row.ip_address }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="80" align="center">
          <template #default="{ row }">
            <el-button text size="small" style="color:var(--indigo)" @click="viewDetail(row)">查看</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="paginator">
        <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ total }}</span> 条记录</span>
        <div style="display:flex;gap:6px">
          <el-button size="small" :disabled="cursor === 0" @click="prevPage">上一页</el-button>
          <el-button size="small" :disabled="!hasMore" @click="nextPage">下一页</el-button>
        </div>
      </div>
    </div>

    <!-- Detail dialog -->
    <el-dialog v-model="showDetail" title="操作详情" width="640px">
      <div v-if="currentLog" class="detail-body">
        <el-descriptions :column="2" border size="small">
          <el-descriptions-item label="时间"><span class="mono">{{ formatDate(currentLog.created_at) }}</span></el-descriptions-item>
          <el-descriptions-item label="操作人">{{ currentLog.admin_username }}</el-descriptions-item>
          <el-descriptions-item label="操作类型" :span="2">
            <span class="action-badge" :class="getActionClass(currentLog.action_type)">{{ currentLog.action_type }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="操作对象">
            <span class="table-code">{{ currentLog.target_table }}</span>
          </el-descriptions-item>
          <el-descriptions-item label="对象 ID"><span class="id-chip">#{{ currentLog.target_id }}</span></el-descriptions-item>
          <el-descriptions-item label="IP 地址"><span class="mono">{{ currentLog.ip_address }}</span></el-descriptions-item>
        </el-descriptions>

        <div v-if="currentLog.before_data || currentLog.after_data" class="diff-section">
          <div class="diff-title">变更内容</div>
          <div class="diff-cols">
            <div class="diff-col">
              <div class="diff-hd diff-hd--before">修改前</div>
              <div class="json-viewer json-viewer--before">{{ JSON.stringify(currentLog.before_data, null, 2) }}</div>
            </div>
            <div class="diff-col">
              <div class="diff-hd diff-hd--after">修改后</div>
              <div class="json-viewer json-viewer--after">{{ JSON.stringify(currentLog.after_data, null, 2) }}</div>
            </div>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { auditLogApi } from '@/api'
import type { AuditLog } from '@/types'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const logs = ref<AuditLog[]>([])
const total = ref(0)
const hasMore = ref(false)
const cursor = ref(0)
const showDetail = ref(false)
const currentLog = ref<AuditLog | null>(null)

const filters = reactive({ admin_username: '', action_type: '', date_range: [] as string[] })

const actionTypes = [
  { value: 'CONFIRM_ANNOTATION', label: '确认标注' },
  { value: 'PUBLISH_QUESTION', label: '发布题目' },
  { value: 'ARCHIVE_QUESTION', label: '下架题目' },
  { value: 'DELETE_QUESTION', label: '删除题目' },
  { value: 'UPDATE_SYSTEM_CONFIG', label: '修改系统参数' },
  { value: 'CREATE_TRAINING_CONFIG', label: '创建训练配置' },
  { value: 'BIND_PARENT', label: '绑定家长' },
  { value: 'UPDATE_COGNITIVE_QUESTION', label: '修改测试题' },
]

const actionLabelMap: Record<string, string> = Object.fromEntries(actionTypes.map(t => [t.value, t.label]))
function getActionLabel(type: string) { return actionLabelMap[type] || type }
function getActionClass(type: string) {
  if (type.startsWith('DELETE') || type.startsWith('ARCHIVE')) return 'action--danger'
  if (type.startsWith('UPDATE') || type.startsWith('MODIFY')) return 'action--warning'
  if (type.startsWith('CREATE') || type.startsWith('PUBLISH') || type.startsWith('CONFIRM')) return 'action--success'
  return 'action--info'
}
function viewDetail(row: AuditLog) { currentLog.value = row; showDetail.value = true }

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { cursor: cursor.value, limit: 20, ...filters }
    if (filters.date_range?.length === 2) { params.date_from = filters.date_range[0]; params.date_to = filters.date_range[1] }
    const res = await auditLogApi.getList(params)
    logs.value = res.list; total.value = res.total; hasMore.value = res.has_more
  } finally { loading.value = false }
}

function handleSearch() { cursor.value = 0; loadData() }
function resetFilters() { Object.assign(filters, { admin_username: '', action_type: '', date_range: [] }); cursor.value = 0; loadData() }
function prevPage() { cursor.value = Math.max(0, cursor.value - 20); loadData() }
function nextPage() { cursor.value += 20; loadData() }

onMounted(loadData)
</script>

<style lang="scss" scoped>
.admin-avatar {
  width: 28px;
  height: 28px;
  border-radius: 8px;
  background: var(--indigo-light);
  color: var(--indigo);
  font-size: 12px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.action-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &.action--success { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &.action--warning { background: var(--amber-dim); color: var(--amber); border-color: var(--amber-border); }
  &.action--danger  { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }
  &.action--info    { background: var(--bg-muted);  color: var(--text-2); border-color: var(--border-hover); }
}

.table-code {
  font-family: var(--font-mono);
  font-size: 12px;
  color: var(--indigo);
  background: var(--indigo-light);
  padding: 2px 8px;
  border-radius: var(--r-sm);
}

.detail-body { display: flex; flex-direction: column; gap: 16px; }

.diff-title { font-size: 13.5px; font-weight: 600; color: var(--text-1); margin-bottom: 12px; }
.diff-cols  { display: grid; grid-template-columns: 1fr 1fr; gap: 12px; }
.diff-col   { display: flex; flex-direction: column; gap: 6px; }

.diff-hd {
  font-size: 12px;
  font-weight: 600;
  padding: 4px 0;

  &--before { color: var(--red); }
  &--after  { color: var(--green); }
}

.json-viewer--before { color: var(--red);   background: var(--red-dim);   border: 1px solid var(--red-border); }
.json-viewer--after  { color: var(--green); background: var(--green-dim); border: 1px solid var(--green-border); }
</style>
