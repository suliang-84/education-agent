<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">五力测试题维护</h1>
        <p class="page-subtitle">20 道固定测试题，用于生成学生五力认知画像</p>
      </div>
    </div>

    <!-- Warning banner -->
    <div class="warn-banner">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="flex-shrink:0">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
      </svg>
      修改选项得分或参考时间会<strong style="font-weight:600">立即影响所有新测试的评分计算</strong>，请谨慎操作。
    </div>

    <!-- Table -->
    <div class="surface" style="overflow:hidden" v-loading="loading">
      <el-table :data="questions" row-key="id" :expand-row-keys="expandedRows" style="width:100%">

        <el-table-column type="expand">
          <template #default="{ row }">
            <div class="expand-panel">
              <!-- Edit mode -->
              <el-form label-width="100px" v-if="editingId === row.id">
                <el-form-item label="各选项得分">
                  <div class="score-inputs">
                    <div v-for="opt in ['A','B','C','D']" :key="opt" class="score-input-item">
                      <span class="score-opt-lbl">{{ opt }}</span>
                      <el-input-number v-model="editForm.option_scores[opt]" :min="0" :max="20" controls-position="right" size="small" style="width:88px" />
                    </div>
                  </div>
                  <div class="score-hint">当前最高分：<span class="num" style="color:var(--green);font-weight:600">{{ maxScoreOption }}</span></div>
                </el-form-item>
                <el-form-item label="参考时间">
                  <div style="display:flex;align-items:center;gap:8px">
                    <el-input-number v-model="editForm.reference_time_sec" :min="30" :max="300" :step="10" size="small" />
                    <span style="color:var(--text-3);font-size:13px">秒</span>
                  </div>
                </el-form-item>
                <el-form-item v-if="row.question_type === 'OPEN'" label="选项权重">
                  <div class="weight-wrap">
                    <el-table :data="openWeightRows" border size="small" style="max-width:600px">
                      <el-table-column label="选项" prop="opt" width="58" align="center">
                        <template #default="{ row: wr }"><span style="font-weight:700;color:var(--indigo)">{{ wr.opt }}</span></template>
                      </el-table-column>
                      <el-table-column v-for="p in powers" :key="p" :label="FivePowerLabels[p as keyof typeof FivePowerLabels]" width="90" align="center">
                        <template #default="{ row: wr }">
                          <el-input-number v-model="editForm.option_force_weights![wr.opt][p]" :min="0" :max="1" :step="0.05" size="small" controls-position="right" style="width:78px" />
                        </template>
                      </el-table-column>
                    </el-table>
                    <p style="font-size:12px;color:var(--text-3);margin-top:6px">每行各列之和建议为 1.0</p>
                  </div>
                </el-form-item>
                <el-form-item>
                  <el-button type="primary" size="small" @click="saveEdit(row)">保存修改</el-button>
                  <el-button size="small" @click="cancelEdit">取消</el-button>
                </el-form-item>
              </el-form>

              <!-- View mode -->
              <div v-else class="score-pills">
                <span v-for="opt in ['A','B','C','D']" :key="opt" class="score-pill" :class="{ 'score-pill--max': isMaxScore(row, opt) }">
                  <span class="score-pill__opt">{{ opt }}</span>
                  <span class="score-pill__val num">{{ row.option_scores?.[opt] ?? 0 }}</span>
                  <span class="score-pill__unit">分</span>
                </span>
                <span class="ref-time-pill">⏱ {{ row.reference_time_sec }} 秒</span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="题号" prop="order_num" width="70" align="center">
          <template #default="{ row }">
            <span class="num" style="font-weight:600;color:var(--indigo)">{{ row.order_num }}</span>
          </template>
        </el-table-column>

        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <span class="type-badge" :class="row.question_type === 'OPEN' ? 'type--open' : 'type--std'">
              {{ row.question_type === 'OPEN' ? '开放题' : '标准题' }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="题干摘要" min-width="320">
          <template #default="{ row }">
            <span style="color:var(--text-1);font-size:13.5px">{{ row.stem?.substring(0, 60) }}…</span>
          </template>
        </el-table-column>

        <el-table-column label="目标维度" width="100">
          <template #default="{ row }">
            <span class="power-badge" :class="`power-badge--${row.target_power}`">
              {{ FivePowerLabels[row.target_power as keyof typeof FivePowerLabels] }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="参考时间" width="100" align="center">
          <template #default="{ row }">
            <span class="num" style="color:var(--text-2)">{{ row.reference_time_sec }}</span>
            <span style="color:var(--text-3);font-size:12px">秒</span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="90" align="center">
          <template #default="{ row }">
            <el-button text size="small" style="color:var(--indigo)" @click="startEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { cognitiveApi } from '@/api'
import type { CognitiveQuestion } from '@/types'
import { FivePowerLabels } from '@/types'

const loading = ref(false)
const questions = ref<CognitiveQuestion[]>([])
const editingId = ref<number | null>(null)
const expandedRows = ref<string[]>([])
const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE']

const editForm = reactive<{
  option_scores: Record<string, number>
  reference_time_sec: number
  option_force_weights?: Record<string, Record<string, number>>
}>({
  option_scores: { A: 0, B: 0, C: 0, D: 0 },
  reference_time_sec: 90,
  option_force_weights: undefined,
})

const maxScoreOption = computed(() =>
  Object.entries(editForm.option_scores).sort((a, b) => b[1] - a[1])[0]?.[0] || 'B'
)
const openWeightRows = computed(() => ['A', 'B', 'C', 'D'].map(opt => ({ opt })))

function isMaxScore(row: CognitiveQuestion, opt: string) {
  if (!row.option_scores) return false
  const max = Math.max(...Object.values(row.option_scores))
  return row.option_scores[opt] === max
}

function startEdit(row: CognitiveQuestion) {
  editingId.value = row.id
  editForm.option_scores = { ...row.option_scores }
  editForm.reference_time_sec = row.reference_time_sec
  editForm.option_force_weights = row.option_force_weights ? JSON.parse(JSON.stringify(row.option_force_weights)) : undefined
  expandedRows.value = [String(row.id)]
}

function cancelEdit() { editingId.value = null }

async function saveEdit(row: CognitiveQuestion) {
  await cognitiveApi.update(row.id, { option_scores: editForm.option_scores, reference_time_sec: editForm.reference_time_sec, option_force_weights: editForm.option_force_weights })
  row.option_scores = { ...editForm.option_scores }
  row.reference_time_sec = editForm.reference_time_sec
  editingId.value = null
  ElMessage.success('修改已保存，将影响新测试会话的评分')
}

onMounted(async () => {
  loading.value = true
  try { questions.value = await cognitiveApi.getList() }
  finally { loading.value = false }
})
</script>

<style lang="scss" scoped>
.warn-banner {
  display: flex; align-items: flex-start; gap: 10px;
  background: var(--amber-dim);
  border: 1.5px solid var(--amber-border);
  border-radius: var(--r-xl);
  padding: 14px 18px;
  font-size: 13.5px; color: var(--amber);
  line-height: 1.5;
}

.expand-panel { padding: 16px 20px; background: var(--bg-muted); border-top: 1px solid var(--border); }

.score-inputs { display: flex; gap: 12px; flex-wrap: wrap; margin-bottom: 8px; }
.score-input-item { display: flex; align-items: center; gap: 6px; }
.score-opt-lbl {
  width: 22px; height: 22px;
  background: var(--indigo-light);
  color: var(--indigo);
  border-radius: var(--r-sm);
  font-size: 12px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.score-hint { font-size: 12.5px; color: var(--text-3); margin-top: 4px; }
.weight-wrap { }

.score-pills { display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }
.score-pill {
  display: flex; align-items: center; gap: 4px;
  padding: 5px 12px;
  border-radius: var(--r-pill);
  background: var(--bg-surface);
  border: 1.5px solid var(--border);
  font-size: 13px;
}
.score-pill--max {
  background: var(--green-dim);
  border-color: var(--green-border);
}
.score-pill--max .score-pill__val { color: var(--green); }
.score-pill__opt { font-weight: 700; color: var(--text-2); }
.score-pill__val { font-weight: 700; color: var(--text-1); margin-left: 2px; }
.score-pill__unit { font-size: 11px; color: var(--text-3); }

.ref-time-pill {
  padding: 5px 12px;
  border-radius: var(--r-pill);
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1.5px solid var(--indigo-border);
  font-size: 13px; font-weight: 500;
}

.type-badge {
  font-size: 12px; font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;
}
.type--open { background: var(--amber-dim); color: var(--amber); border-color: var(--amber-border); }
.type--std  { background: var(--indigo-light); color: var(--indigo); border-color: var(--indigo-border); }
</style>
