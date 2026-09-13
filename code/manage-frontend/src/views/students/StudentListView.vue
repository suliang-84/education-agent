<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">用户管理</h1>
        <p class="page-subtitle">统一管理学生、家长和管理员账号</p>
      </div>
      <el-button v-if="activeTab === 'admins'" type="primary" @click="openCreateAdmin">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        新增管理员
      </el-button>
    </div>

    <!-- ── Tab 切换 ── -->
    <div class="surface" style="padding:0;overflow:hidden">

      <div class="tab-bar">
        <button class="tab-item" :class="{ active: activeTab === 'students' }" @click="activeTab = 'students'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5"/>
          </svg>
          学生管理
        </button>
        <button class="tab-item" :class="{ active: activeTab === 'parents' }" @click="activeTab = 'parents'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
          </svg>
          家长管理
        </button>
        <button class="tab-item" :class="{ active: activeTab === 'admins' }" @click="activeTab = 'admins'">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
          </svg>
          管理员账号
        </button>
      </div>

      <!-- ════ Tab 1：学生管理 ════ -->
      <div v-show="activeTab === 'students'">
        <div class="tab-toolbar">
          <el-input v-model="sFilters.keyword" placeholder="昵称 / 手机号" clearable style="width:180px" @keyup.enter="searchStudents">
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
          <el-select v-model="sFilters.grade" placeholder="年级" clearable style="width:100px">
            <el-option v-for="g in grades" :key="g" :label="g" :value="g" />
          </el-select>
          <el-select v-model="sFilters.has_profile" placeholder="五力画像" clearable style="width:120px">
            <el-option label="有画像" value="true" />
            <el-option label="未测试" value="false" />
          </el-select>
          <el-button type="primary" @click="searchStudents">查询</el-button>
          <el-button @click="resetStudentFilters">重置</el-button>
        </div>

        <el-table :data="students" v-loading="sLoading" style="width:100%">

          <el-table-column label="ID" width="90">
            <template #default="{ row }">
              <span class="id-chip">#{{ row.id }}</span>
            </template>
          </el-table-column>

          <el-table-column label="学生" min-width="140">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:10px">
                <div class="user-avatar user-avatar--student">{{ row.nickname[0] }}</div>
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

          <el-table-column label="最弱力" width="100">
            <template #default="{ row }">
              <span v-if="row.weakest_power" class="power-badge" :class="`power-badge--${row.weakest_power}`">
                {{ FivePowerLabels[row.weakest_power as FivePower] }}
              </span>
              <span v-else class="tag-muted">未测试</span>
            </template>
          </el-table-column>

          <el-table-column label="训练次数" width="85" align="center">
            <template #default="{ row }">
              <span class="num" style="font-size:14px;font-weight:600;color:var(--indigo)">{{ row.training_count }}</span>
            </template>
          </el-table-column>

          <el-table-column label="绑定家长" width="90" align="center">
            <template #default="{ row }">
              <span class="parent-count-badge" :class="row.parent_count === 0 ? 'parent-count-badge--none' : ''">
                {{ row.parent_count }} / 2
              </span>
            </template>
          </el-table-column>

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

          <el-table-column label="操作" width="200" align="center">
            <template #default="{ row }">
              <el-button text size="small" style="color:var(--indigo)" @click="$router.push(`/students/${row.id}`)">画像</el-button>
              <el-button text size="small" style="color:var(--purple)" @click="$router.push(`/students/${row.id}/ai-prompt`)">摘要</el-button>
              <el-button text size="small" style="color:var(--text-2)" @click="openBindParent(row)">
                家长({{ row.parent_count }})
              </el-button>
            </template>
          </el-table-column>

        </el-table>

        <div class="paginator">
          <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ sTotal }}</span> 名学生</span>
          <div style="display:flex;gap:6px">
            <el-button size="small" :disabled="sCursor === 0" @click="sPrevPage">上一页</el-button>
            <el-button size="small" :disabled="!sHasMore" @click="sNextPage">下一页</el-button>
          </div>
        </div>
      </div>

      <!-- ════ Tab 2：家长管理 ════ -->
      <div v-show="activeTab === 'parents'">
        <div class="tab-toolbar">
          <el-input v-model="pKeyword" placeholder="搜索家长昵称 / 手机号" clearable style="width:220px" @keyup.enter="searchParents">
            <template #prefix>
              <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
              </svg>
            </template>
          </el-input>
          <el-button type="primary" @click="searchParents">查询</el-button>
          <el-button @click="pKeyword = ''; searchParents()">重置</el-button>
        </div>

        <el-table :data="parents" v-loading="pLoading" style="width:100%">

          <el-table-column label="ID" width="90">
            <template #default="{ row }">
              <span class="id-chip">#{{ row.id }}</span>
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

          <el-table-column label="操作" width="120" align="center">
            <template #default="{ row }">
              <el-button text size="small" style="color:var(--red)" @click="confirmUnbindParent(row)">
                解绑学生
              </el-button>
            </template>
          </el-table-column>

        </el-table>

        <div class="paginator">
          <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ pTotal }}</span> 位家长</span>
        </div>
      </div>

      <!-- ════ Tab 3：管理员账号 ════ -->
      <div v-show="activeTab === 'admins'">
        <el-table :data="adminUsers" v-loading="aLoading" style="width:100%">

          <el-table-column label="ID" width="70" align="center">
            <template #default="{ row }">
              <span class="num" style="color:var(--text-3)">{{ row.id }}</span>
            </template>
          </el-table-column>

          <el-table-column label="账号" width="130">
            <template #default="{ row }">
              <span class="mono" style="color:var(--indigo);font-weight:600">{{ row.username }}</span>
            </template>
          </el-table-column>

          <el-table-column label="显示名称" width="120">
            <template #default="{ row }">
              <div style="display:flex;align-items:center;gap:8px">
                <div class="user-avatar user-avatar--admin">{{ row.display_name[0] }}</div>
                <span style="font-weight:600;color:var(--text-1)">{{ row.display_name }}</span>
              </div>
            </template>
          </el-table-column>

          <el-table-column label="角色" width="110">
            <template #default="{ row }">
              <span class="role-badge" :class="row.role === 'SUPER_ADMIN' ? 'role-badge--super' : 'role-badge--admin'">
                {{ row.role === 'SUPER_ADMIN' ? '超级管理员' : '管理员' }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="手机号" width="130">
            <template #default="{ row }">
              <span class="mono" style="color:var(--text-3);font-size:13px">{{ row.phone_masked }}</span>
            </template>
          </el-table-column>

          <el-table-column label="状态" width="90" align="center">
            <template #default="{ row }">
              <span class="status-dot" :class="row.is_active ? 'status-dot--ok' : 'status-dot--off'">
                {{ row.is_active ? '启用' : '停用' }}
              </span>
            </template>
          </el-table-column>

          <el-table-column label="最后登录" width="100">
            <template #default="{ row }">
              <span style="color:var(--text-3);font-size:13px">{{ row.last_login_at ? fromNow(row.last_login_at) : '从未' }}</span>
            </template>
          </el-table-column>

          <el-table-column label="操作" width="160" align="center">
            <template #default="{ row }">
              <el-button
                v-if="row.is_active && row.role !== 'SUPER_ADMIN'"
                text size="small" style="color:var(--amber)"
                @click="toggleAdmin(row, false)"
              >停用</el-button>
              <el-button
                v-if="!row.is_active"
                text size="small" style="color:var(--green)"
                @click="toggleAdmin(row, true)"
              >启用</el-button>
              <el-button text size="small" style="color:var(--indigo)" @click="confirmResetPwd(row)">重置密码</el-button>
            </template>
          </el-table-column>

        </el-table>
      </div>

    </div>

    <!-- ── 绑定家长弹窗 ── -->
    <el-dialog v-model="bindDialogVisible" :title="`为学生「${bindTarget?.nickname}」绑定家长`" width="480px">
      <div v-if="bindTarget">
        <div class="bind-info">当前已绑定：<strong class="num">{{ bindTarget.parent_count }}</strong> / 2 位家长</div>

        <!-- 已绑定列表（从详情接口拿，这里简单展示计数）-->
        <div class="bind-hint" v-if="bindTarget.parent_count >= 2">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
          </svg>
          该学生已绑定 2 位家长，已达上限。请先在学生画像页解绑后再绑定新家长。
        </div>
        <template v-else>
          <div class="bind-form-label">家长手机号</div>
          <el-input v-model="bindPhone" placeholder="输入家长手机号" maxlength="11" style="width:100%;margin-bottom:8px" />
          <div class="bind-tip">若该手机号未注册，系统将自动创建家长账号并发送激活短信。</div>
        </template>
      </div>
      <template #footer>
        <el-button @click="bindDialogVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="!!bindTarget && bindTarget.parent_count >= 2"
          :loading="bindLoading"
          @click="doBindParent"
        >立即绑定</el-button>
      </template>
    </el-dialog>

    <!-- ── 解绑家长确认弹窗 ── -->
    <el-dialog v-model="unbindParentDialogVisible" title="解绑学生" width="420px">
      <div v-if="unbindParentTarget" style="font-size:14px;color:var(--text-2);line-height:1.8">
        <p>确认解绑「{{ unbindParentTarget.nickname }}」与其所有绑定学生的关系？</p>
        <p style="color:var(--text-3);font-size:13px">解绑后家长账号仍保留，可重新绑定。</p>
      </div>
      <template #footer>
        <el-button @click="unbindParentDialogVisible = false">取消</el-button>
        <el-button type="danger" :loading="bindLoading" @click="doUnbindParentAll">确认解绑</el-button>
      </template>
    </el-dialog>

    <!-- ── 新增管理员弹窗 ── -->
    <el-dialog v-model="createAdminVisible" title="新增管理员账号" width="480px" :close-on-click-modal="false">
      <el-form :model="adminForm" label-width="90px" @submit.prevent>
        <el-form-item label="登录账号">
          <el-input v-model="adminForm.username" placeholder="仅字母、数字、下划线" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="adminForm.display_name" placeholder="如：运营专员" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="adminForm.phone" placeholder="用于2FA验证和密码重置" maxlength="11" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="adminForm.email" placeholder="选填" />
        </el-form-item>
        <div class="create-admin-tip">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
            <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
          </svg>
          创建后系统将向该手机号发送初始密码，首次登录必须修改。
        </div>
      </el-form>
      <template #footer>
        <el-button @click="createAdminVisible = false">取消</el-button>
        <el-button type="primary" :loading="adminLoading" @click="doCreateAdmin">创建账号</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, watch } from 'vue'
import { useRouter } from 'vue-router'
import { ElMessage, ElMessageBox } from 'element-plus'
import { studentApi, parentApi, adminUserApi } from '@/api'
import type { Student, Parent, AdminUser, FivePower } from '@/types'
import { FivePowerLabels } from '@/types'
import { fromNow } from '@/utils/format'

const router = useRouter()

// ── Tab 状态 ─────────────────────────────────────────────────
const activeTab = ref<'students' | 'parents' | 'admins'>('students')

// ── 常量 ─────────────────────────────────────────────────────
const grades = ['初一', '初二', '初三', '高一', '高二', '高三']

function bindMethodLabel(m: string) {
  return { INVITE_CODE: '学生邀请', PARENT_SELF: '家长主动', ADMIN: '管理员绑定' }[m] ?? m
}

// ═══════════════════════════════════════════════════════════════
// ── Tab 1：学生管理 ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════

const sLoading = ref(false)
const students = ref<Student[]>([])
const sTotal = ref(0)
const sHasMore = ref(false)
const sCursor = ref(0)
const sFilters = reactive({ grade: '', has_profile: '', keyword: '' })

async function loadStudents() {
  sLoading.value = true
  try {
    const res = await studentApi.getList({ ...sFilters, cursor: sCursor.value, limit: 20 })
    students.value = res.list
    sTotal.value = res.total
    sHasMore.value = res.has_more
  } finally { sLoading.value = false }
}

function searchStudents() { sCursor.value = 0; loadStudents() }
function resetStudentFilters() { Object.assign(sFilters, { grade: '', has_profile: '', keyword: '' }); sCursor.value = 0; loadStudents() }
function sPrevPage() { sCursor.value = Math.max(0, sCursor.value - 20); loadStudents() }
function sNextPage() { sCursor.value += 20; loadStudents() }

// ═══════════════════════════════════════════════════════════════
// ── Tab 2：家长管理 ──────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════

const pLoading = ref(false)
const parents = ref<Parent[]>([])
const pTotal = ref(0)
const pKeyword = ref('')

async function loadParents() {
  pLoading.value = true
  try {
    const res = await parentApi.getList({ keyword: pKeyword.value, limit: 50 })
    parents.value = res.list
    pTotal.value = res.total
  } finally { pLoading.value = false }
}

function searchParents() { loadParents() }

// ── 解绑家长（解绑其全部学生）
const unbindParentDialogVisible = ref(false)
const unbindParentTarget = ref<Parent | null>(null)
const bindLoading = ref(false)

function confirmUnbindParent(row: Parent) {
  if (row.bound_students.length === 0) {
    ElMessage.info('该家长当前无绑定学生')
    return
  }
  unbindParentTarget.value = row
  unbindParentDialogVisible.value = true
}

async function doUnbindParentAll() {
  if (!unbindParentTarget.value) return
  bindLoading.value = true
  try {
    // 逐一解绑每个学生
    for (const s of unbindParentTarget.value.bound_students) {
      await parentApi.unbind(unbindParentTarget.value.id, s.id)
    }
    unbindParentDialogVisible.value = false
    ElMessage.success('已解绑所有关联学生')
    await loadParents()
  } finally { bindLoading.value = false }
}

// ═══════════════════════════════════════════════════════════════
// ── Tab 3：管理员账号 ────────────────────────────────────────
// ═══════════════════════════════════════════════════════════════

const aLoading = ref(false)
const adminUsers = ref<AdminUser[]>([])
const adminLoading = ref(false)

async function loadAdmins() {
  aLoading.value = true
  try {
    adminUsers.value = await adminUserApi.getList()
  } finally { aLoading.value = false }
}

async function toggleAdmin(row: AdminUser, active: boolean) {
  await ElMessageBox.confirm(
    `确认${active ? '启用' : '停用'}管理员「${row.display_name}」？${!active ? '\n停用后该账号 Token 立即失效。' : ''}`,
    `${active ? '启用' : '停用'}管理员账号`,
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => { throw new Error('cancelled') })
  try {
    await adminUserApi.setActive(row.id, active)
    row.is_active = active
    ElMessage.success(`管理员「${row.display_name}」已${active ? '启用' : '停用'}`)
  } catch (e) {
    if ((e as Error).message !== 'cancelled') throw e
  }
}

async function confirmResetPwd(row: AdminUser) {
  await ElMessageBox.confirm(
    `确认重置「${row.display_name}」的密码？系统将向 ${row.phone_masked} 发送临时密码。`,
    '重置密码',
    { confirmButtonText: '确认重置', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => { throw new Error('cancelled') })
  try {
    await adminUserApi.resetPassword(row.id)
    ElMessage.success('临时密码已发送至管理员手机号')
  } catch (e) {
    if ((e as Error).message !== 'cancelled') throw e
  }
}

// ── 新增管理员
const createAdminVisible = ref(false)
const adminForm = reactive({ username: '', display_name: '', phone: '', email: '' })

function openCreateAdmin() {
  Object.assign(adminForm, { username: '', display_name: '', phone: '', email: '' })
  createAdminVisible.value = true
}

async function doCreateAdmin() {
  if (!adminForm.username.trim() || !adminForm.display_name.trim() || !adminForm.phone.trim()) {
    ElMessage.warning('账号、显示名称、手机号为必填项')
    return
  }
  adminLoading.value = true
  try {
    const created = await adminUserApi.create({
      username: adminForm.username,
      display_name: adminForm.display_name,
      phone: adminForm.phone,
      email: adminForm.email || undefined,
    })
    adminUsers.value.push(created)
    createAdminVisible.value = false
    ElMessage.success('管理员账号已创建，初始密码已发送至手机')
  } finally { adminLoading.value = false }
}

// ═══════════════════════════════════════════════════════════════
// ── 跨 Tab 操作：绑定家长（从学生列表触发）─────────────────
// ═══════════════════════════════════════════════════════════════

const bindDialogVisible = ref(false)
const bindTarget = ref<Student | null>(null)
const bindPhone = ref('')

function openBindParent(row: Student) {
  bindTarget.value = row
  bindPhone.value = ''
  bindDialogVisible.value = true
}

async function doBindParent() {
  if (!bindPhone.value.trim()) {
    ElMessage.warning('请输入家长手机号')
    return
  }
  if (!bindTarget.value) return
  bindLoading.value = true
  try {
    await studentApi.bindParent(bindTarget.value.id, { parent_phone: bindPhone.value })
    // 更新本地计数
    const idx = students.value.findIndex(s => s.id === bindTarget.value!.id)
    if (idx !== -1) students.value[idx].parent_count = Math.min(2, students.value[idx].parent_count + 1)
    bindDialogVisible.value = false
    ElMessage.success('家长绑定成功')
  } finally { bindLoading.value = false }
}

// ── Tab 切换时按需加载数据 ───────────────────────────────────
watch(activeTab, (tab) => {
  if (tab === 'parents' && parents.value.length === 0) loadParents()
  if (tab === 'admins' && adminUsers.value.length === 0) loadAdmins()
})

onMounted(loadStudents)
</script>

<style lang="scss" scoped>
// ── Tab 栏 ───────────────────────────────────────────────────
.tab-bar {
  display: flex;
  border-bottom: 1px solid var(--border);
  padding: 0 16px;
}

.tab-item {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 13px 18px;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-2);
  background: none;
  border: none;
  border-bottom: 2px solid transparent;
  cursor: pointer;
  transition: all 0.15s;
  white-space: nowrap;

  &:hover { color: var(--text-1); }

  &.active {
    color: var(--indigo);
    border-bottom-color: var(--indigo);
    font-weight: 600;
  }
}

// ── 工具栏 ───────────────────────────────────────────────────
.tab-toolbar {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 16px;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

// ── 用户头像 ─────────────────────────────────────────────────
.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 9px;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  &--student { background: var(--indigo-light); color: var(--indigo); }
  &--parent  { background: var(--teal-dim);     color: var(--teal); }
  &--admin   { background: var(--purple-dim);   color: var(--purple); }
}

// ── 标签 ─────────────────────────────────────────────────────
.subject-tag {
  font-size: 11.5px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--r-pill);
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1px solid var(--indigo-border);
}

.tag-muted {
  font-size: 11.5px;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  background: var(--bg-muted);
  color: var(--text-3);
  border: 1.5px solid var(--border-hover);
}

.tag-pending {
  font-size: 10.5px;
  font-weight: 600;
  padding: 1px 7px;
  border-radius: var(--r-pill);
  background: var(--amber-dim);
  color: var(--amber);
  border: 1px solid var(--amber-border);
  margin-left: 6px;
}

.parent-count-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--indigo);
  font-family: var(--font-mono);

  &--none { color: var(--text-3); }
}

.bound-student-tag {
  font-size: 11.5px;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: var(--r-pill);
  background: var(--teal-dim);
  color: var(--teal);
  border: 1px solid var(--teal-border);
  cursor: default;
}

// ── 角色标签 ─────────────────────────────────────────────────
.role-badge {
  font-size: 11.5px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--super { background: var(--purple-dim);   color: var(--purple);  border-color: var(--purple-border); }
  &--admin { background: var(--indigo-light);  color: var(--indigo);  border-color: var(--indigo-border); }
}

// ── 状态点 ───────────────────────────────────────────────────
.status-dot {
  font-size: 12px;
  font-weight: 600;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &--ok  { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &--off { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }
}

// ── 绑定弹窗内样式 ───────────────────────────────────────────
.bind-info {
  font-size: 13.5px;
  color: var(--text-2);
  margin-bottom: 16px;

  strong { font-family: var(--font-mono); color: var(--text-1); }
}

.bind-form-label {
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  margin-bottom: 6px;
}

.bind-tip {
  font-size: 12px;
  color: var(--text-3);
  line-height: 1.5;
}

.bind-hint {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  padding: 10px 14px;
  background: var(--amber-dim);
  border: 1px solid var(--amber-border);
  border-radius: var(--r-lg);
  font-size: 13px;
  color: var(--amber);
}

// ── 新增管理员弹窗提示 ───────────────────────────────────────
.create-admin-tip {
  display: flex;
  align-items: flex-start;
  gap: 7px;
  padding: 10px 14px;
  background: var(--indigo-light);
  border: 1px solid var(--indigo-border);
  border-radius: var(--r-lg);
  font-size: 12.5px;
  color: var(--indigo);
  margin-top: 4px;
}
</style>
