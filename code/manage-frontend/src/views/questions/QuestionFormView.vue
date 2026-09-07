<template>
  <div class="page-root">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.back()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回
        </el-button>
        <div>
          <h1 class="page-title">{{ isEdit ? '编辑题目' : '新增训练题目' }}</h1>
          <p class="page-subtitle">{{ isEdit ? `正在编辑 #${$route.params.id}` : '填写完整信息后提交 AI 标注审核' }}</p>
        </div>
      </div>
      <div style="display:flex;gap:10px">
        <el-button @click="handleSave('draft')" :loading="loading">保存草稿</el-button>
        <button class="btn-pink" type="button" @click="handleSave('submit')" :disabled="loading">
          提交标注审核
        </button>
      </div>
    </div>

    <el-form ref="formRef" :model="form" :rules="rules" label-width="110px" v-loading="loading">

      <!-- 基础信息 -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">基础信息</span>
        </div>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="知识点" prop="knowledge_point">
              <el-input v-model="form.knowledge_point" placeholder="如：二元一次方程组应用题" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="题型" prop="question_type">
              <el-select v-model="form.question_type" style="width:100%">
                <el-option label="应用题" value="应用题" />
                <el-option label="计算题" value="计算题" />
                <el-option label="证明题" value="证明题" />
                <el-option label="分析题" value="分析题" />
                <el-option label="统计题" value="统计题" />
                <el-option label="填空题" value="填空题" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="难度" prop="difficulty">
              <el-select v-model="form.difficulty" style="width:100%">
                <el-option label="基础" value="basic" />
                <el-option label="进阶" value="advanced" />
                <el-option label="挑战" value="challenge" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
      </div>

      <!-- 题目内容 -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">题目内容</span>
        </div>
        <el-form-item label="题干" prop="stem">
          <el-input v-model="form.stem" type="textarea" :rows="5" placeholder="请输入题目题干..." show-word-limit maxlength="1000" />
        </el-form-item>
        <el-form-item label="配图">
          <el-upload action="#" list-type="picture-card" :auto-upload="false" :limit="1">
            <el-icon><Plus /></el-icon>
          </el-upload>
          <div class="form-hint">可选，支持 PNG/JPG，建议宽度 ≥ 600px</div>
        </el-form-item>
        <el-form-item label="参考解析" prop="solution">
          <el-input v-model="form.solution" type="textarea" :rows="5" placeholder="请输入参考解析（RAG 降级时展示）..." show-word-limit maxlength="2000" />
        </el-form-item>
      </div>

      <!-- 五力标注 -->
      <div class="form-section surface">
        <div class="section-hd">
          <span class="section-title">五力标注</span>
          <span class="section-badge">AI 自动生成后可修改</span>
        </div>
        <el-row :gutter="20">
          <el-col :span="8">
            <el-form-item label="主训练力" prop="primary_power">
              <el-select v-model="form.primary_power" style="width:100%">
                <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key">
                  <div style="display:flex;align-items:center;gap:8px">
                    <span class="power-badge" :class="`power-badge--${key}`" style="padding:1px 7px;font-size:11px">{{ label }}</span>
                  </div>
                </el-option>
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="辅助训练力">
              <el-select v-model="form.secondary_power" clearable placeholder="可选" style="width:100%">
                <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key" />
              </el-select>
            </el-form-item>
          </el-col>
        </el-row>
        <div class="row-divider" />
        <el-form-item label="典型错误">
          <el-input v-model="form.typical_error" placeholder="如：把盈余关系写反（400x+3400=y）" />
        </el-form-item>
        <el-form-item label="主力训练点">
          <el-input v-model="form.primary_training_point" placeholder="如：人数×单价与总价之间的关系建立" />
        </el-form-item>
        <el-form-item label="迁移方向">
          <div class="tag-area">
            <span v-for="(tag, i) in form.migration_directions" :key="i" class="migration-tag">
              {{ tag }}
              <button class="tag-close" @click="form.migration_directions.splice(i, 1)">×</button>
            </span>
            <el-input
              v-if="tagInputVisible"
              ref="tagInputRef"
              v-model="tagInput"
              size="small"
              style="width:120px"
              @keyup.enter="addTag"
              @blur="addTag"
            />
            <button v-else class="tag-add-btn" @click="showTagInput">+ 添加方向</button>
          </div>
        </el-form-item>
      </div>

    </el-form>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import type { FormInstance, FormRules } from 'element-plus'
import { ElMessage } from 'element-plus'
import { Plus } from '@element-plus/icons-vue'
import { questionApi } from '@/api'
import { FivePowerLabels } from '@/types'

const route = useRoute()
const router = useRouter()
const formRef = ref<FormInstance>()
const loading = ref(false)
const isEdit = computed(() => !!route.params.id)

const form = reactive({
  knowledge_point: '',
  question_type: '应用题',
  difficulty: 'basic',
  stem: '',
  solution: '',
  primary_power: 'CONSTRUCT',
  secondary_power: '',
  typical_error: '',
  primary_training_point: '',
  migration_directions: [] as string[],
})

const rules: FormRules = {
  knowledge_point: [{ required: true, message: '请输入知识点', trigger: 'blur' }],
  stem: [{ required: true, message: '请输入题干', trigger: 'blur' }],
  solution: [{ required: true, message: '请输入参考解析', trigger: 'blur' }],
  primary_power: [{ required: true, message: '请选择主训练力', trigger: 'change' }],
}

const tagInputVisible = ref(false)
const tagInput = ref('')
const tagInputRef = ref<HTMLInputElement>()

function showTagInput() { tagInputVisible.value = true; nextTick(() => tagInputRef.value?.focus()) }
function addTag() {
  if (tagInput.value.trim()) form.migration_directions.push(tagInput.value.trim())
  tagInputVisible.value = false; tagInput.value = ''
}

async function handleSave(mode: 'draft' | 'submit') {
  await formRef.value?.validate()
  loading.value = true
  try {
    const payload = { ...form, status: 'draft' as const }
    if (isEdit.value) {
      await questionApi.update(Number(route.params.id), payload)
    } else {
      await questionApi.create(payload)
    }
    ElMessage.success(mode === 'draft' ? '草稿已保存' : '提交成功，AI 标注任务已创建')
    router.push('/questions')
  } finally { loading.value = false }
}

onMounted(async () => {
  if (isEdit.value) {
    loading.value = true
    try { const data = await questionApi.getOne(Number(route.params.id)); Object.assign(form, data) }
    finally { loading.value = false }
  }
})
</script>

<style lang="scss" scoped>
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

.form-hint { font-size: 12.5px; color: var(--text-3); margin-top: 6px; }

.tag-area {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 8px;
  min-height: 34px;
}

.migration-tag {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 3px 10px 3px 12px;
  background: var(--purple-dim);
  color: var(--purple);
  border: 1.5px solid var(--purple-border);
  border-radius: var(--r-pill);
  font-size: 13px;
  font-weight: 500;
}

.tag-close {
  background: none;
  border: none;
  color: var(--purple);
  cursor: pointer;
  font-size: 14px;
  line-height: 1;
  padding: 0;
  opacity: 0.7;
  transition: opacity 0.1s;

  &:hover { opacity: 1; }
}

.tag-add-btn {
  background: none;
  border: 1.5px dashed var(--border-hover);
  border-radius: var(--r-pill);
  color: var(--text-3);
  cursor: pointer;
  font-size: 13px;
  padding: 3px 14px;
  transition: all 0.15s;
  font-family: var(--font-sans);

  &:hover {
    border-color: var(--indigo);
    color: var(--indigo);
    background: var(--indigo-light);
  }
}
</style>
