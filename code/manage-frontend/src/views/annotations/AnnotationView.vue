<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">AI 标注审核</h1>
        <p class="page-subtitle">审核 AI 自动标注结果，确认或修正五力维度归属</p>
      </div>
    </div>

    <!-- Stats bar -->
    <div class="surface stats-bar">
      <div class="stats-bar__left">
        <div class="sbar-item">
          <span class="sbar-label">待审核</span>
          <span class="sbar-val num" style="color:var(--amber)">{{ pendingCount }}</span>
          <span class="sbar-unit">条</span>
        </div>
        <div class="sbar-divider" />
        <div class="sbar-item">
          <span class="sbar-label">高置信度可批量</span>
          <span class="sbar-val num" style="color:var(--green)">{{ highConfidenceCount }}</span>
          <span class="sbar-unit">条</span>
        </div>
        <div class="sbar-divider" />
        <div class="sbar-item" style="gap:12px">
          <span class="sbar-label">置信度范围</span>
          <el-slider
            v-model="confidenceRange"
            range :min="0" :max="1" :step="0.05"
            :format-tooltip="(v: number) => (v * 100).toFixed(0) + '%'"
            style="width:180px"
            @change="loadData"
          />
          <span class="sbar-range num">{{ (confidenceRange[0]*100).toFixed(0) }}% – {{ (confidenceRange[1]*100).toFixed(0) }}%</span>
        </div>
      </div>
      <button class="btn-pink" @click="handleBatchConfirm" style="white-space:nowrap">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
          <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
        </svg>
        批量确认 ≥85%（{{ highConfidenceCount }} 条）
      </button>
    </div>

    <!-- Cards -->
    <div class="annotation-list" v-loading="loading">
      <div
        v-for="item in annotations"
        :key="item.id"
        class="review-card"
        :class="{ 'review-card--confirmed': item.annotation_status !== 'pending' }"
      >
        <div class="rc-header">
          <div style="display:flex;align-items:center;gap:8px">
            <span class="id-chip">#{{ item.question_id }}</span>
            <span class="status-dot-badge" :class="statusDotClass(item.annotation_status)">
              {{ AnnotationStatusLabels[item.annotation_status as keyof typeof AnnotationStatusLabels] }}
            </span>
          </div>
          <span class="conf-badge" :class="getConfBadge(item.ai_confidence)">{{ (item.ai_confidence * 100).toFixed(0) }}%</span>
        </div>

        <div class="stem-preview">{{ item.question_stem }}</div>

        <div class="row-divider" />

        <div class="ai-result-row">
          <div class="ai-result-col">
            <span class="result-key">AI 主训练力</span>
            <span class="power-badge" :class="`power-badge--${item.ai_primary_power}`">
              {{ FivePowerLabels[item.ai_primary_power as keyof typeof FivePowerLabels] }}
            </span>
          </div>
          <div class="ai-result-col" style="flex:1">
            <span class="result-key">标注理由</span>
            <span class="result-reason">{{ item.ai_reason }}</span>
          </div>
        </div>

        <!-- Pending: human confirm -->
        <div v-if="item.annotation_status === 'pending'" class="human-confirm-box">
          <div class="row-divider" />
          <div class="hc-row">
            <div style="display:flex;align-items:center;gap:10px">
              <span style="font-size:13px;font-weight:500;color:var(--text-2)">确认主训练力：</span>
              <el-select v-model="confirmData[item.id].primary_power" style="width:120px" size="small">
                <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </div>
            <div style="display:flex;gap:8px">
              <el-button type="primary" size="small" @click="handleConfirm(item)">确认标注</el-button>
              <el-button type="danger" size="small" plain @click="handleReject(item)">驳回</el-button>
              <el-button size="small" @click="skipItem()">跳过</el-button>
            </div>
          </div>
        </div>

        <!-- Done -->
        <div v-else class="done-row">
          <div class="row-divider" />
          <div style="display:flex;align-items:center;gap:8px;padding-top:2px">
            <span class="status-dot-badge" :class="statusDotClass(item.annotation_status)">
              已{{ item.annotation_status === 'confirmed' ? '确认' : '驳回' }}
            </span>
            <span v-if="item.confirmed_primary_power" style="color:var(--text-3);font-size:12.5px">
              确认力：
              <span class="power-badge" :class="`power-badge--${item.confirmed_primary_power}`" style="padding:1px 7px;font-size:11.5px">
                {{ FivePowerLabels[item.confirmed_primary_power as keyof typeof FivePowerLabels] }}
              </span>
            </span>
          </div>
        </div>
      </div>

      <div v-if="!loading && annotations.length === 0" class="empty-state">
        <span style="font-size:36px">✅</span>
        <span>暂无待审核标注</span>
      </div>
    </div>

    <div class="paginator">
      <span>已加载 <span class="num">{{ annotations.length }}</span> 条</span>
      <div style="display:flex;gap:6px">
        <el-button size="small" :disabled="cursor === 0" @click="prevPage">上一页</el-button>
        <el-button size="small" :disabled="!hasMore" @click="nextPage">下一页</el-button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { annotationApi } from '@/api'
import type { Annotation } from '@/types'
import { FivePowerLabels, AnnotationStatusLabels } from '@/types'

const loading = ref(false)
const annotations = ref<Annotation[]>([])
const pendingCount = ref(87)
const highConfidenceCount = ref(52)
const hasMore = ref(false)
const cursor = ref(0)
const confidenceRange = ref([0, 1])
const confirmData = reactive<Record<number, { primary_power: string }>>({})

function getConfBadge(c: number) {
  if (c >= 0.85) return 'conf-badge--high'
  if (c >= 0.6) return 'conf-badge--mid'
  return 'conf-badge--low'
}

function statusDotClass(s: string) {
  if (s === 'confirmed') return 'dot-green'
  if (s === 'rejected') return 'dot-red'
  return 'dot-amber'
}

async function loadData() {
  loading.value = true
  try {
    const res = await annotationApi.getList({ min_confidence: confidenceRange.value[0], max_confidence: confidenceRange.value[1], cursor: cursor.value })
    annotations.value = res.list
    hasMore.value = res.has_more
    res.list.forEach(a => { if (!confirmData[a.id]) confirmData[a.id] = { primary_power: a.ai_primary_power } })
  } finally { loading.value = false }
}

async function handleConfirm(item: Annotation) {
  await annotationApi.confirm(item.id, { confirmed_primary_power: confirmData[item.id].primary_power })
  item.annotation_status = 'confirmed'
  item.confirmed_primary_power = confirmData[item.id].primary_power as typeof item.confirmed_primary_power
  ElMessage.success('标注已确认')
  pendingCount.value--
}

async function handleReject(item: Annotation) {
  await annotationApi.reject(item.id)
  item.annotation_status = 'rejected'
  ElMessage.warning('已标记为标注错误')
  pendingCount.value--
}

function skipItem() { ElMessage.info('已跳过') }

async function handleBatchConfirm() {
  await ElMessageBox.confirm(`确认批量确认 ${highConfidenceCount.value} 条置信度 ≥85% 的标注？`, '批量确认', { type: 'warning' })
  await annotationApi.batchConfirm(0.85)
  ElMessage.success(`已批量确认 ${highConfidenceCount.value} 条标注`)
  loadData()
}

function prevPage() { cursor.value = Math.max(0, cursor.value - 10); loadData() }
function nextPage() { cursor.value += 10; loadData() }

onMounted(loadData)
</script>

<style scoped>
.stats-bar {
  display: flex; align-items: center; justify-content: space-between;
  padding: 16px 20px; gap: 16px;
}
.stats-bar__left { display: flex; align-items: center; gap: 16px; flex-wrap: wrap; }
.sbar-item { display: flex; align-items: center; gap: 8px; }
.sbar-label { font-size: 13px; color: var(--text-2); font-weight: 500; }
.sbar-val { font-size: 22px; font-weight: 700; line-height: 1; letter-spacing: -0.04em; }
.sbar-unit { font-size: 12px; color: var(--text-3); }
.sbar-divider { width: 1px; height: 32px; background: var(--border); }
.sbar-range { font-size: 12.5px; color: var(--text-3); }

.annotation-list { display: flex; flex-direction: column; gap: 12px; }

.rc-header { display: flex; align-items: center; justify-content: space-between; margin-bottom: 12px; }

.status-dot-badge {
  font-size: 12px; font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;
}
.dot-amber { background: var(--amber-dim); color: var(--amber); border-color: var(--amber-border); }
.dot-green { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
.dot-red   { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }

.stem-preview {
  font-size: 13.5px; color: var(--text-2); line-height: 1.6;
  background: var(--bg-muted);
  border-radius: var(--r-lg);
  padding: 12px 14px;
}

.ai-result-row {
  display: flex; align-items: flex-start; gap: 20px;
  flex-wrap: wrap;
}
.ai-result-col { display: flex; align-items: center; gap: 8px; }
.result-key { font-size: 12.5px; color: var(--text-3); font-weight: 500; white-space: nowrap; }
.result-reason { font-size: 13px; color: var(--text-2); line-height: 1.5; }

.human-confirm-box { }
.hc-row {
  display: flex; align-items: center;
  justify-content: space-between;
  gap: 12px; flex-wrap: wrap;
  padding-top: 4px;
}
</style>
