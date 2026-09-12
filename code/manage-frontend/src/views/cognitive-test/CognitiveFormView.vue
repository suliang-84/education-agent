<template>
  <div class="page-root">

    <!-- ── 页头 ── -->
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="router.push('/cognitive-test')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回列表
        </el-button>
        <div>
          <h1 class="page-title">{{ isEdit ? '编辑测试题目' : '新增测试题目' }}</h1>
          <p class="page-subtitle">{{ isEdit ? `正在编辑题目 #${route.params.id}` : '创建五力认知测试题，保存为草稿后可发布至测试池' }}</p>
        </div>
      </div>
      <div style="display:flex;gap:10px;align-items:center">
        <el-button @click="handleSave('draft')" :loading="saving">保存草稿</el-button>
        <button class="btn-pink" type="button" @click="handleSave('publish')" :disabled="saving || loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          保存并发布
        </button>
      </div>
    </div>

    <!-- ── 已发布状态提示 ── -->
    <div class="publish-tip" :class="publishedCount >= 10 ? 'publish-tip--normal' : 'publish-tip--warn'">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
        <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
      </svg>
      <span v-if="publishedCount >= 10">
        当前已发布 <strong class="num">{{ publishedCount }}</strong> 道，测试功能已就绪。题目数量无上限，可继续新增发布。
      </span>
      <span v-else>
        当前已发布 <strong class="num">{{ publishedCount }}</strong> 道，还需发布 <strong class="num">{{ 10 - publishedCount }}</strong> 道，测试功能方可对学生开放。
      </span>
    </div>

    <div v-loading="loading">

      <!-- ── 基础信息 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">基础信息</span>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="100px">
          <el-row :gutter="24">
            <el-col :span="8">
              <el-form-item label="参考时间" prop="reference_time_sec">
                <div style="display:flex;align-items:center;gap:8px">
                  <el-input-number
                    v-model="form.reference_time_sec"
                    :min="30" :max="600" :step="15"
                    style="width:130px"
                  />
                  <span style="color:var(--text-3);font-size:13px">秒（建议 60~180）</span>
                </div>
              </el-form-item>
            </el-col>
            <el-col :span="16">
              <el-form-item label="题目描述">
                <el-input
                  v-model="form.description"
                  placeholder="管理员内部元数据，不展示给学生。如：测量学生在面对冲突证据时的洞察力倾向"
                  maxlength="200"
                  show-word-limit
                />
                <div class="form-hint">用于记录该题的测量意图，便于题库管理，学生不可见。</div>
              </el-form-item>
            </el-col>
          </el-row>
        </el-form>
      </div>

      <!-- ── 题干内容 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">题干内容</span>
          <span class="section-badge">展示给学生，支持 Markdown / LaTeX</span>
        </div>
        <el-form ref="stemFormRef" :model="form" :rules="rules" label-width="0">
          <el-form-item prop="stem" style="margin-bottom:0">
            <el-input
              v-model="form.stem"
              type="textarea"
              :rows="5"
              placeholder="请输入题目题干，描述具体情境和问题..."
              show-word-limit
              maxlength="800"
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- ── 答案配置 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">答案配置</span>
          <div style="display:flex;align-items:center;gap:10px">
            <span class="section-badge">每行合计需为 1.0（±0.01）</span>
            <el-button
              size="small"
              :disabled="form.answers.length >= 8"
              @click="addAnswer"
            >
              <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:3px">
                <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
              </svg>
              添加答案
            </el-button>
          </div>
        </div>

        <p class="answers-intro">
          每个答案对应学生的一种认知倾向选择，通过五力权重分布评估其认知特征。
          <strong>选项编号（A/B/C/D…）由系统自动生成，最少 2 个，最多 8 个。</strong>
        </p>

        <!-- 答案列表 -->
        <div class="answer-list">
          <div
            v-for="(answer, idx) in form.answers"
            :key="idx"
            class="answer-card"
            :class="{ 'answer-card--invalid': !isWeightValid(idx) }"
          >
            <!-- 答案头部 -->
            <div class="answer-card__header">
              <div class="answer-key-badge">{{ String.fromCharCode(65 + idx) }}</div>
              <div class="answer-text-wrap">
                <el-input
                  v-model="answer.text"
                  placeholder="输入该选项的答案文本..."
                  maxlength="200"
                  show-word-limit
                />
              </div>
              <el-button
                text
                size="small"
                style="color:var(--red);flex-shrink:0"
                :disabled="form.answers.length <= 2"
                @click="removeAnswer(idx)"
              >
                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                  <path stroke-linecap="round" stroke-linejoin="round" d="M14.74 9l-.346 9m-4.788 0L9.26 9m9.968-3.21c.342.052.682.107 1.022.166m-1.022-.165L18.16 19.673a2.25 2.25 0 01-2.244 2.077H8.084a2.25 2.25 0 01-2.244-2.077L4.772 5.79m14.456 0a48.108 48.108 0 00-3.478-.397m-12 .562c.34-.059.68-.114 1.022-.165m0 0a48.11 48.11 0 013.478-.397m7.5 0v-.916c0-1.18-.91-2.164-2.09-2.201a51.964 51.964 0 00-3.32 0c-1.18.037-2.09 1.022-2.09 2.201v.916m7.5 0a48.667 48.667 0 00-7.5 0"/>
                </svg>
                删除
              </el-button>
            </div>

            <!-- 五力权重配置 -->
            <div class="answer-card__weights">
              <span class="weights-label">五力权重分布</span>
              <div class="weights-row">
                <div v-for="p in powers" :key="p" class="weight-item">
                  <div class="weight-item__label">
                    <span class="power-dot" :class="`power-dot--${p}`" />
                    {{ FivePowerLabels[p as FivePower] }}
                  </div>
                  <el-input-number
                    v-model="answer.force_weights[p as FivePower]"
                    :min="0" :max="1" :step="0.05"
                    :precision="2"
                    controls-position="right"
                    size="small"
                    style="width:90px"
                  />
                </div>
                <!-- 合计 -->
                <div class="weight-sum" :class="isWeightValid(idx) ? 'weight-sum--ok' : 'weight-sum--err'">
                  <span class="weight-sum__label">合计</span>
                  <span class="weight-sum__val num">{{ answerWeightSum(idx).toFixed(2) }}</span>
                  <svg v-if="isWeightValid(idx)" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M4.5 12.75l6 6 9-13.5"/>
                  </svg>
                  <svg v-else width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5">
                    <path stroke-linecap="round" stroke-linejoin="round" d="M6 18L18 6M6 6l12 12"/>
                  </svg>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- 答案数量提示 -->
        <div class="answers-footer">
          <span class="answers-count">
            当前 <strong class="num">{{ form.answers.length }}</strong> 个答案
            <span style="color:var(--text-3)">（最少 2 个，最多 8 个）</span>
          </span>
          <div v-if="!allWeightsValid" class="weights-error">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
              <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m9-.75a9 9 0 11-18 0 9 9 0 0118 0zm-9 3.75h.008v.008H12v-.008z"/>
            </svg>
            存在答案权重合计不等于 1.0，请调整后再保存。
          </div>
        </div>
      </div>

    </div>

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

const route  = useRoute()
const router = useRouter()
const formRef     = ref<FormInstance>()
const stemFormRef = ref<FormInstance>()
const loading = ref(false)
const saving  = ref(false)
const publishedCount = ref(0)

const isEdit  = computed(() => !!route.params.id)
const powers  = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 新建一个默认答案（均等权重）──────────────────────────────
function makeAnswer(text = '') {
  return {
    text,
    force_weights: { INSIGHT: 0.20, CONSTRUCT: 0.20, DEDUCE: 0.20, ADAPT: 0.20, MIGRATE: 0.20 } as Record<FivePower, number>,
  }
}

// ── 表单状态 ─────────────────────────────────────────────────
const form = reactive({
  description: '',
  stem: '',
  reference_time_sec: 90,
  answers: [makeAnswer(), makeAnswer(), makeAnswer(), makeAnswer()] as Array<{
    text: string
    force_weights: Record<FivePower, number>
  }>,
})

const rules: FormRules = {
  stem:               [{ required: true, message: '请输入题干内容', trigger: 'blur' }],
  reference_time_sec: [{ required: true, message: '请填写参考时间', trigger: 'change' }],
}

// ── 权重验证辅助 ─────────────────────────────────────────────
function answerWeightSum(idx: number) {
  return Object.values(form.answers[idx].force_weights).reduce((s, v) => s + v, 0)
}

function isWeightValid(idx: number) {
  return Math.abs(answerWeightSum(idx) - 1) < 0.02
}

const allWeightsValid = computed(() => form.answers.every((_, i) => isWeightValid(i)))

// ── 答案增删 ─────────────────────────────────────────────────
function addAnswer() {
  if (form.answers.length >= 8) return
  form.answers.push(makeAnswer())
}

function removeAnswer(idx: number) {
  if (form.answers.length <= 2) return
  form.answers.splice(idx, 1)
}

// ── 初始化 ───────────────────────────────────────────────────
onMounted(async () => {
  loading.value = true
  try {
    const list = await cognitiveApi.getList()
    publishedCount.value = list.filter(q => q.status === 'published').length

    if (isEdit.value) {
      const q = list.find(q => q.id === Number(route.params.id))
      if (q) {
        form.description      = q.description ?? ''
        form.stem             = q.stem
        form.reference_time_sec = q.reference_time_sec
        // 还原答案列表，去掉 key（前端按索引管理）
        form.answers = q.answers.map(a => ({
          text: a.text,
          force_weights: { ...a.force_weights } as Record<FivePower, number>,
        }))
      }
    }
  } finally {
    loading.value = false
  }
})

// ── 保存 ─────────────────────────────────────────────────────
async function handleSave(action: 'draft' | 'publish') {
  // 校验基础表单
  const [v1, v2] = await Promise.all([
    formRef.value?.validate().catch(() => false),
    stemFormRef.value?.validate().catch(() => false),
  ])
  if (!v1 || !v2) return

  // 答案数量校验
  if (form.answers.length < 2) {
    ElMessage.warning('至少需要 2 个答案')
    return
  }
  if (form.answers.some(a => !a.text.trim())) {
    ElMessage.warning('存在答案文本为空，请填写后再保存')
    return
  }

  // 发布时的额外校验
  if (action === 'publish') {
    if (!allWeightsValid.value) {
      ElMessage.warning('存在答案权重合计不等于 1.0，请检查后再发布')
      return
    }
    const willEnable = publishedCount.value < 10 && publishedCount.value + 1 >= 10
    await ElMessageBox.confirm(
      `发布后该题将加入测试池。当前已发布 ${publishedCount.value} 道，发布后将达 ${publishedCount.value + 1} 道。${willEnable ? '\n\n🎉 发布后将达到10道，测试功能将自动对学生开放！' : '\n\n⚠ 发布后题目内容的修改将立即影响新测试会话。'}`,
      '确认发布此题目？',
      { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning' }
    ).catch(() => { throw new Error('cancelled') })
  }

  saving.value = true
  try {
    const payload = {
      description: form.description || undefined,
      stem: form.stem,
      reference_time_sec: form.reference_time_sec,
      // key 由后端自动按序生成，前端不传
      answers: form.answers.map(a => ({
        text: a.text.trim(),
        force_weights: { ...a.force_weights },
      })),
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
    saving.value = false
  }
}
</script>

<style lang="scss" scoped>
// ── 发布状态提示 ─────────────────────────────────────────────
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

  &--warn {
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

// ── 答案区说明文字 ───────────────────────────────────────────
.answers-intro {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.7;
  margin-bottom: 20px;
  padding: 10px 14px;
  background: var(--bg-muted);
  border-radius: var(--r-lg);

  strong { color: var(--text-1); font-weight: 600; }
}

// ── 答案列表 ─────────────────────────────────────────────────
.answer-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
  margin-bottom: 16px;
}

.answer-card {
  border: 1.5px solid var(--border);
  border-radius: var(--r-xl);
  overflow: hidden;
  transition: border-color 0.15s;

  &:hover { border-color: var(--border-hover); }

  &--invalid {
    border-color: rgba(239, 68, 68, 0.40);
    background: rgba(239, 68, 68, 0.02);
  }

  // ── 答案头部（编号 + 文本 + 删除）────────────────────────
  &__header {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px 16px;
    background: var(--bg-surface);
  }

  // ── 权重区 ───────────────────────────────────────────────
  &__weights {
    padding: 12px 16px 14px;
    background: var(--bg-muted);
    border-top: 1px solid var(--border);
  }
}

// 答案编号标牌（A/B/C/D…）
.answer-key-badge {
  width: 32px;
  height: 32px;
  border-radius: var(--r-sm);
  background: var(--indigo);
  color: #fff;
  font-size: 14px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  letter-spacing: 0;
}

// 答案文本输入区（撑满剩余宽度）
.answer-text-wrap {
  flex: 1;
  min-width: 0;
}

// ── 权重配置行 ───────────────────────────────────────────────
.weights-label {
  font-size: 11.5px;
  font-weight: 600;
  color: var(--text-3);
  letter-spacing: 0.04em;
  text-transform: uppercase;
  display: block;
  margin-bottom: 10px;
}

.weights-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

.weight-item {
  display: flex;
  flex-direction: column;
  gap: 5px;
  align-items: center;

  &__label {
    display: flex;
    align-items: center;
    gap: 4px;
    font-size: 11.5px;
    font-weight: 500;
    color: var(--text-2);
    white-space: nowrap;
  }
}

// 五力维度彩色圆点
.power-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

// 合计显示
.weight-sum {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 4px;
  padding: 6px 12px;
  border-radius: var(--r-lg);
  min-width: 64px;
  font-size: 12px;

  &--ok {
    background: var(--green-dim);
    color: var(--green);
    border: 1px solid var(--green-border);
  }

  &--err {
    background: var(--red-dim);
    color: var(--red);
    border: 1px solid var(--red-border);
  }

  &__label {
    font-size: 10.5px;
    font-weight: 600;
    letter-spacing: 0.04em;
    text-transform: uppercase;
    opacity: 0.7;
  }

  &__val {
    font-size: 15px;
    font-weight: 700;
    line-height: 1;
  }
}

// ── 答案区底部 ───────────────────────────────────────────────
.answers-footer {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 16px;
  flex-wrap: wrap;
  padding-top: 14px;
  border-top: 1px solid var(--border);
}

.answers-count {
  font-size: 13px;
  color: var(--text-2);

  strong { color: var(--indigo); }
}

.weights-error {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  color: var(--red);
  background: var(--red-dim);
  padding: 7px 12px;
  border-radius: var(--r-lg);
  border: 1px solid var(--red-border);
}
</style>
