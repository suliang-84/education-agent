<template>
  <div class="page-root" v-loading="loading">
    <!-- 顶部操作栏 -->
    <div class="form-topbar">
      <el-button size="small" class="btn-back" @click="$router.push('/students')">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" style="margin-right:4px">
          <path stroke-linecap="round" stroke-linejoin="round" d="M10.5 19.5L3 12m0 0l7.5-7.5M3 12h18"/>
        </svg>
        返回
      </el-button>
      <div style="flex:1" />
      <el-button @click="$router.push(`/students/${studentId}/ai-prompt`)">
        <SvgIcon name="summary" :size="14" style="margin-right:4px" />摘要
      </el-button>
      <el-button @click="load">
        <SvgIcon name="analyse" :size="14" style="margin-right:4px" />刷新
      </el-button>
    </div>

    <template v-if="p">
      <!-- 基础档案 + 综合评估 -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />综合评估</span>
          <span class="hint-text">数据更新于 {{ formatDate(p.generated_at) }}</span>
        </div>

        <div class="who">
          <div class="who__avatar">{{ (p.basic.nickname || '?').slice(0, 1) }}</div>
          <div class="who__info">
            <div class="who__name">{{ p.basic.nickname || '未设置昵称' }}<span class="who__id">#{{ p.basic.id }}</span></div>
            <div class="who__meta">
              {{ gradeLabel }}<template v-if="p.basic.is_minor"> · 未成年</template>
              · 注册于 {{ formatDate(p.basic.created_at, 'YYYY-MM-DD') }}
              · 最近登录 {{ p.basic.last_login_at ? formatDate(p.basic.last_login_at) : '—' }}
              · 近 30 天活跃 {{ p.basic.active_days_30 }} 天
            </div>
            <div class="who__meta">
              已绑定家长：<template v-if="p.basic.parents.length">{{ p.basic.parents.map(x => x.nickname).join('、') }}</template><template v-else>暂无</template>
            </div>
          </div>
        </div>

        <div class="eval-grid">
          <div class="eval-card">
            <div class="eval-card__label">学习状态</div>
            <div class="status-tag" :class="`status--${statusKey}`">{{ p.summary.status }}</div>
            <div class="eval-card__desc">{{ p.summary.status_reason }}</div>
          </div>
          <div class="eval-card">
            <div class="eval-card__label">学习投入度</div>
            <div class="eval-card__num num">{{ p.summary.engagement_score }}<span class="unit"> / 100</span></div>
            <div class="parts">
              <div v-for="x in engagementParts" :key="x.label" class="part">
                <span class="part__label">{{ x.label }}</span>
                <div class="bar"><div class="bar__fill" :style="{ width: (x.value ?? 0) + '%' }" /></div>
                <span class="part__val num">{{ x.value ?? '—' }}</span>
              </div>
            </div>
            <div v-if="p.summary.engagement_parts.careful === null" class="eval-card__desc">
              带用时的答题不足 {{ MIN_CAREFUL }} 道（现有 {{ p.behavior.fast_wrong_samples }} 道），「认真作答」暂不计入，其余三项按比例折算
            </div>
          </div>
          <div class="eval-card">
            <div class="eval-card__label">近 4 周正确率</div>
            <div ref="trendRef" class="trend-chart" />
            <div class="eval-card__desc" v-if="p.summary.trend.slope !== null">
              平均每周{{ p.summary.trend.slope >= 0 ? '上升' : '下降' }} {{ Math.abs(p.summary.trend.slope) }} 个百分点
            </div>
          </div>
        </div>

        <div class="tips" v-if="p.summary.tips.length">
          <div class="sub-title">建议</div>
          <div v-for="(t, i) in p.summary.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
        </div>
      </div>

      <!-- 预警 -->
      <div class="surface section-block">
        <div class="section-hd">
          <span class="section-title"><SvgIcon name="doubble_triangle" :size="15" style="margin-right:5px;transform:rotate(180deg);flex-shrink:0" />预警（{{ p.warnings.open.length }}）</span>
          <span class="hint-text">规则和阈值可在「配置管理」里修改</span>
        </div>
        <div v-if="p.warnings.open.length" class="warn-list">
          <div v-for="w in p.warnings.open" :key="w.id" class="warn-item">
            <span class="level-tag" :class="`level--${w.level}`">{{ w.level_label }}</span>
            <div class="warn-item__main">
              <div class="warn-item__title">{{ w.rule_name }}</div>
              <div class="warn-item__msg">{{ w.message }}</div>
            </div>
            <span class="warn-item__time">{{ formatDate(w.triggered_at) }}</span>
            <el-button size="small" text class="plain-act" @click="openHandle(w)">
              <SvgIcon name="check_circle" :size="16" color="var(--color-primary)" style="margin-right:4px" />标为已处理
            </el-button>
          </div>
        </div>
        <div v-else class="empty-sm">目前没有需要关注的预警</div>

        <template v-if="p.warnings.handled.length">
          <div class="sub-title" style="margin-top:12px">最近处理过的预警</div>
          <div v-for="w in p.warnings.handled" :key="w.id" class="warn-item warn-item--done">
            <span class="level-tag" :class="`level--${w.level}`">{{ w.level_label }}</span>
            <div class="warn-item__main">
              <div class="warn-item__title">{{ w.rule_name }}</div>
              <div class="warn-item__msg">{{ w.message }}<template v-if="w.note">　处理备注：{{ w.note }}</template></div>
            </div>
            <span class="warn-item__time">{{ formatDate(w.handled_at) }} 处理</span>
          </div>
        </template>
      </div>

      <el-dialog v-model="handleVisible" title="标记为已处理" width="440px" :close-on-click-modal="false">
        <div class="handle-msg" v-if="handling">{{ handling.rule_name }}：{{ handling.message }}</div>
        <el-input v-model="handleNote" type="textarea" :rows="3" maxlength="500" show-word-limit placeholder="处理备注（选填），比如已联系家长、已调整训练计划" />
        <div class="foot-note">标记后，同一规则 7 天内不会再次提醒；条件消失时未处理的预警也会自动关闭。</div>
        <template #footer>
          <el-button @click="handleVisible = false">取消</el-button>
          <el-button type="primary" :loading="handleSaving" @click="submitHandle">确认</el-button>
        </template>
      </el-dialog>

      <!-- 分维度标签页 -->
      <div class="surface section-block tabs-block">
        <el-tabs v-model="tab" @tab-change="onTabChange">
          <!-- ① 认知能力 -->
          <el-tab-pane label="认知能力" name="cognitive">
            <template v-if="p.cognitive.has_profile">
              <div class="cog-grid">
                <div>
                  <div class="seg">
                    <button v-for="s in RADAR_SETS" :key="s.key" class="seg__btn" :class="{ on: radarSet === s.key }" @click="setRadar(s.key)">{{ s.label }}</button>
                  </div>
                  <div ref="radarRef" class="radar-chart" />
                </div>
                <div>
                  <div class="sub-title">五力得分（综合）</div>
                  <div v-for="k in POWERS" :key="k" class="rate-row">
                    <span class="rate-row__label" :style="{ color: POWER_COLORS[k] }">{{ FivePowerLabels[k] }}</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (p.cognitive.final?.[k] ?? 0) + '%', background: POWER_COLORS[k] }" /></div>
                    <span class="rate-row__val num">{{ p.cognitive.final?.[k] ?? '—' }}</span>
                  </div>
                  <div class="facts">
                    <div class="fact"><span>最强项</span><b>{{ powerName(p.cognitive.primary_strength) }}</b></div>
                    <div class="fact"><span>最弱项</span><b>{{ powerName(p.cognitive.primary_weakness) }}</b></div>
                    <div class="fact"><span>次弱项</span><b>{{ powerName(p.cognitive.secondary_weakness) }}</b></div>
                    <div class="fact"><span>推荐训练模式</span><b>{{ modeName(p.cognitive.recommended_mode) }}</b></div>
                    <div class="fact"><span>测试时间</span><b>{{ formatDate(p.cognitive.tested_at) }}</b></div>
                    <div class="fact" v-if="p.cognitive.training_info"><span>累计训练</span><b>{{ p.cognitive.training_info.total_training_count }} 次 / {{ p.cognitive.training_info.total_question_count }} 题</b></div>
                  </div>
                  <div v-if="p.cognitive.tags?.length" class="tag-list">
                    <span v-for="t in p.cognitive.tags" :key="t" class="tag">{{ t }}</span>
                  </div>
                </div>
              </div>
            </template>
            <div v-else class="empty">该学生尚未完成五力测试，暂无能力画像</div>

            <div class="sub-title" style="margin-top:15px">五力训练趋势（最近 8 周，每周各力的做题正确率）</div>
            <template v-if="p.cognitive.power_trend?.has_data">
              <div ref="trendPowerRef" class="history-chart" />
              <div class="foot-note">某一周某一力答题少于 3 道时不画点；这是学生实际做题时各项能力的表现，和上面的测试得分是两回事。</div>
            </template>
            <div v-else class="empty-sm">最近 8 周还没有足够的做题数据</div>
          </el-tab-pane>

          <!-- ② 学业掌握 -->
          <el-tab-pane label="学业掌握" name="mastery">
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.mastery.answered }}</div><div class="tile__lbl">累计答题</div></div>
              <div class="tile"><div class="tile__num num">{{ fmtPct(p.mastery.accuracy) }}</div><div class="tile__lbl">整体正确率</div></div>
              <div class="tile"><div class="tile__num num">{{ p.mastery.wrong_pending }}</div><div class="tile__lbl">待攻克错题</div></div>
              <div class="tile"><div class="tile__num num">{{ p.mastery.wrong_mastered }}</div><div class="tile__lbl">已攻克错题（{{ fmtPct(p.mastery.wrong_mastered_rate) }}）</div></div>
              <div class="tile"><div class="tile__num num">{{ p.mastery.stubborn_questions }}</div><div class="tile__lbl">顽固错题（错 ≥ 3 次）</div></div>
              <div class="tile"><div class="tile__num num">{{ p.mastery.favorites }}</div><div class="tile__lbl">收藏题数</div></div>
            </div>

            <div class="sub-title">当前学期进度</div>
            <div class="rate-row">
              <span class="rate-row__label">已练知识点</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (p.mastery.semester_progress.rate ?? 0) + '%' }" /></div>
              <span class="rate-row__val num">{{ p.mastery.semester_progress.practiced }} / {{ p.mastery.semester_progress.total }}</span>
            </div>

            <div class="three-col">
              <div>
                <div class="sub-title">题型正确率</div>
                <div v-for="r in p.mastery.by_type" :key="r.key" class="rate-row">
                  <span class="rate-row__label"><SvgIcon :name="QT_ICONS[r.key] ?? 'qt_application'" :size="14" :class="`qt-i qt-i--${r.key}`" />{{ r.label }}</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: (r.accuracy ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(r.accuracy) }}<small>{{ r.answered }}题</small></span>
                </div>
                <div v-if="!p.mastery.by_type.length" class="empty-sm">暂无数据</div>
              </div>
              <div>
                <div class="sub-title">难度表现</div>
                <div v-for="r in p.mastery.by_difficulty" :key="r.key" class="rate-row">
                  <span class="rate-row__label">{{ r.label }}</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: (r.accuracy ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(r.accuracy) }}<small>{{ r.answered }}题</small></span>
                </div>
                <div v-if="!p.mastery.by_difficulty.length" class="empty-sm">暂无数据</div>
              </div>
              <div>
                <div class="sub-title">科目表现</div>
                <div v-for="r in p.mastery.by_subject" :key="r.key" class="rate-row">
                  <span class="rate-row__label">{{ r.label }}</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: (r.accuracy ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(r.accuracy) }}<small>{{ r.answered }}题</small></span>
                </div>
                <div v-if="!p.mastery.by_subject.length" class="empty-sm">暂无数据</div>
              </div>
            </div>

            <div class="two-col">
              <div>
                <div class="sub-title">薄弱知识点 Top 5</div>
                <el-table :data="p.mastery.weak_kps" size="small" :show-header="true" class="mini-table" empty-text="还没有错误率达到 40%、且做过 2 次以上的知识点">
                  <el-table-column prop="name" label="知识点" min-width="130" show-overflow-tooltip />
                  <el-table-column label="错误率" width="80"><template #default="{ row }"><span class="num" style="color:var(--red)">{{ fmtPct(row.error_rate) }}</span></template></el-table-column>
                  <el-table-column label="做题" width="60"><template #default="{ row }"><span class="num">{{ row.errors }}/{{ row.attempts }}</span></template></el-table-column>
                  <el-table-column label="错因" min-width="170">
                    <template #default="{ row }">
                      <span class="cause-mini" :title="`没作答 ${row.blank_errors} · 秒答 ${row.rush_errors} · 认真做仍错 ${row.thoughtful_errors}`">
                        空答 {{ row.blank_errors }} · 秒答 {{ row.rush_errors }} · 认真错 {{ row.thoughtful_errors }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="走向" width="64">
                    <template #default="{ row }">
                      <span v-if="row.trend" class="trend-tag" :class="`trend--${row.trend}`">{{ TREND_LABELS[row.trend] }}</span>
                      <span v-else style="color:var(--text-3)">—</span>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div>
                <div class="sub-title">强项知识点 Top 5</div>
                <el-table :data="p.mastery.strong_kps" size="small" class="mini-table" empty-text="还没有错误率低于 40%、且做过 2 次以上的知识点">
                  <el-table-column prop="name" label="知识点" min-width="140" show-overflow-tooltip />
                  <el-table-column prop="chapter" label="单元" min-width="120" show-overflow-tooltip />
                  <el-table-column label="错误率" width="90"><template #default="{ row }"><span class="num" style="color:var(--green)">{{ fmtPct(row.error_rate) }}</span></template></el-table-column>
                  <el-table-column label="做题" width="70"><template #default="{ row }"><span class="num">{{ row.errors }}/{{ row.attempts }}</span></template></el-table-column>
                </el-table>
              </div>
            </div>
          </el-tab-pane>

          <!-- ③ 学习行为 -->
          <el-tab-pane label="学习行为" name="behavior">
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.behavior.sessions_7d }}</div><div class="tile__lbl">近 7 天训练次数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.behavior.sessions_30d }}</div><div class="tile__lbl">近 30 天训练次数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.behavior.streak_days }}</div><div class="tile__lbl">连续学习天数</div></div>
              <div class="tile"><div class="tile__num num">{{ fmtSec(p.behavior.avg_seconds_per_question) }}</div><div class="tile__lbl">平均单题用时</div></div>
              <div class="tile"><div class="tile__num num">{{ fmtPct(p.behavior.complete_rate) }}</div><div class="tile__lbl">答题完成度（{{ p.behavior.answered_questions }}/{{ p.behavior.issued_questions }} 题）</div></div>
              <div class="tile"><div class="tile__num num">{{ fmtPct(p.behavior.fast_wrong_ratio) }}</div><div class="tile__lbl">「快而错」占比</div></div>
            </div>
            <div class="two-col">
              <div>
                <div class="sub-title">学习时段分布</div>
                <div v-for="b in p.behavior.time_buckets" :key="b.key" class="rate-row">
                  <span class="rate-row__label">{{ b.label }}</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: (b.ratio ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(b.ratio) }}<small>{{ b.count }}题{{ b.accuracy !== null ? ` · 对 ${b.accuracy}%` : '' }}</small></span>
                </div>
                <div class="foot-note">上午 6–12 点，下午 12–18 点，晚上 18–22 点，深夜 22 点至次日 6 点</div>
              </div>
              <div>
                <div class="sub-title">训练方式偏好</div>
                <div v-for="d in p.behavior.dimensions" :key="d.key" class="rate-row">
                  <span class="rate-row__label">{{ d.label }}</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: dimRatio(d.count) + '%' }" /></div>
                  <span class="rate-row__val num">{{ d.count }}<small>次</small></span>
                </div>
                <div v-if="!p.behavior.dimensions.length" class="empty-sm">暂无训练记录</div>
                <div class="foot-note">平均每次训练作答 {{ fmtSec(p.behavior.avg_seconds_per_session) }}</div>
              </div>
            </div>

            <div class="sub-title" style="margin-top:15px">答题诊断</div>
            <div v-if="p.diagnosis.answered" class="three-col">
              <div>
                <div class="diag-hd">没作答就提交 <b class="num">{{ fmtPct(p.diagnosis.blank_rate) }}</b><small>（{{ p.diagnosis.blank }} / {{ p.diagnosis.answered }} 道）</small></div>
                <div v-for="r in p.diagnosis.blank_by_type" :key="r.key" class="rate-row">
                  <span class="rate-row__label"><SvgIcon :name="QT_ICONS[r.key] ?? 'qt_application'" :size="14" :class="`qt-i qt-i--${r.key}`" />{{ r.label }}</span>
                  <div class="bar"><div class="bar__fill bar__fill--warn" :style="{ width: (r.rate ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(r.rate) }}<small>{{ r.blank }}/{{ r.answered }}</small></span>
                </div>
              </div>
              <div>
                <div class="diag-hd">错题是怎么错的 <small>（共 {{ p.diagnosis.wrong }} 道错题）</small></div>
                <div v-for="c in p.diagnosis.causes" :key="c.key" class="rate-row">
                  <span class="rate-row__label cause-label">{{ c.label }}</span>
                  <div class="bar"><div class="bar__fill" :class="c.key === 'thoughtful' ? '' : 'bar__fill--warn'" :style="{ width: (c.ratio ?? 0) + '%' }" /></div>
                  <span class="rate-row__val num">{{ fmtPct(c.ratio) }}<small>{{ c.count }}道</small></span>
                </div>
                <div class="foot-note" v-if="diagVerdict.cause">{{ diagVerdict.cause }}</div>
              </div>
              <div>
                <div class="diag-hd">同一道题反复做有没有进步 <small>（{{ p.diagnosis.repeat.questions }} 道题做过 2 次以上）</small></div>
                <template v-if="p.diagnosis.repeat.attempts.length">
                  <div v-for="a in p.diagnosis.repeat.attempts" :key="a.attempt" class="rate-row">
                    <span class="rate-row__label cause-label">{{ a.label }}</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (a.accuracy ?? 0) + '%' }" /></div>
                    <span class="rate-row__val num">{{ fmtPct(a.accuracy) }}<small>{{ a.answered }}题</small></span>
                  </div>
                  <div class="foot-note" v-if="diagVerdict.repeat">{{ diagVerdict.repeat }}</div>
                </template>
                <div v-else class="empty-sm">还没有重复做过的题</div>
              </div>
            </div>
            <div v-else class="empty-sm">还没有答题记录</div>
          </el-tab-pane>

          <!-- ④ AI 互动 -->
          <el-tab-pane label="AI 互动" name="ai">
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.student_messages }}</div><div class="tile__lbl">学生发言数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.assistant_messages }}</div><div class="tile__lbl">助教回复数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.aha_count }}</div><div class="tile__lbl">顿悟次数</div></div>
              <div class="tile"><div class="tile__num ts">{{ p.ai_interaction.last_chat_at ? formatDate(p.ai_interaction.last_chat_at) : '—' }}</div><div class="tile__lbl">最近聊天</div></div>
            </div>
            <div class="two-col">
              <div>
                <div class="sub-title">启发策略效果（得分越高越适合该学生）</div>
                <el-table :data="p.ai_interaction.strategies" size="small" class="mini-table" empty-text="还没有用过启发策略">
                  <el-table-column prop="name" label="策略" min-width="120" />
                  <el-table-column label="得分" width="80"><template #default="{ row }"><span class="num">{{ row.score ?? '—' }}</span></template></el-table-column>
                  <el-table-column prop="uses" label="使用" width="60" />
                  <el-table-column prop="likes" label="点赞" width="60" />
                  <el-table-column prop="dislikes" label="点踩" width="60" />
                </el-table>
              </div>
              <div>
                <div class="sub-title">近期交流概况</div>
                <div class="text-box" v-if="p.ai_interaction.chat_summary">{{ p.ai_interaction.chat_summary }}</div>
                <div class="empty-sm" v-else>暂无聊天概况</div>
                <div class="sub-title" style="margin-top:10px">近期困惑</div>
                <div v-if="intentList.length" class="tag-list">
                  <span v-for="t in intentList" :key="t" class="tag">{{ t }}</span>
                </div>
                <div class="empty-sm" v-else>暂无</div>
              </div>
            </div>
          </el-tab-pane>

          <!-- ⑤ 个人特质 -->
          <el-tab-pane label="个人特质" name="traits">
            <div class="sub-title">个人洞察</div>
            <div class="text-box" v-if="p.traits.personal_insight">{{ p.traits.personal_insight }}</div>
            <div class="empty-sm" v-else>暂无个人洞察。学生与 AI 助教聊天后会自动生成，也可以在「摘要」页手动填写。</div>
            <div class="foot-note" v-if="p.traits.personal_insight_updated_at">更新于 {{ formatDate(p.traits.personal_insight_updated_at) }}</div>
            <div class="sub-title" style="margin-top:15px">学习信息摘要</div>
            <div class="text-box" v-if="p.traits.learning_summary">{{ p.traits.learning_summary }}</div>
            <div class="empty-sm" v-else>暂无</div>
            <div class="foot-note">编辑请前往「摘要」页。</div>
          </el-tab-pane>
        </el-tabs>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { studentApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { StudentProfile, ProfileWarning, FivePower } from '@/types'
import { FivePowerLabels } from '@/types'
import { formatDate } from '@/utils/format'

const TREND_LABELS: Record<string, string> = { up: '在进步', flat: '没起色', down: '在退步' }
const MIN_CAREFUL = 20   // 与后端 MIN_CAREFUL_SAMPLES 一致
const POWERS = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as FivePower[]
const POWER_COLORS: Record<string, string> = {
  INSIGHT: '#0D9488', CONSTRUCT: '#E11D48', DEDUCE: '#0EA5E9', ADAPT: '#D97706', MIGRATE: '#7C3AED',
}
const QT_ICONS: Record<string, string> = {
  SINGLE_CHOICE: 'qt_single', MULTIPLE_CHOICE: 'qt_multi', TRUE_FALSE: 'qt_judge', FILL_BLANK: 'qt_fill', APPLICATION: 'qt_application',
}
const RADAR_SETS = [
  { key: 'final', label: '综合' }, { key: 'ability', label: '能力' }, { key: 'preference', label: '偏好' }, { key: 'training', label: '训练表现' },
] as const
// 年级名称与学生列表保持一致
const GRADES: Record<string, string> = { G7: '初一', G8: '初二', G9: '初三', G10: '高一', G11: '高二', G12: '高三' }
const SEMESTERS: Record<string, string> = { S1: '上学期', S2: '下学期' }
const MODES: Record<string, string> = { TRAIN_WEAKNESS: '补弱训练', TRAIN_STRENGTH: '强化优势', BALANCED: '均衡训练' }

const route = useRoute()
const studentId = Number(route.params.id)
const loading = ref(false)
const p = ref<StudentProfile>()
const tab = ref('cognitive')
const radarSet = ref<(typeof RADAR_SETS)[number]['key']>('final')
const trendRef = ref<HTMLElement>()
const radarRef = ref<HTMLElement>()
const trendPowerRef = ref<HTMLElement>()
const charts: echarts.ECharts[] = []

const handleVisible = ref(false)
const handleSaving = ref(false)
const handleNote = ref('')
const handling = ref<ProfileWarning | null>(null)
function openHandle(w: ProfileWarning) {
  handling.value = w
  handleNote.value = ''
  handleVisible.value = true
}
async function submitHandle() {
  if (!handling.value || handleSaving.value) return
  handleSaving.value = true
  try {
    await studentApi.handleWarning(studentId, handling.value.id, handleNote.value.trim())
    ElMessage.success('已标记为已处理')
    handleVisible.value = false
    await load()
  } finally { handleSaving.value = false }
}

const gradeLabel = computed(() => {
  const b = p.value?.basic
  if (!b) return ''
  return `${GRADES[b.grade ?? ''] ?? b.grade ?? '未设置年级'} ${SEMESTERS[b.semester ?? ''] ?? b.semester ?? ''}`.trim()
})
const statusKey = computed(() => ({
  稳步提升: 'up', 状态平稳: 'flat', 遇到瓶颈: 'stuck', 近期懈怠: 'idle', 数据不足: 'none',
}[p.value?.summary.status ?? ''] ?? 'none'))
const engagementParts = computed(() => {
  const e = p.value?.summary.engagement_parts
  return e ? [
    { label: '训练频次', value: e.frequency }, { label: '连续天数', value: e.streak },
    { label: '答题完成度', value: e.complete }, { label: '认真作答', value: e.careful },
  ] : []
})
const intentList = computed(() => (p.value?.ai_interaction.intents ?? []).map((x) => {
  if (typeof x === 'string') return x
  const o = x as Record<string, unknown>
  return String(o.kp_name ?? o.name ?? o.topic ?? o.label ?? '')
}).filter(Boolean))
// 诊断结论：只在数据足够时给出，避免对很少的样本下结论
const diagVerdict = computed(() => {
  const d = p.value?.diagnosis
  const out = { cause: '', repeat: '' }
  if (!d) return out
  if (d.wrong >= 10) {
    const blank = d.causes.find(c => c.key === 'blank')
    const thoughtful = d.causes.find(c => c.key === 'thoughtful')
    if ((blank?.ratio ?? 0) >= 50) out.cause = '大部分错题是没作答就提交的，更像是在跳题或没有投入，而不是知识不会；建议先了解原因（题太难、没时间、不想做）'
    else if ((thoughtful?.ratio ?? 0) >= 50) out.cause = '大部分错题是认真做了仍然错，说明有真正的知识缺口，适合针对性讲解和训练'
  }
  const r = d.repeat
  if (r.questions >= 5 && r.gain !== null) {
    out.repeat = r.gain <= 0
      ? `重复做之后正确率没有提高（后面几次比第 1 次${r.gain === 0 ? '持平' : `低 ${Math.abs(r.gain)} 个百分点`}），反复刷题帮助不大，建议配合讲解（智能解答 / AI 助教）`
      : `重复做之后正确率提高了 ${r.gain} 个百分点，反复练习有效果`
  }
  return out
})
const dimTotal = computed(() => (p.value?.behavior.dimensions ?? []).reduce((a, b) => a + b.count, 0) || 1)

const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v}%`)
const fmtSec = (v: number | null | undefined) => (v === null || v === undefined ? '—' : v >= 60 ? `${Math.round(v / 6) / 10} 分钟` : `${v} 秒`)
const dimRatio = (n: number) => Math.round((n / dimTotal.value) * 100)
const powerName = (k?: string) => (k ? FivePowerLabels[k as FivePower] ?? k : '—')
const modeName = (k?: string) => (k ? MODES[k] ?? k : '—')

function cssVar(name: string, fallback: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}
function initChart(el?: HTMLElement) {
  if (!el) return null
  echarts.getInstanceByDom(el)?.dispose()
  const c = echarts.init(el)
  charts.push(c)
  return c
}

function renderTrend() {
  const c = initChart(trendRef.value)
  if (!c || !p.value) return
  const weeks = p.value.summary.trend.weeks
  const primary = cssVar('--color-primary', '#608df9')
  c.setOption({
    grid: { left: 30, right: 10, top: 10, bottom: 22 },
    xAxis: { type: 'category', data: weeks.map(w => (w.weeks_ago === 0 ? '本周' : `${w.weeks_ago}周前`)), axisLabel: { color: cssVar('--text-3', '#999'), fontSize: 11 }, axisLine: { show: false }, axisTick: { show: false } },
    yAxis: { type: 'value', min: 0, max: 100, splitNumber: 2, axisLabel: { color: cssVar('--text-3', '#999'), fontSize: 11 }, splitLine: { lineStyle: { color: 'rgba(128,128,128,0.15)' } } },
    tooltip: { trigger: 'axis', formatter: (ps: { dataIndex: number }[]) => { const w = weeks[ps[0].dataIndex]; return w.accuracy === null ? '无数据' : `正确率 ${w.accuracy}%（${w.answered} 题）` } },
    series: [{ type: 'line', data: weeks.map(w => w.accuracy), connectNulls: true, smooth: true, symbolSize: 6, itemStyle: { color: primary }, lineStyle: { color: primary, width: 2 }, areaStyle: { color: primary, opacity: 0.12 } }],
  })
}

function renderRadar() {
  const c = initChart(radarRef.value)
  const cog = p.value?.cognitive
  if (!c || !cog?.has_profile) return
  const data = (cog[radarSet.value] ?? {}) as Record<string, number>
  const primary = cssVar('--color-primary', '#608df9')
  c.setOption({
    backgroundColor: 'transparent',
    radar: {
      indicator: POWERS.map(k => ({ name: FivePowerLabels[k], max: radarSet.value === 'preference' ? Math.max(30, ...Object.values(data)) : 100 })),
      radius: 90,
      axisName: { color: cssVar('--text-2', '#888'), fontSize: 12 },
      splitLine: { lineStyle: { color: 'rgba(128,128,128,0.22)' } },
      splitArea: { show: false },
      axisLine: { lineStyle: { color: 'rgba(128,128,128,0.22)' } },
    },
    series: [{
      type: 'radar',
      data: [{ value: POWERS.map(k => data[k] ?? 0), lineStyle: { color: primary, width: 2 }, itemStyle: { color: primary }, areaStyle: { color: primary, opacity: 0.22 } }],
    }],
  })
}
function setRadar(k: (typeof RADAR_SETS)[number]['key']) {
  radarSet.value = k
  renderRadar()
}

function renderPowerTrend() {
  const c = initChart(trendPowerRef.value)
  const t = p.value?.cognitive.power_trend
  if (!c || !t?.has_data) return
  c.setOption({
    grid: { left: 36, right: 16, top: 30, bottom: 26 },
    legend: { top: 0, textStyle: { color: cssVar('--text-2', '#888') } },
    tooltip: {
      trigger: 'axis',
      formatter: (ps: { dataIndex: number; seriesName: string; marker: string; value: number | null }[]) =>
        `${t.weeks[ps[0].dataIndex].label}<br/>` + ps.map((x) => `${x.marker}${x.seriesName}：${x.value === null || x.value === undefined ? '数据不足' : x.value + '%'}`).join('<br/>'),
    },
    xAxis: { type: 'category', data: t.weeks.map(w => w.label), axisLabel: { color: cssVar('--text-3', '#999'), fontSize: 11 } },
    yAxis: { type: 'value', min: 0, max: 100, splitLine: { lineStyle: { color: 'rgba(128,128,128,0.15)' } }, axisLabel: { color: cssVar('--text-3', '#999') } },
    series: POWERS.map(k => ({
      name: FivePowerLabels[k], type: 'line', smooth: true, symbolSize: 7, connectNulls: true,
      data: t.weeks.map(w => w.powers[k]?.accuracy ?? null),
      itemStyle: { color: POWER_COLORS[k] }, lineStyle: { color: POWER_COLORS[k], width: 2 },
    })),
  })
}

async function drawTab() {
  await nextTick()
  if (tab.value === 'cognitive') { renderRadar(); renderPowerTrend() }
}
function onTabChange() { drawTab() }

async function load() {
  loading.value = true
  try {
    p.value = await studentApi.getProfile(studentId)
    await nextTick()
    renderTrend()
    await drawTab()
  } finally { loading.value = false }
}

function onResize() { charts.forEach(c => c.resize()) }
onMounted(() => { load(); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); charts.forEach(c => c.dispose()) })
</script>

<style lang="scss" scoped>
.page-root { scrollbar-width: none; &::-webkit-scrollbar { display: none; } }

.form-topbar { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.form-topbar :deep(.el-button + .el-button) { margin-left: 0; }

.section-block {
  padding: 5px 15px 15px;
  flex-shrink: 0;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;
}
.hint-text { font-size: 12px; color: var(--text-3); }

.sub-title { font-size: 13px; font-weight: 600; color: var(--text-1); margin: 10px 0 8px; }
.foot-note { margin-top: 8px; font-size: 12px; color: var(--text-3); }
.empty, .empty-sm { color: var(--text-3); font-size: 13px; }
.empty { padding: 40px 0; text-align: center; }
.empty-sm { padding: 6px 0; }

// ── 学生信息 ─────────────────────────────────────────────
.who { display: flex; align-items: center; gap: 15px; margin: 8px 0 15px; }
.who__avatar {
  width: 48px; height: 48px; border-radius: 50%; flex-shrink: 0;
  display: flex; align-items: center; justify-content: center;
  font-size: 20px; font-weight: 700; color: var(--color-primary);
  background: color-mix(in srgb, var(--color-primary) 16%, transparent);
}
.who__name { font-size: 16px; font-weight: 700; color: var(--text-1); }
.who__id { margin-left: 8px; font-size: 12px; font-weight: 400; color: var(--text-3); }
.who__meta { margin-top: 3px; font-size: 12.5px; color: var(--text-3); }

// ── 综合评估三张卡片 ─────────────────────────────────────
.eval-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 15px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.eval-card {
  padding: 12px 15px;
  border: 1px solid rgba(96, 141, 248, 0.15);
  border-radius: 4px;
  min-height: 150px;
  &__label { font-size: 13px; color: var(--text-2); margin-bottom: 8px; }
  &__num { font-size: 30px; font-weight: 700; color: var(--text-1); .unit { font-size: 13px; font-weight: 400; color: var(--text-3); } }
  &__desc { margin-top: 8px; font-size: 12.5px; line-height: 1.6; color: var(--text-3); }
}
.status-tag {
  display: inline-block; padding: 3px 14px; border-radius: 999px; font-size: 14px; font-weight: 600;
  &.status--up    { background: color-mix(in srgb, var(--green) 16%, transparent); color: var(--green); }
  &.status--flat  { background: color-mix(in srgb, var(--color-primary) 16%, transparent); color: var(--color-primary); }
  &.status--stuck { background: color-mix(in srgb, var(--amber) 18%, transparent); color: var(--amber); }
  &.status--idle  { background: color-mix(in srgb, var(--red) 16%, transparent); color: var(--red); }
  &.status--none  { background: color-mix(in srgb, var(--text-3) 18%, transparent); color: var(--text-3); }
}
.parts { margin-top: 10px; }
.part { display: flex; align-items: center; gap: 8px; margin-bottom: 4px; font-size: 12px; color: var(--text-2); &__label { width: 68px; } &__val { width: 28px; text-align: right; color: var(--text-3); } }
.trend-chart { height: 100px; }

.tips { margin-top: 5px; }
.tip { display: flex; gap: 8px; margin-bottom: 5px; font-size: 13px; line-height: 1.6; color: var(--text-1); }
.tip__no { flex-shrink: 0; width: 18px; height: 18px; margin-top: 2px; border-radius: 50%; text-align: center; line-height: 18px; font-size: 11px; color: var(--color-primary); background: color-mix(in srgb, var(--color-primary) 16%, transparent); }

// ── 条形指标 ─────────────────────────────────────────────
.bar { flex: 1; height: 6px; border-radius: 3px; background: color-mix(in srgb, var(--text-3) 18%, transparent); overflow: hidden; }
.bar__fill { height: 100%; border-radius: 3px; background: var(--color-primary); transition: width 0.3s; }
.rate-row { display: flex; align-items: center; gap: 10px; margin-bottom: 8px; font-size: 13px; }
.rate-row__label { display: flex; align-items: center; gap: 4px; width: 84px; flex-shrink: 0; color: var(--text-2); white-space: nowrap; }
.rate-row__val { min-width: 92px; white-space: nowrap; flex-shrink: 0; text-align: right; color: var(--text-1); small { margin-left: 4px; font-size: 11px; color: var(--text-3); } }

.tiles { display: grid; grid-template-columns: repeat(6, minmax(0, 1fr)); gap: 15px; margin: 5px 0 10px; @media (max-width: 1200px) { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
.tile { padding: 10px 12px; border: 1px solid rgba(96, 141, 248, 0.15); border-radius: 4px; }
.tile__num { font-size: 22px; font-weight: 700; color: var(--text-1); &.ts { font-size: 14px; line-height: 30px; } }
.tile__lbl { margin-top: 2px; font-size: 12px; color: var(--text-3); }

.two-col { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 24px; margin-top: 5px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.three-col { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; @media (max-width: 1200px) { grid-template-columns: 1fr; } }
.mini-table { width: 100%; }

// 题型图标颜色同训练题管理「题目类型」列
.qt-i { flex-shrink: 0; color: var(--text-3);
  &--SINGLE_CHOICE { color: var(--qt-single); } &--MULTIPLE_CHOICE { color: var(--qt-multi); }
  &--FILL_BLANK { color: var(--qt-fill); } &--TRUE_FALSE { color: var(--qt-judge); } &--APPLICATION { color: var(--qt-application); } }

// ── 认知能力 ─────────────────────────────────────────────
.cog-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.radar-chart { height: 260px; }
.history-chart { height: 240px; }
.cause-mini { font-size: 12px; color: var(--text-2); white-space: nowrap; }
.trend-tag { font-size: 12px; font-weight: 600; &.trend--up { color: var(--green); } &.trend--flat { color: var(--amber); } &.trend--down { color: var(--red); } }
.diag-hd { margin-bottom: 8px; font-size: 13px; color: var(--text-2); b { margin-left: 6px; font-size: 18px; color: var(--text-1); } small { margin-left: 6px; font-size: 12px; color: var(--text-3); } }
.cause-label { width: 130px; }
.bar__fill--warn { background: var(--amber); }
.seg { display: inline-flex; gap: 15px; margin-bottom: 5px; }
.seg__btn { padding: 0; border: none; background: transparent; font-size: 13px; color: var(--text-3); cursor: pointer; &.on { color: var(--color-primary); font-weight: 600; } }
.facts { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 6px 15px; margin-top: 10px; }
.fact { display: flex; justify-content: space-between; font-size: 13px; color: var(--text-3); b { font-weight: 500; color: var(--text-1); } }
.tag-list { display: flex; flex-wrap: wrap; gap: 8px; margin-top: 10px; }
.tag { padding: 2px 10px; border-radius: 999px; font-size: 12px; color: var(--color-primary); background: color-mix(in srgb, var(--color-primary) 14%, transparent); }

.text-box { padding: 10px 12px; border: 1px solid rgba(96, 141, 248, 0.15); border-radius: 4px; font-size: 13px; line-height: 1.8; color: var(--text-1); white-space: pre-wrap; word-break: break-word; }

.warn-list { margin-top: 5px; }
.warn-item { display: flex; align-items: center; gap: 12px; padding: 8px 0; border-bottom: 1px solid rgba(96, 141, 248, 0.1); &:last-child { border-bottom: none; } }
.warn-item--done { opacity: 0.7; }
.warn-item__main { flex: 1; min-width: 0; }
.warn-item__title { font-size: 13px; font-weight: 600; color: var(--text-1); }
.warn-item__msg { margin-top: 2px; font-size: 12.5px; line-height: 1.6; color: var(--text-3); }
.warn-item__time { flex-shrink: 0; font-size: 12px; color: var(--text-3); }
.level-tag {
  flex-shrink: 0; width: 44px; text-align: center; padding: 2px 0; border-radius: 999px; font-size: 12px; font-weight: 600;
  &.level--notice    { background: color-mix(in srgb, var(--color-primary) 16%, transparent); color: var(--color-primary); }
  &.level--attention { background: color-mix(in srgb, var(--amber) 18%, transparent); color: var(--amber); }
  &.level--critical  { background: color-mix(in srgb, var(--red) 16%, transparent); color: var(--red); }
}
.plain-act { padding: 0 !important; height: auto !important; margin-left: 0 !important; color: var(--color-primary); background: transparent !important; border-color: transparent !important; flex-shrink: 0;
  &:hover, &:focus { background: transparent !important; border-color: transparent !important; } }
.handle-msg { margin-bottom: 10px; font-size: 13px; line-height: 1.7; color: var(--text-2); }

.tabs-block :deep(.el-tabs__header) { margin-bottom: 8px; }
</style>
