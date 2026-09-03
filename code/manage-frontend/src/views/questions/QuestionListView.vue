<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { questionApi } from '../../api'
import type { Question } from '../../types'

const router = useRouter()
const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)

const filter = reactive({ primary_power: '', difficulty: '', status: '', keyword: '' })
const page = reactive({ current: 1, size: 15 })

const powerOptions = [
  { label: '洞察力', value: 'INSIGHT' },
  { label: '建构力', value: 'STRUCTURE' },
  { label: '推演力', value: 'INFERENCE' },
  { label: '调适力', value: 'ADAPTATION' },
  { label: '迁移力', value: 'TRANSFER' },
]

const difficultyMap: Record<string, {label:string, type:string}> = {
  basic: { label: '基础', type: 'success' },
  advanced: { label: '进阶', type: 'warning' },
  challenge: { label: '挑战', type: 'danger' },
}

const statusMap: Record<string, {label:string, type:string}> = {
  draft: { label: '草稿', type: 'info' },
  published: { label: '已发布', type: 'success' },
  archived: { label: '已归档', type: '' },
}

const powerLabelMap: Record<string, string> = {
  INSIGHT: '洞察力', STRUCTURE: '建构力', INFERENCE: '推演力',
  ADAPTATION: '调适力', TRANSFER: '迁移力',
}

async function load() {
  loading.value = true
  try {
    const res = await questionApi.list(filter.primary_power, filter.difficulty, filter.status, page.current, page.size)
    questions.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

async function handleStatusChange(row: Question, status: string) {
  const label = status === 'published' ? '发布' : status === 'archived' ? '下架' : '操作'
  try {
    await ElMessageBox.confirm(`确认${label}该题目？`, '提示', { type: 'warning' })
    await questionApi.updateStatus(row.question_id, status)
    ElMessage.success(`${label}成功`)
    load()
  } catch {}
}

async function handleDelete(row: Question) {
  try {
    await ElMessageBox.confirm('确认删除该题目？删除后不可恢复', '警告', { type: 'error' })
    await questionApi.delete(row.question_id)
    ElMessage.success('删除成功')
    load()
  } catch {}
}

function handleSearch() { page.current = 1; load() }
function handleReset() { Object.assign(filter, { primary_power:'', difficulty:'', status:'', keyword:'' }); handleSearch() }

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>题目列表</h2>
      <div style="display:flex;gap:8px">
        <el-button @click="router.push('/questions/create')" type="primary" :icon="'Plus'">新增题目</el-button>
        <el-button :icon="'Upload'">批量导入</el-button>
      </div>
    </div>

    <!-- 过滤栏 -->
    <div class="filter-bar">
      <el-form inline>
        <el-form-item label="主训练力">
          <el-select v-model="filter.primary_power" placeholder="全部" clearable style="width:120px">
            <el-option v-for="o in powerOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="难度">
          <el-select v-model="filter.difficulty" placeholder="全部" clearable style="width:100px">
            <el-option label="基础" value="basic" />
            <el-option label="进阶" value="advanced" />
            <el-option label="挑战" value="challenge" />
          </el-select>
        </el-form-item>
        <el-form-item label="状态">
          <el-select v-model="filter.status" placeholder="全部" clearable style="width:110px">
            <el-option label="草稿" value="draft" />
            <el-option label="已发布" value="published" />
            <el-option label="已归档" value="archived" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input v-model="filter.keyword" placeholder="搜索题干..." style="width:200px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <!-- 表格 -->
    <div class="card" style="padding:0">
      <el-table :data="questions" v-loading="loading" style="width:100%" stripe>
        <el-table-column prop="question_id" label="ID" width="80" />
        <el-table-column label="题干" min-width="280">
          <template #default="{ row }">
            <span style="display:-webkit-box;-webkit-line-clamp:2;-webkit-box-orient:vertical;overflow:hidden;font-size:13px">
              {{ row.stem }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="主训练力" width="100">
          <template #default="{ row }">
            <span class="power-tag" :class="row.primary_power">{{ powerLabelMap[row.primary_power] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="难度" width="80">
          <template #default="{ row }">
            <el-tag :type="difficultyMap[row.difficulty]?.type as any" size="small">
              {{ difficultyMap[row.difficulty]?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any" size="small">
              {{ statusMap[row.status]?.label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="向量化" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.embedding_status === 'completed'" color="#22C55E"><CircleCheck /></el-icon>
            <el-icon v-else-if="row.embedding_status === 'pending'" color="#F59E0B"><Loading /></el-icon>
            <el-icon v-else color="#EF4444"><CircleClose /></el-icon>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="180" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/questions/edit/${row.question_id}`)">编辑</el-button>
            <el-button v-if="row.status === 'draft'" size="small" type="success" @click="handleStatusChange(row, 'published')">发布</el-button>
            <el-button v-if="row.status === 'published'" size="small" type="warning" @click="handleStatusChange(row, 'archived')">下架</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
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
