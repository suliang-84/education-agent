<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { trainingConfigApi } from '../../api'
import type { TrainingConfigVersion } from '../../types'

const loading = ref(false)
const active = ref<TrainingConfigVersion | null>(null)
const history = ref<TrainingConfigVersion[]>([])
const createDialog = ref(false)

const newConfig = reactive({
  training_total_questions: 5,
  weak_boost_level1: 0.40,
  weak_boost_level2: 0.20,
  weak_power_threshold: 65,
  basic_ratio: 50,
  advanced_ratio: 35,
  challenge_ratio: 15,
  dedup_window_size: 30,
  rag_trigger_mode: 'all',
  rag_topk_questions: 3,
  rag_topk_strategies: 2,
  rag_similarity_threshold: 0.75,
  rag_timeout_seconds: 8,
  profile_decay_coefficient: 0.30,
  description: '',
})

async function load() {
  loading.value = true
  try {
    const [activeRes, histRes] = await Promise.all([
      trainingConfigApi.getActive(),
      trainingConfigApi.getHistory(),
    ])
    active.value = activeRes.data
    history.value = histRes.data?.list || []
  } finally { loading.value = false }
}

async function handleCreate() {
  if (newConfig.basic_ratio + newConfig.advanced_ratio + newConfig.challenge_ratio !== 100) {
    ElMessage.error('难度比例之和必须等于100%')
    return
  }
  try {
    const { description, basic_ratio, advanced_ratio, challenge_ratio, ...rest } = newConfig
    await trainingConfigApi.create({
      config: { ...rest, difficulty_ratio: { basic: basic_ratio, advanced: advanced_ratio, challenge: challenge_ratio } } as Record<string, unknown>,
      description,
    })
    ElMessage.success('新配置版本已创建并生效')
    createDialog.value = false
    load()
  } catch {}
}

const ragModeOptions = [
  { label: '所有题目（答对/错均生成）', value: 'all' },
  { label: '仅答错触发', value: 'wrong_only' },
  { label: '禁用', value: 'disabled' },
]

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>训练配置管理</h2>
      <el-button type="primary" @click="createDialog = true">+ 创建新版本</el-button>
    </div>

    <!-- 当前生效版本 -->
    <div class="card" v-loading="loading">
      <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:16px">
        <h3 style="font-size:15px;margin:0">当前生效版本：{{ active?.version_number }}</h3>
        <el-tag type="success">生效中</el-tag>
      </div>

      <el-descriptions :column="3" border v-if="active">
        <el-descriptions-item label="每次训练题数">{{ active.config.training_total_questions }} 题</el-descriptions-item>
        <el-descriptions-item label="弱力判定阈值">{{ active.config.weak_power_threshold }} 分</el-descriptions-item>
        <el-descriptions-item label="去重窗口">{{ active.config.dedup_window_size }} 题</el-descriptions-item>
        <el-descriptions-item label="严重弱力加权">+{{ (active.config.weak_boost_level1 * 100).toFixed(0) }}%</el-descriptions-item>
        <el-descriptions-item label="一般弱力加权">+{{ (active.config.weak_boost_level2 * 100).toFixed(0) }}%</el-descriptions-item>
        <el-descriptions-item label="画像衰减系数">{{ active.config.profile_decay_coefficient }}</el-descriptions-item>
        <el-descriptions-item label="难度比例">
          基础 {{ active.config.difficulty_ratio?.basic }}% / 进阶 {{ active.config.difficulty_ratio?.advanced }}% / 挑战 {{ active.config.difficulty_ratio?.challenge }}%
        </el-descriptions-item>
        <el-descriptions-item label="RAG触发">{{ active.config.rag_trigger_mode }}</el-descriptions-item>
        <el-descriptions-item label="RAG超时">{{ active.config.rag_timeout_seconds }} 秒</el-descriptions-item>
        <el-descriptions-item label="创建时间">{{ active.created_at?.slice(0,10) }}</el-descriptions-item>
      </el-descriptions>
    </div>

    <!-- 历史版本 -->
    <div class="card" style="padding:0">
      <div style="padding:16px 20px;border-bottom:1px solid #F3F4F6"><h3 style="font-size:15px;margin:0">历史版本记录</h3></div>
      <el-table :data="history" stripe>
        <el-table-column prop="version_number" label="版本号" width="90" />
        <el-table-column label="题数" width="70" align="center">
          <template #default="{row}">{{ row.config.training_total_questions }}</template>
        </el-table-column>
        <el-table-column label="RAG超时" width="90" align="center">
          <template #default="{row}">{{ row.config.rag_timeout_seconds }}s</template>
        </el-table-column>
        <el-table-column prop="description" label="描述" />
        <el-table-column prop="created_at" label="创建时间" width="120">
          <template #default="{row}">{{ row.created_at?.slice(0,10) }}</template>
        </el-table-column>
        <el-table-column label="状态" width="90">
          <template #default="{row}">
            <el-tag :type="row.is_active ? 'success' : 'info'" size="small">{{ row.is_active ? '生效中' : '历史' }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 创建新版本对话框 -->
    <el-dialog v-model="createDialog" title="创建新训练配置版本" width="680px">
      <el-form :model="newConfig" label-position="top">
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="每次训练题数">
              <el-input-number v-model="newConfig.training_total_questions" :min="3" :max="20" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="弱力判定阈值（分）">
              <el-input-number v-model="newConfig.weak_power_threshold" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="严重弱力加权（<50分）">
              <el-input-number v-model="newConfig.weak_boost_level1" :min="0" :max="0.6" :step="0.05" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="一般弱力加权（50~65分）">
              <el-input-number v-model="newConfig.weak_boost_level2" :min="0" :max="0.4" :step="0.05" :precision="2" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="基础占比 (%)">
              <el-input-number v-model="newConfig.basic_ratio" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="进阶占比 (%)">
              <el-input-number v-model="newConfig.advanced_ratio" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="8">
            <el-form-item label="挑战占比 (%)">
              <el-input-number v-model="newConfig.challenge_ratio" :min="0" :max="100" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="RAG触发模式">
              <el-select v-model="newConfig.rag_trigger_mode" style="width:100%">
                <el-option v-for="o in ragModeOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="RAG超时（秒）">
              <el-input-number v-model="newConfig.rag_timeout_seconds" :min="3" :max="30" style="width:100%" />
            </el-form-item>
          </el-col>
          <el-col :span="24">
            <el-form-item label="变更说明">
              <el-input v-model="newConfig.description" placeholder="描述本次配置变更内容..." />
            </el-form-item>
          </el-col>
        </el-row>
        <el-alert v-if="newConfig.basic_ratio + newConfig.advanced_ratio + newConfig.challenge_ratio !== 100"
          type="error" :closable="false" title="难度占比之和必须等于100%" style="margin-top:8px" />
      </el-form>
      <template #footer>
        <el-button @click="createDialog = false">取消</el-button>
        <el-button type="primary" @click="handleCreate">创建并生效</el-button>
      </template>
    </el-dialog>
  </div>
</template>
