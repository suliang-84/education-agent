<template>
  <div class="page-root">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/students')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回用户管理
        </el-button>
        <div>
          <h1 class="page-title">{{ student?.nickname || '学生' }}（ID: {{ route.params.id }}）的知识点练习统计</h1>
          <p class="page-subtitle" v-if="student">
            当前：{{ student.grade }} · {{ currentSemester }}
          </p>
        </div>
      </div>
    </div>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <el-select v-model="selectedSubject" placeholder="学科" style="width:120px">
        <el-option label="数学" value="数学" />
        <el-option label="物理" value="物理" />
        <el-option label="化学" value="化学" />
      </el-select>
      <el-button type="primary" @click="loadStats" :loading="loading">查询</el-button>
      <div style="margin-left:auto">
        <el-button size="small">导出 CSV</el-button>
      </div>
    </div>

    <!-- 统计表格 -->
    <div class="surface" style="overflow:hidden" v-loading="loading">
      <el-table :data="stats" style="width:100%">

        <el-table-column label="知识点" min-width="220">
          <template #default="{ row }">
            <span style="color:var(--text-1);font-size:13.5px">{{ row.knowledge_point }}</span>
          </template>
        </el-table-column>

        <el-table-column label="练习题数" width="110" align="center">
          <template #default="{ row }">
            <span class="num" style="font-weight:600;color:var(--indigo)">{{ row.practice_count }}</span>
          </template>
        </el-table-column>

        <el-table-column label="错误率" width="140" align="center">
          <template #default="{ row }">
            <template v-if="row.is_stat_valid && row.error_rate !== null">
              <div style="display:flex;align-items:center;gap:8px">
                <span class="error-dot" :class="errorLevel(row.error_rate)" />
                <span class="num" style="font-weight:600" :class="errorTextClass(row.error_rate)">
                  {{ (row.error_rate * 100).toFixed(1) }}%
                </span>
              </div>
            </template>
            <span v-else style="font-size:12px;color:var(--text-3)">—</span>
          </template>
        </el-table-column>

        <el-table-column label="统计状态" width="140">
          <template #default="{ row }">
            <span v-if="row.is_stat_valid" class="stat-badge stat-badge--valid">已统计</span>
            <span v-else class="stat-badge stat-badge--pending">
              ⏳ 不足5题
            </span>
          </template>
        </el-table-column>

      </el-table>

      <!-- 汇总行 -->
      <div class="summary-bar" v-if="stats.length">
        <span>
          共 <strong class="num">{{ stats.length }}</strong> 个知识点
          · <strong class="num" style="color:var(--green)">{{ validCount }}</strong> 个已统计
          · <strong class="num" style="color:var(--text-3)">{{ invalidCount }}</strong> 个待积累（练习题不足5道）
        </span>
      </div>

      <div class="empty-state" v-if="!loading && stats.length === 0">
        <svg width="40" height="40" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" stroke-width="1.5">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9 17.25v1.007a3 3 0 01-.879 2.122L7.5 21h9l-.621-.621A3 3 0 0115 18.257V17.25m6-12V15a2.25 2.25 0 01-2.25 2.25H5.25A2.25 2.25 0 013 15V5.25m18 0A2.25 2.25 0 0018.75 3H5.25A2.25 2.25 0 003 5.25m18 0H3"/>
        </svg>
        <p>该学科暂无练习记录</p>
      </div>
    </div>

    <!-- 图例 -->
    <div class="legend-card surface">
      <div class="legend-title">图例说明</div>
      <div class="legend-items">
        <div class="legend-item">
          <span class="error-dot error-dot--high" />
          <span>错误率 ≥ 60%：重点薄弱知识点，建议重点关注</span>
        </div>
        <div class="legend-item">
          <span class="error-dot error-dot--mid" />
          <span>错误率 30%~59%：中等掌握，有提升空间</span>
        </div>
        <div class="legend-item">
          <span class="error-dot error-dot--low" />
          <span>错误率 &lt; 30%：掌握良好</span>
        </div>
        <div class="legend-item">
          <span style="font-size:14px;color:var(--text-3)">⏳</span>
          <span>不足5题：练习量不足，错误率不做统计</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { studentApi } from '@/api'
import type { StudentDetail, StudentKpStat } from '@/types'

const route  = useRoute()
const router = useRouter()

const loading = ref(false)
const student = ref<StudentDetail | null>(null)
const stats = ref<StudentKpStat[]>([])
const selectedSubject = ref('数学')
const currentSemester = '上学期（S1）'

const validCount = computed(() => stats.value.filter(s => s.is_stat_valid).length)
const invalidCount = computed(() => stats.value.filter(s => !s.is_stat_valid).length)

function errorLevel(rate: number): string {
  if (rate >= 0.6) return 'error-dot--high'
  if (rate >= 0.3) return 'error-dot--mid'
  return 'error-dot--low'
}

function errorTextClass(rate: number): string {
  if (rate >= 0.6) return 'text-red'
  if (rate >= 0.3) return 'text-amber'
  return 'text-green'
}

async function loadStudent() {
  student.value = await studentApi.getOne(Number(route.params.id))
}

async function loadStats() {
  loading.value = true
  try {
    stats.value = await studentApi.getKpStats(Number(route.params.id), { subject: selectedSubject.value })
  } finally { loading.value = false }
}

onMounted(async () => {
  await Promise.all([loadStudent(), loadStats()])
})
</script>

<style lang="scss" scoped>
.stat-badge {
  font-size: 12px;
  font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--valid  { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &--pending { background: var(--bg-muted); color: var(--text-3); border-color: var(--border-hover); }
}

.error-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  flex-shrink: 0;

  &--high { background: var(--red); }
  &--mid  { background: var(--amber); }
  &--low  { background: var(--green); }
}

.text-red   { color: var(--red); }
.text-amber { color: var(--amber); }
.text-green { color: var(--green); }

.summary-bar {
  padding: 12px 20px;
  border-top: 1px solid var(--border);
  font-size: 13.5px;
  color: var(--text-2);

  strong { font-family: var(--font-mono); }
}

.empty-state {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 10px;
  padding: 48px 24px;
  color: var(--text-3);
  font-size: 13.5px;
}

.legend-card {
  padding: 16px 20px;
  margin-top: 12px;
}

.legend-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-3);
  letter-spacing: 0.05em;
  text-transform: uppercase;
  margin-bottom: 12px;
}

.legend-items {
  display: flex;
  flex-wrap: wrap;
  gap: 16px;
}

.legend-item {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--text-2);
}
</style>
