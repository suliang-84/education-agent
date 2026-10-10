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
          <div class="nav-section__label">题库</div>
          <router-link to="/questions/entry" class="nav-item" :class="{ active: route.name === 'QuestionEntry' || route.name === 'QuestionCreate' || route.name === 'QuestionEdit' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
              </svg>
            </span>
            <span class="nav-item__label">训练题录入</span>
          </router-link>
          <router-link to="/questions" class="nav-item" :class="{ active: route.name === 'QuestionList' || route.name === 'QuestionReview' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 14.25v-2.625a3.375 3.375 0 00-3.375-3.375h-1.5A1.125 1.125 0 0113.5 7.125v-1.5a3.375 3.375 0 00-3.375-3.375H8.25m0 12.75h7.5m-7.5 3H12M10.5 2.25H5.625c-.621 0-1.125.504-1.125 1.125v17.25c0 .621.504 1.125 1.125 1.125h12.75c.621 0 1.125-.504 1.125-1.125V11.25a9 9 0 00-9-9z"/>
              </svg>
            </span>
            <span class="nav-item__label">训练题管理</span>
          </router-link>
          <!-- AI 标注审核已并入训练题管理（v1.2.0），此入口已移除 -->
          <router-link to="/cognitive-test" class="nav-item" :class="{ active: route.path === '/cognitive-test' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M3.75 12h16.5m-16.5 3.75h16.5M3.75 19.5h16.5M5.625 4.5h12.75a1.875 1.875 0 010 3.75H5.625a1.875 1.875 0 010-3.75z"/>
              </svg>
            </span>
            <span class="nav-item__label">测试题管理</span>
          </router-link>
        </div>

        <!-- 数据看板、训练配置、系统参数、审计日志暂时隐藏 -->
        <div class="nav-section">
          <div class="nav-section__label">运营</div>
          <router-link to="/students" class="nav-item" :class="{ active: route.path === '/students' || route.path.startsWith('/students/') }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5"/>
              </svg>
            </span>
            <span class="nav-item__label">学生管理</span>
          </router-link>
          <router-link to="/parents" class="nav-item" :class="{ active: route.path === '/parents' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0zM4.501 20.118a7.5 7.5 0 0114.998 0A17.933 17.933 0 0112 21.75c-2.676 0-5.216-.584-7.499-1.632z"/>
              </svg>
            </span>
            <span class="nav-item__label">家长管理</span>
          </router-link>
          <router-link to="/admin-users" class="nav-item" :class="{ active: route.path === '/admin-users' }">
            <span class="nav-item__icon">
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
                <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75m-3-7.036A11.959 11.959 0 013.598 6 11.99 11.99 0 003 9.749c0 5.592 3.824 10.29 9 11.623 5.176-1.332 9-6.03 9-11.622 0-1.31-.21-2.571-.598-3.751h-.152c-3.196 0-6.1-1.248-8.25-3.285z"/>
              </svg>
            </span>
            <span class="nav-item__label">管理员管理</span>
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
