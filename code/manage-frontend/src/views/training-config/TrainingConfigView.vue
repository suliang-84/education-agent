<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">训练参数配置</h1>
        <p class="page-subtitle">管理训练系统各维度参数版本，新版本创建后立即生效</p>
      </div>
    </div>

    <!-- ── 全局算法参数 ── -->
    <div class="section-card surface" v-loading="globalLoading">
      <div class="section-hd">
        <div style="display:flex;align-items:center;gap:10px">
          <span class="section-title">全局算法参数</span>
          <span class="active-badge" v-if="globalActive">{{ globalActive.version }} · 生效中</span>
        </div>
        <div style="display:flex;align-items:center;gap:12px">
          <span style="font-size:12.5px;color:var(--text-3)" v-if="globalActive">生效时间：{{ formatDate(globalActive.created_at) }}</span>
          <button class="btn-create" @click="openGlobalCreate">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>
            创建新版本
          </button>
        </div>
      </div>

      <div class="params-grid" v-if="globalActive">
        <div class="param-group">
          <div class="param-group__title">RAG 参数</div>
          <div class="param-row">
            <span class="param-label">触发模式</span>
            <span class="mode-badge">{{ ragModeLabel[globalActive.rag_mode] }}</span>
          </div>
          <div class="param-row">
            <span class="param-label">生成超时</span>
            <span class="param-val num">{{ globalActive.rag_timeout_sec }}<span class="param-unit">秒</span></span>
          </div>
          <div class="param-row">
            <span class="param-label">题目 / 策略召回数</span>
            <span class="param-val num">{{ globalActive.rag_question_recall }} / {{ globalActive.rag_strategy_recall }}</span>
          </div>
          <div class="param-row">
            <span class="param-label">相似度阈值</span>
            <span class="param-val num">{{ globalActive.rag_similarity_threshold }}</span>
          </div>
        </div>

        <div class="param-group">
          <div class="param-group__title">训练画像</div>
          <div class="param-row">
            <span class="param-label">EWMA 衰减系数</span>
            <span class="param-val num">{{ globalActive.ewma_decay }}</span>
          </div>
        </div>

        <div class="param-group">
          <div class="param-group__title">判题阈值</div>
          <div class="param-row">
            <span class="param-label">文字题答对阈值</span>
            <span class="param-val num">{{ globalActive.is_correct_threshold }}</span>
          </div>
        </div>
      </div>

      <!-- 历史版本 -->
      <div class="history-section">
        <div class="history-hd" @click="globalHistoryOpen = !globalHistoryOpen">
          <span>历史版本记录</span>
          <span class="readonly-tag">只读</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transform: globalHistoryOpen ? 'rotate(180deg)' : 'none', transition: '0.2s' }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
          </svg>
        </div>
        <el-table v-if="globalHistoryOpen" :data="globalHistory" size="small" style="margin-top:8px">
          <el-table-column label="版本" width="70"><template #default="{ row }"><span class="mono" style="color:var(--indigo);font-weight:600">{{ row.version }}</span></template></el-table-column>
          <el-table-column label="状态" width="90"><template #default="{ row }"><span class="status-pill" :class="row.is_active ? 'pill--active' : 'pill--off'">{{ row.is_active ? '生效中' : '已停用' }}</span></template></el-table-column>
          <el-table-column label="RAG模式" width="100"><template #default="{ row }">{{ ragModeLabel[row.rag_mode as keyof typeof ragModeLabel] }}</template></el-table-column>
          <el-table-column label="EWMA" width="80" align="center"><template #default="{ row }"><span class="num">{{ row.ewma_decay }}</span></template></el-table-column>
          <el-table-column label="创建时间" min-width="140"><template #default="{ row }"><span style="color:var(--text-2)">{{ formatDate(row.created_at) }}</span></template></el-table-column>
          <el-table-column label="创建人" width="100"><template #default="{ row }"><span style="color:var(--text-2)">{{ row.created_by }}</span></template></el-table-column>
        </el-table>
      </div>
    </div>

    <!-- ── 五维度训练参数 Tab ── -->
    <div class="section-card surface" v-loading="dimLoading">
      <div class="section-hd">
        <span class="section-title">五维度训练参数</span>
        <button class="btn-create" @click="openDimCreate">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/></svg>
          创建新版本
        </button>
      </div>

      <!-- 维度 Tab -->
      <div class="dim-tabs">
        <button
          v-for="(label, key) in TrainingModeLabels" :key="key"
          class="dim-tab"
          :class="{ active: activeMode === key }"
          @click="switchMode(key as TrainingMode)"
        >
          <span class="dim-tab__icon">{{ modeIcons[key as TrainingMode] }}</span>
          {{ label }}
        </button>
      </div>

      <!-- 当前维度参数展示 -->
      <div class="params-grid" v-if="dimActive">
        <!-- 基础参数 -->
        <div class="param-group">
          <div class="param-group__title">基础参数</div>
          <div class="param-row">
            <span class="param-label">每次训练题数</span>
            <span class="param-val num" style="color:var(--indigo);font-size:18px;font-weight:700">{{ dimActive.questions_per_session }}<span class="param-unit">题</span></span>
          </div>
          <div class="param-row" v-if="activeMode !== 'wrong_answer'">
            <span class="param-label">近期去重窗口</span>
            <span class="param-val num">{{ dimActive.dedup_window }}<span class="param-unit">题</span></span>
          </div>
        </div>

        <!-- 难度分布 -->
        <div class="param-group" v-if="activeMode !== 'wrong_answer'">
          <div class="param-group__title">题目难度分布</div>
          <div class="diff-dist">
            <div class="diff-seg diff-seg--basic" :style="{ width: dimActive.difficulty_basic_pct + '%' }">
              基础 {{ dimActive.difficulty_basic_pct }}%
            </div>
            <div class="diff-seg diff-seg--advanced" :style="{ width: dimActive.difficulty_advanced_pct + '%' }">
              进阶 {{ dimActive.difficulty_advanced_pct }}%
            </div>
            <div class="diff-seg diff-seg--challenge" :style="{ width: dimActive.difficulty_challenge_pct + '%' }">
              挑战 {{ dimActive.difficulty_challenge_pct }}%
            </div>
          </div>
        </div>

        <div class="param-group" v-else>
          <div class="param-group__title">题目难度分布</div>
          <div class="param-row">
            <span class="param-label">难度策略</span>
            <span style="font-size:13px;color:var(--text-2)">按原始题目难度（不强制分布）</span>
          </div>
        </div>

        <!-- 五力薄弱加权 -->
        <div class="param-group">
          <div class="param-group__title">五力薄弱加权</div>
          <div class="param-row">
            <span class="param-label">薄弱判定阈值</span>
            <span class="param-val num" style="color:var(--amber)">{{ dimActive.weak_threshold }}<span class="param-unit">分</span></span>
          </div>
          <div class="param-row">
            <span class="param-label">严重薄弱加权（&lt;50分）</span>
            <span class="bonus-pct bonus-pct--strong">+{{ (dimActive.severe_weak_bonus * 100).toFixed(0) }}%</span>
          </div>
          <div class="param-row">
            <span class="param-label">一般薄弱加权（50~阈值）</span>
            <span class="bonus-pct">+{{ (dimActive.general_weak_bonus * 100).toFixed(0) }}%</span>
          </div>
        </div>

        <!-- 错题集专属参数 -->
        <div class="param-group" v-if="activeMode === 'wrong_answer' && dimActive">
          <div class="param-group__title">
            错题攻克策略
            <span class="exclusive-tag">错题集专属</span>
          </div>
          <div class="param-row">
            <span class="param-label">优先排序</span>
            <span class="mode-badge">{{ wrongSortLabel[dimActive.wrong_sort_by || 'error_count'] }}</span>
          </div>
          <div class="param-row">
            <span class="param-label">新旧题混入</span>
            <span class="param-val">旧错题 <strong class="num">{{ ((1 - (dimActive.new_question_mix_ratio || 0.2)) * 100).toFixed(0) }}%</strong> / 新题 <strong class="num">{{ ((dimActive.new_question_mix_ratio || 0.2) * 100).toFixed(0) }}%</strong></span>
          </div>
          <div class="param-row">
            <span class="param-label">连对移除阈值</span>
            <span class="param-val num">连续答对 <strong>{{ dimActive.consecutive_correct_to_remove || 3 }}</strong> 次后移出</span>
          </div>
        </div>
      </div>

      <div class="version-info" v-if="dimActive">
        当前版本：<span class="mono" style="color:var(--indigo)">{{ dimActive.version }}</span>
        · 生效时间：{{ formatDate(dimActive.created_at) }}
        · 创建人：{{ dimActive.created_by }}
      </div>

      <!-- 历史版本 -->
      <div class="history-section">
        <div class="history-hd" @click="dimHistoryOpen = !dimHistoryOpen">
          <span>历史版本记录</span>
          <span class="readonly-tag">只读</span>
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transform: dimHistoryOpen ? 'rotate(180deg)' : 'none', transition: '0.2s' }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
          </svg>
        </div>
        <el-table v-if="dimHistoryOpen" :data="dimHistory" size="small" style="margin-top:8px">
          <el-table-column label="版本" width="70"><template #default="{ row }"><span class="mono" style="color:var(--indigo);font-weight:600">{{ row.version }}</span></template></el-table-column>
          <el-table-column label="状态" width="90"><template #default="{ row }"><span class="status-pill" :class="row.is_active ? 'pill--active' : 'pill--off'">{{ row.is_active ? '生效中' : '已停用' }}</span></template></el-table-column>
          <el-table-column label="题数" width="70" align="center"><template #default="{ row }"><span class="num">{{ row.questions_per_session }}</span></template></el-table-column>
          <el-table-column label="难度分布" min-width="150">
            <template #default="{ row }">
              <span v-if="row.difficulty_basic_pct" style="font-size:12px;color:var(--text-2)">
                基{{ row.difficulty_basic_pct }}% / 进{{ row.difficulty_advanced_pct }}% / 挑{{ row.difficulty_challenge_pct }}%
              </span>
              <span v-else style="font-size:12px;color:var(--text-3)">按原题</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="140"><template #default="{ row }"><span style="color:var(--text-2)">{{ formatDate(row.created_at) }}</span></template></el-table-column>
        </el-table>
      </div>
    </div>

    <!-- ── 创建全局算法参数弹窗 ── -->
    <el-dialog v-model="globalCreateVisible" title="创建新全局算法参数版本" width="600px" :close-on-click-modal="false">
      <el-form :model="newGlobal" label-width="140px">
        <div class="form-section-title">RAG 参数</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="触发模式">
              <el-select v-model="newGlobal.rag_mode" style="width:100%">
                <el-option label="所有题目" value="all" />
                <el-option label="仅答错" value="wrong_only" />
                <el-option label="禁用" value="disabled" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="生成超时（秒）">
              <el-input-number v-model="newGlobal.rag_timeout_sec" :min="5" :max="30" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="题目召回数">
              <el-input-number v-model="newGlobal.rag_question_recall" :min="1" :max="10" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="策略召回数">
              <el-input-number v-model="newGlobal.rag_strategy_recall" :min="1" :max="5" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="相似度阈值">
              <el-input-number v-model="newGlobal.rag_similarity_threshold" :min="0.5" :max="0.99" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
        <div class="form-section-title">训练画像</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="EWMA 衰减系数">
              <el-input-number v-model="newGlobal.ewma_decay" :min="0.1" :max="0.5" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="文字题答对阈值">
              <el-input-number v-model="newGlobal.is_correct_threshold" :min="0.5" :max="0.95" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>
      </el-form>
      <template #footer>
        <el-button @click="globalCreateVisible = false">取消</el-button>
        <el-button type="primary" :loading="saving" @click="handleCreateGlobal">创建并生效</el-button>
      </template>
    </el-dialog>

    <!-- ── 创建维度训练参数弹窗 ── -->
    <el-dialog v-model="dimCreateVisible" :title="`创建新版本 — ${TrainingModeLabels[activeMode]}训练参数`" width="680px" :close-on-click-modal="false">
      <el-form :model="newDim" label-width="150px">
        <div class="form-section-title">基础参数</div>
        <el-row :gutter="20">
          <el-col :span="12">
            <el-form-item label="每次训练题数">
              <el-input-number v-model="newDim.questions_per_session" :min="3" :max="15" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12" v-if="activeMode !== 'wrong_answer'">
            <el-form-item label="近期去重窗口（题）">
              <el-input-number v-model="newDim.dedup_window" :min="5" :max="200" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <template v-if="activeMode !== 'wrong_answer'">
          <div class="form-section-title">
            题目难度分布
            <span style="font-size:12px;color:var(--text-3);font-weight:400">三项之和必须 = 100%</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="8"><el-form-item label="基础 %"><el-input-number v-model="newDim.difficulty_basic_pct" :min="0" :max="100" style="width:100%" /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="进阶 %"><el-input-number v-model="newDim.difficulty_advanced_pct" :min="0" :max="100" style="width:100%" /></el-form-item></el-col>
            <el-col :span="8"><el-form-item label="挑战 %"><el-input-number :model-value="dimDiffChallenge" disabled style="width:100%" /></el-form-item></el-col>
          </el-row>
          <div v-if="dimDiffSum !== 100" class="sum-error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/></svg>
            当前各难度之和 = {{ dimDiffSum }}%，必须等于 100%
          </div>
        </template>

        <div class="form-section-title">五力薄弱加权</div>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="薄弱阈值（分）">
              <el-input-number v-model="newDim.weak_threshold" :min="40" :max="80" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="严重薄弱加权">
              <el-input-number v-model="newDim.severe_weak_bonus" :min="0" :max="1" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="一般薄弱加权">
              <el-input-number v-model="newDim.general_weak_bonus" :min="0" :max="1" :step="0.05" style="width:100%" />
            </el-form-item>
          </el-col>
        </el-row>

        <!-- 错题集专属参数 -->
        <template v-if="activeMode === 'wrong_answer'">
          <div class="form-section-title">
            错题攻克策略
            <span class="exclusive-tag">错题集专属</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="优先排序方式">
                <el-select v-model="newDim.wrong_sort_by" style="width:100%">
                  <el-option label="出错次数多" value="error_count" />
                  <el-option label="最近出错" value="recent" />
                  <el-option label="最久未练" value="oldest_practice" />
                </el-select>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="新题混入比例">
                <el-input-number v-model="newDim.new_question_mix_ratio" :min="0" :max="0.5" :step="0.05" style="width:100%" />
                <div style="font-size:12px;color:var(--text-3);margin-top:4px">新题占比 ≤ 50%</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="连对移除阈值（次）">
                <el-input-number v-model="newDim.consecutive_correct_to_remove" :min="1" :max="10" style="width:100%" />
                <div style="font-size:12px;color:var(--text-3);margin-top:4px">连续答对 N 次后移出错题列表</div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>
      </el-form>
      <template #footer>
        <el-button @click="dimCreateVisible = false">取消</el-button>
        <el-button type="primary" :disabled="activeMode !== 'wrong_answer' && dimDiffSum !== 100" :loading="saving" @click="handleCreateDimension">创建并生效</el-button>
      </template>
    </el-dialog>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { trainingConfigApi } from '@/api'
import type { GlobalAlgoConfig, DimensionTrainingConfig, TrainingMode } from '@/types'
import { TrainingModeLabels } from '@/types'
import { formatDate } from '@/utils/format'

// ── 常量 ─────────────────────────────────────────────────────
const ragModeLabel: Record<string, string> = { all: '所有题目', wrong_only: '仅答错', disabled: '禁用' }
const wrongSortLabel: Record<string, string> = { error_count: '出错次数多', recent: '最近出错', oldest_practice: '最久未练' }
const modeIcons: Record<TrainingMode, string> = { knowledge_point: '📚', chapter: '📖', semester: '📅', wrong_answer: '❌', random: '🎲' }

// ── 全局算法参数 ─────────────────────────────────────────────
const globalLoading = ref(false)
const globalActive = ref<GlobalAlgoConfig | null>(null)
const globalHistory = ref<GlobalAlgoConfig[]>([])
const globalHistoryOpen = ref(false)
const globalCreateVisible = ref(false)
const saving = ref(false)

const newGlobal = reactive({
  rag_mode: 'all' as 'all' | 'wrong_only' | 'disabled',
  rag_timeout_sec: 8,
  rag_question_recall: 3,
  rag_strategy_recall: 2,
  rag_similarity_threshold: 0.75,
  ewma_decay: 0.3,
  is_correct_threshold: 0.70,
})

async function loadGlobal() {
  globalLoading.value = true
  try {
    const [active, list] = await Promise.all([
      trainingConfigApi.getGlobalActive(),
      trainingConfigApi.getGlobalList(),
    ])
    globalActive.value = active
    globalHistory.value = list
    // 初始化创建表单为当前版本值
    Object.assign(newGlobal, {
      rag_mode: active.rag_mode,
      rag_timeout_sec: active.rag_timeout_sec,
      rag_question_recall: active.rag_question_recall,
      rag_strategy_recall: active.rag_strategy_recall,
      rag_similarity_threshold: active.rag_similarity_threshold,
      ewma_decay: active.ewma_decay,
      is_correct_threshold: active.is_correct_threshold,
    })
  } finally { globalLoading.value = false }
}

function openGlobalCreate() { globalCreateVisible.value = true }

async function handleCreateGlobal() {
  await ElMessageBox.confirm('创建后新版本立即生效，旧版本自动停用，确认？', '确认创建全局参数', { type: 'warning' })
  saving.value = true
  try {
    await trainingConfigApi.createGlobal({ ...newGlobal })
    ElMessage.success('全局算法参数新版本已创建并生效')
    globalCreateVisible.value = false
    await loadGlobal()
  } finally { saving.value = false }
}

// ── 维度训练参数 ─────────────────────────────────────────────
const dimLoading = ref(false)
const activeMode = ref<TrainingMode>('knowledge_point')
const dimActive = ref<DimensionTrainingConfig | null>(null)
const dimHistory = ref<DimensionTrainingConfig[]>([])
const dimHistoryOpen = ref(false)
const dimCreateVisible = ref(false)

// 默认值查表
const modeDefaults: Record<TrainingMode, Partial<DimensionTrainingConfig>> = {
  knowledge_point: { questions_per_session: 5,  dedup_window: 30,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
  chapter:         { questions_per_session: 8,  dedup_window: 50,  difficulty_basic_pct: 40, difficulty_advanced_pct: 40, difficulty_challenge_pct: 20, weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2 },
  semester:        { questions_per_session: 10, dedup_window: 100, difficulty_basic_pct: 30, difficulty_advanced_pct: 40, difficulty_challenge_pct: 30, weak_threshold: 55, severe_weak_bonus: 0.2, general_weak_bonus: 0.1 },
  wrong_answer:    { questions_per_session: 5,  dedup_window: 10,  difficulty_basic_pct: 0,  difficulty_advanced_pct: 0,  difficulty_challenge_pct: 0,  weak_threshold: 65, severe_weak_bonus: 0.4, general_weak_bonus: 0.2, wrong_sort_by: 'error_count', new_question_mix_ratio: 0.2, consecutive_correct_to_remove: 3 },
  random:          { questions_per_session: 5,  dedup_window: 20,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15, weak_threshold: 65, severe_weak_bonus: 0.1, general_weak_bonus: 0.05 },
}

const newDim = reactive<Partial<DimensionTrainingConfig>>({ ...modeDefaults['knowledge_point'] })

const dimDiffChallenge = computed(() => 100 - (newDim.difficulty_basic_pct || 0) - (newDim.difficulty_advanced_pct || 0))
const dimDiffSum = computed(() => (newDim.difficulty_basic_pct || 0) + (newDim.difficulty_advanced_pct || 0) + dimDiffChallenge.value)

async function loadDimension(mode: TrainingMode) {
  dimLoading.value = true
  try {
    const [active, list] = await Promise.all([
      trainingConfigApi.getDimensionActive(mode),
      trainingConfigApi.getDimensionList(mode),
    ])
    dimActive.value = active
    dimHistory.value = list
  } finally { dimLoading.value = false }
}

async function switchMode(mode: TrainingMode) {
  activeMode.value = mode
  dimHistoryOpen.value = false
  await loadDimension(mode)
}

function openDimCreate() {
  // 用当前生效版本作为新版本初始值
  const defaults = dimActive.value ? { ...dimActive.value } : { ...modeDefaults[activeMode.value] }
  Object.assign(newDim, defaults)
  dimCreateVisible.value = true
}

async function handleCreateDimension() {
  if (activeMode.value !== 'wrong_answer' && dimDiffSum.value !== 100) return
  await ElMessageBox.confirm(
    `创建后「${TrainingModeLabels[activeMode.value]}」维度新参数立即生效，旧版本自动停用，确认？`,
    '确认创建维度参数',
    { type: 'warning' }
  )
  saving.value = true
  try {
    await trainingConfigApi.createDimension(activeMode.value, {
      ...newDim,
      difficulty_challenge_pct: activeMode.value !== 'wrong_answer' ? dimDiffChallenge.value : 0,
    })
    ElMessage.success(`「${TrainingModeLabels[activeMode.value]}」训练参数新版本已创建并生效`)
    dimCreateVisible.value = false
    await loadDimension(activeMode.value)
  } finally { saving.value = false }
}

// ── 初始化 ───────────────────────────────────────────────────
onMounted(async () => {
  await Promise.all([loadGlobal(), loadDimension('knowledge_point')])
})
</script>

<style lang="scss" scoped>
// ── 卡片区块 ─────────────────────────────────────────────────
.section-card {
  padding: 22px 24px;
  margin-bottom: 16px;
}

// ── 版本徽章 ─────────────────────────────────────────────────
.active-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
  background: var(--green-dim);
  border: 1.5px solid var(--green-border);
  border-radius: var(--r-pill);
  padding: 3px 10px;
}

// ── 创建按钮 ─────────────────────────────────────────────────
.btn-create {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  font-weight: 500;
  color: var(--indigo);
  background: var(--indigo-light);
  border: 1.5px solid var(--indigo-border);
  border-radius: var(--r-pill);
  padding: 5px 14px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;

  &:hover { background: var(--indigo); color: #fff; }
}

// ── 参数展示网格 ─────────────────────────────────────────────
.params-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
  gap: 16px;
  margin: 16px 0;
}

.param-group {
  background: var(--bg-muted);
  border-radius: var(--r-xl);
  padding: 14px 16px;

  &__title {
    font-size: 11.5px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }
}

.param-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 8px;
  padding: 5px 0;

  &:not(:last-child) { border-bottom: 1px solid rgba(0,0,0,0.04); }
}

.param-label {
  font-size: 13px;
  color: var(--text-2);
  flex-shrink: 0;
}

.param-val {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-1);
}

.param-unit {
  font-size: 12px;
  font-weight: 400;
  color: var(--text-3);
  margin-left: 3px;
}

.mode-badge {
  font-size: 12px;
  font-weight: 500;
  background: var(--indigo-light);
  color: var(--indigo);
  border-radius: var(--r-pill);
  padding: 2px 10px;
  border: 1px solid var(--indigo-border);
}

.bonus-pct {
  font-size: 14px;
  font-weight: 700;
  color: var(--green);

  &--strong { color: var(--red); }
}

.version-info {
  font-size: 12.5px;
  color: var(--text-3);
  margin-top: 4px;
  padding-top: 12px;
  border-top: 1px solid var(--border);
}

// ── 难度分布条 ───────────────────────────────────────────────
.diff-dist {
  display: flex;
  width: 100%;
  height: 28px;
  border-radius: var(--r-md);
  overflow: hidden;
  gap: 2px;
  margin-top: 8px;
}

.diff-seg {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11.5px;
  font-weight: 600;
  color: #fff;
  border-radius: var(--r-sm);
  white-space: nowrap;
  overflow: hidden;
  min-width: 0;

  &--basic    { background: var(--teal); }
  &--advanced { background: var(--amber); }
  &--challenge { background: var(--red); }
}

// ── 维度 Tab ─────────────────────────────────────────────────
.dim-tabs {
  display: flex;
  gap: 6px;
  margin: 12px 0 16px;
  flex-wrap: wrap;
}

.dim-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 7px 16px;
  border-radius: var(--r-pill);
  border: 1.5px solid var(--border-hover);
  background: var(--bg-surface);
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;

  &:hover { border-color: var(--indigo); color: var(--indigo); background: var(--indigo-light); }

  &.active {
    border-color: var(--indigo);
    background: var(--indigo);
    color: #fff;
    font-weight: 600;
  }

  &__icon { font-size: 14px; }
}

// ── 错题集专属标签 ───────────────────────────────────────────
.exclusive-tag {
  font-size: 10px;
  font-weight: 600;
  color: var(--purple);
  background: var(--purple-dim);
  border: 1px solid var(--purple-border);
  border-radius: 4px;
  padding: 1px 6px;
  text-transform: none;
  letter-spacing: 0;
}

// ── 历史版本折叠区 ───────────────────────────────────────────
.history-section {
  margin-top: 16px;
  border-top: 1px solid var(--border);
  padding-top: 12px;
}

.history-hd {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  cursor: pointer;
  user-select: none;

  &:hover { color: var(--text-1); }
}

.readonly-tag { font-size: 11.5px; color: var(--text-3); }

// ── 弹窗内小节标题 ───────────────────────────────────────────
.form-section-title {
  font-size: 12px;
  font-weight: 700;
  color: var(--text-3);
  letter-spacing: 0.06em;
  text-transform: uppercase;
  padding: 12px 0 10px;
  border-bottom: 1px solid var(--border);
  margin-bottom: 14px;
  display: flex;
  align-items: center;
  gap: 8px;
}

.status-pill {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &.pill--active { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &.pill--off    { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }
}

.sum-error {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 13px;
  color: var(--red);
  background: var(--red-dim);
  border: 1px solid var(--red-border);
  border-radius: var(--r-lg);
  padding: 10px 14px;
  margin-bottom: 12px;
}
</style>
