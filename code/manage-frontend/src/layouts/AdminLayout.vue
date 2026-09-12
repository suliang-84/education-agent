<template>
  <div class="admin-shell" :class="{ collapsed: isCollapsed }">

    <!-- ── Sidebar ── -->
    <aside class="sidebar">
      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="sidebar-logo__icon">
          <svg width="18" height="18" viewBox="0 0 256 256" fill="none">
            <path fill="#fff" d="M 160 88 L 194 34 L 216 0 L 256 0 L 256 40 L 221.5 93.5 L 200 128 L 256 128 L 256 256 L 96 256 L 96 168 L 64.246 220 L 40 256 L 0 256 L 0 216 L 34 162 L 56 128 L 0 128 L 0 0 L 160 0 Z"/>
          </svg>
        </div>
        <span class="sidebar-logo__name">MESH Admin</span>
      </div>

      <!-- Nav -->
      <nav class="sidebar-nav">
        <div class="nav-section">
          <div class="nav-section__label">概览</div>
          <router-link to="/dashboard" class="nav-item" :class="{ active: route.path === '/dashboard' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <rect x="3" y="3" width="7" height="7" rx="1.5"/><rect x="14" y="3" width="7" height="7" rx="1.5"/>
                <rect x="3" y="14" width="7" height="7" rx="1.5"/><rect x="14" y="14" width="7" height="7" rx="1.5"/>
              </svg>
            </span>
            <span class="nav-item__label">数据看板</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section__label">题库</div>
          <router-link to="/questions" class="nav-item" :class="{ active: route.path.startsWith('/questions') }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
              </svg>
            </span>
            <span class="nav-item__label">题库管理</span>
          </router-link>
          <router-link to="/annotations" class="nav-item" :class="{ active: route.path === '/annotations' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.568 3H5.25A2.25 2.25 0 003 5.25v4.318c0 .597.237 1.17.659 1.591l9.581 9.581c.699.699 1.78.872 2.607.33a18.095 18.095 0 005.223-5.223c.542-.827.369-1.908-.33-2.607L9.568 3z"/>
                <path stroke-linecap="round" stroke-linejoin="round" d="M6 6h.008v.008H6V6z"/>
              </svg>
            </span>
            <span class="nav-item__label">AI 标注审核</span>
            <span class="nav-badge" v-if="!isCollapsed">45</span>
          </router-link>
          <router-link to="/cognitive-test" class="nav-item" :class="{ active: route.path === '/cognitive-test' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"/>
              </svg>
            </span>
            <span class="nav-item__label">五力测试题</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section__label">配置</div>
          <router-link to="/training-config" class="nav-item" :class="{ active: route.path === '/training-config' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 6h9.75M10.5 6a1.5 1.5 0 11-3 0m3 0a1.5 1.5 0 10-3 0M3.75 6H7.5m3 12h9.75m-9.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-3.75 0H7.5m9-6h3.75m-3.75 0a1.5 1.5 0 01-3 0m3 0a1.5 1.5 0 00-3 0m-9.75 0h9.75"/>
              </svg>
            </span>
            <span class="nav-item__label">训练配置</span>
          </router-link>
          <router-link to="/system-config" class="nav-item" :class="{ active: route.path === '/system-config' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z"/>
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
              </svg>
            </span>
            <span class="nav-item__label">系统参数</span>
          </router-link>
        </div>

        <div class="nav-section">
          <div class="nav-section__label">运营</div>
          <router-link to="/students" class="nav-item" :class="{ active: route.path.startsWith('/students') }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15 19.128a9.38 9.38 0 002.625.372 9.337 9.337 0 004.121-.952 4.125 4.125 0 00-7.533-2.493M15 19.128v-.003c0-1.113-.285-2.16-.786-3.07M15 19.128v.106A12.318 12.318 0 018.624 21c-2.331 0-4.512-.645-6.374-1.766l-.001-.109a6.375 6.375 0 0111.964-3.07M12 6.375a3.375 3.375 0 11-6.75 0 3.375 3.375 0 016.75 0zm8.25 2.25a2.625 2.625 0 11-5.25 0 2.625 2.625 0 015.25 0z"/>
              </svg>
            </span>
            <span class="nav-item__label">用户管理</span>
          </router-link>
          <router-link to="/audit-logs" class="nav-item" :class="{ active: route.path === '/audit-logs' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12h3.75M9 15h3.75M9 18h3.75m3 .75H18a2.25 2.25 0 002.25-2.25V6.108c0-1.135-.845-2.098-1.976-2.192a48.424 48.424 0 00-1.123-.08m-5.801 0c-.065.21-.1.433-.1.664 0 .414.336.75.75.75h4.5a.75.75 0 00.75-.75 2.25 2.25 0 00-.1-.664m-5.8 0A2.251 2.251 0 0113.5 2.25H15c1.012 0 1.867.668 2.15 1.586m-5.8 0c-.376.023-.75.05-1.124.08C9.095 4.01 8.25 4.973 8.25 6.108V8.25m0 0H4.875c-.621 0-1.125.504-1.125 1.125v11.25c0 .621.504 1.125 1.125 1.125h9.75c.621 0 1.125-.504 1.125-1.125V9.375c0-.621-.504-1.125-1.125-1.125H8.25zM6.75 12h.008v.008H6.75V12zm0 3h.008v.008H6.75V15zm0 3h.008v.008H6.75V18z"/>
              </svg>
            </span>
            <span class="nav-item__label">审计日志</span>
          </router-link>
        </div>
      </nav>

      <!-- Collapse button -->
      <button class="collapse-btn" @click="isCollapsed = !isCollapsed">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path stroke-linecap="round" stroke-linejoin="round" :d="isCollapsed ? 'M13 5l7 7-7 7' : 'M11 5l-7 7 7 7'"/>
        </svg>
      </button>

      <!-- User info -->
      <div class="sidebar-user">
        <div class="user-avatar">{{ userInitial }}</div>
        <div class="user-info" v-if="!isCollapsed">
          <div class="user-name">{{ authStore.user?.username }}</div>
          <div class="user-role">超级管理员</div>
        </div>
        <el-dropdown @command="handleCommand" v-if="!isCollapsed">
          <button class="user-menu-btn">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 6.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 12.75a.75.75 0 110-1.5.75.75 0 010 1.5zM12 18.75a.75.75 0 110-1.5.75.75 0 010 1.5z"/>
            </svg>
          </button>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item command="logout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </div>
    </aside>

    <!-- ── Main ── -->
    <div class="main-wrap">
      <!-- Content -->
      <main class="content-area">
        <router-view />
      </main>
    </div>

  </div>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapsed = ref(false)

const userInitial = computed(() => authStore.user?.username?.[0]?.toUpperCase() || 'A')

async function handleCommand(cmd: string) {
  if (cmd === 'logout') {
    await ElMessageBox.confirm('确认退出登录？', '提示', { type: 'warning' })
    await authApi.logout().catch(() => {})
    authStore.clearAuth()
    router.push('/login')
    ElMessage.success('已退出登录')
  }
}
</script>

<style lang="scss" scoped>
// ── Shell ──────────────────────────────────────────────────
.admin-shell {
  display: flex;
  height: 100dvh;
  overflow: hidden;
  background: var(--bg-page);

  // Collapsed state — controls nested element visibility
  &.collapsed {
    .sidebar          { width: var(--sidebar-w-collapsed); }
    .sidebar-logo__name { opacity: 0; pointer-events: none; }
    .nav-section__label { opacity: 0; }
    .nav-item__label    { opacity: 0; pointer-events: none; }
  }
}

// ── Sidebar ─────────────────────────────────────────────────
.sidebar {
  width: var(--sidebar-w);
  height: 100%;
  background: var(--bg-surface);
  border-right: 1px solid var(--border);
  display: flex;
  flex-direction: column;
  flex-shrink: 0;
  overflow: hidden;
  transition: width var(--t-slow) var(--ease-out);
  box-shadow: 2px 0 12px rgba(79, 70, 229, 0.05);
}

// Logo
.sidebar-logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 0 16px;
  height: var(--header-h);
  border-bottom: 1px solid var(--border);
  flex-shrink: 0;
  overflow: hidden;

  &__icon {
    width: 32px;
    height: 32px;
    background: var(--indigo);
    border-radius: 10px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    box-shadow: 0 2px 8px rgba(79, 70, 229, 0.35);
  }

  &__name {
    font-size: 14px;
    font-weight: 700;
    color: var(--text-1);
    letter-spacing: -0.02em;
    white-space: nowrap;
    transition: opacity var(--t-base);
  }
}

// Nav
.sidebar-nav {
  flex: 1;
  overflow-y: auto;
  overflow-x: hidden;
  padding: 12px 10px;
  display: flex;
  flex-direction: column;
  gap: 18px;
}

.nav-section {
  display: flex;
  flex-direction: column;
  gap: 2px;

  &__label {
    font-size: 11px;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 0.08em;
    color: var(--text-3);
    padding: 0 8px 6px;
    white-space: nowrap;
    transition: opacity var(--t-base);
  }
}

.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 9px 10px;
  border-radius: 12px;
  color: var(--text-2);
  text-decoration: none;
  font-size: 13.5px;
  font-weight: 500;
  transition: all var(--t-fast);
  white-space: nowrap;
  overflow: hidden;
  position: relative;

  &:hover {
    background: var(--bg-muted);
    color: var(--text-1);
  }

  &.active {
    background: var(--indigo-light);
    color: var(--indigo);
    font-weight: 600;
  }

  &__icon {
    width: 20px;
    height: 20px;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }

  &__label {
    flex: 1;
    transition: opacity var(--t-base);
  }
}

.nav-badge {
  background: var(--pink-light);
  color: var(--pink);
  border-radius: var(--r-pill);
  font-size: 11px;
  font-weight: 700;
  padding: 0 6px;
  height: 18px;
  line-height: 18px;
  flex-shrink: 0;
  font-family: var(--font-mono);
}

// Collapse button
.collapse-btn {
  margin: 8px 10px;
  padding: 8px;
  background: var(--bg-muted);
  border: none;
  border-radius: 10px;
  color: var(--text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all var(--t-fast);
  flex-shrink: 0;

  &:hover {
    background: var(--indigo-light);
    color: var(--indigo);
  }
}

// User
.sidebar-user {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 14px 12px 16px;
  border-top: 1px solid var(--border);
  flex-shrink: 0;
  overflow: hidden;
}

.user-avatar {
  width: 32px;
  height: 32px;
  border-radius: 10px;
  background: var(--indigo);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  box-shadow: 0 2px 8px rgba(79, 70, 229, 0.3);

  &--sm {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    font-size: 11.5px;
  }
}

.user-info {
  flex: 1;
  min-width: 0;
  overflow: hidden;
}

.user-name {
  font-size: 13px;
  font-weight: 600;
  color: var(--text-1);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.user-role {
  font-size: 11.5px;
  color: var(--text-3);
  margin-top: 1px;
}

.user-menu-btn {
  background: transparent;
  border: none;
  color: var(--text-3);
  cursor: pointer;
  display: flex;
  align-items: center;
  padding: 4px;
  border-radius: var(--r-sm);
  transition: all var(--t-fast);
  flex-shrink: 0;

  &:hover {
    background: var(--bg-muted);
    color: var(--text-1);
  }
}

// ── Main ────────────────────────────────────────────────────
.main-wrap {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  min-width: 0;
}

// Content area
.content-area {
  flex: 1;
  overflow-y: auto;
  padding: 26px 28px;
  background: var(--bg-page);
}
</style>
