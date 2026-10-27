<template>
  <div class="page-root">
    <div class="inner-toolbar">
      <el-input v-model="filters.keyword" placeholder="昵称 / 手机号" clearable>
        <template #prefix>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
          </svg>
        </template>
      </el-input>
      <el-select v-model="filters.grade" placeholder="年级" clearable style="width:90px" @change="search">
        <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
      </el-select>
      <el-select v-model="filters.has_profile" placeholder="五力画像" clearable style="width:110px" @change="search">
        <el-option label="有画像" value="true" />
        <el-option label="未测试" value="false" />
      </el-select>
    </div>
    <div class="surface surface--table">
      <el-table :data="students" v-loading="loading" style="width:100%">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            <span class="num" style="color:var(--text-3);font-size:12px">{{ (page - 1) * pageSize + $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="学生" width="110" prop="nickname" />

        <el-table-column label="年级" width="90">
          <template #default="{ row }">
            {{ gradeLabel(row.grade) }}
          </template>
        </el-table-column>

        <el-table-column label="五力权重分布" min-width="260">
          <template #default="{ row }">
            <span v-if="row.five_power_scores" class="power-dist">
              <template v-for="(item, idx) in sortedPowers(row.five_power_scores)" :key="item.key">
                <span class="power-dist__item">
                  <span class="power-dot-label__dot" :class="`power-dot--${item.key}`" />
                  {{ FivePowerLabels[item.key as FivePower] }}({{ item.val }})
                </span>
                <span v-if="idx < 4" style="color:var(--text-3);margin:0 2px">></span>
              </template>
            </span>
            <span v-else style="color:var(--text-3);font-size:12px">未测试</span>
          </template>
        </el-table-column>


        <el-table-column label="绑定家长" width="90" align="center" prop="bound_parents_count" />

        <el-table-column label="手机号" width="130">
          <template #default="{ row }">
            <span class="mono" style="color:var(--text-3);font-size:13px">{{ row.phone_masked }}</span>
          </template>
        </el-table-column>

        <el-table-column label="最后登录" width="100">
          <template #default="{ row }">
            <span style="color:var(--text-3);font-size:13px">{{ fromNow(row.last_login_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="110" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" style="color:var(--color-primary)" @click="$router.push(`/students/${row.id}`)">
              <SvgIcon name="profile" :size="18" color="var(--color-primary)" title="画像" />
            </el-button>
            <el-button text size="small" style="color:var(--green)" @click="$router.push(`/students/${row.id}/ai-prompt`)">
              <SvgIcon name="summary" :size="18" color="var(--green)" title="摘要" />
            </el-button>
            <el-button text size="small" style="color:#f3c601" @click="openBindParent(row)">
              <SvgIcon name="bind" :size="18" color="#f3c601" title="绑定家长" />
            </el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="paginator">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :page-sizes="[10, 20, 50, 100, 200]"
          :total="total"
          background
          size="small"
          layout="total, ->, prev, pager, next, sizes"
          @current-change="loadData"
          @size-change="onSizeChange"
        />
      </div>
    </div>

    <!-- ── 绑定家长弹窗 ── -->
    <el-dialog v-model="bindDialogVisible" :title="`为学生「${bindTarget?.nickname}」绑定家长`" width="480px">
      <div v-if="bindTarget">
        <div class="bind-info">当前已绑定：<strong class="num">{{ bindTarget.bound_parents_count }}</strong> 位家长</div>
        <div class="bind-form-label">家长手机号</div>
        <el-input v-model="bindPhone" placeholder="输入家长手机号" maxlength="11" style="width:100%;margin-bottom:8px" />
        <div class="bind-tip">若该手机号未注册，系统将自动创建家长账号。</div>
      </div>
      <template #footer>
        <el-button @click="bindDialogVisible = false">取消</el-button>
        <el-button type="primary" :loading="bindLoading" @click="doBindParent">立即绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage } from 'element-plus'
import { studentApi } from '@/api'
import type { Student, FivePower } from '@/types'
import { FivePowerLabels } from '@/types'
import { fromNow } from '@/utils/format'

const router = useRouter()

const loading = ref(false)
const students = ref<Student[]>([])
const total = ref(0)
const totalPages = ref(1)
const pageSize = ref(50)
const page = ref(1)
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']

const GRADE_LABELS: Record<string, string> = {
  G7: '初一', G8: '初二', G9: '初三',
  G10: '高一', G11: '高二', G12: '高三',
}
function gradeLabel(grade: string) {
  return GRADE_LABELS[grade] ?? grade ?? '—'
}

function sortedPowers(scores: Record<string, number>) {
  return Object.entries(scores)
    .map(([key, val]) => ({ key, val }))
    .sort((a, b) => b.val - a.val)
}
const filters = reactive({ grade: '', has_profile: '', keyword: '' })

async function loadData() {
  loading.value = true
  try {
    const params: Record<string, unknown> = { page: page.value, limit: pageSize.value }
    if (filters.grade) params.grade = filters.grade
    if (filters.keyword) params.keyword = filters.keyword
    if (filters.has_profile !== '') params.has_profile = filters.has_profile === 'true'
    const res = await studentApi.getList(params as Parameters<typeof studentApi.getList>[0])
    students.value = res.list
    total.value = res.total
    totalPages.value = res.total_pages
  } finally { loading.value = false }
}

function search() { page.value = 1; loadData() }
function onSizeChange() { page.value = 1; loadData() }
function prevPage() { if (page.value > 1) { page.value--; loadData() } }

// 防抖搜索（输入框专用）
let _searchTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (_searchTimer) clearTimeout(_searchTimer)
  _searchTimer = setTimeout(search, 1000)
}
watch(() => filters.keyword, debouncedSearch)
function nextPage() { if (page.value < totalPages.value) { page.value++; loadData() } }

// ── 绑定家长 ─────────────────────────────────────────────────
const bindDialogVisible = ref(false)
const bindTarget = ref<Student | null>(null)
const bindPhone = ref('')
const bindLoading = ref(false)

function openBindParent(row: Student) {
  bindTarget.value = row
  bindPhone.value = ''
  bindDialogVisible.value = true
}

async function doBindParent() {
  if (!bindPhone.value.trim()) { ElMessage.warning('请输入家长手机号'); return }
  if (!bindTarget.value) return
  bindLoading.value = true
  try {
    await studentApi.bindParent(bindTarget.value.id, { parent_phone: bindPhone.value })
    const idx = students.value.findIndex(s => s.id === bindTarget.value!.id)
    if (idx !== -1) students.value[idx].bound_parents_count += 1
    bindDialogVisible.value = false
    ElMessage.success('家长绑定成功')
  } finally { bindLoading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.power-dist {
  display: inline-flex;
  align-items: center;
  flex-wrap: nowrap;
  gap: 2px;
  font-size: 12px;
  color: var(--text-2);

  &__item {
    display: inline-flex;
    align-items: center;
    gap: 3px;
    white-space: nowrap;
  }
}

.power-dot {
  width: 5px;
  height: 5px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

.user-avatar {
  width: 32px; height: 32px; border-radius: 9px;
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  &--student { background: var(--indigo-light); color: var(--indigo); }
}

.tag-muted {
  font-size: 11.5px; padding: 3px 10px; border-radius: var(--r-pill);
  background: var(--bg-muted); color: var(--text-3); border: 1.5px solid var(--border-hover);
}

.power-dot-label {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  font-size: 13.5px;
  font-weight: 400;

  &__dot {
    width: 5px;
    height: 5px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  &--INSIGHT   { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-insight); } }
  &--CONSTRUCT { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-construct); } }
  &--DEDUCE    { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-deduce); } }
  &--ADAPT     { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-adapt); } }
  &--MIGRATE   { color: var(--el-table-text-color); .power-dot-label__dot { background: var(--power-migrate); } }
}


.bind-info { font-size: 13.5px; color: var(--text-2); margin-bottom: 16px; strong { font-family: var(--font-mono); color: var(--text-1); } }
.bind-form-label { font-size: 13px; font-weight: 500; color: var(--text-2); margin-bottom: 6px; }
.bind-tip { font-size: 12px; color: var(--text-3); line-height: 1.5; }
</style>
