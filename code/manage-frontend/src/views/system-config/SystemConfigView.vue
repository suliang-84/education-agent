<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">系统参数配置</h1>
        <p class="page-subtitle">所有修改立即生效，无需重启服务</p>
      </div>
      <span class="live-pill">● LIVE</span>
    </div>

    <el-row :gutter="16">
      <!-- 左：系统参数 -->
      <el-col :span="15">
        <div class="surface" style="overflow:hidden" v-loading="configLoading">
          <div class="panel-hd">
            <span class="section-title">系统参数</span>
            <span class="count-badge">{{ configs.length }} 项</span>
          </div>
          <div class="config-list">
            <div
              v-for="(row, idx) in configs"
              :key="row.key"
              class="config-row"
              :class="{ 'config-row--last': idx === configs.length - 1 }"
            >
              <div class="config-row__main">
                <div class="config-key mono">{{ row.key }}</div>
                <div class="config-desc">{{ row.description }}</div>
              </div>
              <div class="config-row__right">
                <span class="config-val">{{ row.value }}</span>
                <button class="edit-link" @click="startEdit(row)">修改</button>
              </div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右：启发策略 -->
      <el-col :span="9">
        <div class="surface" style="overflow:hidden" v-loading="strategyLoading">
          <div class="panel-hd">
            <span class="section-title">启发策略库</span>
            <el-tooltip content="优先级数字越小越优先">
              <span class="help-tip">优先级排序 (?)</span>
            </el-tooltip>
          </div>
          <div class="strategy-list">
            <div
              v-for="(row, idx) in strategies"
              :key="row.id"
              class="strategy-row"
              :class="{ 'strategy-row--last': idx === strategies.length - 1, 'strategy-row--off': !row.is_enabled }"
            >
              <span class="priority-num">{{ row.priority }}</span>
              <div class="strategy-info">
                <div class="strategy-name">{{ row.name }}</div>
                <div class="strategy-powers">{{ row.applicable_powers }}</div>
              </div>
              <el-switch v-model="row.is_enabled" size="small" @change="toggleStrategy(row)" />
            </div>
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Edit dialog -->
    <el-dialog v-model="showEditDialog" title="修改系统参数" width="480px">
      <div v-if="editingConfig" class="edit-body">
        <div class="param-info">
          <div class="param-info-row">
            <span class="param-info-lbl">参数键</span>
            <span class="mono" style="color:var(--indigo);font-weight:500">{{ editingConfig.key }}</span>
          </div>
          <div class="param-info-row">
            <span class="param-info-lbl">当前值</span>
            <span class="config-val">{{ editingConfig.value }}</span>
          </div>
          <div class="param-info-row">
            <span class="param-info-lbl">说明</span>
            <span style="color:var(--text-2);font-size:13.5px;line-height:1.5">{{ editingConfig.description }}</span>
          </div>
        </div>
        <div class="row-divider" />
        <el-form label-width="60px" style="margin-top:4px">
          <el-form-item label="新值">
            <el-select v-if="editingConfig.key === 'active_llm_provider'" v-model="newValue" style="width:100%">
              <el-option label="通义千问 (tongyi)" value="tongyi" />
              <el-option label="OpenAI (openai)" value="openai" />
              <el-option label="Anthropic (claude)" value="claude" />
            </el-select>
            <el-input v-else v-model="newValue" :placeholder="`当前值：${editingConfig.value}`" />
          </el-form-item>
        </el-form>
        <div class="live-warning">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="flex-shrink:0">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
          </svg>
          修改后立即对所有新请求生效，请确认无误再提交
        </div>
      </div>
      <template #footer>
        <el-button @click="showEditDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">确认修改</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { systemConfigApi, strategyApi } from '@/api'
import type { SystemConfig, Strategy } from '@/types'

const configs = ref<SystemConfig[]>([])
const strategies = ref<Strategy[]>([])
const configLoading = ref(false)
const strategyLoading = ref(false)
const showEditDialog = ref(false)
const editingConfig = ref<SystemConfig | null>(null)
const newValue = ref('')

function startEdit(row: SystemConfig) { editingConfig.value = row; newValue.value = row.value; showEditDialog.value = true }

async function handleSave() {
  if (!editingConfig.value) return
  await systemConfigApi.update(editingConfig.value.key, newValue.value)
  editingConfig.value.value = newValue.value
  ElMessage.success('参数已更新，立即生效')
  showEditDialog.value = false
}

async function toggleStrategy(row: Strategy) {
  await strategyApi.update(row.id, { is_enabled: row.is_enabled })
  ElMessage.success(`策略"${row.name}"已${row.is_enabled ? '启用' : '禁用'}`)
}

async function loadData() {
  configLoading.value = true
  strategyLoading.value = true
  try {
    const [c, s] = await Promise.all([systemConfigApi.getList(), strategyApi.getList()])
    configs.value = c; strategies.value = s
  } finally { configLoading.value = false; strategyLoading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.live-pill {
  font-size: 12px; font-weight: 700;
  color: var(--green);
  background: var(--green-dim);
  border: 1.5px solid var(--green-border);
  border-radius: var(--r-pill);
  padding: 4px 12px;
  letter-spacing: 0.04em;
}

.panel-hd {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px 0;
  margin-bottom: 4px;
}

.count-badge {
  font-size: 12px; color: var(--text-3);
  background: var(--bg-muted);
  border-radius: var(--r-pill);
  padding: 2px 8px;
}

.help-tip { font-size: 12.5px; color: var(--text-3); cursor: help; }

/* Config list */
.config-list { padding-bottom: 8px; }
.config-row {
  display: flex; align-items: center; justify-content: space-between;
  gap: 12px; padding: 14px 20px;
  border-bottom: 1px solid var(--border);
  transition: background var(--t-fast);
}
.config-row:hover { background: var(--bg-muted); }
.config-row--last { border-bottom: none; }
.config-row__main { flex: 1; min-width: 0; }
.config-key { font-size: 13px; color: var(--indigo); font-weight: 500; margin-bottom: 3px; }
.config-desc { font-size: 12px; color: var(--text-3); line-height: 1.4; }
.config-row__right { display: flex; align-items: center; gap: 14px; flex-shrink: 0; }
.config-val {
  font-family: var(--font-mono);
  font-size: 13px; font-weight: 600;
  color: var(--text-1);
  background: var(--bg-muted);
  padding: 3px 10px;
  border-radius: var(--r-md);
  border: 1px solid var(--border);
}
.edit-link {
  background: none; border: none;
  color: var(--text-3); cursor: pointer;
  font-size: 13px; font-weight: 500;
  font-family: var(--font-sans);
  padding: 4px 8px; border-radius: var(--r-sm);
  transition: all var(--t-fast);
}
.edit-link:hover { background: var(--indigo-light); color: var(--indigo); }

/* Strategy list */
.strategy-list { padding-bottom: 8px; }
.strategy-row {
  display: flex; align-items: center; gap: 10px;
  padding: 12px 20px;
  border-bottom: 1px solid var(--border);
  transition: background var(--t-fast);
}
.strategy-row:hover { background: var(--bg-muted); }
.strategy-row--last { border-bottom: none; }
.strategy-row--off { opacity: 0.45; }
.priority-num {
  width: 24px; height: 24px;
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1.5px solid var(--indigo-border);
  border-radius: var(--r-full);
  font-size: 11.5px; font-weight: 700; font-family: var(--font-mono);
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.strategy-info { flex: 1; min-width: 0; }
.strategy-name { font-size: 13.5px; font-weight: 500; color: var(--text-1); }
.strategy-powers { font-size: 12px; color: var(--text-3); margin-top: 2px; }

/* Dialog */
.edit-body { display: flex; flex-direction: column; gap: 14px; }
.param-info {
  background: var(--bg-muted);
  border-radius: var(--r-lg);
  padding: 14px 16px;
  display: flex; flex-direction: column; gap: 10px;
}
.param-info-row { display: flex; align-items: flex-start; gap: 10px; }
.param-info-lbl { font-size: 12.5px; color: var(--text-3); min-width: 52px; padding-top: 1px; }
.live-warning {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--amber);
  background: var(--amber-dim);
  border-radius: var(--r-lg);
  padding: 10px 14px;
  border: 1px solid var(--amber-border);
}
</style>
