<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElMessage } from 'element-plus'
import { cognitiveApi } from '../../api'
import type { CognitiveQuestion } from '../../types'

const loading = ref(false)
const questions = ref<CognitiveQuestion[]>([])
const editDialog = ref(false)
const editRow = ref<CognitiveQuestion | null>(null)
const editForm = reactive<any>({})
import { reactive } from 'vue'

const powerLabelMap: Record<string, string> = {
  INSIGHT: '洞察力', STRUCTURE: '建构力', INFERENCE: '推演力',
  ADAPTATION: '调适力', TRANSFER: '迁移力',
}

async function load() {
  loading.value = true
  try {
    const res = await cognitiveApi.getList()
    questions.value = res.data?.list || []
  } finally { loading.value = false }
}

function openEdit(row: CognitiveQuestion) {
  editRow.value = { ...row }
  Object.assign(editForm, {
    id: row.id,
    option_scores: row.option_scores ? JSON.stringify(row.option_scores, null, 2) : '',
    option_force_weights: row.option_force_weights ? JSON.stringify(row.option_force_weights, null, 2) : '',
    reference_time_sec: row.reference_time_sec,
  })
  editDialog.value = true
}

async function handleSave() {
  try {
    await cognitiveApi.update(editForm.id, {
      option_scores: editRow.value?.question_type === 'STANDARD' ? JSON.parse(editForm.option_scores) : undefined,
      option_force_weights: editRow.value?.question_type === 'OPEN' ? JSON.parse(editForm.option_force_weights) : undefined,
      reference_time_sec: editForm.reference_time_sec,
    })
    ElMessage.success('保存成功')
    editDialog.value = false
    load()
  } catch (e) { ElMessage.error('JSON格式有误，请检查') }
}

onMounted(load)
</script>

<template>
  <div>
    <div class="page-header">
      <h2>五力测试题维护</h2>
      <el-tag type="warning">⚠️ 修改将影响所有新测试的评分，请谨慎操作</el-tag>
    </div>

    <div class="card" style="padding:0">
      <el-table :data="questions" v-loading="loading" stripe>
        <el-table-column prop="question_no" label="题号" width="60" align="center" />
        <el-table-column prop="display_order" label="展示顺序" width="80" align="center" />
        <el-table-column label="类型" width="90">
          <template #default="{ row }">
            <el-tag :type="row.question_type === 'STANDARD' ? 'primary' : 'success'" size="small">
              {{ row.question_type === 'STANDARD' ? '标准答案' : '开放题' }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="目标维度" width="90">
          <template #default="{ row }">
            <span class="power-tag" :class="row.target_power">{{ powerLabelMap[row.target_power] }}</span>
          </template>
        </el-table-column>
        <el-table-column label="题干摘要" min-width="300">
          <template #default="{ row }">
            <span style="font-size:13px">{{ row.stem.slice(0, 80) }}...</span>
          </template>
        </el-table-column>
        <el-table-column label="参考时间" width="90" align="center">
          <template #default="{ row }">{{ row.reference_time_sec }}秒</template>
        </el-table-column>
        <el-table-column label="操作" width="80" fixed="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <!-- 编辑对话框 -->
    <el-dialog v-model="editDialog" :title="`编辑第${editRow?.question_no}题（${editRow?.question_type}）`" width="600px">
      <el-form label-position="top">
        <el-form-item v-if="editRow?.question_type === 'STANDARD'" label="各选项得分（JSON格式）">
          <el-input v-model="editForm.option_scores" type="textarea" :rows="5"
            placeholder='{"A":1,"B":10,"C":4,"D":1}' style="font-family:monospace" />
          <div style="color:#6B7280;font-size:12px;margin-top:4px">最高分选项代表"正确"答案</div>
        </el-form-item>
        <el-form-item v-if="editRow?.question_type === 'OPEN'" label="各选项五力权重（JSON格式）">
          <el-input v-model="editForm.option_force_weights" type="textarea" :rows="8"
            style="font-family:monospace;font-size:12px" />
        </el-form-item>
        <el-form-item label="参考作答时间（秒）">
          <el-input-number v-model="editForm.reference_time_sec" :min="30" :max="300" :step="15" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="editDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSave">保存</el-button>
      </template>
    </el-dialog>
  </div>
</template>
