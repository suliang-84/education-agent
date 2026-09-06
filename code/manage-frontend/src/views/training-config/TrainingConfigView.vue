<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">训练参数配置</h1>
        <p class="page-subtitle">管理训练系统配置版本，新版本创建后立即生效</p>
      </div>
      <button class="btn-pink" @click="showCreateDialog = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
        </svg>
        创建新版本
      </button>
    </div>

    <!-- 当前生效版本 -->
    <div class="surface active-section" v-loading="loading">
      <div class="section-hd">
        <div style="display:flex;align-items:center;gap:10px">
          <span class="section-title">当前生效版本</span>
          <span class="active-badge">{{ activeConfig?.version }} · 生效中</span>
        </div>
        <span style="font-size:12.5px;color:var(--text-3)">生效时间：{{ formatDate(activeConfig?.created_at || '') }}</span>
      </div>

      <el-descriptions :column="3" border v-if="activeConfig">
        <el-descriptions-item label="每次训练题数">
          <span class="num" style="font-size:16px;font-weight:700;color:var(--indigo)">{{ activeConfig.questions_per_session }}</span>
          <span style="color:var(--text-3);margin-left:4px;font-size:12px">题</span>
        </el-descriptions-item>
        <el-descriptions-item label="去重窗口">
          近 <span class="num" style="color:var(--indigo);font-weight:600">{{ activeConfig.dedup_window }}</span> 题
        </el-descriptions-item>
        <el-descriptions-item label="弱力判定阈值">
          <span class="num" style="color:var(--amber);font-weight:700;font-size:15px">{{ activeConfig.weak_threshold }}</span>
          <span style="color:var(--text-3);margin-left:4px;font-size:12px">分</span>
        </el-descriptions-item>
        <el-descriptions-item label="严重弱力加权">
          <span class="bonus-pct bonus-pct--strong">+{{ (activeConfig.severe_weak_bonus * 100).toFixed(0) }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="一般弱力加权">
          <span class="bonus-pct">+{{ (activeConfig.general_weak_bonus * 100).toFixed(0) }}%</span>
        </el-descriptions-item>
        <el-descriptions-item label="EWMA 衰减系数">
          <span class="num" style="font-weight:600">{{ activeConfig.ewma_decay }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="题目难度分布" :span="3">
          <div class="diff-dist">
            <div class="diff-seg diff-seg--basic" :style="{ width: activeConfig.difficulty_basic_pct + '%' }">
              基础 {{ activeConfig.difficulty_basic_pct }}%
            </div>
            <div class="diff-seg diff-seg--advanced" :style="{ width: activeConfig.difficulty_advanced_pct + '%' }">
              进阶 {{ activeConfig.difficulty_advanced_pct }}%
            </div>
            <div class="diff-seg diff-seg--challenge" :style="{ width: activeConfig.difficulty_challenge_pct + '%' }">
              挑战 {{ activeConfig.difficulty_challenge_pct }}%
            </div>
          </div>
        </el-descriptions-item>
        <el-descriptions-item label="RAG 触发模式">
          <span class="mode-badge">{{ ragModeLabel[activeConfig.rag_mode] }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="RAG 超时">
          <span class="num" style="font-weight:600">{{ activeConfig.rag_timeout_sec }}</span>
          <span style="color:var(--text-3);margin-left:4px;font-size:12px">秒</span>
        </el-descriptions-item>
        <el-descriptions-item label="题目 / 策略召回数">
          <span class="num" style="font-weight:600">{{ activeConfig.rag_question_recall }}</span>
          <span style="color:var(--text-3);margin:0 6px">/</span>
          <span class="num" style="font-weight:600">{{ activeConfig.rag_strategy_recall }}</span>
        </el-descriptions-item>
        <el-descriptions-item label="相似度阈值">
          <span class="num" style="font-weight:600">{{ activeConfig.rag_similarity_threshold }}</span>
        </el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 历史版本 -->
    <div class="surface" style="overflow:hidden">
      <div class="panel-hd"><span class="section-title">历史版本记录</span><span class="readonly-tag">只读</span></div>
      <el-table :data="historyConfigs" style="width:100%">
        <el-table-column label="版本" width="80">
          <template #default="{ row }"><span class="mono" style="color:var(--indigo);font-weight:600">{{ row.version }}</span></template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <span class="status-pill" :class="row.is_active ? 'pill--active' : 'pill--off'">
              {{ row.is_active ? '生效中' : '已停用' }}
            </span>
          </template>
        </el-table-column>
        <el-table-column label="题数" width="70" align="center">
          <template #default="{ row }"><span class="num">{{ row.questions_per_session }}</span></template>
        </el-table-column>
        <el-table-column label="弱力阈值" width="90" align="center">
          <template #default="{ row }"><span class="num">{{ row.weak_threshold }}</span> 分</template>
        </el-table-column>
        <el-table-column label="RAG 模式" width="110">
          <template #default="{ row }">{{ ragModeLabel[row.rag_mode as keyof typeof ragModeLabel] }}</template>
        </el-table-column>
        <el-table-column label="创建时间" min-width="150">
          <template #default="{ row }"><span style="color:var(--text-2)">{{ formatDate(row.created_at) }}</span></template>
        </el-table-column>
        <el-table-column label="创建人" prop="created_by" width="100">
          <template #default="{ row }"><span style="color:var(--text-2)">{{ row.created_by }}</span></template>
        </el-table-column>
      </el-table>
    </div>

    <!-- Create dialog -->
    <el-dialog v-model="showCreateDialog" title="创建新训练配置版本" width="700px">
      <el-form ref="createFormRef" :model="newConfig" :rules="createRules" label-width="140px">
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="每次训练题数" prop="questions_per_session">
              <el-input-number v-model="newConfig.questions_per_session" :min="3" :max="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="去重窗口（题）">
              <el-input-number v-model="newConfig.dedup_window" :min="10" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="弱力判定阈值">
              <el-input-number v-model="newConfig.weak_threshold" :min="50" :max="80" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="EWMA衰减系数">
              <el-input-number v-model="newConfig.ewma_decay" :min="0.1" :max="0.5" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <div class="dialog-divider">
          <span>题目难度分布</span>
          <span style="font-size:12px;color:var(--text-3)">三项之和必须 = 100%</span>
        </div>

        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="基础 %">
              <el-input-number v-model="newConfig.difficulty_basic_pct" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="进阶 %">
              <el-input-number v-model="newConfig.difficulty_advanced_pct" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="挑战 %">
              <el-input-number :model-value="diffChallenge" disabled style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <div v-if="diffSum !== 100" class="sum-error">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
          </svg>
          当前各难度之和 = {{ diffSum }}%，必须等于 100%
        </div>

        <div class="dialog-divider"><span>RAG 参数</span></div>

        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="触发模式">
              <el-select v-model="newConfig.rag_mode" style="width:100%">
                <el-option label="所有题目" value="all" />
                <el-option label="仅答错" value="wrong_only" />
                <el-option label="禁用" value="disabled" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生成超时（秒）">
              <el-input-number v-model="newConfig.rag_timeout_sec" :min="5" :max="30" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题目召回数">
              <el-input-number v-model="newConfig.rag_question_recall" :min="1" :max="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="相似度阈值">
              <el-input-number v-model="newConfig.rag_similarity_threshold" :min="0.5" :max="0.99" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="showCreateDialog = false">取消</el-button>
        <el-button type="primary" :disabled="diffSum !== 100" @click="handleCreate">创建并生效</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { FormInstance, FormRules } from 'element-plus'
import { trainingConfigApi } from '@/api'
import type { TrainingConfig } from '@/types'
import { formatDate } from '@/utils/format'

const loading = ref(false)
const activeConfig = ref<TrainingConfig>()
const historyConfigs = ref<TrainingConfig[]>([])
const showCreateDialog = ref(false)
const createFormRef = ref<FormInstance>()

const ragModeLabel: Record<string, string> = { all: '所有题目', wrong_only: '仅答错', disabled: '禁用' }

const newConfig = reactive({
  questions_per_session: 5,
  dedup_window: 30,
  weak_threshold: 65,
  severe_weak_bonus: 0.4,
  general_weak_bonus: 0.2,
  difficulty_basic_pct: 50,
  difficulty_advanced_pct: 35,
  rag_mode: 'all',
  rag_timeout_sec: 8,
  rag_question_recall: 3,
  rag_strategy_recall: 2,
  rag_similarity_threshold: 0.75,
  ewma_decay: 0.3,
})

const diffChallenge = computed(() => 100 - newConfig.difficulty_basic_pct - newConfig.difficulty_advanced_pct)
const diffSum = computed(() => newConfig.difficulty_basic_pct + newConfig.difficulty_advanced_pct + diffChallenge.value)

const createRules: FormRules = {
  questions_per_session: [{ required: true, type: 'number', min: 3, max: 10, message: '3~10题', trigger: 'change' }],
}

async function handleCreate() {
  if (diffSum.value !== 100) return
  await ElMessageBox.confirm('创建后新版本立即生效，旧版本自动停用，确认？', '确认创建', { type: 'warning' })
  await trainingConfigApi.create({ ...newConfig, difficulty_challenge_pct: diffChallenge.value })
  ElMessage.success('新配置版本已创建并生效')
  showCreateDialog.value = false
  loadData()
}

async function loadData() {
  loading.value = true
  try {
    const [active, all] = await Promise.all([trainingConfigApi.getActive(), trainingConfigApi.getList()])
    activeConfig.value = active; historyConfigs.value = all
  } finally { loading.value = false }
}

onMounted(loadData)
</script>

<style lang="scss" scoped>
.active-section { padding: 22px 24px; }
.active-badge {
  font-size: 12px; font-weight: 600;
  color: var(--green);
  background: var(--green-dim);
  border: 1.5px solid var(--green-border);
  border-radius: var(--r-pill);
  padding: 3px 10px;
}

.diff-dist {
  display: flex; width: 100%; height: 28px;
  border-radius: var(--r-md);
  overflow: hidden;
  gap: 2px;
  margin-top: 4px;
}
.diff-seg {
  display: flex; align-items: center; justify-content: center;
  font-size: 11.5px; font-weight: 600; color: #fff;
  border-radius: var(--r-sm);
  white-space: nowrap;
  overflow: hidden;
  min-width: 0;
}
.diff-seg--basic    { background: var(--teal); }
.diff-seg--advanced { background: var(--amber); }
.diff-seg--challenge{ background: var(--red); }

.bonus-pct { font-size: 14px; font-weight: 700; color: var(--green); }
.bonus-pct--strong { color: var(--red); }

.mode-badge {
  font-size: 12.5px; font-weight: 500;
  background: var(--indigo-light);
  color: var(--indigo);
  border-radius: var(--r-pill);
  padding: 3px 10px;
  border: 1px solid var(--indigo-border);
}

.panel-hd { display: flex; align-items: center; justify-content: space-between; padding: 16px 20px 0; margin-bottom: 4px; }
.readonly-tag { font-size: 12px; color: var(--text-3); }

.status-pill { font-size: 12px; font-weight: 500; padding: 3px 10px; border-radius: var(--r-pill); border: 1.5px solid; }
.pill--active { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
.pill--off    { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }

.dialog-divider {
  display: flex; align-items: center; justify-content: space-between;
  border-top: 1px solid var(--border);
  padding: 14px 0 12px;
  margin-bottom: 4px;
  font-size: 13px; font-weight: 600; color: var(--text-1);
}

.sum-error {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--red);
  background: var(--red-dim);
  border: 1px solid var(--red-border);
  border-radius: var(--r-lg);
  padding: 10px 14px;
  margin-bottom: 12px;
}
</style>
