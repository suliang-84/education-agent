<template>
  <el-container class="admin-layout">
    <!-- ── 左侧导航 ── -->
    <el-aside :width="isCollapsed ? '64px' : '240px'" class="sidebar">

      <!-- Logo -->
      <div class="sidebar-logo">
        <div class="logo-mark">
          <span class="logo-m">M</span>
        </div>
        <transition name="slide-fade">
          <span v-if="!isCollapsed" class="logo-text">MESH 管理平台</span>
        </transition>
        <el-icon class="collapse-btn" @click="isCollapsed = !isCollapsed">
          <component :is="isCollapsed ? Expand : Fold" />
        </el-icon>
      </div>

      <!-- 导航菜单 -->
      <el-menu
        :default-active="activeMenu"
        :collapse="isCollapsed"
        :collapse-transition="false"
        router
        class="sidebar-menu"
        background-color="#0B1A35"
        text-color="rgba(255,255,255,0.42)"
        active-text-color="#FFFFFF"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataAnalysis /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>

        <el-sub-menu index="questions-group">
          <template #title>
            <el-icon><Document /></el-icon>
            <span>题库管理</span>
          </template>
          <el-menu-item index="/questions">题目列表</el-menu-item>
          <el-menu-item index="/questions/create">新增题目</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/annotations">
          <el-icon><Check /></el-icon>
          <template #title>AI 标注审核</template>
        </el-menu-item>

        <el-menu-item index="/cognitive-test">
          <el-icon><EditPen /></el-icon>
          <template #title>五力测试题</template>
        </el-menu-item>

        <el-menu-item index="/training-config">
          <el-icon><Setting /></el-icon>
          <template #title>训练配置</template>
        </el-menu-item>

        <el-sub-menu index="config-group">
          <template #title>
            <el-icon><Tools /></el-icon>
            <span>系统配置</span>
          </template>
          <el-menu-item index="/system-config">系统参数</el-menu-item>
          <el-menu-item index="/strategies">启发策略</el-menu-item>
        </el-sub-menu>

        <el-menu-item index="/students">
          <el-icon><User /></el-icon>
          <template #title>学生管理</template>
        </el-menu-item>

        <el-menu-item index="/audit-logs">
          <el-icon><List /></el-icon>
          <template #title>审计日志</template>
        </el-menu-item>
      </el-menu>

      <!-- 五力认知星图 (expanded only) -->
      <transition name="fade">
        <div v-if="!isCollapsed" class="constellation-panel">
          <div class="cst-title">五力认知图谱</div>
          <svg viewBox="0 0 150 135" class="cst-svg" xmlns="http://www.w3.org/2000/svg">
            <!-- Pentagon edges -->
            <line class="c-edge" x1="75" y1="10" x2="132" y2="52" style="animation-delay:0s" />
            <line class="c-edge" x1="132" y1="52" x2="110" y2="118" style="animation-delay:0.18s" />
            <line class="c-edge" x1="110" y1="118" x2="40" y2="118" style="animation-delay:0.36s" />
            <line class="c-edge" x1="40" y1="118" x2="18" y2="52" style="animation-delay:0.54s" />
            <line class="c-edge" x1="18" y1="52" x2="75" y2="10" style="animation-delay:0.72s" />

            <!-- Node glows (larger circle, dim) -->
            <circle class="c-glow" cx="75"  cy="10"  r="10" fill="#4361EE" style="animation-delay:1.0s" />
            <circle class="c-glow" cx="132" cy="52"  r="10" fill="#7B2FBE" style="animation-delay:1.1s" />
            <circle class="c-glow" cx="110" cy="118" r="10" fill="#10B981" style="animation-delay:1.2s" />
            <circle class="c-glow" cx="40"  cy="118" r="10" fill="#F59E0B" style="animation-delay:1.3s" />
            <circle class="c-glow" cx="18"  cy="52"  r="10" fill="#EF4444" style="animation-delay:1.4s" />

            <!-- Ripple rings -->
            <circle class="c-ripple" cx="75"  cy="10"  r="5" stroke="#4361EE" style="animation-delay:1.8s" />
            <circle class="c-ripple" cx="132" cy="52"  r="5" stroke="#7B2FBE" style="animation-delay:2.2s" />
            <circle class="c-ripple" cx="110" cy="118" r="5" stroke="#10B981" style="animation-delay:2.6s" />
            <circle class="c-ripple" cx="40"  cy="118" r="5" stroke="#F59E0B" style="animation-delay:3.0s" />
            <circle class="c-ripple" cx="18"  cy="52"  r="5" stroke="#EF4444" style="animation-delay:3.4s" />

            <!-- Core nodes -->
            <circle class="c-node" cx="75"  cy="10"  r="5"  fill="#4361EE" style="animation-delay:0.9s" />
            <circle class="c-node" cx="132" cy="52"  r="5"  fill="#7B2FBE" style="animation-delay:1.0s" />
            <circle class="c-node" cx="110" cy="118" r="5"  fill="#10B981" style="animation-delay:1.1s" />
            <circle class="c-node" cx="40"  cy="118" r="5"  fill="#F59E0B" style="animation-delay:1.2s" />
            <circle class="c-node" cx="18"  cy="52"  r="5"  fill="#EF4444" style="animation-delay:1.3s" />

            <!-- Labels -->
            <text x="75"  y="3"   class="c-label" text-anchor="middle" fill="#4361EE">洞察</text>
            <text x="148" y="56"  class="c-label" text-anchor="start"  fill="#7B2FBE">结构</text>
            <text x="112" y="130" class="c-label" text-anchor="middle" fill="#10B981">推断</text>
            <text x="38"  y="130" class="c-label" text-anchor="middle" fill="#F59E0B">适应</text>
            <text x="2"   y="56"  class="c-label" text-anchor="start"  fill="#EF4444">迁移</text>
          </svg>
        </div>
      </transition>

      <!-- 底部用户信息 -->
      <div class="sidebar-footer" v-if="!isCollapsed">
        <div class="admin-info">
          <el-avatar :size="28" class="admin-avatar">
            {{ adminInfo?.display_name?.charAt(0) || 'A' }}
          </el-avatar>
          <span class="admin-name">{{ adminInfo?.username || 'admin' }}</span>
          <el-button link @click="handleLogout" class="logout-btn">退出</el-button>
        </div>
      </div>
    </el-aside>

    <!-- ── 右侧主区域 ── -->
    <el-container class="main-container">
      <!-- Header -->
      <el-header class="admin-header">
        <div class="header-left">
          <el-breadcrumb separator="/">
            <el-breadcrumb-item
              v-for="(item, index) in breadcrumbs"
              :key="index"
            >{{ item }}</el-breadcrumb-item>
          </el-breadcrumb>
        </div>
        <div class="header-right">
          <el-tag size="small" class="admin-role-tag">SUPER_ADMIN</el-tag>
          <span class="admin-username">{{ adminInfo?.display_name || '系统管理员' }}</span>
          <el-button link @click="handleLogout" class="header-logout-btn">
            <el-icon><SwitchButton /></el-icon>
            退出登录
          </el-button>
        </div>
      </el-header>

      <!-- 内容区 -->
      <el-main class="admin-main">
        <router-view v-slot="{ Component }">
          <Transition name="page" mode="out-in">
            <component :is="Component" :key="$route.path" />
          </Transition>
        </router-view>
      </el-main>
    </el-container>
  </el-container>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import {
  DataAnalysis, Document, Check, EditPen, Setting, Tools,
  User, List, Expand, Fold, SwitchButton
} from '@element-plus/icons-vue'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()

const isCollapsed = ref(false)
const adminInfo = computed(() => authStore.adminInfo)
const activeMenu = computed(() => route.path)
const breadcrumbs = computed(() => {
  return (route.meta.breadcrumb as string[]) || [route.meta.title as string || '']
})

async function handleLogout() {
  authStore.clearAuth()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  height: 100vh;
  overflow: hidden;
}

/* ──────────────────────────────────────────
   Sidebar — Deep Navy with Knowledge Constellation
──────────────────────────────────────────── */
.sidebar {
  background: #0B1A35;
  background-image:
    /* Subtle dot grid */
    radial-gradient(rgba(67, 97, 238, 0.07) 1px, transparent 1px),
    /* Blue halo at top */
    radial-gradient(ellipse at 50% -5%, rgba(67, 97, 238, 0.18) 0%, transparent 55%);
  background-size: 20px 20px, 100% 100%;
  transition: width 0.3s ease;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  flex-shrink: 0;
  border-right: 1px solid rgba(67, 97, 238, 0.1);
}

/* Logo */
.sidebar-logo {
  height: 64px;
  display: flex;
  align-items: center;
  padding: 0 14px;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
}

.logo-mark {
  width: 34px;
  height: 34px;
  background: linear-gradient(135deg, #4361EE 0%, #7B2FBE 100%);
  border-radius: 9px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  animation: logoBreathe 3.5s ease-in-out infinite;
}

.logo-m {
  font-family: 'Outfit', sans-serif;
  color: #FFFFFF;
  font-size: 17px;
  font-weight: 800;
  letter-spacing: -1px;
}

.logo-text {
  font-family: 'Outfit', sans-serif;
  color: rgba(255, 255, 255, 0.88);
  font-weight: 600;
  font-size: 14px;
  white-space: nowrap;
  flex: 1;
  letter-spacing: 0.2px;
}

.collapse-btn {
  color: rgba(255, 255, 255, 0.22);
  cursor: pointer;
  margin-left: auto;
  flex-shrink: 0;
  transition: color 0.2s;
}
.collapse-btn:hover { color: rgba(255, 255, 255, 0.65); }

/* Menu */
.sidebar-menu {
  flex: 1;
  border-right: none !important;
  overflow-y: auto;
  overflow-x: hidden;
}
.sidebar-menu::-webkit-scrollbar { width: 3px; }
.sidebar-menu::-webkit-scrollbar-thumb {
  background: rgba(67, 97, 238, 0.18);
  border-radius: 2px;
}

/* Active item: indigo gradient + glowing left bar */
:deep(.el-menu-item.is-active) {
  background: linear-gradient(90deg, rgba(67, 97, 238, 0.22) 0%, rgba(67, 97, 238, 0.04) 100%) !important;
  border-left: 2px solid #4361EE !important;
  position: relative;
}
:deep(.el-menu-item.is-active)::before {
  content: '';
  position: absolute;
  left: 0;
  top: 22%;
  height: 56%;
  width: 2px;
  background: #4361EE;
  border-radius: 0 2px 2px 0;
  box-shadow: 0 0 10px rgba(67, 97, 238, 0.85), 0 0 22px rgba(67, 97, 238, 0.4);
  animation: activePulse 2.5s ease-in-out infinite;
}

:deep(.el-sub-menu__title:hover),
:deep(.el-menu-item:hover) {
  background-color: rgba(255, 255, 255, 0.05) !important;
}

:deep(.el-sub-menu .el-menu) {
  background-color: rgba(0, 0, 0, 0.2) !important;
}
:deep(.el-sub-menu .el-menu-item) {
  color: rgba(255, 255, 255, 0.32) !important;
  font-size: 13px;
  padding-left: 48px !important;
}
:deep(.el-sub-menu .el-menu-item.is-active) { color: #FFFFFF !important; }
:deep(.el-sub-menu__title) { font-size: 13.5px; }
:deep(.el-menu-item) { font-size: 13.5px; }

/* ── Knowledge Constellation Panel ── */
.constellation-panel {
  padding: 14px 16px 8px;
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  flex-shrink: 0;
}

.cst-title {
  font-family: 'DM Sans', sans-serif;
  font-size: 10px;
  font-weight: 500;
  color: rgba(255, 255, 255, 0.25);
  letter-spacing: 1px;
  text-transform: uppercase;
  margin-bottom: 10px;
  text-align: center;
}

.cst-svg {
  width: 100%;
  height: auto;
  overflow: visible;
}

/* Edges — draw in sequence */
.c-edge {
  stroke: rgba(255, 255, 255, 0.1);
  stroke-width: 1;
  stroke-dasharray: 150;
  stroke-dashoffset: 150;
  opacity: 0;
  animation: edgeDraw 0.7s ease-out forwards;
}

/* Glow halos behind nodes */
.c-glow {
  opacity: 0;
  animation: nodeAppear 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
  filter: blur(4px);
}
.c-glow { opacity: 0.18 !important; }

/* Ripple rings */
.c-ripple {
  fill: none;
  stroke-width: 1.5;
  opacity: 0;
  transform-origin: center;
  transform-box: fill-box;
  animation: nodeRipple 2.5s ease-out infinite;
}

/* Solid nodes */
.c-node {
  opacity: 0;
  transform-origin: center;
  transform-box: fill-box;
  animation: nodeAppear 0.4s cubic-bezier(0.16, 1, 0.3, 1) both;
}

/* Labels */
.c-label {
  font-size: 7px;
  font-family: 'DM Sans', sans-serif;
  opacity: 0.65;
}

/* ── Sidebar footer ── */
.sidebar-footer {
  border-top: 1px solid rgba(255, 255, 255, 0.05);
  padding: 12px 14px;
  flex-shrink: 0;
}

.admin-info { display: flex; align-items: center; gap: 8px; }

.admin-avatar {
  background: linear-gradient(135deg, #4361EE, #7B2FBE) !important;
  color: #FFFFFF !important;
  flex-shrink: 0;
  font-size: 12px !important;
  font-weight: 800 !important;
}

.admin-name {
  color: rgba(255, 255, 255, 0.4);
  font-size: 13px;
  flex: 1;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.logout-btn {
  color: rgba(255, 255, 255, 0.22) !important;
  font-size: 12px;
  flex-shrink: 0;
  transition: color 0.2s !important;
}
.logout-btn:hover { color: rgba(255, 255, 255, 0.65) !important; }

/* Slide-fade transition for logo text */
.slide-fade-enter-active { transition: all 0.22s cubic-bezier(0.16, 1, 0.3, 1); }
.slide-fade-leave-active { transition: all 0.15s ease; }
.slide-fade-enter-from,
.slide-fade-leave-to { opacity: 0; transform: translateX(-8px); }

/* ── Main container ── */
.main-container {
  flex: 1;
  overflow: hidden;
  display: flex;
  flex-direction: column;
}

/* ── Header — light glass ── */
.admin-header {
  height: 56px !important;
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(16px);
  -webkit-backdrop-filter: blur(16px);
  border-bottom: 1px solid rgba(67, 97, 238, 0.08);
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  flex-shrink: 0;
  box-shadow: 0 1px 0 rgba(67, 97, 238, 0.05);
}

.header-left { display: flex; align-items: center; }
.header-right { display: flex; align-items: center; gap: 12px; }

.admin-role-tag {
  font-size: 10px !important;
  font-weight: 700 !important;
  letter-spacing: 0.5px;
  border-color: rgba(67, 97, 238, 0.25) !important;
  color: #4361EE !important;
  background: rgba(67, 97, 238, 0.07) !important;
}

.admin-username {
  font-size: 13px;
  color: var(--text-secondary);
  font-weight: 500;
}

.header-logout-btn {
  color: rgba(67, 97, 238, 0.4) !important;
  font-size: 13px;
  transition: color 0.2s !important;
}
.header-logout-btn:hover { color: #4361EE !important; }

/* ── Main content ── */
.admin-main {
  flex: 1;
  background: var(--bg-base, #F5F8FF);
  overflow-y: auto;
  padding: 24px;
}

/* Fade for constellation */
.fade-enter-active, .fade-leave-active { transition: opacity 0.2s; }
.fade-enter-from, .fade-leave-to { opacity: 0; }
</style>
