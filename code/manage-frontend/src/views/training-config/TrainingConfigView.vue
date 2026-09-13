<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div>
        <h1 class="page-title">训练参数配置</h1>
        <p class="page-subtitle">管理各训练维度的参数版本，新版本创建后立即生效</p>
      </div>
      <!-- 全局算法参数入口 -->
      <button class="btn-global" @click="globalDrawerVisible = true">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.324.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.24-.438.613-.431.992a6.759 6.759 0 010 .255c-.007.378.138.75.43.99l1.005.828c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.57 6.57 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.28c-.09.543-.56.941-1.11.941h-2.594c-.55 0-1.02-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.076-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.992a6.932 6.932 0 010-.255c.007-.378-.138-.75-.43-.99l-1.004-.828a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z"/>
          <path stroke-linecap="round" stroke-linejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z"/>
        </svg>
        全局算法参数
      </button>
    </div>

    <!-- ── 主卡片：五维度训练参数 ── -->
    <div class="surface main-card" v-loading="dimLoading">

      <!-- Tab 行 -->
      <div class="tab-row">
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
        <button class="btn-create" @click="openDimCreate" :disabled="!dimActive">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
          创建新版本
        </button>
      </div>

      <!-- 当前版本信息栏 -->
      <div class="version-bar" v-if="dimActive">
        <div class="version-bar__left">
          <span class="dim-title">{{ TrainingModeLabels[activeMode] }}训练参数</span>
          <span class="active-badge">{{ dimActive.version }} · 生效中</span>
        </div>
        <span class="version-bar__time">生效时间：{{ formatDate(dimActive.created_at) }}</span>
      </div>

      <!-- 参数展示区 -->
      <div class="params-body" v-if="dimActive">

        <!-- 基础参数 -->
        <div class="params-section">
          <div class="params-section__row">
            <div class="param-item">
              <span class="param-item__label">每次训练题数</span>
              <span class="param-item__val num big-val">{{ dimActive.questions_per_session }}<em>题</em></span>
            </div>
            <div class="param-item" v-if="activeMode !== 'wrong_answer'">
              <span class="param-item__label">近期去重窗口</span>
              <span class="param-item__val num">{{ dimActive.dedup_window }}<em>题（避免短期重复同题）</em></span>
            </div>
          </div>
        </div>

        <div class="params-divider" />

        <!-- 题目难度分布 -->
        <div class="params-section">
          <div class="params-section__title">题目难度分布</div>
          <template v-if="activeMode !== 'wrong_answer'">
            <div class="diff-dist">
              <div class="diff-seg diff-seg--basic" :style="{ flex: dimActive.difficulty_basic_pct }">
                基础 {{ dimActive.difficulty_basic_pct }}%
              </div>
              <div class="diff-seg diff-seg--advanced" :style="{ flex: dimActive.difficulty_advanced_pct }">
                进阶 {{ dimActive.difficulty_advanced_pct }}%
              </div>
              <div class="diff-seg diff-seg--challenge" :style="{ flex: dimActive.difficulty_challenge_pct }">
                挑战 {{ dimActive.difficulty_challenge_pct }}%
              </div>
            </div>
          </template>
          <template v-else>
            <span class="param-note">按原始题目难度（不强制分布）</span>
          </template>
        </div>

        <!-- 错题攻克策略（错题集专属） -->
        <template v-if="activeMode === 'wrong_answer'">
          <div class="params-divider" />
          <div class="params-section">
            <div class="params-section__title">
              错题攻克策略
              <span class="exclusive-tag">错题集专属</span>
            </div>
            <div class="wrong-strategy-grid">
              <div class="wrong-strategy-item">
                <span class="wrong-strategy-item__label">优先排序</span>
                <div class="sort-options">
                  <span
                    v-for="(label, val) in wrongSortLabel" :key="val"
                    class="sort-option"
                    :class="{ active: dimActive.wrong_sort_by === val }"
                  >
                    <span class="sort-option__dot" />
                    {{ label }}
                  </span>
                </div>
              </div>
              <div class="wrong-strategy-item">
                <span class="wrong-strategy-item__label">新旧题混入</span>
                <span class="param-item__val">
                  旧错题 <strong class="num">{{ ((1 - (dimActive.new_question_mix_ratio || 0.2)) * 100).toFixed(0) }}%</strong>
                  ／新题目 <strong class="num">{{ ((dimActive.new_question_mix_ratio || 0.2) * 100).toFixed(0) }}%</strong>
                </span>
              </div>
              <div class="wrong-strategy-item">
                <span class="wrong-strategy-item__label">连对移除</span>
                <span class="param-item__val num">
                  连续答对 <strong>{{ dimActive.consecutive_correct_to_remove || 3 }}</strong> 次后移出错题列表
                </span>
              </div>
            </div>
          </div>
        </template>

      </div>

      <!-- 历史版本（折叠） -->
      <div class="history-section">
        <div class="history-hd" @click="dimHistoryOpen = !dimHistoryOpen">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transform: dimHistoryOpen ? 'rotate(180deg)' : 'none', transition: '0.2s' }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
          </svg>
          <span>历史版本记录</span>
          <span class="readonly-tag">只读，不可回滚</span>
        </div>
        <el-table v-if="dimHistoryOpen" :data="dimHistory" size="small" style="margin-top:8px">
          <el-table-column label="版本" width="70">
            <template #default="{ row }"><span class="mono" style="color:var(--indigo);font-weight:600">{{ row.version }}</span></template>
          </el-table-column>
          <el-table-column label="状态" width="90">
            <template #default="{ row }">
              <span class="status-pill" :class="row.is_active ? 'pill--active' : 'pill--off'">{{ row.is_active ? '生效中' : '已停用' }}</span>
            </template>
          </el-table-column>
          <el-table-column label="每次题数" width="80" align="center">
            <template #default="{ row }"><span class="num">{{ row.questions_per_session }}</span></template>
          </el-table-column>
          <el-table-column label="难度分布" min-width="160">
            <template #default="{ row }">
              <span v-if="row.difficulty_basic_pct" style="font-size:12px;color:var(--text-2)">
                基{{ row.difficulty_basic_pct }}% / 进{{ row.difficulty_advanced_pct }}% / 挑{{ row.difficulty_challenge_pct }}%
              </span>
              <span v-else style="font-size:12px;color:var(--text-3)">按原题</span>
            </template>
          </el-table-column>
          <el-table-column label="创建时间" min-width="140">
            <template #default="{ row }"><span style="color:var(--text-2)">{{ formatDate(row.created_at) }}</span></template>
          </el-table-column>
          <el-table-column label="创建人" width="100">
            <template #default="{ row }"><span style="color:var(--text-2)">{{ row.created_by }}</span></template>
          </el-table-column>
        </el-table>
      </div>

    </div>

    <!-- ── 全局算法参数侧抽屉 ── -->
    <el-drawer v-model="globalDrawerVisible" title="全局算法参数" direction="rtl" size="460px">
      <div v-loading="globalLoading">
        <!-- 当前生效版本信息 -->
        <div class="global-version-bar" v-if="globalActive">
          <span class="active-badge">{{ globalActive.version }} · 生效中</span>
          <span style="font-size:12.5px;color:var(--text-3)">{{ formatDate(globalActive.created_at) }}</span>
        </div>

        <!-- 参数展示 -->
        <div class="global-params" v-if="globalActive">
          <div class="global-group">
            <div class="global-group__title">RAG 参数</div>
            <div class="global-row">
              <span class="global-label">触发模式</span>
              <span class="mode-badge">{{ ragModeLabel[globalActive.rag_mode] }}</span>
            </div>
            <div class="global-row">
              <span class="global-label">生成超时</span>
              <span class="num" style="font-weight:600">{{ globalActive.rag_timeout_sec }}<span style="font-size:12px;font-weight:400;color:var(--text-3);margin-left:3px">秒</span></span>
            </div>
            <div class="global-row">
              <span class="global-label">题目召回数 / 策略召回数</span>
              <span class="num" style="font-weight:600">{{ globalActive.rag_question_recall }} / {{ globalActive.rag_strategy_recall }}</span>
            </div>
            <div class="global-row">
              <span class="global-label">相似度阈值</span>
              <span class="num" style="font-weight:600">{{ globalActive.rag_similarity_threshold }}</span>
            </div>
          </div>

          <div class="global-group">
            <div class="global-group__title">训练画像</div>
            <div class="global-row">
              <span class="global-label">EWMA 衰减系数</span>
              <span class="num" style="font-weight:600">{{ globalActive.ewma_decay }}</span>
            </div>
          </div>

          <div class="global-group">
            <div class="global-group__title">判题阈值</div>
            <div class="global-row">
              <span class="global-label">文字题答对阈值</span>
              <span class="num" style="font-weight:600">{{ globalActive.is_correct_threshold }}</span>
            </div>
          </div>
        </div>

        <!-- 创建新版本 -->
        <el-divider />
        <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:16px">
          <span style="font-size:14px;font-weight:600;color:var(--text-1)">创建新版本</span>
          <span style="font-size:12px;color:var(--text-3)">创建后立即全局生效</span>
        </div>

        <el-form :model="newGlobal" label-width="130px" size="small">
          <div class="form-section-title">RAG 参数</div>
          <el-form-item label="触发模式">
            <el-select v-model="newGlobal.rag_mode" style="width:100%">
              <el-option label="所有题目" value="all" />
              <el-option label="仅答错" value="wrong_only" />
              <el-option label="禁用" value="disabled" />
            </el-select>
          </el-form-item>
          <el-form-item label="生成超时（秒）">
            <el-input-number v-model="newGlobal.rag_timeout_sec" :min="5" :max="30" style="width:100%" />
          </el-form-item>
          <el-form-item label="题目召回数">
            <el-input-number v-model="newGlobal.rag_question_recall" :min="1" :max="10" style="width:100%" />
          </el-form-item>
          <el-form-item label="策略召回数">
            <el-input-number v-model="newGlobal.rag_strategy_recall" :min="1" :max="5" style="width:100%" />
          </el-form-item>
          <el-form-item label="相似度阈值">
            <el-input-number v-model="newGlobal.rag_similarity_threshold" :min="0.5" :max="0.99" :step="0.05" style="width:100%" />
          </el-form-item>
          <div class="form-section-title">训练画像</div>
          <el-form-item label="EWMA 衰减系数">
            <el-input-number v-model="newGlobal.ewma_decay" :min="0.1" :max="0.5" :step="0.05" style="width:100%" />
          </el-form-item>
          <el-form-item label="文字题答对阈值">
            <el-input-number v-model="newGlobal.is_correct_threshold" :min="0.5" :max="0.95" :step="0.05" style="width:100%" />
          </el-form-item>
        </el-form>

        <div style="display:flex;justify-content:flex-end;margin-top:16px">
          <el-button @click="globalDrawerVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleCreateGlobal" style="margin-left:10px">创建并生效</el-button>
        </div>

        <!-- 全局历史版本 -->
        <el-divider />
        <div class="history-hd" @click="globalHistoryOpen = !globalHistoryOpen" style="margin-bottom:10px">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" :style="{ transform: globalHistoryOpen ? 'rotate(180deg)' : 'none', transition: '0.2s' }">
            <path stroke-linecap="round" stroke-linejoin="round" d="M19.5 8.25l-7.5 7.5-7.5-7.5"/>
          </svg>
          <span>历史版本记录</span>
          <span class="readonly-tag">只读</span>
        </div>
        <el-table v-if="globalHistoryOpen" :data="globalHistory" size="small">
          <el-table-column label="版本" width="60"><template #default="{ row }"><span class="mono" style="color:var(--indigo);font-weight:600">{{ row.version }}</span></template></el-table-column>
          <el-table-column label="状态" width="80"><template #default="{ row }"><span class="status-pill" :class="row.is_active ? 'pill--active' : 'pill--off'">{{ row.is_active ? '生效中' : '已停用' }}</span></template></el-table-column>
          <el-table-column label="EWMA" width="70" align="center"><template #default="{ row }"><span class="num">{{ row.ewma_decay }}</span></template></el-table-column>
          <el-table-column label="创建时间" min-width="120"><template #default="{ row }"><span style="color:var(--text-2);font-size:12px">{{ formatDate(row.created_at) }}</span></template></el-table-column>
        </el-table>
      </div>
    </el-drawer>

    <!-- ── 创建维度参数弹窗 ── -->
    <el-dialog
      v-model="dimCreateVisible"
      :title="`创建新版本 · ${TrainingModeLabels[activeMode]}训练参数`"
      width="640px"
      :close-on-click-modal="false"
    >
      <el-form :model="newDim" label-width="140px">

        <!-- 基础参数 -->
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

        <!-- 难度分布（错题集无此项） -->
        <template v-if="activeMode !== 'wrong_answer'">
          <div class="form-section-title">
            题目难度分布
            <span style="font-size:12px;color:var(--text-3);font-weight:400;text-transform:none;letter-spacing:0">三项之和必须 = 100%</span>
          </div>
          <el-row :gutter="20">
            <el-col :span="8">
              <el-form-item label="基础 %">
                <el-input-number v-model="newDim.difficulty_basic_pct" :min="0" :max="100" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="进阶 %">
                <el-input-number v-model="newDim.difficulty_advanced_pct" :min="0" :max="100" style="width:100%" />
              </el-form-item>
            </el-col>
            <el-col :span="8">
              <el-form-item label="挑战 %">
                <el-input-number :model-value="dimDiffChallenge" disabled style="width:100%" />
              </el-form-item>
            </el-col>
          </el-row>

          <!-- 难度预览条 -->
          <div v-if="dimDiffSum === 100" class="diff-preview">
            <div class="diff-seg diff-seg--basic" :style="{ flex: newDim.difficulty_basic_pct }">基础 {{ newDim.difficulty_basic_pct }}%</div>
            <div class="diff-seg diff-seg--advanced" :style="{ flex: newDim.difficulty_advanced_pct }">进阶 {{ newDim.difficulty_advanced_pct }}%</div>
            <div class="diff-seg diff-seg--challenge" :style="{ flex: dimDiffChallenge }">挑战 {{ dimDiffChallenge }}%</div>
          </div>
          <div v-else class="sum-error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/></svg>
            当前各难度之和 = {{ dimDiffSum }}%，必须等于 100%
          </div>
        </template>

        <!-- 错题攻克策略（错题集专属） -->
        <template v-if="activeMode === 'wrong_answer'">
          <div class="form-section-title">
            错题攻克策略
            <span class="exclusive-tag">错题集专属</span>
          </div>
          <el-form-item label="优先排序方式">
            <el-radio-group v-model="newDim.wrong_sort_by">
              <el-radio-button value="error_count">出错次数多</el-radio-button>
              <el-radio-button value="recent">最近出错</el-radio-button>
              <el-radio-button value="oldest_practice">最久未练</el-radio-button>
            </el-radio-group>
          </el-form-item>
          <el-row :gutter="20">
            <el-col :span="12">
              <el-form-item label="新题混入比例">
                <el-input-number v-model="newDim.new_question_mix_ratio" :min="0" :max="0.5" :step="0.05" style="width:100%" />
                <div style="font-size:12px;color:var(--text-3);margin-top:4px">新题占比 ≤ 50%，其余为旧错题</div>
              </el-form-item>
            </el-col>
            <el-col :span="12">
              <el-form-item label="连对移除阈值">
                <el-input-number v-model="newDim.consecutive_correct_to_remove" :min="1" :max="10" style="width:100%" />
                <div style="font-size:12px;color:var(--text-3);margin-top:4px">连续答对 N 次后移出错题列表</div>
              </el-form-item>
            </el-col>
          </el-row>
        </template>

      </el-form>

      <template #footer>
        <el-button @click="dimCreateVisible = false">取消</el-button>
        <el-button
          type="primary"
          :disabled="activeMode !== 'wrong_answer' && dimDiffSum !== 100"
          :loading="saving"
          @click="handleCreateDimension"
        >
          创建并生效
        </el-button>
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
const modeIcons: Record<TrainingMode, string> = {
  knowledge_point: '📚',
  chapter:         '📖',
  semester:        '📅',
  wrong_answer:    '❌',
  random:          '🎲',
}

// ── 全局算法参数（抽屉） ─────────────────────────────────────
const globalLoading = ref(false)
const globalDrawerVisible = ref(false)
const globalHistoryOpen = ref(false)
const globalActive = ref<GlobalAlgoConfig | null>(null)
const globalHistory = ref<GlobalAlgoConfig[]>([])
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
    Object.assign(newGlobal, {
      rag_mode:                  active.rag_mode,
      rag_timeout_sec:           active.rag_timeout_sec,
      rag_question_recall:       active.rag_question_recall,
      rag_strategy_recall:       active.rag_strategy_recall,
      rag_similarity_threshold:  active.rag_similarity_threshold,
      ewma_decay:                active.ewma_decay,
      is_correct_threshold:      active.is_correct_threshold,
    })
  } finally { globalLoading.value = false }
}

async function handleCreateGlobal() {
  await ElMessageBox.confirm('创建后新版本立即全局生效，旧版本自动停用，确认？', '确认创建全局参数', { type: 'warning' })
  saving.value = true
  try {
    await trainingConfigApi.createGlobal({ ...newGlobal })
    ElMessage.success('全局算法参数新版本已创建并生效')
    await loadGlobal()
  } finally { saving.value = false }
}

// ── 维度训练参数（主卡片）────────────────────────────────────
const dimLoading = ref(false)
const activeMode = ref<TrainingMode>('knowledge_point')
const dimActive = ref<DimensionTrainingConfig | null>(null)
const dimHistory = ref<DimensionTrainingConfig[]>([])
const dimHistoryOpen = ref(false)
const dimCreateVisible = ref(false)

const modeDefaults: Record<TrainingMode, Partial<DimensionTrainingConfig>> = {
  knowledge_point: { questions_per_session: 5,  dedup_window: 30,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15 },
  chapter:         { questions_per_session: 8,  dedup_window: 50,  difficulty_basic_pct: 40, difficulty_advanced_pct: 40, difficulty_challenge_pct: 20 },
  semester:        { questions_per_session: 10, dedup_window: 100, difficulty_basic_pct: 30, difficulty_advanced_pct: 40, difficulty_challenge_pct: 30 },
  wrong_answer:    { questions_per_session: 5,  dedup_window: 10,  difficulty_basic_pct: 0,  difficulty_advanced_pct: 0,  difficulty_challenge_pct: 0, wrong_sort_by: 'error_count', new_question_mix_ratio: 0.2, consecutive_correct_to_remove: 3 },
  random:          { questions_per_session: 5,  dedup_window: 20,  difficulty_basic_pct: 50, difficulty_advanced_pct: 35, difficulty_challenge_pct: 15 },
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
  const base = dimActive.value ? { ...dimActive.value } : { ...modeDefaults[activeMode.value] }
  Object.assign(newDim, base)
  dimCreateVisible.value = true
}

async function handleCreateDimension() {
  if (activeMode.value !== 'wrong_answer' && dimDiffSum.value !== 100) return
  await ElMessageBox.confirm(
    `创建后「${TrainingModeLabels[activeMode.value]}」新参数版本立即生效，旧版本自动停用，确认？`,
    '确认创建',
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

onMounted(async () => {
  await Promise.all([loadGlobal(), loadDimension('knowledge_point')])
})
</script>

<style lang="scss" scoped>
// ── 全局参数入口按钮 ─────────────────────────────────────────
.btn-global {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-2);
  background: var(--bg-surface);
  border: 1.5px solid var(--border-hover);
  border-radius: var(--r-pill);
  padding: 7px 16px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;

  &:hover { border-color: var(--indigo); color: var(--indigo); background: var(--indigo-light); }
}

// ── 主卡片 ───────────────────────────────────────────────────
.main-card {
  padding: 0;
  overflow: hidden;
}

// ── Tab 行 ───────────────────────────────────────────────────
.tab-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 12px;
  padding: 16px 24px 0;
  border-bottom: 1px solid var(--border);
  flex-wrap: wrap;
}

.dim-tabs {
  display: flex;
  gap: 2px;
  padding-bottom: 0;
}

.dim-tab {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 10px 16px;
  border-radius: 0;
  border: none;
  border-bottom: 2.5px solid transparent;
  background: transparent;
  font-size: 13.5px;
  font-weight: 500;
  color: var(--text-2);
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;
  margin-bottom: -1px;

  &:hover { color: var(--text-1); background: var(--bg-muted); }

  &.active {
    color: var(--indigo);
    font-weight: 600;
    border-bottom-color: var(--indigo);
    background: transparent;
  }

  &__icon { font-size: 14px; }
}

// 创建按钮（Tab 行右侧）
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
  padding: 6px 14px;
  cursor: pointer;
  font-family: var(--font-sans);
  transition: all 0.15s;
  flex-shrink: 0;
  margin-bottom: 10px;

  &:hover:not(:disabled) { background: var(--indigo); color: #fff; }
  &:disabled { opacity: 0.5; cursor: not-allowed; }
}

// ── 版本信息栏 ───────────────────────────────────────────────
.version-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 24px;
  background: var(--bg-muted);
  border-bottom: 1px solid var(--border);

  &__left { display: flex; align-items: center; gap: 10px; }
  &__time { font-size: 12.5px; color: var(--text-3); }
}

.dim-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--text-1);
}

.active-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
  background: var(--green-dim);
  border: 1.5px solid var(--green-border);
  border-radius: var(--r-pill);
  padding: 3px 10px;
}

// ── 参数展示区 ───────────────────────────────────────────────
.params-body {
  padding: 20px 24px;
}

.params-section {
  &__title {
    font-size: 12px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.06em;
    text-transform: uppercase;
    margin-bottom: 12px;
    display: flex;
    align-items: center;
    gap: 8px;
  }

  &__row {
    display: flex;
    gap: 40px;
    flex-wrap: wrap;
  }
}

.params-divider {
  height: 1px;
  background: var(--border);
  margin: 18px 0;
}

.param-item {
  display: flex;
  flex-direction: column;
  gap: 4px;

  &__label {
    font-size: 12px;
    color: var(--text-3);
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 0.04em;
  }

  &__val {
    font-size: 14px;
    font-weight: 600;
    color: var(--text-1);

    em {
      font-style: normal;
      font-size: 12px;
      font-weight: 400;
      color: var(--text-3);
      margin-left: 3px;
    }
  }
}

.big-val {
  font-size: 28px !important;
  font-weight: 700 !important;
  color: var(--indigo) !important;
  line-height: 1;
}

.param-note {
  font-size: 13px;
  color: var(--text-2);
  font-style: italic;
}

// ── 难度分布条 ───────────────────────────────────────────────
.diff-dist, .diff-preview {
  display: flex;
  width: 100%;
  height: 32px;
  border-radius: var(--r-md);
  overflow: hidden;
  gap: 2px;
}

.diff-preview { height: 28px; margin-top: 12px; }

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
  min-width: 48px;

  &--basic    { background: var(--teal); }
  &--advanced { background: var(--amber); }
  &--challenge { background: var(--red); }
}

// ── 错题攻克策略 ─────────────────────────────────────────────
.wrong-strategy-grid {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.wrong-strategy-item {
  display: flex;
  align-items: center;
  gap: 16px;

  &__label {
    font-size: 13px;
    color: var(--text-2);
    min-width: 80px;
    flex-shrink: 0;
  }
}

.sort-options {
  display: flex;
  gap: 12px;
}

.sort-option {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  font-size: 13px;
  color: var(--text-3);

  &.active {
    color: var(--indigo);
    font-weight: 600;
  }

  &__dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    border: 2px solid currentColor;
    flex-shrink: 0;
  }

  &.active .sort-option__dot {
    background: var(--indigo);
    border-color: var(--indigo);
  }
}

// ── 历史版本 ─────────────────────────────────────────────────
.history-section {
  border-top: 1px solid var(--border);
  padding: 14px 24px 20px;
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

.readonly-tag { font-size: 11.5px; color: var(--text-3); margin-left: auto; }

// ── 全局抽屉内样式 ───────────────────────────────────────────
.global-version-bar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.global-params {
  display: flex;
  flex-direction: column;
  gap: 16px;
  margin-bottom: 4px;
}

.global-group {
  background: var(--bg-muted);
  border-radius: var(--r-xl);
  padding: 14px 16px;

  &__title {
    font-size: 11px;
    font-weight: 700;
    color: var(--text-3);
    letter-spacing: 0.07em;
    text-transform: uppercase;
    margin-bottom: 10px;
  }
}

.global-row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 5px 0;
  font-size: 13px;

  &:not(:last-child) { border-bottom: 1px solid rgba(0,0,0,0.04); }
}

.global-label { color: var(--text-2); }

.mode-badge {
  font-size: 12px;
  font-weight: 500;
  background: var(--indigo-light);
  color: var(--indigo);
  border-radius: var(--r-pill);
  padding: 2px 10px;
  border: 1px solid var(--indigo-border);
}

// ── 弹窗小节标题 ─────────────────────────────────────────────
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

.status-pill {
  font-size: 12px;
  font-weight: 500;
  padding: 2px 9px;
  border-radius: var(--r-pill);
  border: 1.5px solid;

  &.pill--active { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
  &.pill--off    { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }
}
</style>
