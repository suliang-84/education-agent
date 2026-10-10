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

      <!-- Bottom controls: theme toggle + collapse -->
      <div class="sidebar-controls">
        <button class="theme-btn" @click="toggleTheme" :title="isDark ? '切换浅色模式' : '切换深色模式'">
          <!-- 月亮（当前浅色，点击切深色） -->
          <svg v-if="!isDark" width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21.752 15.002A9.718 9.718 0 0118 15.75c-5.385 0-9.75-4.365-9.75-9.75 0-1.33.266-2.597.748-3.752A9.753 9.753 0 003 11.25C3 16.635 7.365 21 12.75 21a9.753 9.753 0 009.002-5.998z"/>
          </svg>
          <!-- 太阳（当前深色，点击切浅色） -->
          <svg v-else width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 3v2.25m6.364.386l-1.591 1.591M21 12h-2.25m-.386 6.364l-1.591-1.591M12 18.75V21m-4.773-4.227l-1.591 1.591M5.25 12H3m4.227-4.773L5.636 5.636M15.75 12a3.75 3.75 0 11-7.5 0 3.75 3.75 0 017.5 0z"/>
          </svg>
        </button>
        <button class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path stroke-linecap="round" stroke-linejoin="round" :d="isCollapsed ? 'M13 5l7 7-7 7' : 'M11 5l-7 7 7 7'"/>
          </svg>
        </button>
      </div>

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
import { ref, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import { authApi } from '@/api'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const isCollapsed = ref(false)

// ── 主题切换 ─────────────────────────────────────────────────
const isDark = ref(false)

function applyTheme(dark: boolean) {
  document.documentElement.setAttribute('data-theme', dark ? 'dark' : 'light')
  isDark.value = dark
}

function toggleTheme() {
  const next = !isDark.value
  applyTheme(next)
  localStorage.setItem('mesh-theme', next ? 'dark' : 'light')
}

onMounted(() => {
  const saved = localStorage.getItem('mesh-theme')
  applyTheme(saved === 'dark')
})

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
    .sidebar            { width: var(--sidebar-w-collapsed); }
    .sidebar-logo__name { opacity: 0; pointer-events: none; }
    .nav-section__label { opacity: 0; }
    .nav-item__label    { opacity: 0; pointer-events: none; }
    // 折叠时 theme-btn 依然完整显示（只有图标，本就无文字）
    .sidebar-controls   { padding: 6px 8px; gap: 2px; }
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

// Sidebar bottom controls（主题切换 + 折叠）
.sidebar-controls {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 6px 10px;
  flex-shrink: 0;
}

.theme-btn,
.collapse-btn {
  flex: 1;
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
  min-height: 0;   // 允许 flex 子元素在垂直方向收缩
  min-width: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

// Content area — 固定高度滚动容器，内容超出时出现滚动条
.content-area {
  flex: 1;
  min-height: 0;          // flex 子元素必须设置，否则无法收缩
  overflow-y: auto;
  padding: 15px;
  padding-bottom: 15px;   // 明确底部边距
  background: var(--bg-page);
}
</style>
