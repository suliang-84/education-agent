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
      <el-date-picker
        v-model="dateRange" type="daterange" :clearable="false" :editable="false"
        range-separator="–" start-placeholder="开始日期" end-placeholder="结束日期"
        format="YYYY-MM-DD" value-format="YYYY-MM-DD"
        :shortcuts="rangeShortcuts" :disabled-date="disableFuture"
        style="width:300px;flex:none" @change="onRangeChange"
      />
      <el-button @click="$router.push(`/students/${studentId}/ai-prompt`)">
        <SvgIcon name="summary" :size="14" style="margin-right:4px" />摘要
      </el-button>
      <el-button @click="load">
        <SvgIcon name="analyse" :size="14" style="margin-right:4px" />刷新
      </el-button>
    </div>

    <template v-if="p">
      <!-- 基础档案 + 综合评估 -->
      <!-- 顶部统计小卡片 -->
      <div v-if="p.kpis?.length" class="kpi-strip">
        <div v-for="k in p.kpis" :key="k.key" class="kpi">
          <div class="kpi__txt">
            <div class="kpi__lbl">{{ k.label }}
              <el-tooltip :content="k.tip" placement="top" :show-after="150" popper-class="st-popper">
                <SvgIcon name="help" :size="12" class="part__help" />
              </el-tooltip>
            </div>
            <div class="kpi__val num">{{ k.value }}</div>
            <div class="kpi__delta">
              <span v-if="k.delta != null && k.delta !== 0" class="delta" :class="kpiTone(k)" :title="`较前一周期${k.delta > 0 ? '上升' : '下降'} ${Math.abs(k.delta)}${k.unit === '%' ? ' 个百分点' : k.unit}`">
                <SvgIcon name="arrow_up" :size="11" :class="{ 'delta__down': k.delta < 0 }" />{{ Math.abs(k.delta) }}{{ k.unit }}
              </span>
              <span v-else-if="k.delta === 0" class="delta">持平</span>
              <span v-else>&nbsp;</span>
            </div>
          </div>
          <div v-if="k.series?.length > 1" class="kpi__viz"><KpiSpark :values="k.series" :kind="KPI_VIZ[k.key] ?? 'bars'" :gid="`kpi-${k.key}`" /></div>
        </div>
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
                  <div ref="radarRef" class="radar-chart" />
                </div>
                <div>
                  <div class="sub-title">五力训练态势</div>
                  <template v-if="p.cognitive.power_trend?.has_data">
                    <div ref="trendPowerRef" class="history-chart" />
                  </template>
                  <div v-else class="empty-sm">{{ rangeLabel }}还没有足够的做题数据</div>
                </div>
              </div>
              <div class="cog-compare">
                <div class="sub-title">测试得分 vs 实战表现</div>
                <el-table v-if="cogInsights" :data="cogInsights.powers" size="small" class="mini-table cog-table">
                  <el-table-column label="能力" width="70"><template #default="{ row }"><span :style="{ color: POWER_COLORS[row.key], fontWeight: 600 }">{{ row.label }}</span></template></el-table-column>
                  <el-table-column label="测试得分" min-width="120">
                    <template #default="{ row }">
                      <div class="cog-bar"><div class="bar"><div class="bar__fill" :style="{ width: (row.test ?? 0) + '%', background: POWER_COLORS[row.key] }" /></div><span class="num">{{ row.test ?? '—' }}</span></div>
                    </template>
                  </el-table-column>
                  <el-table-column label="实战正确率" min-width="120">
                    <template #default="{ row }">
                      <div class="cog-bar"><div class="bar"><div class="bar__fill bar__fill--real" :style="{ width: (row.accuracy ?? 0) + '%' }" /></div><span class="num">{{ fmtPct(row.accuracy) }}</span><small>{{ row.answered }}题</small></div>
                    </template>
                  </el-table-column>
                  <el-table-column label="较前期" width="76">
                    <template #default="{ row }">
                      <span v-if="row.delta !== null" class="delta" :class="row.delta > 0 ? 'delta--up' : row.delta < 0 ? 'delta--down' : ''" :title="`前一周期正确率 ${row.prev_accuracy}%`">
                        <SvgIcon v-if="row.delta !== 0" name="arrow_up" :size="11" :class="{ 'delta__down': row.delta < 0 }" />{{ Math.abs(row.delta) }}%
                      </span>
                      <span v-else class="cause-mini">—</span>
                    </template>
                  </el-table-column>
                  <el-table-column label="做题占比" width="76"><template #default="{ row }"><span class="num">{{ fmtPct(row.share) }}</span></template></el-table-column>
                  <el-table-column label="评价" width="92">
                    <template #default="{ row }">
                      <el-tooltip :content="row.status === 'below' ? `实战比测试低 ${Math.abs(row.gap)} 个百分点` : row.status === 'above' ? `实战比测试高 ${row.gap} 个百分点` : row.status === 'few' ? `${rangeLabel}答题不足 6 道，暂不比较` : '实战表现和测试得分基本相符'" placement="top">
                        <span class="cog-chip" :class="`cog-chip--${row.status}`">{{ COG_STATUS[row.status] }}</span>
                      </el-tooltip>
                    </template>
                  </el-table-column>
                </el-table>
              </div>
              <div v-if="cogInsights?.highlights.length" class="cog-hl">
                <div class="sub-title">认知洞察</div>
                <div v-for="(h, i) in cogInsights.highlights" :key="i" class="hl-item"><span class="hl-item__dot" :class="`tone--${h.tone}`" />{{ h.text }}</div>
              </div>
            </template>
            <template v-else>
              <div class="empty">该学生尚未完成五力测试，暂无能力画像</div>
              <div class="sub-title" style="margin-top:15px">五力训练态势</div>
              <div v-if="p.cognitive.power_trend?.has_data" ref="trendPowerRef" class="history-chart" />
              <div v-else class="empty-sm">{{ rangeLabel }}还没有足够的做题数据</div>
            </template>
          </el-tab-pane>

          <!-- ② 学业掌握 -->
          <el-tab-pane label="学业掌握" name="mastery" lazy>
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.mastery.answered }}</div><div class="tile__lbl">{{ rangeLabel }}答题</div></div>
              <div class="tile"><div class="tile__num num">{{ fmtPct(p.mastery.accuracy) }}</div><div class="tile__lbl">{{ rangeLabel }}正确率</div></div>
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

            <div class="two-col two-col--stack">
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
                  <el-table-column label="可能的前置" min-width="120" show-overflow-tooltip>
                    <template #default="{ row }"><span v-if="row.root_kp" class="cause-mini">{{ row.root_kp.name }}</span><span v-else style="color:var(--text-3)">—</span></template>
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
          <el-tab-pane label="学习行为" name="behavior" lazy>
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.behavior.sessions_range }}</div><div class="tile__lbl">{{ rangeLabel }}训练次数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.behavior.active_days }}</div><div class="tile__lbl">{{ rangeLabel }}活跃天数</div></div>
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

            <div class="sub-title" style="margin-top:15px">更多发现</div>
            <div class="three-col">
              <div>
                <div class="diag-hd">做题时越做越累吗 <small>（同一次训练前半段 vs 后半段）</small></div>
                <template v-if="p.insights.fatigue.early && p.insights.fatigue.late">
                  <div v-for="x in fatigueRows" :key="x.label" class="rate-row">
                    <span class="rate-row__label cause-label">{{ x.label }}</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (x.accuracy ?? 0) + '%' }" /></div>
                    <span class="rate-row__val num">{{ fmtPct(x.accuracy) }}<small>没作答 {{ fmtPct(x.blank) }}</small></span>
                  </div>
                  <div class="foot-note">{{ p.insights.fatigue.verdict || '前后半段差别不大，或答题数还不够下结论' }}</div>
                </template>
                <div v-else class="empty-sm">每次抽题 4 道以上、答题足够多后才能分析</div>
              </div>
              <div>
                <div class="diag-hd">看过智能解答有用吗 <small>（{{ p.insights.explanation.questions }} 道题看过解答）</small></div>
                <template v-if="p.insights.explanation.questions">
                  <div class="rate-row">
                    <span class="rate-row__label cause-label">看解答之前</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (p.insights.explanation.before.accuracy ?? 0) + '%' }" /></div>
                    <span class="rate-row__val num">{{ fmtPct(p.insights.explanation.before.accuracy) }}<small>{{ p.insights.explanation.before.answered }}题</small></span>
                  </div>
                  <div class="rate-row">
                    <span class="rate-row__label cause-label">看解答之后</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (p.insights.explanation.after.accuracy ?? 0) + '%' }" /></div>
                    <span class="rate-row__val num">{{ fmtPct(p.insights.explanation.after.accuracy) }}<small>{{ p.insights.explanation.after.answered }}题</small></span>
                  </div>
                  <div class="foot-note">{{ p.insights.explanation.verdict || '看过解答后再做的题还不够多，暂不下结论' }}</div>
                </template>
                <div v-else class="empty-sm">还没有看过智能解答</div>
              </div>
              <div>
                <div class="diag-hd">是不是总选同一个答案</div>
                <div v-for="m in p.insights.misconceptions" :key="m.question_id" class="mis-item">{{ m.text }}</div>
                <div v-for="b in p.insights.bias.items" :key="b.type" class="rate-row">
                  <span class="rate-row__label cause-label">{{ b.label }}最常选「{{ b.answer }}」</span>
                  <div class="bar"><div class="bar__fill" :style="{ width: b.share + '%' }" /></div>
                  <span class="rate-row__val num">{{ b.share }}%<small>{{ b.answered }}题</small></span>
                </div>
                <div class="foot-note" v-if="p.insights.bias.text">{{ p.insights.bias.text }}</div>
                <div v-if="!p.insights.misconceptions.length && !p.insights.bias.items.length" class="empty-sm">选择 / 判断题答得还不够多</div>
              </div>
            </div>
          </el-tab-pane>

          <!-- ④ AI 互动 -->
          <el-tab-pane label="AI 互动" name="ai" lazy>
            <div class="tiles">
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.student_messages }}</div><div class="tile__lbl">{{ rangeLabel }}学生发言数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.assistant_messages }}</div><div class="tile__lbl">{{ rangeLabel }}助教回复数</div></div>
              <div class="tile"><div class="tile__num num">{{ p.ai_interaction.aha_count }}</div><div class="tile__lbl">{{ rangeLabel }}顿悟次数</div></div>
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
          <el-tab-pane label="个人特质" name="traits" lazy>
            <div class="sub-title">个人洞察</div>
            <div class="text-box" v-if="p.traits.personal_insight">{{ p.traits.personal_insight }}</div>
            <div class="empty-sm" v-else>暂无个人洞察。学生与 AI 助教聊天后会自动生成，也可以在「摘要」页手动填写。</div>
            <div class="foot-note" v-if="p.traits.personal_insight_updated_at">更新于 {{ formatDate(p.traits.personal_insight_updated_at) }}</div>
            <div class="sub-title" style="margin-top:15px">学习信息摘要</div>
            <div class="text-box" v-if="p.traits.learning_summary">{{ p.traits.learning_summary }}</div>
            <div class="empty-sm" v-else>暂无</div>
            <div class="foot-note">编辑请前往「摘要」页。</div>
          </el-tab-pane>
          <!-- ⑥ 预警 -->
          <el-tab-pane :label="`预警（${p.warnings.open.length}）`" name="warnings" lazy>
            <div class="hint-text" style="margin-bottom:8px">规则和阈值可在「配置管理」里修改</div>
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
          </el-tab-pane>

          <!-- ⑦ 建议 -->
          <el-tab-pane label="建议" name="tips" lazy>
            <div v-if="p.summary.tips.length" class="tips">
              <div v-for="(t, i) in p.summary.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
            </div>
            <div v-else class="empty-sm">暂无建议</div>
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
import type { StudentProfile, ProfileWarning, ProfileKpi, FivePower } from '@/types'
import { FivePowerLabels } from '@/types'
import KpiSpark from '@/components/KpiSpark.vue'
import { formatDate } from '@/utils/format'

const TREND_LABELS: Record<string, string> = { up: '在进步', flat: '没起色', down: '在退步' }
const POWERS = ['INSIGHT', 'CONSTRUCT', 'DEDUCE', 'ADAPT', 'MIGRATE'] as FivePower[]
const POWER_COLORS: Record<string, string> = {
  INSIGHT: '#0D9488', CONSTRUCT: '#E11D48', DEDUCE: '#0EA5E9', ADAPT: '#D97706', MIGRATE: '#7C3AED',
}
const QT_ICONS: Record<string, string> = {
  SINGLE_CHOICE: 'qt_single', MULTIPLE_CHOICE: 'qt_multi', TRUE_FALSE: 'qt_judge', FILL_BLANK: 'qt_fill', APPLICATION: 'qt_application',
}
const KPI_VIZ: Record<string, 'line' | 'bars' | 'wave' | 'dots'> = { study_time: 'line', sessions: 'bars', answered: 'wave', accuracy: 'line', ai_asks: 'bars' }
const COG_STATUS: Record<string, string> = { below: '发挥不稳', above: '实战更强', ok: '与测试相符', few: '做题太少' }
// 年级名称与学生列表保持一致
const GRADES: Record<string, string> = { G7: '初一', G8: '初二', G9: '初三', G10: '高一', G11: '高二', G12: '高三' }
const SEMESTERS: Record<string, string> = { S1: '上学期', S2: '下学期' }

const route = useRoute()
const studentId = Number(route.params.id)
const loading = ref(false)
const p = ref<StudentProfile>()
const tab = ref('cognitive')
// 统计日期范围：默认近 7 天（含今天），可自选，最长 90 天
const MAX_RANGE_DAYS = 90
const ymd = (d: Date) => `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, '0')}-${String(d.getDate()).padStart(2, '0')}`
const daysAgo = (n: number) => { const d = new Date(); d.setDate(d.getDate() - n); return d }
const lastDays = (n: number): [string, string] => [ymd(daysAgo(n - 1)), ymd(new Date())]
const dateRange = ref<[string, string]>(lastDays(7))
const rangeShortcuts = [
  { text: '近一周', value: () => lastDays(7) },
  { text: '近一个月', value: () => lastDays(30) },
]
const disableFuture = (d: Date) => d.getTime() > Date.now()
// 变大是好事的指标：上升绿 / 下降红；变小是好事的（空答率等）反过来；没有好坏的（每题用时）用灰色
function kpiTone(k: ProfileKpi) {
  if (!k.delta) return ''
  if (!k.good) return ''
  return (k.delta > 0) === (k.good === 'up') ? 'delta--up' : 'delta--down'
}
const rangeLabel = computed(() => p.value?.range.label ?? '近 7 天')
function onRangeChange() {
  const [s, e] = dateRange.value
  if ((new Date(e).getTime() - new Date(s).getTime()) / 86400000 + 1 > MAX_RANGE_DAYS) {
    ElMessage.warning(`日期范围最长 ${MAX_RANGE_DAYS} 天`)
    const r = p.value?.range
    dateRange.value = r ? [r.start, r.end] : lastDays(7)
    return
  }
  load()
}
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
const fatigueRows = computed(() => {
  const f = p.value?.insights.fatigue
  if (!f?.early || !f.late) return []
  return [
    { label: '前半段', accuracy: f.early.accuracy, blank: f.early.blank_rate },
    { label: '后半段', accuracy: f.late.accuracy, blank: f.late.blank_rate },
  ]
})
const cogInsights = computed(() => p.value?.cognitive.insights)
const dimTotal = computed(() => (p.value?.behavior.dimensions ?? []).reduce((a, b) => a + b.count, 0) || 1)

const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v}%`)
const fmtSec = (v: number | null | undefined) => (v === null || v === undefined ? '—' : v >= 60 ? `${Math.round(v / 6) / 10} 分钟` : `${v} 秒`)
const dimRatio = (n: number) => Math.round((n / dimTotal.value) * 100)

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

function renderRadar() {
  const c = initChart(radarRef.value)
  const cog = p.value?.cognitive
  if (!c || !cog?.has_profile) return
  const primary = cssVar('--color-primary', '#608df9')
  {
    // 测试综合得分 vs 所选范围内的实战正确率：两个多边形的差距就是「会但没发挥出来」或「实战超预期」
    const real = Object.fromEntries((cog.insights?.powers ?? []).map(x => [x.key, x.accuracy ?? 0]))
    const green = cssVar('--green', '#22c55e')
    c.setOption({
      backgroundColor: 'transparent',
      legend: { bottom: 0, itemWidth: 12, itemHeight: 8, textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
      tooltip: {},
      radar: {
        indicator: POWERS.map(k => ({ name: FivePowerLabels[k], max: 100 })), radius: 85, center: ['50%', '47%'],
        axisName: { color: cssVar('--text-2', '#888'), fontSize: 12 },
        splitLine: { lineStyle: { color: 'rgba(128,128,128,0.22)' } }, splitArea: { show: false }, axisLine: { lineStyle: { color: 'rgba(128,128,128,0.22)' } },
      },
      series: [{
        type: 'radar',
        data: [
          { name: '测试得分', value: POWERS.map(k => cog.final?.[k] ?? 0), lineStyle: { color: primary, width: 2 }, itemStyle: { color: primary }, areaStyle: { color: primary, opacity: 0.18 } },
          { name: `实战正确率`, value: POWERS.map(k => real[k] ?? 0), lineStyle: { color: green, width: 2, type: 'dashed' }, itemStyle: { color: green }, areaStyle: { color: green, opacity: 0.12 } },
        ],
      }],
    })
  }
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
function onTabChange() {
  drawTab()
  // 表格在没显示的标签页里算不出列宽，切过来后通知它重新布局
  nextTick(() => window.dispatchEvent(new Event('resize')))
}

async function load() {
  loading.value = true
  try {
    p.value = await studentApi.getProfile(studentId, dateRange.value[0], dateRange.value[1])
    await nextTick()
    await drawTab()
  } finally { loading.value = false }
}

function onResize() { charts.forEach(c => c.resize()) }
onMounted(() => { load(); window.addEventListener('resize', onResize) })
onBeforeUnmount(() => { window.removeEventListener('resize', onResize); charts.forEach(c => c.dispose()) })
</script>

<style lang="scss" scoped>
.page-root { gap: 15px; scrollbar-width: none; &::-webkit-scrollbar { display: none; } }
// 暗色主题下全局 --text-3 (#4B5563) 在深色底上偏暗：本页的次要文字（指标名、提示、脚注、空状态等）统一提亮，仍比 --text-2 暗一档
:global([data-theme="dark"]) .page-root { --text-3: #7A8496; }

.form-topbar { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.form-topbar :deep(.el-button + .el-button) { margin-left: 0; }

.section-block {
  padding: 5px 15px 15px;
  flex-shrink: 0;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;
}
.kpi-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 15px; flex-shrink: 0; @media (max-width: 1100px) { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
// 顶部统计小卡片（参考图）：深海军蓝底，左上略亮；1px 渐变描边（四角亮、边中淡）；
// 右侧约一半宽、整卡高的区域铺细方格（向左淡出），迷你图画在方格上；标题灰蓝、数字用等宽字体、较大较细
.kpi { position: relative; display: flex; align-items: stretch; min-width: 0; min-height: 96px; padding: 14px 16px; border-radius: 6px; overflow: hidden;
  --spark: #8b9bff; --grid: rgba(190, 200, 255, 0.09); --edge-a: rgba(200, 210, 255, 0.32); --edge-b: rgba(200, 210, 255, 0.06);
  background:
    radial-gradient(180px circle at 6% 0%, rgba(110, 122, 200, 0.22), transparent 72%),
    linear-gradient(165deg, rgba(24, 28, 50, 0.86), rgba(13, 15, 28, 0.90));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.04);
  &::before { content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px; pointer-events: none; z-index: 2;
    background: linear-gradient(150deg, var(--edge-a), var(--edge-b) 34%, var(--edge-b) 66%, var(--edge-a));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite: xor; mask-composite: exclude; }
  &__txt { position: relative; z-index: 1; min-width: 0; display: flex; flex-direction: column; }
  &__lbl { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--text-3); white-space: nowrap; }
  &__val { margin-top: 8px; font-size: 32px; line-height: 1.1; font-weight: 400; letter-spacing: -0.03em; color: var(--text-1); white-space: nowrap; }
  &__delta { margin-top: auto; padding-top: 4px; min-height: 22px; font-size: 12px; color: var(--text-3); .delta { font-size: 12px; } }
  &__viz { position: absolute; z-index: 0; right: 0; top: 0; bottom: 0; width: 46%; padding: 22px 16px 20px 12px;
    &::before { content: ''; position: absolute; inset: 0; z-index: -1; pointer-events: none;
      background: linear-gradient(var(--grid) 1px, transparent 1px) 0 0 / 100% 22px, linear-gradient(90deg, var(--grid) 1px, transparent 1px) 0 0 / 22px 100%;
      -webkit-mask-image: linear-gradient(90deg, transparent, #000 55%); mask-image: linear-gradient(90deg, transparent, #000 55%); } } }
:global(html[data-theme="light"]) .page-root .kpi {
  --spark: var(--color-primary); --spark-hi: #cdd9ff; --grid: rgba(94, 141, 249, 0.16); --edge-a: rgba(94, 141, 249, 0.42); --edge-b: rgba(94, 141, 249, 0.10);
  background:
    radial-gradient(180px circle at 6% 0%, rgba(124, 112, 255, 0.14), transparent 72%),
    linear-gradient(165deg, rgba(244, 247, 255, 0.96), rgba(252, 253, 255, 0.92));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9); }
.delta { display: inline-flex; align-items: center; gap: 2px; font-size: 13px; font-weight: 600; color: var(--text-3); cursor: default;
  &--up { color: var(--green); } &--down { color: var(--red); }
  &__down { transform: rotate(180deg); } }
.tone--good { color: var(--green) !important; }
.tone--warn { color: var(--amber) !important; }
:global(.st-popper) { max-width: 480px; line-height: 1.6; }
.part__help { color: var(--text-3); cursor: help; &:hover { color: var(--color-primary); } }

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
.two-col--stack { grid-template-columns: minmax(0, 1fr) !important; }
.two-col > div, .three-col > div, .cog-grid > div { min-width: 0; }   // 否则表格的最小列宽会把网格撑宽
.three-col { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 24px; @media (max-width: 1200px) { grid-template-columns: 1fr; } }
.mini-table { width: 100%; }

// 题型图标颜色同训练题管理「题目类型」列
.qt-i { flex-shrink: 0; color: var(--text-3);
  &--SINGLE_CHOICE { color: var(--qt-single); } &--MULTIPLE_CHOICE { color: var(--qt-multi); }
  &--FILL_BLANK { color: var(--qt-fill); } &--TRUE_FALSE { color: var(--qt-judge); } &--APPLICATION { color: var(--qt-application); } }

// ── 认知能力 ─────────────────────────────────────────────
.cog-grid { display: grid; grid-template-columns: minmax(0, 1fr) minmax(0, 1fr); gap: 24px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.radar-chart { height: 270px; }
.history-chart { height: 270px; }
.cog-table :deep(.el-table__cell) { padding: 6px 0; }
.cog-bar { display: flex; align-items: center; gap: 8px; font-size: 13px; color: var(--text-1); .bar { flex: 1; min-width: 36px; } small { font-size: 11px; color: var(--text-3); } }
.bar__fill--real { background: var(--green); }
.cog-chip { display: inline-block; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; cursor: default;
  &--below { background: color-mix(in srgb, var(--red) 16%, transparent); color: var(--red); }
  &--above { background: color-mix(in srgb, var(--green) 16%, transparent); color: var(--green); }
  &--ok, &--few { background: color-mix(in srgb, var(--text-3) 18%, transparent); color: var(--text-3); } }
.cog-compare { margin-top: 15px; }
.cog-hl { margin-top: 15px; }
.hl-item { position: relative; padding-left: 14px; margin-bottom: 5px; font-size: 13px; line-height: 1.7; color: var(--text-1);
  &__dot { position: absolute; left: 2px; top: 9px; width: 6px; height: 6px; border-radius: 50%; background: currentColor; } }
.mis-item { margin-bottom: 8px; padding: 8px 10px; border: 1px solid rgba(96, 141, 248, 0.15); border-radius: 4px; font-size: 12.5px; line-height: 1.6; color: var(--text-1); }
.cause-mini { font-size: 12px; color: var(--text-2); white-space: nowrap; }
.trend-tag { font-size: 12px; font-weight: 600; &.trend--up { color: var(--green); } &.trend--flat { color: var(--amber); } &.trend--down { color: var(--red); } }
.diag-hd { margin-bottom: 8px; font-size: 13px; color: var(--text-2); b { margin-left: 6px; font-size: 18px; color: var(--text-1); } small { margin-left: 6px; font-size: 12px; color: var(--text-3); } }
.cause-label { width: 130px; }
.bar__fill--warn { background: var(--amber); }
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
