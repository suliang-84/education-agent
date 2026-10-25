<template>
  <div class="page-root">

    <!-- ── 顶部操作栏 ── -->
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="router.push('/cognitive-test')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <!-- 草稿：保存草稿 + 保存并发布 -->
      <template v-if="!isEdit || currentStatus === 'draft'">
        <el-button @click="handleSave('draft')" :loading="saving">
          <SvgIcon v-if="!saving" name="save" :size="14" style="margin-right:4px" />
          保存草稿
        </el-button>
        <button class="btn-pink" type="button" @click="handleSave('publish')" :disabled="saving || loading">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          保存并发布
        </button>
      </template>
      <!-- 已下架：保存修改 + 保存并重新发布 -->
      <template v-else-if="currentStatus === 'archived'">
        <el-button @click="handleSave('save')" :loading="saving">
          <SvgIcon v-if="!saving" name="save" :size="14" style="margin-right:4px" />
          保存修改
        </el-button>
        <button class="btn-pink" type="button" @click="handleSave('republish')" :disabled="saving || loading">
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9 12.75L11.25 15 15 9.75M21 12a9 9 0 11-18 0 9 9 0 0118 0z"/>
          </svg>
          保存并重新发布
        </button>
      </template>
      <!-- 已发布：保存修改（自动生效）-->
      <template v-else>
        <el-button type="primary" @click="handleSave('save')" :loading="saving">保存修改</el-button>
      </template>
    </div>

    <!-- ── 已发布题目修改提醒 ── -->
    <div v-if="currentStatus === 'published'" class="published-notice">
      <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" style="flex-shrink:0">
        <path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"/>
      </svg>
      <span>此题目已发布，修改将<strong>立即影响新测试会话</strong>，历史成绩不受影响。</span>
    </div>

    <!-- ── 新增 / 草稿状态提示 ── -->
    <div v-else-if="!isEdit || currentStatus === 'draft'" class="publish-tip" :class="publishedCount >= 10 ? 'publish-tip--normal' : 'publish-tip--warn'">
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

      <!-- ── 题干内容 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">
            <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />
            题干内容
          </span>
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

      <!-- ── 基础信息 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">
            <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />
            基础信息
          </span>
        </div>
        <el-form ref="formRef" :model="form" :rules="rules" label-width="80px" style="margin-bottom:0">
          <el-form-item label="参考时间" prop="reference_time_sec" style="margin-bottom:10px">
            <div style="display:flex;align-items:center;gap:8px">
              <el-input-number
                v-model="form.reference_time_sec"
                :min="30" :max="600" :step="15"
                style="width:130px"
              />
              <span style="color:var(--text-3);font-size:13px">秒</span>
            </div>
          </el-form-item>
          <el-form-item label="题目描述" style="margin-bottom:0">
            <el-input
              v-model="form.description"
              placeholder="管理员内部元数据，不展示给学生。如：测量学生在面对冲突证据时的洞察力倾向"
              maxlength="200"
              show-word-limit
            />
          </el-form-item>
        </el-form>
      </div>

      <!-- ── 答案配置 ── -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">
            <SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />
            答案配置
          </span>
          <span class="section-badge">每行合计需为 10（整数）</span>
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
                style="flex-shrink:0"
                :disabled="form.answers.length >= 8"
                @click="form.answers.splice(idx + 1, 0, makeAnswer())"
              >
                <SvgIcon name="add" :size="16" color="var(--color-primary)" />
              </el-button>
              <el-button
                text
                size="small"
                style="color:var(--red);flex-shrink:0"
                :disabled="form.answers.length <= 2"
                @click="removeAnswer(idx)"
              >
                <SvgIcon name="delete" :size="16" color="var(--red)" />
              </el-button>
            </div>

            <!-- 五力权重配置 -->
            <div class="answer-card__weights">
              <div class="weights-row">
                <div v-for="p in powers" :key="p" class="weight-item">
                  <div class="weight-item__label">
                    <span class="power-dot" :class="`power-dot--${p}`" />
                    {{ FivePowerLabels[p as FivePower] }}
                  </div>
                  <el-input-number
                    v-model="answer.force_weights[p as FivePower]"
                    :min="0" :max="10" :step="1"
                    :precision="0"
                    controls-position="right"
                    size="small"
                    style="width:90px"
                  />
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

const isEdit        = computed(() => !!route.params.id)
const currentStatus = ref<'draft' | 'published' | 'archived' | null>(null)
const powers        = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as const

// ── 页头动态文案 ──────────────────────────────────────────────
const pageTitle = computed(() => {
  if (!isEdit.value) return '新增测试题目'
  if (currentStatus.value === 'archived')  return '编辑已下架题目'
  if (currentStatus.value === 'published') return '编辑已发布题目'
  return '编辑草稿题目'
})

const pageSubtitle = computed(() => {
  if (!isEdit.value) return '创建五力认知测试题，保存为草稿后可发布至测试池'
  if (currentStatus.value === 'archived')  return `题目 #${route.params.id} · 修改完成后可重新发布，不影响历史成绩`
  if (currentStatus.value === 'published') return `题目 #${route.params.id} · 已发布，修改立即对新测试会话生效`
  return `题目 #${route.params.id} · 草稿状态`
})

// ── 新建一个默认答案（均等权重）──────────────────────────────
function makeAnswer(text = '') {
  return {
    text,
    force_weights: { INSIGHT: 2, CONSTRUCT: 2, DEDUCE: 2, ADAPT: 2, MIGRATE: 2 } as Record<FivePower, number>,
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
  return answerWeightSum(idx) === 10
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
    const res = await cognitiveApi.getList()
    publishedCount.value = res.published_count

    if (isEdit.value) {
      const q = res.list.find(q => q.id === Number(route.params.id))
      if (q) {
        currentStatus.value     = q.status
        form.description        = q.description ?? ''
        form.stem               = q.stem
        form.reference_time_sec = q.reference_time_sec
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
async function handleSave(action: 'draft' | 'publish' | 'save' | 'republish') {
  const [v1, v2] = await Promise.all([
    formRef.value?.validate().catch(() => false),
    stemFormRef.value?.validate().catch(() => false),
  ])
  if (!v1 || !v2) return

  if (form.answers.length < 2) {
    ElMessage.warning('至少需要 2 个答案')
    return
  }
  if (form.answers.some(a => !a.text.trim())) {
    ElMessage.warning('存在答案文本为空，请填写后再保存')
    return
  }

  // 所有保存动作都校验权重（后端强制要求五项之和 = 10）
  if (!allWeightsValid.value) {
    const invalid = form.answers
      .map((_, i) => ({ idx: i, sum: answerWeightSum(i) }))
      .filter(({ sum }) => sum !== 10)
    const msg = invalid.map(({ idx, sum }) =>
      `答案 ${String.fromCharCode(65 + idx)}：合计 ${sum} 分（需为 10 分）`
    ).join('；')
    ElMessage.warning(`五力权重不合法，请调整后再保存 — ${msg}`)
    return
  }

  if (action === 'publish' || action === 'republish') {

    if (action === 'republish') {
      await ElMessageBox.confirm(
        `重新发布后该题将重新加入测试题池。\n\n` +
        `当前已发布：${publishedCount.value} 道，发布后将达：${publishedCount.value + 1} 道。\n\n` +
        `✅ 历史测试会话的评分结果不受影响——系统已为每次测试生成内容快照，历史成绩始终基于测试时的快照版本计算。`,
        '确认重新发布此题目？',
        { confirmButtonText: '确认重新发布', cancelButtonText: '取消', type: 'info' }
      ).catch(() => { throw new Error('cancelled') })
    } else {
      const willEnable = publishedCount.value < 10 && publishedCount.value + 1 >= 10
      await ElMessageBox.confirm(
        `发布后该题将加入测试池。当前已发布 ${publishedCount.value} 道，发布后将达 ${publishedCount.value + 1} 道。` +
        (willEnable ? '\n\n🎉 发布后将达到10道，测试功能将自动对学生开放！' : '\n\n⚠ 发布后题目内容的修改将立即影响新测试会话。'),
        '确认发布此题目？',
        { confirmButtonText: '确认发布', cancelButtonText: '取消', type: 'warning' }
      ).catch(() => { throw new Error('cancelled') })
    }
  }

  saving.value = true
  try {
    const payload = {
      description: form.description || undefined,
      stem: form.stem,
      reference_time_sec: form.reference_time_sec,
      answers: form.answers.map(a => ({
        text: a.text.trim(),
        force_weights: { ...a.force_weights },
      })),
    }

    if (isEdit.value) {
      await cognitiveApi.update(Number(route.params.id), payload)
      if (action === 'publish' || action === 'republish') {
        await cognitiveApi.publish(Number(route.params.id))
      }
      const successMsg: Record<typeof action, string> = {
        draft:     '草稿已保存',
        save:      '修改已保存',
        publish:   '修改已保存并发布',
        republish: '修改已保存，题目已重新发布至测试池',
      }
      ElMessage.success(successMsg[action])
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
// ── 隐藏页面滚动条 ────────────────────────────────────────────
.page-root {
  scrollbar-width: none;
  &::-webkit-scrollbar { display: none; }
}

// ── 顶部操作栏 ───────────────────────────────────────────────
.form-topbar {
  display: flex;
  align-items: center;
  gap: 10px;
}

// ── 返回按钮 ─────────────────────────────────────────────────
[data-theme="light"] .btn-back.el-button {
  background-color: #ffffff;
  color: #9ca2af;
  border-color: #ffffff;
  &:hover { color: var(--color-primary); border-color: var(--color-primary); }
}
[data-theme="dark"] .btn-back.el-button {
  background-color: #242424;
  color: #9ca2af;
  border-color: #242424;
  &:hover { color: var(--color-primary); border-color: var(--color-primary); }
}

// ── 表单分区 ─────────────────────────────────────────────────
.form-section {
  padding: 5px 15px 15px;
  margin-bottom: 10px;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;
}

.section-badge {
  font-size: 12px;
  color: var(--indigo);
  background: var(--indigo-light);
  padding: 3px 10px;
  border-radius: 4px;
  font-weight: 500;
}

.form-hint {
  font-size: 12px;
  color: var(--text-3);
  margin-top: 6px;
  line-height: 1.5;
}

// ── 已下架题目安全编辑提示 ───────────────────────────────────
.archive-notice {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 18px;
  border-radius: var(--r-xl);
  background: var(--indigo-light);
  border: 1.5px solid var(--indigo-border);
  color: var(--indigo);

  &__title {
    font-size: 13.5px;
    font-weight: 600;
    margin-bottom: 4px;
  }

  &__body {
    font-size: 13px;
    line-height: 1.65;
    color: var(--text-2);

    strong { color: var(--text-1); font-weight: 600; }
  }
}

// ── 已发布题目修改提醒 ───────────────────────────────────────
.published-notice {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 18px;
  border-radius: var(--r-xl);
  background: var(--amber-dim);
  border: 1.5px solid var(--amber-border);
  font-size: 13.5px;
  color: var(--amber);

  strong { font-weight: 600; color: var(--text-1); }
}

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

// ── 答案区说明文字 ───────────────────────────────────────────
.answers-intro {
  font-size: 13px;
  color: var(--text-2);
  line-height: 1.7;
  margin-bottom: 10px;
  padding: 8px 10px;
  background: var(--bg-muted);
  border-radius: 4px;

  strong { color: var(--text-1); font-weight: 600; }
}

// ── 答案列表 ─────────────────────────────────────────────────
.answer-list {
  display: flex;
  flex-direction: column;
  gap: 10px;
  margin-bottom: 10px;
}

.answer-card {
  border: 1px solid rgba(96, 141, 248, 0.15);
  border-radius: 4px;
  overflow: hidden;

  &--invalid {
    border-color: rgba(239, 68, 68, 0.40);
  }

  &__header {
    display: flex;
    align-items: center;
    gap: 10px;
    padding: 8px 10px;
    background: var(--bg-surface);

    // 图标按钮去除内边距和自动 margin，间距完全由 gap 控制
    .el-button {
      padding: 0 !important;
      min-width: unset !important;
      margin-left: 0 !important;
    }
  }

  &__weights {
    padding: 8px 10px 10px;
    background: var(--bg-muted);
    border-top: 1px solid rgba(96, 141, 248, 0.10);
  }
}

.answer-key-badge {
  width: 26px;
  height: 26px;
  border-radius: 4px;
  background: var(--color-primary);
  color: #fff;
  font-size: 13px;
  font-weight: 700;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

[data-theme="dark"] .answer-key-badge {
  color: #0D0D0D;
}

.answer-text-wrap {
  flex: 1;
  min-width: 0;
}

// ── 权重配置行 ───────────────────────────────────────────────
.weights-label {
  font-size: 12px;
  font-weight: 500;
  color: var(--text-2);
  display: block;
  margin-bottom: 8px;
}

.weights-row {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
}

:deep(.weight-item .el-input__inner) {
  text-align: left !important;
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
    font-size: 13px;
    font-weight: 500;
    color: var(--text-2);
    white-space: nowrap;
  }
}

.power-dot {
  width: 6px;
  height: 6px;
  border-radius: 50%;
  flex-shrink: 0;

  &--INSIGHT   { background: var(--power-insight); }
  &--CONSTRUCT { background: var(--power-construct); }
  &--DEDUCE    { background: var(--power-deduce); }
  &--ADAPT     { background: var(--power-adapt); }
  &--MIGRATE   { background: var(--power-migrate); }
}

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

<style>
[data-theme="dark"] .form-section {
  background: #1a1a1a !important;
  border-color: #202020 !important;
}
</style>
