<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">学生管理</h1>
        <p class="page-subtitle">查看学生五力画像、训练记录及家长绑定状态</p>
      </div>
    </div>

    <div class="filter-bar">
      <el-input v-model="filters.keyword" placeholder="昵称 / 手机号" clearable style="width:180px" @keyup.enter="handleSearch">
        <template #prefix>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
          </svg>
        </template>
      </el-input>
      <el-select v-model="filters.grade" placeholder="年级" clearable style="width:100px">
        <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
      </el-select>
      <el-select v-model="filters.has_profile" placeholder="五力画像" clearable style="width:120px">
        <el-option label="有画像" value="true" />
        <el-option label="未测试" value="false" />
      </el-select>
      <div style="margin-left:auto;display:flex;gap:8px">
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </div>

    <div class="surface" style="overflow:hidden">
      <el-table :data="students" v-loading="loading" style="width:100%">
        <el-table-column label="ID" width="90">
          <template #default="{ row }">
            <span class="id-chip">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="学生" min-width="140">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:10px">
              <div class="student-avatar">{{ row.nickname[0] }}</div>
              <div>
                <div style="font-weight:600;color:var(--text-1)">{{ row.nickname }}</div>
                <div style="font-size:12px;color:var(--text-3)">{{ row.grade }}</div>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="科目" min-width="130">
          <template #default="{ row }">
            <div style="display:flex;gap:4px;flex-wrap:wrap">
              <span v-for="sub in row.subjects" :key="sub" class="subject-tag">{{ sub }}</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最弱力" width="110">
          <template #default="{ row }">
            <span v-if="row.weakest_power" class="power-badge" :class="`power-badge--${row.weakest_power}`">
              {{ FivePowerLabels[row.weakest_power as keyof typeof FivePowerLabels] }}
            </span>
            <span v-else class="no-test-tag">未测试</span>
          </template>
        </el-table-column>

        <el-table-column label="训练次数" width="90" align="center">
          <template #default="{ row }">
            <span class="num" style="font-size:14px;font-weight:600;color:var(--indigo)">{{ row.training_count }}</span>
          </template>
        </el-table-column>

        <el-table-column label="手机号" width="130">
          <template #default="{ row }">
            <span class="mono" style="color:var(--text-3);font-size:13px">{{ row.phone_masked }}</span>
          </template>
        </el-table-column>

        <el-table-column label="最后登录" min-width="110">
          <template #default="{ row }">
            <span style="color:var(--text-3);font-size:13px">{{ fromNow(row.last_login_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="100" align="center">
          <template #default="{ row }">
            <el-button text size="small" style="color:var(--indigo)" @click="$router.push(`/students/${row.id}`)">查看详情</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="paginator">
        <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ total }}</span> 名学生</span>
        <div style="display:flex;gap:6px">
          <el-button size="small" :disabled="cursor === 0" @click="prevPage">上一页</el-button>
          <el-button size="small" :disabled="!hasMore" @click="nextPage">下一页</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { studentApi } from '@/api'
import type { Student } from '@/types'
import { FivePowerLabels } from '@/types'
import { fromNow } from '@/utils/format'

const loading = ref(false)
const students = ref<Student[]>([])
const total = ref(0)
const hasMore = ref(false)
const cursor = ref(0)
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']
const filters = reactive({ grade: '', has_profile: '', keyword: '' })

async function loadData() {
  loading.value = true
  try {
    const res = await studentApi.getList({ ...filters, cursor: cursor.value, limit: 20 })
    students.value = res.list; total.value = res.total; hasMore.value = res.has_more
  } finally { loading.value = false }
}

function handleSearch() { cursor.value = 0; loadData() }
function resetFilters() { Object.assign(filters, { grade: '', has_profile: '', keyword: '' }); cursor.value = 0; loadData() }
function prevPage() { cursor.value = Math.max(0, cursor.value - 20); loadData() }
function nextPage() { cursor.value += 20; loadData() }

onMounted(loadData)
</script>

<style scoped>
.student-avatar {
  width: 34px; height: 34px;
  border-radius: 10px;
  background: var(--indigo-light);
  color: var(--indigo);
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.subject-tag {
  font-size: 11.5px; font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--r-pill);
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1px solid var(--indigo-border);
}
.no-test-tag {
  font-size: 11.5px; padding: 3px 10px;
  border-radius: var(--r-pill);
  background: var(--bg-muted);
  color: var(--text-3);
  border: 1.5px solid var(--border-hover);
}
</style>
