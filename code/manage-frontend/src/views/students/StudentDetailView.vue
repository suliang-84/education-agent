<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { studentApi } from '../../api'
import type { StudentDetail } from '../../types'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const student = ref<StudentDetail | null>(null)
const bindDialog = ref(false)
const parentId = ref('')

const levelColor = (s: number) => s < 50 ? '#EF4444' : s < 65 ? '#F59E0B' : s < 80 ? '#22C55E' : '#059669'
const levelLabel = (s: number) => s < 50 ? '重点强化' : s < 65 ? '次重点' : s < 80 ? '良好' : '优势'

async function load() {
  loading.value = true
  try {
    const res = await studentApi.detail(Number(route.params.id))
    student.value = res.data
  } finally { loading.value = false }
}

async function handleBind() {
  if (!parentId.value) return
  await studentApi.bindParent(Number(route.params.id), Number(parentId.value))
  bindDialog.value = false
  load()
}

const forces = ['insight', 'structure', 'inference', 'adaptation', 'transfer'] as const
const forceNames = { insight:'洞察力', structure:'建构力', inference:'推演力', adaptation:'调适力', transfer:'迁移力' }

onMounted(load)
</script>

<template>
  <div v-loading="loading">
    <div class="page-header">
      <h2>学生详情</h2>
      <el-button @click="router.back()">返回列表</el-button>
    </div>

    <el-row :gutter="16" v-if="student">
      <!-- 基本信息 -->
      <el-col :span="8">
        <div class="card">
          <div style="text-align:center;margin-bottom:16px">
            <el-avatar :size="64" style="background:#2563EB;font-size:24px;margin-bottom:8px">{{ student.nickname?.slice(0,1) }}</el-avatar>
            <div style="font-size:18px;font-weight:600;color:#111827">{{ student.nickname }}</div>
            <div style="color:#6B7280;font-size:13px;margin-top:4px">
              {{ ({ G7:'初一',G8:'初二',G9:'初三',G10:'高一',G11:'高二',G12:'高三' } as Record<string,string>)[student.grade] || student.grade }}
              <el-tag v-if="student.is_minor" type="warning" size="small" style="margin-left:4px">未成年</el-tag>
            </div>
          </div>
          <el-descriptions :column="1" border size="small">
            <el-descriptions-item label="学生ID">{{ student.student_id }}</el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ student.created_at?.slice(0,10) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 绑定家长 -->
        <div class="card">
          <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:12px">
            <h3 style="font-size:14px;margin:0">已绑定家长</h3>
            <el-button size="small" @click="bindDialog=true">手动绑定</el-button>
          </div>
          <div v-if="student.bound_parents?.length">
            <div v-for="p in student.bound_parents" :key="p.parent_id"
              style="padding:8px 0;border-bottom:1px solid #F3F4F6;display:flex;justify-content:space-between;align-items:center">
              <div>
                <div style="font-size:14px;color:#111827">{{ p.nickname }}</div>
                <div style="font-size:12px;color:#9CA3AF">{{ p.bind_date?.slice(0,10) }} 绑定</div>
              </div>
              <el-tag size="small" type="success">已绑定</el-tag>
            </div>
          </div>
          <div v-else style="color:#9CA3AF;font-size:13px;text-align:center;padding:16px">暂无绑定家长</div>
        </div>
      </el-col>

      <!-- 五力画像 -->
      <el-col :span="16">
        <div class="card" v-if="student.five_power_profile">
          <h3 style="font-size:15px;margin-bottom:16px">五力画像（{{ student.five_power_profile.test_date?.slice(0,10) }}）</h3>
          <el-row :gutter="12">
            <el-col :span="12" v-for="f in forces" :key="f">
              <div style="padding:12px;border-radius:8px;margin-bottom:8px"
                :style="{ background: levelColor(student.five_power_profile.forces?.[f]?.final || 0) + '15',
                           borderLeft: `4px solid ${levelColor(student.five_power_profile.forces?.[f]?.final || 0)}` }">
                <div style="display:flex;justify-content:space-between;align-items:center">
                  <span style="font-size:14px;font-weight:500">{{ forceNames[f] }}</span>
                  <span style="font-size:18px;font-weight:700" :style="{color: levelColor(student.five_power_profile.forces?.[f]?.final || 0)}">
                    {{ student.five_power_profile.forces?.[f]?.final ?? '—' }}
                  </span>
                </div>
                <div style="margin-top:6px">
                  <el-progress :percentage="student.five_power_profile.forces?.[f]?.final || 0"
                    :color="levelColor(student.five_power_profile.forces?.[f]?.final || 0)"
                    :stroke-width="6" :show-text="false" />
                </div>
                <div style="font-size:11px;color:#6B7280;margin-top:4px">{{ levelLabel(student.five_power_profile.forces?.[f]?.final || 0) }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
        <div class="card" v-else>
          <div style="text-align:center;color:#9CA3AF;padding:32px">该学生尚未完成五力测试</div>
        </div>

        <!-- 训练统计 -->
        <div class="card" v-if="student.training_stats">
          <h3 style="font-size:15px;margin-bottom:16px">训练统计</h3>
          <el-row :gutter="16">
            <el-col :span="6" v-for="(v, k) in {累计训练: student.training_stats.total_sessions, 累计答题: student.training_stats.total_questions, 平均正确率: (student.training_stats.avg_accuracy * 100).toFixed(0) + '%', 最近训练: student.training_stats.last_trained_at?.slice(0,10)}" :key="k">
              <div style="text-align:center;padding:12px;background:#F9FAFB;border-radius:8px">
                <div style="font-size:20px;font-weight:700;color:#111827">{{ v }}</div>
                <div style="font-size:12px;color:#6B7280;margin-top:4px">{{ k }}</div>
              </div>
            </el-col>
          </el-row>
        </div>
      </el-col>
    </el-row>

    <el-dialog v-model="bindDialog" title="手动绑定家长" width="400px">
      <el-form>
        <el-form-item label="家长ID">
          <el-input v-model="parentId" placeholder="输入家长账号ID..." />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="bindDialog=false">取消</el-button>
        <el-button type="primary" @click="handleBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>
