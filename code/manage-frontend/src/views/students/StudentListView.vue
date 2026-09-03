<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { studentApi } from '../../api'
import type { Student } from '../../types'

const router = useRouter()
const loading = ref(false)
const students = ref<Student[]>([])
const total = ref(0)
const filter = reactive({ grade: '', has_profile: '', keyword: '' })
const page = reactive({ current: 1, size: 15 })

const gradeOptions = ['G7','G8','G9','G10','G11','G12'].map(v => ({ label: { G7:'初一',G8:'初二',G9:'初三',G10:'高一',G11:'高二',G12:'高三' }[v], value: v }))

const powerLabelMap: Record<string, string> = {
  INSIGHT: '洞察力', STRUCTURE: '建构力', INFERENCE: '推演力',
  ADAPTATION: '调适力', TRANSFER: '迁移力',
}

async function load() {
  loading.value = true
  try {
    const res = await studentApi.list(filter.grade, filter.has_profile === '' ? undefined : filter.has_profile === 'true', filter.keyword, page.current, page.size)
    students.value = res.data?.list || []
    total.value = res.data?.total || 0
  } finally { loading.value = false }
}

function handleSearch() { page.current = 1; load() }
function handleReset() { Object.assign(filter, { grade:'', has_profile:'', keyword:'' }); handleSearch() }

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>学生管理</h2>
      <el-text type="info">共 {{ total }} 名学生</el-text>
    </div>

    <div class="filter-bar">
      <el-form inline>
        <el-form-item label="年级">
          <el-select v-model="filter.grade" placeholder="全部" clearable style="width:100px">
            <el-option v-for="o in gradeOptions" :key="o.value" :label="o.label" :value="o.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="有五力画像">
          <el-select v-model="filter.has_profile" placeholder="全部" clearable style="width:100px">
            <el-option label="有" value="true" />
            <el-option label="无" value="false" />
          </el-select>
        </el-form-item>
        <el-form-item>
          <el-input v-model="filter.keyword" placeholder="搜索昵称..." style="width:160px" clearable />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" @click="handleSearch">查询</el-button>
          <el-button @click="handleReset">重置</el-button>
        </el-form-item>
      </el-form>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="students" v-loading="loading" stripe>
        <el-table-column prop="student_id" label="ID" width="80" />
        <el-table-column label="昵称" width="120">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <el-avatar :size="28" style="background:#2563EB;font-size:12px">{{ row.nickname?.slice(0, 1) }}</el-avatar>
              <span>{{ row.nickname }}</span>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="年级" width="80">
          <template #default="{ row }">
            <el-tag size="small">{{ ({ G7:'初一',G8:'初二',G9:'初三',G10:'高一',G11:'高二',G12:'高三' } as Record<string,string>)[row.grade] || row.grade }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="未成年" width="80" align="center">
          <template #default="{ row }">
            <el-icon v-if="row.is_minor" color="#F59E0B"><WarningFilled /></el-icon>
            <span v-else style="color:#D1D5DB">—</span>
          </template>
        </el-table-column>
        <el-table-column label="最弱力" width="100">
          <template #default="{ row }">
            <span v-if="row.primary_weakness" class="power-tag" :class="row.primary_weakness">
              {{ powerLabelMap[row.primary_weakness] }}
            </span>
            <span v-else style="color:#D1D5DB">未测试</span>
          </template>
        </el-table-column>
        <el-table-column prop="training_count" label="训练次数" width="90" align="center" />
        <el-table-column label="最后登录" width="120">
          <template #default="{ row }">
            <span style="font-size:13px;color:#6B7280">{{ row.last_login_at?.slice(0, 10) || '—' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="90" fixed="right">
          <template #default="{ row }">
            <el-button size="small" type="primary" plain @click="router.push(`/students/${row.student_id}`)">详情</el-button>
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
