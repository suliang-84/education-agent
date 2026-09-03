<script setup lang="ts">
import { ref, reactive } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import { questionApi } from '../../api'

const router = useRouter()
const route = useRoute()
const isEdit = computed(() => !!route.params.id)
const submitLoading = ref(false)

import { computed } from 'vue'

const form = reactive({
  knowledge_point_id: 1001,
  stem: '',
  solution: '',
  question_type: 'app',
  difficulty: 'basic',
  primary_power: 'STRUCTURE',
  secondary_power: '',
  common_error: '',
  insight_point: '',
  construct_point: '',
  inference_point: '',
  adapt_point: '',
  transfer_direction: [] as string[],
  image_url: '',
})

const transferInput = ref('')

const powerOptions = [
  { label: '洞察力', value: 'INSIGHT' },
  { label: '建构力', value: 'STRUCTURE' },
  { label: '推演力', value: 'INFERENCE' },
  { label: '调适力', value: 'ADAPTATION' },
  { label: '迁移力', value: 'TRANSFER' },
]

function addTransfer() {
  if (transferInput.value.trim()) {
    form.transfer_direction.push(transferInput.value.trim())
    transferInput.value = ''
  }
}
function removeTransfer(i: number) { form.transfer_direction.splice(i, 1) }

async function handleSubmit(status: string) {
  if (!form.stem.trim()) { ElMessage.warning('请填写题干'); return }
  if (!form.solution.trim()) { ElMessage.warning('请填写参考解析'); return }
  submitLoading.value = true
  try {
    await questionApi.create({ ...form })
    ElMessage.success(status === 'published' ? '发布成功' : '保存草稿成功')
    router.push('/questions')
  } finally { submitLoading.value = false }
}
</script>

<template>
  <div>
    <div class="page-header">
      <h2>{{ isEdit ? '编辑题目' : '新增题目' }}</h2>
      <el-button @click="router.back()">返回</el-button>
    </div>

    <el-row :gutter="16">
      <!-- 左侧主信息 -->
      <el-col :span="15">
        <div class="card">
          <h3 style="font-size:15px;margin-bottom:16px;color:#374151">基础信息</h3>
          <el-form label-position="top">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="题型 *">
                  <el-select v-model="form.question_type" style="width:100%">
                    <el-option label="应用题" value="app" />
                    <el-option label="计算题" value="calc" />
                    <el-option label="证明题" value="proof" />
                    <el-option label="判断题" value="judge" />
                  </el-select>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="难度 *">
                  <el-select v-model="form.difficulty" style="width:100%">
                    <el-option label="基础" value="basic" />
                    <el-option label="进阶" value="advanced" />
                    <el-option label="挑战" value="challenge" />
                  </el-select>
                </el-form-item>
              </el-col>
            </el-row>

            <el-form-item label="题干 *">
              <el-input v-model="form.stem" type="textarea" :rows="5"
                placeholder="输入题目内容，支持数学表达式..." />
            </el-form-item>

            <el-form-item label="参考解析 *">
              <el-input v-model="form.solution" type="textarea" :rows="5"
                placeholder="输入参考解析，用于RAG降级时展示..." />
            </el-form-item>

            <el-form-item label="题目配图">
              <el-upload action="#" :auto-upload="false" accept="image/*" :limit="1">
                <el-button>点击上传图片</el-button>
                <template #tip>
                  <div style="color:#9CA3AF;font-size:12px">支持 JPG/PNG，大小不超过 2MB</div>
                </template>
              </el-upload>
            </el-form-item>
          </el-form>
        </div>
      </el-col>

      <!-- 右侧标注信息 -->
      <el-col :span="9">
        <div class="card">
          <h3 style="font-size:15px;margin-bottom:16px;color:#374151">五力标注</h3>
          <el-form label-position="top">
            <el-form-item label="主训练力 *">
              <el-select v-model="form.primary_power" style="width:100%">
                <el-option v-for="o in powerOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="辅助训练力">
              <el-select v-model="form.secondary_power" clearable style="width:100%">
                <el-option v-for="o in powerOptions" :key="o.value" :label="o.label" :value="o.value" />
              </el-select>
            </el-form-item>
            <el-form-item label="典型错误">
              <el-input v-model="form.common_error" type="textarea" :rows="2" placeholder="描述学生常见错误..." />
            </el-form-item>
            <el-form-item label="洞察力训练点">
              <el-input v-model="form.insight_point" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="建构力训练点">
              <el-input v-model="form.construct_point" type="textarea" :rows="2" />
            </el-form-item>
            <el-form-item label="迁移方向">
              <div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:8px">
                <el-tag v-for="(t, i) in form.transfer_direction" :key="i" closable @close="removeTransfer(i)">
                  {{ t }}
                </el-tag>
              </div>
              <div style="display:flex;gap:8px">
                <el-input v-model="transferInput" placeholder="添加迁移方向..." size="small" @keyup.enter="addTransfer" />
                <el-button size="small" @click="addTransfer">添加</el-button>
              </div>
            </el-form-item>
          </el-form>
        </div>

        <div style="display:flex;gap:8px;justify-content:flex-end">
          <el-button @click="handleSubmit('draft')" :loading="submitLoading">保存草稿</el-button>
          <el-button type="primary" @click="handleSubmit('published')" :loading="submitLoading">保存并发布</el-button>
        </div>
      </el-col>
    </el-row>
  </div>
</template>
