<template>
  <div class="page-root">
    <div class="page-header">
      <div>
        <h1 class="page-title">题库管理</h1>
        <p class="page-subtitle">管理所有训练题目，支持批量导入和 AI 自动标注</p>
      </div>
      <div style="display:flex;gap:10px">
        <el-button @click="showImport = true">批量导入</el-button>
        <button class="btn-pink" @click="$router.push('/questions/create')">
          <svg width="15" height="15" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M12 4.5v15m7.5-7.5h-15"/>
          </svg>
          新增题目
        </button>
      </div>
    </div>

    <!-- Filter bar -->
    <div class="filter-bar">
      <el-input v-model="filters.keyword" placeholder="搜索题干..." clearable style="width:180px" @keyup.enter="handleSearch">
        <template #prefix>
          <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <path stroke-linecap="round" stroke-linejoin="round" d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z"/>
          </svg>
        </template>
      </el-input>
      <el-input v-model="filters.knowledge_point" placeholder="知识点" clearable style="width:140px" />
      <el-select v-model="filters.primary_power" placeholder="五力维度" clearable style="width:120px">
        <el-option v-for="(label, key) in FivePowerLabels" :key="key" :label="label" :value="key" />
      </el-select>
      <el-select v-model="filters.difficulty" placeholder="难度" clearable style="width:100px">
        <el-option v-for="(label, key) in DifficultyLabels" :key="key" :label="label" :value="key" />
      </el-select>
      <el-select v-model="filters.status" placeholder="状态" clearable style="width:100px">
        <el-option v-for="(label, key) in QuestionStatusLabels" :key="key" :label="label" :value="key" />
      </el-select>
      <el-select v-model="filters.annotation_status" placeholder="标注状态" clearable style="width:120px">
        <el-option v-for="(label, key) in AnnotationStatusLabels" :key="key" :label="label" :value="key" />
      </el-select>
      <div style="margin-left:auto;display:flex;gap:8px">
        <el-button type="primary" @click="handleSearch">查询</el-button>
        <el-button @click="resetFilters">重置</el-button>
      </div>
    </div>

    <!-- Table -->
    <div class="surface" style="overflow:hidden">
      <el-table :data="questions" v-loading="loading" style="width:100%">
        <el-table-column label="ID" width="90">
          <template #default="{ row }">
            <span class="id-chip">#{{ row.id }}</span>
          </template>
        </el-table-column>

        <el-table-column label="题干" min-width="300">
          <template #default="{ row }">
            <div class="stem-cell">
              <div class="stem-text">{{ row.stem.substring(0, 68) }}{{ row.stem.length > 68 ? '…' : '' }}</div>
              <div class="stem-meta">
                <span class="conf-badge" :class="getAnnotationBadge(row.annotation_status)">
                  {{ AnnotationStatusLabels[row.annotation_status as keyof typeof AnnotationStatusLabels] }}
                </span>
                <span v-if="row.annotation_confidence" class="meta-num num">
                  {{ (row.annotation_confidence * 100).toFixed(0) }}%
                </span>
                <span class="embed-badge" :class="embedClass(row.embedding_status)">
                  {{ embedLabel(row.embedding_status) }}
                </span>
              </div>
            </div>
          </template>
        </el-table-column>

        <el-table-column label="五力" width="100">
          <template #default="{ row }">
            <span class="power-badge" :class="`power-badge--${row.primary_power}`">
              {{ FivePowerLabels[row.primary_power as keyof typeof FivePowerLabels] }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="难度" width="80">
          <template #default="{ row }">
            <span class="diff-badge" :class="`diff--${row.difficulty}`">
              {{ DifficultyLabels[row.difficulty as keyof typeof DifficultyLabels] }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="状态" width="90">
          <template #default="{ row }">
            <span class="status-pill" :class="`status--${row.status}`">
              {{ QuestionStatusLabels[row.status as keyof typeof QuestionStatusLabels] }}
            </span>
          </template>
        </el-table-column>

        <el-table-column label="操作" width="170" fixed="right">
          <template #default="{ row }">
            <el-button text size="small" @click="$router.push(`/questions/${row.id}/edit`)" class="op-btn">编辑</el-button>
            <el-button v-if="row.status === 'draft'" text size="small" class="op-btn op-btn--green" @click="handlePublish(row)">发布</el-button>
            <el-button v-if="row.status === 'published'" text size="small" class="op-btn op-btn--amber" @click="handleArchive(row)">下架</el-button>
            <el-button v-if="row.status === 'draft'" text size="small" class="op-btn op-btn--red" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="paginator">
        <span>共 <span class="num" style="color:var(--text-1);font-weight:600">{{ total }}</span> 条记录</span>
        <div style="display:flex;gap:6px">
          <el-button size="small" :disabled="cursor === 0" @click="prevPage">上一页</el-button>
          <el-button size="small" :disabled="!hasMore" @click="nextPage">下一页</el-button>
        </div>
      </div>
    </div>

    <!-- Import dialog -->
    <el-dialog v-model="showImport" title="批量导入题目" width="560px">
      <div class="import-hint">
        请上传 JSON 格式文件，每道题需包含 <code class="inline-code">stem、solution、knowledge_point、difficulty、question_type</code> 字段。
      </div>
      <el-upload drag accept=".json" :auto-upload="false" :on-change="handleFileChange" style="margin-top:16px">
        <el-icon class="el-icon--upload" style="font-size:32px;color:var(--indigo)"><UploadFilled /></el-icon>
        <div class="el-upload__text" style="margin-top:8px">将 JSON 文件拖到此处，或<em style="color:var(--indigo)">点击上传</em></div>
      </el-upload>
      <template #footer>
        <el-button @click="showImport = false">取消</el-button>
        <el-button type="primary" @click="handleImport">开始导入</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted } from 'vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { UploadFilled } from '@element-plus/icons-vue'
import { questionApi } from '@/api'
import type { Question } from '@/types'
import { FivePowerLabels, DifficultyLabels, QuestionStatusLabels, AnnotationStatusLabels } from '@/types'

const loading = ref(false)
const questions = ref<Question[]>([])
const total = ref(0)
const hasMore = ref(false)
const cursor = ref(0)
const showImport = ref(false)

const filters = reactive({ primary_power: '', difficulty: '', status: '', annotation_status: '', knowledge_point: '', keyword: '' })

function getAnnotationBadge(status: string) {
  if (status === 'confirmed') return 'conf-badge--high'
  if (status === 'rejected') return 'conf-badge--low'
  return 'conf-badge--mid'
}

function embedClass(s: string) {
  if (s === 'completed') return 'embed--ok'
  if (s === 'failed') return 'embed--fail'
  return 'embed--pending'
}

function embedLabel(s: string) {
  if (s === 'completed') return '向量化 ✓'
  if (s === 'failed') return '向量化 ✗'
  return '待向量化'
}

async function loadData() {
  loading.value = true
  try {
    const res = await questionApi.getList({ ...filters, cursor: cursor.value, limit: 20 })
    questions.value = res.list
    total.value = res.total
    hasMore.value = res.has_more
  } finally { loading.value = false }
}

function handleSearch() { cursor.value = 0; loadData() }
function resetFilters() {
  Object.assign(filters, { primary_power: '', difficulty: '', status: '', annotation_status: '', knowledge_point: '', keyword: '' })
  cursor.value = 0; loadData()
}
function prevPage() { cursor.value = Math.max(0, cursor.value - 20); loadData() }
function nextPage() { cursor.value += 20; loadData() }

async function handlePublish(row: Question) {
  await ElMessageBox.confirm(`确认发布题目 #${row.id}？发布后将触发向量化索引`, '确认发布', { type: 'warning' })
  await questionApi.publish(row.id)
  ElMessage.success('题目已发布')
  loadData()
}
async function handleArchive(row: Question) {
  await ElMessageBox.confirm(`确认下架题目 #${row.id}？下架后不再参与选题`, '确认下架', { type: 'warning' })
  await questionApi.archive(row.id)
  ElMessage.success('题目已下架')
  loadData()
}
async function handleDelete(row: Question) {
  await ElMessageBox.confirm(`确认删除草稿 #${row.id}？此操作不可恢复`, '确认删除', { type: 'error' })
  await questionApi.delete(row.id)
  ElMessage.success('已删除')
  loadData()
}
function handleFileChange() { ElMessage.info('文件已选择') }
function handleImport() { ElMessage.success('导入成功，AI 标注任务已提交'); showImport.value = false }

onMounted(loadData)
</script>

<style lang="scss" scoped>
.stem-cell { display: flex; flex-direction: column; gap: 5px; padding: 2px 0; }
.stem-text { font-size: 13.5px; color: var(--text-1); line-height: 1.5; }
.stem-meta { display: flex; align-items: center; gap: 6px; flex-wrap: wrap; }
.meta-num { font-size: 11.5px; color: var(--text-3); }

.embed-badge {
  font-size: 11.5px;
  font-weight: 500;
  padding: 2px 8px;
  border-radius: var(--r-pill);
  border: 1px solid;
}
.embed--ok   { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
.embed--fail { background: var(--red-dim);   color: var(--red);   border-color: var(--red-border); }
.embed--pending { background: var(--bg-muted); color: var(--text-3); border-color: var(--border-hover); }

.diff-badge {
  font-size: 11.5px; font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;
}
.diff--basic    { background: var(--teal-dim);    color: var(--teal);    border-color: var(--teal-border); }
.diff--advanced { background: var(--amber-dim);   color: var(--amber);   border-color: var(--amber-border); }
.diff--challenge{ background: var(--red-dim);     color: var(--red);     border-color: var(--red-border); }

.status-pill {
  font-size: 11.5px; font-weight: 500;
  padding: 3px 10px;
  border-radius: var(--r-pill);
  border: 1.5px solid;
}
.status--published { background: var(--green-dim); color: var(--green); border-color: var(--green-border); }
.status--draft     { background: var(--amber-dim); color: var(--amber); border-color: var(--amber-border); }
.status--archived  { background: var(--bg-muted);  color: var(--text-3); border-color: var(--border-hover); }

.op-btn { font-size: 13px !important; color: var(--text-2) !important; }
.op-btn:hover { color: var(--indigo) !important; }
.op-btn--green:hover { color: var(--green) !important; }
.op-btn--amber:hover { color: var(--amber) !important; }
.op-btn--red:hover   { color: var(--red)   !important; }

.import-hint {
  font-size: 13.5px;
  color: var(--text-2);
  line-height: 1.6;
  background: var(--indigo-light);
  border-radius: var(--r-lg);
  padding: 12px 16px;
}
.inline-code {
  font-family: var(--font-mono);
  font-size: 12.5px;
  background: var(--bg-muted);
  padding: 1px 5px;
  border-radius: 4px;
  color: var(--indigo);
}
</style>
