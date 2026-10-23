<template>
  <div class="page-root">
    <div class="inner-toolbar">
      <div style="flex:1" />
      <el-button v-if="isSuperAdmin" type="primary" @click="openCreate">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        新增管理员
      </el-button>
    </div>
    <div class="surface surface--table">
      <el-table :data="adminUsers" v-loading="loading" style="width:100%">
        <el-table-column label="序号" width="60" align="center">
          <template #default="{ $index }">
            <span class="num" style="color:var(--text-3);font-size:12px">{{ $index + 1 }}</span>
          </template>
        </el-table-column>

        <el-table-column label="账号" width="130">
          <template #default="{ row }">
            <span class="mono" style="color:var(--indigo);font-weight:600">{{ row.username }}</span>
          </template>
        </el-table-column>

        <el-table-column label="显示名称" width="140">
          <template #default="{ row }">
            <div style="display:flex;align-items:center;gap:8px">
              <div class="user-avatar user-avatar--admin">{{ row.display_name[0] }}</div>
              <span style="font-weight:600;color:var(--text-1)">{{ row.display_name }}</span>
            </div>
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

        <el-table-column label="操作" width="200" align="center" fixed="right">
          <template #default="{ row }">
            <el-button v-if="row.is_active === 1" text size="small" style="color:var(--amber)" @click="toggleAdmin(row, 0)">
              <SvgIcon name="pause" :size="18" color="var(--amber)" title="停用" />
            </el-button>
            <el-button v-if="row.is_active === 0" text size="small" style="color:var(--green)" @click="toggleAdmin(row, 1)">
              <SvgIcon name="play" :size="18" color="var(--green)" title="启用" />
            </el-button>
            <el-button text size="small" style="color:var(--indigo)" @click="confirmResetPwd(row)">重置密码</el-button>
            <el-button v-if="row.is_active === 0" text size="small" style="color:var(--red)" @click="confirmDelete(row)">
              <SvgIcon name="delete" :size="18" color="var(--red)" title="删除" />
            </el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- ── 新增管理员弹窗 ── -->
    <el-dialog v-model="createVisible" title="新增管理员账号" width="480px" :close-on-click-modal="false">
      <el-form :model="form" label-width="90px" @submit.prevent>
        <el-form-item label="登录账号">
          <el-input v-model="form.username" placeholder="仅字母、数字、下划线" />
        </el-form-item>
        <el-form-item label="显示名称">
          <el-input v-model="form.display_name" placeholder="如：运营专员" />
        </el-form-item>
        <el-form-item label="手机号">
          <el-input v-model="form.phone" placeholder="11位手机号" maxlength="11" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="form.email" placeholder="选填" />
        </el-form-item>
        <el-form-item label="密码">
          <el-input v-model="form.password" type="password" placeholder="请输入密码" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="form.confirm_password" type="password" placeholder="再次输入密码" show-password />
          <div v-if="form.confirm_password && form.password !== form.confirm_password"
               style="color:var(--red);font-size:12px;margin-top:4px">
            两次密码输入不一致
          </div>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="createVisible = false">取消</el-button>
        <el-button type="primary" :loading="createLoading" @click="doCreate">创建账号</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { adminUserApi } from '@/api'
import type { AdminUser } from '@/types'
import { fromNow } from '@/utils/format'
import { useAuthStore } from '@/stores/auth'

const authStore = useAuthStore()
const isSuperAdmin = authStore.isSuperAdmin

const loading = ref(false)
const adminUsers = ref<AdminUser[]>([])

async function loadData() {
  loading.value = true
  try {
    const res = await adminUserApi.getList()
    adminUsers.value = res.list
  } finally { loading.value = false }
}

async function toggleAdmin(row: AdminUser, active: 0 | 1) {
  const label = active === 1 ? '启用' : '停用'
  await ElMessageBox.confirm(
    `确认${label}管理员「${row.display_name}」？${active === 0 ? '\n停用后该账号 Token 立即失效。' : ''}`,
    `${label}管理员账号`,
    { confirmButtonText: '确认', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => { throw new Error('cancelled') })
  try {
    await adminUserApi.setActive(row.id, active)
    row.is_active = active
    ElMessage.success(`管理员「${row.display_name}」已${label}`)
  } catch (e) { if ((e as Error).message !== 'cancelled') throw e }
}

async function confirmResetPwd(row: AdminUser) {
  await ElMessageBox.confirm(
    `确认重置「${row.display_name}」的密码？密码将重置为 123456。`,
    '重置密码',
    { confirmButtonText: '确认重置', cancelButtonText: '取消', type: 'warning' }
  ).catch(() => { throw new Error('cancelled') })
  try {
    await adminUserApi.resetPassword(row.id)
    ElMessage.success('密码已重置为 123456')
  } catch (e) { if ((e as Error).message !== 'cancelled') throw e }
}

async function confirmDelete(row: AdminUser) {
  await ElMessageBox.confirm(
    `确认删除管理员「${row.display_name}」？删除后不可恢复，该账号的操作记录将予以保留。`,
    '删除管理员账号',
    { confirmButtonText: '确认删除', cancelButtonText: '取消', type: 'error' }
  ).catch(() => { throw new Error('cancelled') })
  try {
    await adminUserApi.delete(row.id)
    ElMessage.success('管理员账号已删除')
    await loadData()
  } catch (e) { if ((e as Error).message !== 'cancelled') throw e }
}

// ── 新增 ─────────────────────────────────────────────────────
const createVisible = ref(false)
const createLoading = ref(false)
const form = reactive({ username: '', display_name: '', phone: '', email: '', password: '', confirm_password: '' })

function openCreate() {
  Object.assign(form, { username: '', display_name: '', phone: '', email: '', password: '', confirm_password: '' })
  createVisible.value = true
}

async function doCreate() {
  if (!form.username.trim() || !form.display_name.trim() || !form.phone.trim()) {
    ElMessage.warning('账号、显示名称、手机号为必填项'); return
  }
  if (!form.password) { ElMessage.warning('请输入密码'); return }
  if (form.password !== form.confirm_password) { ElMessage.warning('两次密码输入不一致'); return }
  createLoading.value = true
  try {
    await adminUserApi.create({
      username: form.username, display_name: form.display_name,
      phone: form.phone, email: form.email || undefined, password: form.password,
    })
    createVisible.value = false
    ElMessage.success('管理员账号已创建')
    await loadData()
  } finally { createLoading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.user-avatar {
  width: 32px; height: 32px; border-radius: 9px;
  font-size: 13px; font-weight: 700;
  display: flex; align-items: center; justify-content: center; flex-shrink: 0;
  &--admin { background: var(--purple-dim); color: var(--purple); }
}

.status-dot {
  font-size: 12px; font-weight: 600; padding: 3px 10px;
  border-radius: var(--r-pill); border: 1.5px solid;
  &--ok  { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &--off { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }
}
</style>
