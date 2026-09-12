<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/cognitive-test')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回
        </el-button>
        <div>
          <h1 class="page-title">{{ isEdit ? '编辑测试题目' : '新增测试题目' }}</h1>
          <p class="page-subtitle">{{ isEdit ? `正在编辑题目 #${route.params.id}` : '创建五力认知测试题，保存为草稿后可发布至测试池' }}</p>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <el-button @click="handleSave('draft')" :loading="loading">保存草稿</el-button>
        <button class="btn-pink" type="button" @click="handleSave('publish')" :disabled="loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          保存并发布
        </button>
      </div>
    </div>

    <!-- ── 已发布题目数量提示 ── -->
    <div v-if="!isEdit" class="publish-tip" :class="publishedCount >= 20 ? 'publish-tip--full' : 'publish-tip--normal'">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
        <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
      </svg>
      <span v-if="publishedCount >= 20">
        当前已发布 <strong class="num">{{ publishedCount }}/20</strong> 道，已达上限。若需发布新题，请先前往列表下架旧题。
      </span>
      <span v-else>
        当前已发布 <strong class="num">{{ publishedCount }}/20</strong> 道，还需发布 <strong class="num">{{ 20 - publishedCount }}</strong> 道测试功能方可启用。
      </span>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" v-loading="loading">

      <!-- ── 基础信息 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">基础信息</span>
        </div>
        <el-row :gutter="24">
          <el-col :span="8">
            <el-form-item label="题目类型" prop="question_type">
              <el-radio-group v-model="form.question_type">
                <el-radio-button value="STANDARD">标准题</el-radio-button>
                <el-radio-button value="OPEN">开放题</el-radio-button>
              </el-radio-group>
              <div class="form-hint">
                {{ form.question_type === 'STANDARD' ? 'STANDARD：有唯一正确答案，以选项得分判断' : 'OPEN：无唯一答案，以五力权重分布评估认知偏好' }}
              </div>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="目标维度" prop="target_power">
              <el-select v-model="form.target_power" style="width:100%" placeholder="选择目标五力维度">
                <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key">
                  <span class="power-badge" :class="`power-badge--${key}`" style="padding:2px 8px;font-size:11px">{{ label }}</span>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="参考时间" prop="reference_time_sec">
              <div style="display:flex;align-items:center;gap:8px">
                <el-input-number v-model="form.reference_time_sec" :min="30" :max="300" :step="10" style="width:130px" />
                <span style="color:var(--text-3);font-size:13px">秒（建议 60~180 秒）</span>
              </div>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- ── 题干内容 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">题干内容</span>
        </div>
        <el-form-item label="题干" prop="stem">
          <el-input
            v-model="form.stem"
            type="textarea"
            :rows="5"
            placeholder="请输入题目题干，描述具体情境和问题..."
            show-word-limit
            maxlength="800"
          />
        </el-form-item>
      </div>

      <!-- ── 选项配置（STANDARD 题：得分） ── -->
      <div class="form-section surface" v-if="form.question_type === 'STANDARD'">
        <div class="section-hd">
          <span class="section-title">选项得分配置</span>
          <span class="section-badge">最高分选项视为正确答案</span>
        </div>
        <div class="option-grid">
          <div v-for="opt in ['A','B','C','D']" :key="opt" class="option-row">
            <div class="option-label" :class="{ 'option-label--max': isMaxScore(opt) }">{{ opt }}</div>
            <div class="option-score-wrap">
              <el-input-number
                v-model="form.option_scores[opt]"
                :min="0"
                :max="20"
                controls-position="right"
                style="width:110px"
              />
              <span class="score-unit">分</span>
              <span v-if="isMaxScore(opt)" class="max-badge">← 正确答案</span>
            </div>
          </div>
        </div>
        <div class="score-preview">
          <span v-for="opt in ['A','B','C','D']" :key="opt" class="score-pill" :class="{ 'score-pill--max': isMaxScore(opt) }">
            <span class="score-pill__opt">{{ opt }}</span>
            <span class="score-pill__val num">{{ form.option_scores[opt] }}</span>
            <span class="score-pill__unit">分</span>
          </span>
        </div>
      </div>

      <!-- ── 选项配置（OPEN 题：五力权重矩阵） ── -->
      <div class="form-section surface" v-else>
        <div class="section-hd">
          <span class="section-title">选项五力权重配置</span>
          <span class="section-badge">每行合计建议为 1.0</span>
        </div>
        <p style="font-size:13px;color:var(--text-2);margin-bottom:18px;line-height:1.6">
          为每个选项配置五力维度权重分布，表示选择该选项的学生在各维度上的认知倾向强度。
        </p>
        <div class="weight-table-wrap">
          <table class="weight-table">
            <thead>
              <tr>
                <th style="width:60px">选项</th>
                <th v-for="p in powers" :key="p">
                  <span class="power-badge" :class="`power-badge--${p}`" style="font-size:11px;padding:2px 8px">
                    {{ FivePowerLabels[p as FivePower] }}
                  </span>
                </th>
                <th style="width:80px;color:var(--text-3)">合计</th>
              </tr>
            </thead>
            <tbody>
              <tr v-for="opt in ['A','B','C','D']" :key="opt">
                <td class="opt-cell">
                  <span class="opt-badge">{{ opt }}</span>
                </td>
                <td v-for="p in powers" :key="p" class="num-cell">
                  <el-input-number
                    v-model="form.option_force_weights[opt][p]"
                    :min="0" :max="1" :step="0.05"
                    controls-position="right"
                    size="small"
                    style="width:84px"
                  />
                </td>
                <td class="sum-cell">
                  <span class="num" :class="isSumValid(opt) ? 'sum--ok' : 'sum--err'">
                    {{ rowSum(opt).toFixed(2) }}
                  </span>
                </td>
              </tr>
            </tbody>
          </table>
        </div>
        <div v-if="!allSumsValid" class="sum-error-tip">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
          </svg>
          存在行权重合计不等于 1.0，请检查后再保存（允许 ±0.01 误差）。
        </div>
      </div>

    </el-form>

  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage, ElMessageBox } from 'element-plus'
import { cognitiveApi } from '@/api'
import type { FivePower } from '@/types'
import { FivePowerLabels } from '@/types'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const publishedCount = ref(0)

const isEdit = computed(() => !!route.params.id)
const powers = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

function makeDefaultWeights() {
  const result: Record<string, Record<string, number>> = {}
  for (const opt of ['A', 'B', 'C', 'D']) {
    result[opt] = { INSIGHT: 0.2, CONSTRUCT: 0.2, DEDUCE: 0.2, ADAPT: 0.2, MIGRATE: 0.2 }
  }
  return result
}

const form = reactive({
  stem: '',
  question_type: 'STANDARD' as 'STANDARD' | 'OPEN',
  target_power: 'INSIGHT' as FivePower,
  reference_time_sec: 90,
  option_scores: { A: 1, B: 10, C: 4, D: 1 } as Record<string, number>,
  option_force_weights: makeDefaultWeights() as Record<string, Record<string, number>>,
})

const rules: FormRules = {
  stem: [{ required: true, message: '请输入题干内容', trigger: 'blur' }],
  target_power: [{ required: true, message: '请选择目标维度', trigger: 'change' }],
  reference_time_sec: [{ required: true, message: '请填写参考时间', trigger: 'change' }],
}

// ── 选项得分辅助 ──────────────────────────────────────────────
function isMaxScore(opt: string) {
  const max = Math.max(...Object.values(form.option_scores))
  return form.option_scores[opt] === max
}

// ── 权重合计辅助 ──────────────────────────────────────────────
function rowSum(opt: string) {
  return Object.values(form.option_force_weights[opt] || {}).reduce((s, v) => s + v, 0)
}

function isSumValid(opt: string) {
  return Math.abs(rowSum(opt) - 1) < 0.02
}

const allSumsValid = computed(() =>
  ['A', 'B', 'C', 'D'].every(o => isSumValid(o))
)

// ── 初始化：加载已有数据（编辑模式）或读取发布计数 ──────────
onMounted(async () => {
  loading.value = true
  try {
    const list = await cognitiveApi.getList()
    publishedCount.value = list.filter(q => q.status === 'published').length

    if (isEdit.value) {
      const question = list.find(q => q.id === Number(route.params.id))
      if (question) {
        form.stem = question.stem
        form.question_type = question.question_type
        form.target_power = question.target_power
        form.reference_time_sec = question.reference_time_sec
        form.option_scores = { ...question.option_scores }
        if (question.option_force_weights) {
          form.option_force_weights = JSON.parse(JSON.stringify(question.option_force_weights))
        }
      }
    }
  } finally {
    loading.value = false
  }
})

// ── 保存逻辑 ─────────────────────────────────────────────────
async function handleSave(action: 'draft' | 'publish') {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return

  if (action === 'publish' && form.question_type === 'OPEN' && !allSumsValid.value) {
    ElMessage.warning('开放题各选项权重合计需为 1.0，请检查后再发布')
    return
  }

  if (action === 'publish' && publishedCount.value >= 20) {
    ElMessage.error('已发布题目数已达 20 道，请先下架一道后再发布新题')
    return
  }

  if (action === 'publish') {
    await ElMessageBox.confirm(
      `发布后该题将加入测试池。当前已发布 ${publishedCount.value}/20 道，发布后将达 ${publishedCount.value + 1}/20 道。`,
      '确认发布此题目？',
      { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning' }
    ).catch(() => { throw new Error('cancelled') })
  }

  loading.value = true
  try {
    const payload = {
      stem: form.stem,
      question_type: form.question_type,
      target_power: form.target_power,
      reference_time_sec: form.reference_time_sec,
      option_scores: { ...form.option_scores },
      option_force_weights: form.question_type === 'OPEN'
        ? JSON.parse(JSON.stringify(form.option_force_weights))
        : undefined,
    }

    if (isEdit.value) {
      await cognitiveApi.update(Number(route.params.id), payload)
      if (action === 'publish') {
        await cognitiveApi.publish(Number(route.params.id))
      }
      ElMessage.success(action === 'publish' ? '修改已保存并发布' : '修改已保存为草稿')
    } else {
      const created = await cognitiveApi.create(payload)
      if (action === 'publish') {
        await cognitiveApi.publish(created.id)
      }
      ElMessage.success(action === 'publish' ? '题目已创建并发布至测试池' : '草稿已保存')
    }

    router.push('/cognitive-test')
  } catch (e) {
    if ((e as Error).message !== 'cancelled') throw e
  } finally {
    loading.value = false
  }
}
</script>

<style lang="scss" scoped>
// ── 发布提示栏 ───────────────────────────────────────────────
.publish-tip {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: var(--r-xl);
  border: 1.5px solid;
  font-size: 13.5px;

  &--normal {
    background: var(--indigo-light);
    border-color: var(--indigo-border);
    color: var(--indigo);
  }

  &--full {
    background: var(--amber-dim);
    border-color: var(--amber-border);
    color: var(--amber);
  }

  strong { font-family: var(--font-mono); font-weight: 700; }
}

// ── 表单分区 ─────────────────────────────────────────────────
.form-section {
  padding: 22px 24px;
  margin-bottom: 16px;
}

.section-badge {
  font-size: 12px;
  color: var(--indigo);
  background: var(--indigo-light);
  padding: 3px 10px;
  border-radius: var(--r-pill);
  font-weight: 500;
}

.form-hint {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 6px;
  line-height: 1.5;
}

// ── STANDARD 选项得分 ────────────────────────────────────────
.option-grid {
  display: flex;
  flex-direction: column;
  gap: 12px;
  margin-bottom: 20px;
}

.option-row {
  display: flex;
  align-items: center;
  gap: 14px;
}

.option-label {
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--bg-muted);
  border: 1.5px solid var(--border-hover);
  color: var(--text-2);
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  transition: all 0.15s;

  &--max {
    background: var(--green-dim);
    border-color: var(--green-border);
    color: var(--green);
  }
}

.option-score-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.score-unit {
  font-size: 13px;
  color: var(--text-3);
}

.max-badge {
  font-size: 12px;
  font-weight: 600;
  color: var(--green);
  background: var(--green-dim);
  padding: 2px 10px;
  border-radius: var(--r-pill);
  border: 1px solid var(--green-border);
}

// 得分预览
.score-preview {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
  padding-top: 16px;
  border-top: 1px solid var(--border);
}

.score-pill {
  display: flex;
  align-items: center;
  gap: 4px;
  padding: 5px 12px;
  border-radius: var(--r-pill);
  background: var(--bg-surface);
  border: 1.5px solid var(--border);
  font-size: 13px;

  &--max {
    background: var(--green-dim);
    border-color: var(--green-border);

    .score-pill__val { color: var(--green); }
  }

  &__opt  { font-weight: 700; color: var(--text-2); }
  &__val  { font-weight: 700; color: var(--text-1); margin-left: 2px; }
  &__unit { font-size: 11px; color: var(--text-3); }
}

// ── OPEN 权重矩阵 ────────────────────────────────────────────
.weight-table-wrap {
  overflow-x: auto;
}

.weight-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 13.5px;

  th {
    padding: 10px 12px;
    background: #F8F9FD;
    color: var(--text-3);
    font-size: 11.5px;
    font-weight: 600;
    text-align: center;
    border-bottom: 1px solid var(--border);
  }

  td {
    padding: 10px 12px;
    text-align: center;
    border-bottom: 1px solid var(--border);
    vertical-align: middle;
  }

  tr:last-child td { border-bottom: none; }
  tr:hover td { background: #F5F7FF; }
}

.opt-cell { text-align: center; }

.opt-badge {
  width: 28px;
  height: 28px;
  border-radius: var(--r-sm);
  background: var(--indigo-light);
  color: var(--indigo);
  font-size: 13px;
  font-weight: 700;
  display: inline-flex;
  align-items: center;
  justify-content: center;
}

.num-cell { }

.sum-cell { font-size: 13px; font-weight: 700; }

.sum--ok { color: var(--green); }
.sum--err { color: var(--red); }

.sum-error-tip {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 14px;
  padding: 10px 14px;
  background: var(--red-dim);
  border: 1px solid var(--red-border);
  border-radius: var(--r-lg);
  font-size: 13px;
  color: var(--red);
}
</style>
