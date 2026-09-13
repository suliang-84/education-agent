<template>
  <div class="page-root">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.push('/questions')">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回
        </el-button>
        <div>
          <h1 class="page-title">录入训练题目</h1>
          <p class="page-subtitle">填写题干后，由大模型自动分析知识点、难度、五力权重等全部字段</p>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <el-button @click="handleSave('draft')" :loading="loading">保存草稿</el-button>
        <button class="btn-pink" type="button" @click="handleSave('analyze')" :disabled="loading">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" style="margin-right:5px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M9.813 15.904L9 18.75l-.813-2.846a4.5 4.5 0 00-3.09-3.09L2.25 12l2.846-.813a4.5 4.5 0 003.09-3.09L9 5.25l.813 2.846a4.5 4.5 0 003.09 3.09L15.75 12l-2.846.813a4.5 4.5 0 00-3.09 3.09z"/>
          </svg>
          保存并立即分析
        </button>
      </div>
    </div>

    <!-- 流程说明横幅 -->
    <div class="flow-banner">
      <div class="flow-step" :class="{ 'flow-step--active': true }">
        <span class="flow-step__num">1</span>
        <span>录入题干</span>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">
        <span class="flow-step__num">2</span>
        <span>大模型分析</span>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">
        <span class="flow-step__num">3</span>
        <span>审核结果</span>
      </div>
      <div class="flow-arrow">→</div>
      <div class="flow-step">
        <span class="flow-step__num">4</span>
        <span>发布上线</span>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="0" v-loading="loading">

      <!-- 题干 -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">题干内容</span>
          <span class="section-hint">仅需填写题干，其余字段由大模型自动生成</span>
        </div>
        <el-form-item prop="stem">
          <el-input
            v-model="form.stem"
            type="textarea"
            :rows="7"
            placeholder="请输入完整的题目题干，包含题目情境、已知条件和设问...

示例：
几个人一起买一件东西。如果每人出400钱，会多出3400钱；如果每人出300钱，会多出100钱。请建立人数与总价之间的方程关系。"
            show-word-limit
            maxlength="1000"
          />
        </el-form-item>
      </div>

      <!-- 配图 -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">配图（可选）</span>
          <span class="section-hint">含图表、几何图形时上传，支持 PNG / JPG，建议宽度 ≥ 600px</span>
        </div>
        <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="1">
          <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--text-3)" stroke-width="1.5">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
        </el-upload>
      </div>

      <!-- 大模型分析说明 -->
      <div class="analysis-preview surface">
        <div class="section-hd">
          <span class="section-title">大模型将自动分析以下内容</span>
        </div>
        <div class="preview-grid">
          <div class="preview-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="preview-item__icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M4.26 10.147a60.436 60.436 0 00-.491 6.347A48.627 48.627 0 0112 20.904a48.627 48.627 0 018.232-4.41 60.46 60.46 0 00-.491-6.347m-15.482 0a50.57 50.57 0 00-2.658-.813A59.905 59.905 0 0112 3.493a59.902 59.902 0 0110.399 5.84c-.896.248-1.783.52-2.658.814m-15.482 0A50.697 50.697 0 0112 13.489a50.702 50.702 0 017.74-3.342M6.75 15a.75.75 0 100-1.5.75.75 0 000 1.5zm0 0v-3.675A55.378 55.378 0 0112 8.443m-7.007 11.55A5.981 5.981 0 006.75 15.75v-1.5"/>
            </svg>
            <div>
              <div class="preview-item__title">五级归属体系</div>
              <div class="preview-item__desc">科目 · 年级 · 学期 · 单元 · 知识点</div>
            </div>
          </div>
          <div class="preview-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="preview-item__icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M3 13.125C3 12.504 3.504 12 4.125 12h2.25c.621 0 1.125.504 1.125 1.125v6.75C7.5 20.496 6.996 21 6.375 21h-2.25A1.125 1.125 0 013 19.875v-6.75z"/>
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 8.625c0-.621.504-1.125 1.125-1.125h2.25c.621 0 1.125.504 1.125 1.125v11.25c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V8.625z"/>
              <path stroke-linecap="round" stroke-linejoin="round" d="M16.5 4.125c0-.621.504-1.125 1.125-1.125h2.25C20.496 3 21 3.504 21 4.125v15.75c0 .621-.504 1.125-1.125 1.125h-2.25a1.125 1.125 0 01-1.125-1.125V4.125z"/>
            </svg>
            <div>
              <div class="preview-item__title">题目类型 + 难度 + 答案</div>
              <div class="preview-item__desc">单选/多选/填空/判断/应用题 · 难度等级 · 结构化答案 · 参考解析</div>
            </div>
          </div>
          <div class="preview-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="preview-item__icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23-.693L5 14.5m14.8.8l1.402 1.402c1.232 1.232.65 3.318-1.067 3.611A48.309 48.309 0 0112 21c-2.773 0-5.491-.235-8.135-.687-1.718-.293-2.3-2.379-1.067-3.61L5 14.5"/>
            </svg>
            <div>
              <div class="preview-item__title">五力权重分析</div>
              <div class="preview-item__desc">各维度权重（合计10分）+ 训练思路</div>
            </div>
          </div>
          <div class="preview-item">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" class="preview-item__icon">
              <path stroke-linecap="round" stroke-linejoin="round" d="M7.5 21L3 16.5m0 0L7.5 12M3 16.5h13.5m0-13.5L21 7.5m0 0L16.5 12M21 7.5H7.5"/>
            </svg>
            <div>
              <div class="preview-item__title">典型错误 + 迁移方向</div>
              <div class="preview-item__desc">学生常见错误 + 可迁移应用场景</div>
            </div>
          </div>
        </div>
        <div class="analysis-tip">
          分析完成后，所有字段均可在「审核结果」页面手动修改，确认无误后再发布。
        </div>
      </div>

    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { questionApi } from '@/api'

const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)

const form = reactive({ stem: '' })

const rules: FormRules = {
  stem: [{ required: true, message: '请输入题干内容', trigger: 'blur' }],
}

async function handleSave(mode: 'draft' | 'analyze') {
  await formRef.value?.validate()
  loading.value = true
  try {
    const created = await questionApi.create({ stem: form.stem })
    if (mode === 'analyze') {
      await questionApi.analyze(created.id)
      ElMessage.success('题干已保存，大模型分析任务已提交，约 10~30 秒完成')
    } else {
      ElMessage.success('草稿已保存')
    }
    router.push('/questions')
  } finally { loading.value = false }
}
</script>

<style lang="scss" scoped>
// ── 流程说明横幅 ─────────────────────────────────────────────
.flow-banner {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 14px 20px;
  background: var(--indigo-light);
  border: 1.5px solid var(--indigo-border);
  border-radius: var(--r-xl);
  flex-wrap: wrap;
}

.flow-step {
  display: flex;
  align-items: center;
  gap: 7px;
  font-size: 13px;
  font-weight: 500;
  color: var(--text-3);

  &--active {
    color: var(--indigo);
    font-weight: 600;

    .flow-step__num {
      background: var(--indigo);
      color: #fff;
    }
  }

  &__num {
    width: 22px;
    height: 22px;
    border-radius: 50%;
    background: var(--bg-muted);
    color: var(--text-3);
    font-size: 12px;
    font-weight: 700;
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
  }
}

.flow-arrow {
  font-size: 14px;
  color: var(--indigo-border);
  font-weight: 600;
}

// ── 表单分区 ─────────────────────────────────────────────────
.form-section {
  padding: 22px 24px;
  margin-bottom: 16px;
}

.section-hint {
  font-size: 12.5px;
  color: var(--text-3);
  font-weight: 400;
}

// ── 大模型分析预览 ───────────────────────────────────────────
.analysis-preview {
  padding: 22px 24px;
  margin-bottom: 16px;
}

.preview-grid {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 14px;
  margin: 16px 0;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.preview-item {
  display: flex;
  align-items: flex-start;
  gap: 10px;
  padding: 12px 14px;
  background: var(--bg-muted);
  border-radius: var(--r-lg);

  &__icon {
    color: var(--indigo);
    flex-shrink: 0;
    margin-top: 2px;
  }

  &__title {
    font-size: 13px;
    font-weight: 600;
    color: var(--text-1);
    margin-bottom: 2px;
  }

  &__desc {
    font-size: 12px;
    color: var(--text-3);
    line-height: 1.5;
  }
}

.analysis-tip {
  font-size: 12.5px;
  color: var(--text-3);
  padding-top: 12px;
  border-top: 1px solid var(--border);
  line-height: 1.5;
}
</style>
