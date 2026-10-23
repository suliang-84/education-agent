<template>
  <div class="page-root">
    <div class="inner-toolbar">
      <el-input v-model="keyword" placeholder="搜索家长昵称 / 手机号" clearable>
        <template #prefix>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
          </svg>
        </template>
      </el-input>
    </div>
    <div class="surface surface--table">
      <el-table :data="parents" v-loading="loading" style="width:100%">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            <span class="num" style="color:var(--text-3);font-size:12px">{{ (page - 1) * pageSize + $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="家长" min-width="150">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:10px">
              <div class="user-avatar user-avatar--parent">{{ row.nickname[0] }}</div>
              <div>
                <div style="font-weight:600;color:var(--text-1)">{{ row.nickname }}</div>
                <span v-if="!row.is_confirmed" class="tag-pending">待激活</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="手机号" width="130">
          <template #default="{ row }">
            <span class="mono" style="color:var(--text-3);font-size:13px">{{ row.phone_masked }}</span>
          </template>
        </el-table-column>

        <el-table-column label="绑定学生" min-width="200">
          <template #default="{ row }">
            <div style="display:flex;gap:6px;flex-wrap:wrap">
              <span
                v-for="s in row.bound_students" :key="s.id"
                class="bound-student-tag"
                :title="`绑定方式：${bindMethodLabel(s.bind_method)}`"
              >
                {{ s.nickname }}({{ s.grade }})
              </span>
              <span v-if="row.bound_students.length === 0" class="tag-muted">暂无绑定</span>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="最后登录" width="100">
          <template #default="{ row }">
            <span style="color:var(--text-3);font-size:13px">{{ fromNow(row.last_login_at) }}</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="120" align="center" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" style="color:var(--red)" @click="openUnbind(row)">解绑学生</el-button>
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

    <!-- ── 解绑学生弹窗 ── -->
    <el-dialog v-model="unbindVisible" title="解绑学生" width="460px">
      <div v-if="unbindTarget">
        <p style="font-size:14px;color:var(--text-2);margin-bottom:14px">
          家长「{{ unbindTarget.nickname }}」当前绑定
          <strong class="num">{{ unbindTarget.bound_students.length }}</strong> 位学生，请选择要解绑的学生：
        </p>
        <el-checkbox-group v-model="unbindSelected" style="display:flex;flex-direction:column;gap:8px">
          <el-checkbox
            v-for="s in unbindTarget.bound_students"
            :key="s.student_id"
            :value="s.student_id"
            style="font-size:14px"
          >
            {{ s.nickname }}（{{ s.grade || '未知年级' }}）
          </el-checkbox>
        </el-checkbox-group>
        <div style="margin-top:14px;padding:10px 12px;background:var(--amber-dim);border:1px solid var(--amber-border);border-radius:var(--r-lg);font-size:13px;color:var(--amber)">
          解绑后若家长无任何绑定学生，家长账号将被自动删除。
        </div>
      </div>
      <template #footer>
        <el-button @click="unbindVisible = false">取消</el-button>
        <el-button type="danger" :loading="unbindLoading" :disabled="unbindSelected.length === 0" @click="doUnbind">
          确认解绑（{{ unbindSelected.length }}）
        </el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { ElMessage } from 'element-plus'
import { parentApi } from '@/api'
import type { Parent } from '@/types'
import { fromNow } from '@/utils/format'

const loading = ref(false)
const parents = ref<Parent[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(50)
const keyword = ref('')

async function loadData() {
  loading.value = true
  try {
    const res = await parentApi.getList({ keyword: keyword.value, page: page.value, limit: pageSize.value })
    parents.value = res.list
    total.value = res.total
  } finally { loading.value = false }
}

function search() { page.value = 1; loadData() }
function onSizeChange() { page.value = 1; loadData() }

// 防抖搜索（输入框专用）
let _searchTimer: ReturnType<typeof setTimeout> | null = null
function debouncedSearch() {
  if (_searchTimer) clearTimeout(_searchTimer)
  _searchTimer = setTimeout(search, 1000)
}
watch(keyword, debouncedSearch)

function bindMethodLabel(m: string) {
  return { INVITE_CODE: '学生邀请', PARENT_SELF: '家长主动', ADMIN: '管理员绑定' }[m] ?? m
}

// ── 解绑 ─────────────────────────────────────────────────────
const unbindVisible = ref(false)
const unbindTarget = ref<Parent | null>(null)
const unbindSelected = ref<number[]>([])
const unbindLoading = ref(false)

function openUnbind(row: Parent) {
  if (row.bound_students.length === 0) { ElMessage.info('该家长当前无绑定学生'); return }
  unbindTarget.value = row
  unbindSelected.value = row.bound_students.length === 1 ? [row.bound_students[0].student_id] : []
  unbindVisible.value = true
}

async function doUnbind() {
  if (!unbindTarget.value || unbindSelected.value.length === 0) return
  unbindLoading.value = true
  try {
    let parentDeleted = false
    for (const studentId of unbindSelected.value) {
      const res = await parentApi.unbind(unbindTarget.value.id, studentId)
      if (res?.parent_deleted) parentDeleted = true
    }
    unbindVisible.value = false
    ElMessage.success(parentDeleted ? '解绑成功，家长账号已自动删除' : '解绑成功')
    await loadData()
  } finally { unbindLoading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.user-avatar {
  width: 32px; height: 32px; border-radius: 9px;
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  &--parent { background: var(--teal-dim); color: var(--teal); }
}

.tag-muted {
  font-size: 11.5px; padding: 3px 10px; border-radius: var(--r-pill);
  background: var(--bg-muted); color: var(--text-3); border: 1.5px solid var(--border-hover);
}

.tag-pending {
  font-size: 10.5px; font-weight: 600; padding: 1px 7px; border-radius: var(--r-pill);
  background: var(--amber-dim); color: var(--amber); border: 1px solid var(--amber-border); margin-left: 6px;
}

.bound-student-tag {
  font-size: 11.5px; font-weight: 500; padding: 2px 9px; border-radius: var(--r-pill);
  background: var(--teal-dim); color: var(--teal); border: 1px solid var(--teal-border); cursor: default;
}
</style>
