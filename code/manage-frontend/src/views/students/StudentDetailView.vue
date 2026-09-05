<template>
  <div class="page-root" v-loading="loading">
    <div class="page-header">
      <div style="display:flex;align-items:center;gap:12px">
        <el-button size="small" @click="$router.back()">
          <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
            <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
          </svg>
          返回
        </el-button>
        <div>
          <h1 class="page-title">{{ student?.nickname || '学生详情' }}</h1>
          <p class="page-subtitle" v-if="student">
            <span class="id-chip">#{{ student.id }}</span>
            <span style="margin-left:8px">{{ student.grade }} · {{ student.subjects?.join(' / ') }}</span>
          </p>
        </div>
      </div>
    </div>

    <el-row :gutter="16" v-if="student">
      <!-- 左列 -->
      <el-col :span="16">

        <!-- 基本信息 -->
        <div class="surface info-block">
          <div class="section-hd"><span class="section-title">基本信息</span></div>
          <el-descriptions :column="3" border>
            <el-descriptions-item label="昵称">
              <span style="font-weight:600;color:var(--text-1)">{{ student.nickname }}</span>
            </el-descriptions-item>
            <el-descriptions-item label="年级">{{ student.grade }}</el-descriptions-item>
            <el-descriptions-item label="科目">{{ student.subjects?.join(' / ') }}</el-descriptions-item>
            <el-descriptions-item label="手机号"><span class="mono">{{ student.phone_masked }}</span></el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ formatDate(student.created_at) }}</el-descriptions-item>
            <el-descriptions-item label="最后登录">{{ formatDate(student.last_login_at) }}</el-descriptions-item>
          </el-descriptions>
        </div>

        <!-- 五力画像 -->
        <div class="surface radar-block">
          <div class="section-hd">
            <span class="section-title">五力画像</span>
            <span style="font-size:12.5px;color:var(--text-3)">更新于 {{ formatDate(student.profile_updated_at) }}</span>
          </div>
          <el-row :gutter="24" v-if="student.five_power_scores" align="middle">
            <el-col :span="12">
              <div ref="radarRef" class="radar-chart" />
            </el-col>
            <el-col :span="12">
              <div class="power-score-list">
                <div v-for="(label, key) in FivePowerLabels" :key="key" class="ps-row">
                  <span class="ps-label" :style="{ color: POWER_COLORS[key] }">{{ label }}</span>
                  <div class="ps-track">
                    <div class="ps-fill" :style="{ width: student.five_power_scores[key as keyof typeof student.five_power_scores] + '%', background: POWER_COLORS[key] }" />
                  </div>
                  <span class="ps-val num" :style="{ color: POWER_COLORS[key] }">
                    {{ student.five_power_scores[key as keyof typeof student.five_power_scores] }}
                  </span>
                </div>
              </div>
            </el-col>
          </el-row>
          <div class="empty-state" v-else style="padding:32px 0">
            <span style="font-size:32px">📊</span>
            <span>该学生尚未完成五力测试</span>
          </div>
          <div v-if="student.ai_analysis" class="ai-analysis-box">
            <div class="row-divider" />
            <div class="ai-label">AI 分析</div>
            <p class="ai-text">{{ student.ai_analysis }}</p>
          </div>
        </div>

        <!-- 训练统计 -->
        <div class="surface stats-block">
          <div class="section-hd"><span class="section-title">训练统计</span></div>
          <div class="train-stats">
            <div class="train-stat-item">
              <div class="train-stat-num num">{{ student.training_count }}</div>
              <div class="train-stat-lbl">累计训练次数</div>
            </div>
            <div class="train-divider" />
            <div class="train-stat-item">
              <div class="train-stat-num num">{{ student.total_answers }}</div>
              <div class="train-stat-lbl">累计答题数</div>
            </div>
            <div class="train-divider" />
            <div class="train-stat-item">
              <div class="train-stat-num num" :class="accuracyColorClass">
                {{ ((student.accuracy_rate ?? 0) * 100).toFixed(0) }}%
              </div>
              <div class="train-stat-lbl">平均正确率</div>
            </div>
          </div>
        </div>
      </el-col>

      <!-- 右列 -->
      <el-col :span="8">
        <div class="surface parent-block">
          <div class="section-hd">
            <span class="section-title">已绑定家长</span>
            <button class="text-btn" @click="showBindDialog = true">+ 手动绑定</button>
          </div>
          <div class="parent-list" v-if="student.parents?.length">
            <div v-for="parent in student.parents" :key="parent.id" class="parent-item">
              <div class="parent-avatar">{{ parent.nickname[0] }}</div>
              <div class="parent-info">
                <div class="parent-name">{{ parent.nickname }}</div>
                <div class="parent-meta">
                  <span class="bind-tag">{{ parent.bind_method }}</span>
                  <span style="font-size:12px;color:var(--text-3)">{{ formatDate(parent.bound_at, 'YYYY-MM-DD') }}</span>
                </div>
              </div>
            </div>
          </div>
          <div class="empty-state" v-else style="padding:32px 16px">
            <span style="font-size:28px">👨‍👩‍👧</span>
            <span>暂无绑定家长</span>
          </div>
          <div class="parent-tip" v-if="student.parents?.length">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="flex-shrink:0;color:var(--text-3)">
              <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
            </svg>
            每名学生最多绑定 2 位家长
          </div>
        </div>
      </el-col>
    </el-row>

    <!-- Bind dialog -->
    <el-dialog v-model="showBindDialog" title="手动绑定家长" width="400px">
      <el-form :model="bindForm" label-width="80px" style="margin-top:4px">
        <el-form-item label="家长手机">
          <el-input v-model="bindForm.parent_phone" placeholder="请输入家长手机号" />
        </el-form-item>
      </el-form>
      <div class="bind-hint">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" style="flex-shrink:0;color:var(--indigo)">
          <path stroke-linecap="round" stroke-linejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z"/>
        </svg>
        管理员代操作，将记录为 <code class="mono" style="color:var(--indigo)">bind_method=ADMIN</code>
      </div>
      <template #footer>
        <el-button @click="showBindDialog = false">取消</el-button>
        <el-button type="primary" @click="handleBind">确认绑定</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted, nextTick } from 'vue'
import { useRoute } from 'vue-router'
import { ElMessage } from 'element-plus'
import * as echarts from 'echarts'
import { studentApi } from '@/api'
import type { StudentDetail } from '@/types'
import { FivePowerLabels } from '@/types'
import { formatDate } from '@/utils/format'

const POWER_COLORS: Record<string, string> = {
  INSIGHT: '#0D9488', CONSTRUCT: '#E11D48',
  DEDUCE: '#4F46E5', ADAPT: '#D97706', MIGRATE: '#7C3AED',
}

const route = useRoute()
const loading = ref(false)
const student = ref<StudentDetail>()
const radarRef = ref<HTMLElement>()
const showBindDialog = ref(false)
const bindForm = reactive({ parent_phone: '' })

const accuracyColorClass = computed(() => {
  const r = (student.value?.accuracy_rate ?? 0) * 100
  return r >= 70 ? 'accuracy--good' : r < 50 ? 'accuracy--poor' : ''
})

function renderRadar() {
  if (!radarRef.value || !student.value?.five_power_scores) return
  const chart = echarts.init(radarRef.value)
  const scores = student.value.five_power_scores
  chart.setOption({
    backgroundColor: 'transparent',
    radar: {
      indicator: Object.entries(FivePowerLabels).map(([key, label]) => ({ name: label, max: 100 })),
      radius: 95,
      axisName: { color: '#64748B', fontSize: 12, fontFamily: 'Inter, system-ui' },
      splitLine: { lineStyle: { color: 'rgba(79,70,229,0.10)' } },
      splitArea: { areaStyle: { color: ['rgba(79,70,229,0.03)', 'rgba(79,70,229,0.01)'] } },
      axisLine: { lineStyle: { color: 'rgba(79,70,229,0.12)' } },
    },
    series: [{
      type: 'radar',
      data: [{
        value: Object.keys(FivePowerLabels).map(k => scores[k as keyof typeof scores] ?? 0),
        name: student.value?.nickname,
        lineStyle: { color: '#4F46E5', width: 2 },
        areaStyle: { color: 'rgba(79,70,229,0.12)' },
        itemStyle: { color: '#4F46E5' },
        symbolSize: 5,
      }],
    }],
  })
}

async function handleBind() {
  if (!student.value) return
  await studentApi.bindParent(student.value.id, bindForm)
  ElMessage.success('绑定成功')
  showBindDialog.value = false
}

onMounted(async () => {
  loading.value = true
  try {
    student.value = await studentApi.getOne(Number(route.params.id))
    await nextTick()
    renderRadar()
  } finally { loading.value = false }
})
</script>

<style scoped>
.info-block, .radar-block, .stats-block { padding: 22px 24px; margin-bottom: 16px; }
.parent-block { padding: 22px 24px; }

.radar-chart { height: 280px; }

.power-score-list { display: flex; flex-direction: column; gap: 14px; }
.ps-row { display: flex; align-items: center; gap: 10px; }
.ps-label { font-size: 13px; font-weight: 600; min-width: 48px; flex-shrink: 0; }
.ps-track { flex: 1; height: 6px; background: var(--bg-muted); border-radius: 3px; overflow: hidden; }
.ps-fill { height: 100%; border-radius: 3px; transition: width 0.8s cubic-bezier(0.16,1,0.3,1); }
.ps-val { font-size: 13px; font-weight: 700; min-width: 28px; text-align: right; }

.ai-analysis-box { margin-top: 4px; }
.ai-label { font-size: 13px; font-weight: 600; color: var(--text-2); margin-bottom: 8px; }
.ai-text {
  font-size: 13.5px; color: var(--text-2); line-height: 1.7;
  background: var(--indigo-light);
  border-radius: var(--r-lg);
  padding: 14px 16px;
}

.train-stats { display: flex; align-items: center; }
.train-stat-item { flex: 1; text-align: center; padding: 12px 0; }
.train-divider { width: 1px; height: 56px; background: var(--border); }
.train-stat-num { font-size: 34px; font-weight: 700; color: var(--indigo); line-height: 1; letter-spacing: -0.04em; }
.train-stat-num.accuracy--good { color: var(--green); }
.train-stat-num.accuracy--poor { color: var(--red); }
.train-stat-lbl { font-size: 12px; color: var(--text-3); margin-top: 6px; }

.parent-list { display: flex; flex-direction: column; gap: 12px; margin-bottom: 12px; }
.parent-item { display: flex; align-items: center; gap: 12px; padding: 12px 14px; background: var(--bg-muted); border-radius: var(--r-lg); }
.parent-avatar {
  width: 36px; height: 36px; border-radius: 10px;
  background: var(--indigo);
  color: #fff;
  font-size: 15px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  flex-shrink: 0;
}
.parent-info { flex: 1; }
.parent-name { font-size: 13.5px; font-weight: 600; color: var(--text-1); }
.parent-meta { display: flex; align-items: center; gap: 8px; margin-top: 3px; }
.bind-tag {
  font-size: 11px; font-weight: 600;
  padding: 2px 7px;
  border-radius: var(--r-pill);
  background: var(--indigo-light);
  color: var(--indigo);
  border: 1px solid var(--indigo-border);
}
.parent-tip {
  display: flex; align-items: center; gap: 6px;
  font-size: 12.5px; color: var(--text-3);
  margin-top: 14px;
}
.text-btn {
  background: none; border: none; color: var(--indigo);
  font-size: 13px; font-weight: 500; cursor: pointer; font-family: var(--font-sans);
  padding: 4px 10px; border-radius: var(--r-md);
  transition: background 0.12s;
}
.text-btn:hover { background: var(--indigo-light); }
.bind-hint {
  display: flex; align-items: center; gap: 8px;
  font-size: 13px; color: var(--text-2);
  background: var(--indigo-light);
  border-radius: var(--r-lg);
  padding: 10px 14px;
  margin-top: 12px;
}
</style>
