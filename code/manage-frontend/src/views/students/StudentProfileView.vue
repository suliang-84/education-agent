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
      <el-button class="btn-back" @click="$router.push(`/students/${studentId}/ai-prompt`)">
        <SvgIcon name="summary" :size="14" style="margin-right:4px" />摘要
      </el-button>
      <el-button class="btn-back" @click="load">
        <SvgIcon name="analyse" :size="14" style="margin-right:4px" />刷新
      </el-button>
    </div>

    <template v-if="p">
      <!-- 基础档案 + 综合评估 -->
      <!-- 顶部统计小卡片 -->
      <div v-if="p.kpis?.length" class="kpi-strip">
        <div v-for="k in p.kpis" :key="k.key" class="kpi" :class="{ 'kpi--link': DETAIL_KEYS.includes(k.key), 'kpi--active': activeKpi === k.key }" @click="pickKpi(k.key)">
          <div class="kpi__txt">
            <div class="kpi__lbl">{{ k.label }}
              <el-tooltip :content="k.tip" placement="top" :show-after="150" popper-class="st-popper">
                <SvgIcon name="help" :size="12" class="part__help" />
              </el-tooltip>
            </div>
            <div class="kpi__val num">{{ splitUnit(k.value).num }}<small v-if="splitUnit(k.value).unit" class="kpi__unit">{{ splitUnit(k.value).unit }}</small></div>
            <div class="kpi__delta">
              <span v-if="k.delta != null && k.delta !== 0" class="delta" :class="kpiTone(k)" :title="`较前一周期${k.delta > 0 ? '上升' : '下降'} ${Math.abs(k.delta)}${k.unit === '%' ? ' 个百分点' : k.unit}`">
                <SvgIcon name="arrow_up" :size="11" :class="{ 'delta__down': k.delta < 0 }" />{{ Math.abs(k.delta) }}{{ k.unit }}
              </span>
              <span v-else-if="k.delta === 0" class="delta">持平</span>
              <span v-else>&nbsp;</span>
            </div>
          </div>
          <div class="kpi__viz" :class="{ 'kpi__viz--dots': KPI_VIZ[k.key] === 'dots', 'kpi__viz--ring': KPI_VIZ[k.key] === 'ring' }"><KpiSpark :kind="KPI_VIZ[k.key] ?? 'bars'" :gid="`kpi-${k.key}`" /></div>
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

      <!-- ═══ 中间明细区：跟着顶部统计卡当前选中的维度切换（activeKpi）═══ -->
      <!-- 上面一行：4 张统计卡（detailStats 按维度取）| 右边一张图（学习时长：学科分布；训练次数：次数趋势） -->
      <template v-if="DETAIL_KEYS.includes(activeKpi)">
      <div class="chart-row" :class="{ 'chart-row--3': activeKpi === 'answered' || activeKpi === 'accuracy' }">
        <div v-if="activeKpi !== 'accuracy'" class="stat-grid">
          <div v-for="x in detailStats" :key="x.label" class="kpi kpi--plain" :title="x.hint">
            <div class="kpi__txt">
              <div class="kpi__lbl">{{ x.label }}</div>
              <div class="kpi__val num">{{ splitUnit(x.value).num }}<small v-if="splitUnit(x.value).unit" class="kpi__unit">{{ splitUnit(x.value).unit }}</small></div>
              <div class="kpi__delta">
                <span v-if="x.delta != null && x.delta !== 0" class="delta" :class="kpiTone(x)" :title="`较前一周期${x.delta > 0 ? '上升' : '下降'} ${Math.abs(x.delta)}${x.unit}`">
                  <SvgIcon name="arrow_up" :size="11" :class="{ 'delta__down': x.delta < 0 }" />{{ Math.abs(x.delta) }}{{ x.unit }}
                </span>
                <span v-else-if="x.delta === 0" class="delta">持平</span>
                <span v-else>&nbsp;</span>
              </div>
            </div>
            <div class="kpi__viz"><KpiSpark :kind="x.viz" :gid="`st-${x.viz}`" /></div>
          </div>
        </div>
        <!-- 正确率：正确率趋势（整体 + 各科），占统计卡的位置 -->
        <div v-else class="chart-card">
          <div class="chart-card__title">正确率趋势</div>
          <div v-if="p.accuracy?.has_data && p.accuracy.trend" ref="accTrendRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无答题记录</div>
        </div>
        <!-- AI 提问：提问趋势（提问数 + 顿悟数） -->
        <div v-if="activeKpi === 'ai_asks'" class="chart-card">
          <div class="chart-card__title">提问趋势</div>
          <div v-if="p.ai_asks?.has_data" ref="aiTrendRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无 AI 提问</div>
        </div>
        <!-- 学习时长：学科学习时长分布 -->
        <div v-else-if="activeKpi === 'study_time'" class="chart-card">
          <div class="chart-card__title">学科学习时长分布</div>
          <div v-if="p.study_time?.has_data" ref="studyRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无学习记录</div>
        </div>
        <!-- 训练次数：次数分布（按科目堆叠） -->
        <div v-else-if="activeKpi === 'sessions'" class="chart-card">
          <div class="chart-card__title">训练次数分布</div>
          <div v-if="p.training?.has_data" ref="sessTrendRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无训练记录</div>
        </div>
        <!-- 答题数：各科目答题数 | 答题类型分布（按科目切换） -->
        <template v-else-if="activeKpi === 'answered'">
          <div class="chart-card">
            <div class="chart-card__title">科目答题数统计</div>
            <div v-if="p.answers?.has_data" ref="ansSubjRef" class="chart-card__body" />
            <div v-else class="chart-card__empty">{{ rangeLabel }}暂无答题记录</div>
          </div>
          <div class="chart-card">
            <div class="chart-card__head">
              <div class="chart-card__title">答题类型分布</div>
              <div v-if="ansTypeSubjects.length" class="seg" role="tablist">
                <button v-for="sj in ansTypeSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': ansTypeCode === sj.code }" @click="ansTypeSubject = sj.code">{{ sj.name }}</button>
              </div>
            </div>
            <div v-if="ansTypeItems.length" ref="ansTypeRef" class="chart-card__body" />
            <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无答题记录</div>
          </div>
        </template>
        <!-- 正确率：难度正确率（按科目切换）| 题型正确率（按科目切换） -->
        <template v-else>
          <div class="chart-card">
            <div class="chart-card__head">
              <div class="chart-card__title">难度正确率</div>
              <div v-if="accDiffSubjects.length" class="seg" role="tablist">
                <button v-for="sj in accDiffSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': accDiffCode === sj.code }" @click="accDiffSubject = sj.code">{{ sj.name }}</button>
              </div>
            </div>
            <div v-if="accDiffItems.length" ref="accDiffRef" class="chart-card__body" />
            <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无答题记录</div>
          </div>
          <div class="chart-card">
            <div class="chart-card__head">
              <div class="chart-card__title">题型正确率</div>
              <div v-if="accTypeSubjects.length" class="seg" role="tablist">
                <button v-for="sj in accTypeSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': accTypeCode === sj.code }" @click="accTypeSubject = sj.code">{{ sj.name }}</button>
              </div>
            </div>
            <div v-if="accTypeItems.length" ref="accTypeRef" class="chart-card__body" />
            <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无答题记录</div>
          </div>
        </template>
      </div>

      <!-- 下面一行：3 张卡 -->
      <div v-if="activeKpi === 'study_time'" class="detail-row">
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">类型时长分布</div>
            <div v-if="typeSubjects.length" class="seg" role="tablist">
              <button v-for="sj in typeSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': typeCode === sj.code }" @click="typeSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="typeItems.length" ref="studyTypeRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无学习记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">知识点学习时长Top5</div>
            <div v-if="kpSubjects.length" class="seg" role="tablist">
              <button v-for="sj in kpSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': kpCode === sj.code }" @click="kpSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="kpItems.length" class="chart-card__body kp-list">
            <div v-for="(x, i) in kpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.minutes / kpMax * 100) + '%', background: SUBJECT_COLORS[kpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num">{{ fmtMin(x.minutes) }}</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点学习记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">建议</div>
          <div v-if="behaviorTips.length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in behaviorTips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无学习记录</div>
        </div>
      </div>
      <div v-else-if="activeKpi === 'sessions'" class="detail-row">
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">练习方式次数分布</div>
            <div v-if="sessTypeSubjects.length" class="seg" role="tablist">
              <button v-for="sj in sessTypeSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': sessTypeCode === sj.code }" @click="sessTypeSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="sessTypeItems.length" ref="sessTypeRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无训练记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">知识点训练次数Top5</div>
            <div v-if="tkpSubjects.length" class="seg" role="tablist">
              <button v-for="sj in tkpSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': tkpCode === sj.code }" @click="tkpSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="tkpItems.length" class="chart-card__body kp-list">
            <div v-for="(x, i) in tkpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.count / tkpMax * 100) + '%', background: SUBJECT_COLORS[tkpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num" :title="`其中完成 ${x.done} 次`">{{ x.count }} 次</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点训练记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">建议</div>
          <div v-if="p.training?.tips?.length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in p.training.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无训练记录</div>
        </div>
      </div>
      <!-- 答题数下面一行：难度分布（按科目切换）| 知识点答题数 Top5（按科目切换）| 总结。列宽、行高和学习时长、训练次数那两屏的第三行完全一致 -->
      <div v-else-if="activeKpi === 'answered'" class="detail-row">
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">难度分布</div>
            <div v-if="ansDiffSubjects.length" class="seg" role="tablist">
              <button v-for="sj in ansDiffSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': ansDiffCode === sj.code }" @click="ansDiffSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="ansDiffItems.length" ref="ansDiffRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无答题记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">知识点答题数Top5</div>
            <div v-if="akpSubjects.length" class="seg" role="tablist">
              <button v-for="sj in akpSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': akpCode === sj.code }" @click="akpSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="akpItems.length" class="chart-card__body kp-list">
            <div v-for="(x, i) in akpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.count / akpMax * 100) + '%', background: SUBJECT_COLORS[akpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num" :title="`答对 ${x.correct} 题，正确率 ${x.accuracy ?? 0}%`">{{ x.count }} 题</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点答题记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="p.answers?.tips?.length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in p.answers.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无答题记录</div>
        </div>
      </div>
      <!-- 正确率下面一行：科目正确率 | 知识点正确率 Top5（按科目切换，薄弱 / 强项）| 总结 -->
      <!-- AI 提问下面一行：提问时段分布 | 启发策略使用 Top5 | 总结 -->
      <div v-else-if="activeKpi === 'ai_asks'" class="detail-row">
        <div class="chart-card">
          <div class="chart-card__title">提问时段分布</div>
          <div v-if="p.ai_asks?.has_data" ref="aiPeriodRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无 AI 提问</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">启发策略使用Top5</div>
          <div v-if="p.ai_asks?.strategies?.length" class="chart-card__body kp-list">
            <div v-for="(x, i) in p.ai_asks.strategies" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.uses / aiStrategyMax * 100) + '%', background: SUBJECT_COLORS.MATH }" /></div>
              <span class="kp-row__val num" :title="`点赞 ${x.likes} · 点踩 ${x.dislikes}`">{{ x.uses }} 次</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}助教暂未使用启发策略</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="p.ai_asks?.tips?.length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in p.ai_asks.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无 AI 提问</div>
        </div>
      </div>
      <div v-else class="detail-row">
        <!-- 薄弱知识点 Top 5：按科目切换，表格形式，列和「学业掌握」标签页的薄弱知识点一致（占前两列的宽度） -->
        <div class="chart-card chart-card--span2">
          <div class="chart-card__head">
            <div class="chart-card__title">薄弱知识点 Top 5</div>
            <div v-if="accKpSubjects.length" class="seg" role="tablist">
              <button v-for="sj in accKpSubjects" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': accKpCode === sj.code }" @click="accKpSubject = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="accKpItems.length" class="chart-card__body">
            <el-table :data="accKpItems" size="small" class="mini-table" :max-height="204">
              <el-table-column prop="name" label="知识点" min-width="150" show-overflow-tooltip />
              <el-table-column label="错误率" width="80"><template #default="{ row }"><span class="num" style="color:var(--red)">{{ fmtPct(row.error_rate) }}</span></template></el-table-column>
              <el-table-column label="做题" width="64"><template #default="{ row }"><span class="num">{{ row.wrong }}/{{ row.count }}</span></template></el-table-column>
              <el-table-column label="错因" min-width="190">
                <template #default="{ row }">
                  <span class="cause-mini" :title="`没作答 ${row.blank} · 秒答 ${row.rush} · 认真做仍错 ${row.thoughtful}`">空答 {{ row.blank }} · 秒答 {{ row.rush }} · 认真错 {{ row.thoughtful }}</span>
                </template>
              </el-table-column>
              <el-table-column label="可能的前置" min-width="130" show-overflow-tooltip>
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
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无薄弱知识点（需做过 2 次以上、错误率 ≥ 40%）</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="p.accuracy?.tips?.length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in p.accuracy.tips" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无答题记录</div>
        </div>
      </div>
      </template>

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
                  <el-table-column label="评价" width="112">
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

          <!-- ② 学习时长 -->
          <el-tab-pane label="学习时长" name="study" lazy>
            <template v-if="p.study_time?.has_data && p.study_time.stats">
              <div class="tiles" style="grid-template-columns:repeat(5,minmax(0,1fr))">
                <div class="tile"><div class="tile__num num">{{ fmtMin(p.study_time.stats.total_minutes) }}</div>
                  <div class="tile__lbl">总时长<template v-if="p.study_time.stats.delta_pct != null">（<span class="delta" :class="p.study_time.stats.delta_pct >= 0 ? 'delta--up' : 'delta--down'">{{ p.study_time.stats.delta_pct >= 0 ? '+' : '' }}{{ p.study_time.stats.delta_pct }}%</span>）</template></div></div>
                <div class="tile"><div class="tile__num num">{{ fmtMin(p.study_time.stats.avg_per_active_day) }}</div><div class="tile__lbl">活跃日均（{{ p.study_time.stats.active_days }} 天）</div></div>
                <div class="tile"><div class="tile__num num">{{ fmtMin(p.study_time.stats.best_day?.minutes) }}</div><div class="tile__lbl">单日最长（{{ p.study_time.stats.best_day ? p.study_time.stats.best_day.date.slice(5).replace('-', '/') : '—' }}）</div></div>
                <div class="tile"><div class="tile__num num">{{ fmtMin(p.study_time.stats.avg_per_session) }}</div><div class="tile__lbl">平均每次训练</div></div>
                <div class="tile"><div class="tile__num num">{{ fmtMin(p.study_time.stats.weekday_avg) }} / {{ fmtMin(p.study_time.stats.weekend_avg) }}</div><div class="tile__lbl">工作日 / 周末日均</div></div>
              </div>
              <div class="two-col" style="margin-top:10px">
                <div>
                  <div class="sub-title">学科学习时长分布</div>
                  <div v-for="x in p.study_time.subjects" :key="x.code" class="rate-row">
                    <span class="rate-row__label"><i class="subj-dot" :style="{ background: SUBJECT_COLORS[x.code] ?? SUBJECT_COLORS.OTHER }" />{{ x.name }}</span>
                    <div class="bar"><div class="bar__fill" :style="{ width: (x.share ?? 0) + '%', background: SUBJECT_COLORS[x.code] ?? SUBJECT_COLORS.OTHER }" /></div>
                    <span class="num">{{ fmtMin(x.minutes) }}　{{ x.share ?? 0 }}%</span>
                  </div>
                </div>
                <div v-if="p.study_time.highlights?.length">
                  <div class="sub-title">学习时长洞察</div>
                  <div v-for="(h, i) in p.study_time.highlights" :key="i" class="hl-item"><span class="hl-item__dot" :class="`tone--${h.tone}`" />{{ h.text }}</div>
                </div>
              </div>
            </template>
            <div v-else class="empty">{{ rangeLabel }}还没有足够的学习记录</div>
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
import { ref, computed, watch, nextTick, onMounted, onBeforeUnmount } from 'vue'
import { useRoute } from 'vue-router'
import * as echarts from 'echarts'
import { studentApi } from '@/api'
import { ElMessage } from 'element-plus'
import type { StudentProfile, ProfileWarning, FivePower } from '@/types'
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
// 5 张统计卡各用一种固定图案（纯装饰，不随统计数据变化），互不重复：起伏面积（W 形）/ 蜡烛 / 声波 / 圆环 / 点阵柱
const KPI_VIZ: Record<string, 'bars' | 'wave' | 'dots' | 'ring' | 'swing'> = { study_time: 'swing', sessions: 'bars', answered: 'wave', accuracy: 'ring', ai_asks: 'dots' }
// 学科色：定义在下方非 scoped 样式块的 --subj-* 变量里（亮 / 暗各一套，随主题切换）。模板直接用 var()，图表用 subjColor() 取实际色值
const SUBJECT_COLORS: Record<string, string> = { MATH: 'var(--subj-math)', PHYSICS: 'var(--subj-physics)', CHEMISTRY: 'var(--subj-chemistry)', OTHER: 'var(--subj-other)' }
const SUBJECT_CODES = ['MATH', 'PHYSICS', 'CHEMISTRY']
const SUBJECT_FALLBACK: Record<string, string> = { MATH: '#e4e7fb', PHYSICS: '#9aa3dc', CHEMISTRY: '#5c6499', OTHER: '#444a66' }
function subjColor(code: string) {
  const k = code in SUBJECT_FALLBACK ? code : 'OTHER'
  return cssVar(`--subj-${k.toLowerCase()}`, SUBJECT_FALLBACK[k])
}
// 「1.5 小时」「78.0%」拆成数字和单位，单位用小一号的字显示
function splitUnit(v: string) {
  const m = /^([-\d.,]+)\s*(.*)$/.exec(v ?? '')
  return m ? { num: m[1], unit: m[2] } : { num: v ?? '', unit: '' }
}
// 分钟 → 「45 分钟」「1.6 小时」；空值显示 —
function fmtMin(m?: number | null) {
  if (m == null) return '—'
  return m < 60 ? `${Math.round(m * 10) / 10} 分钟` : `${Math.round(m / 6) / 10} 小时`
}
// 练习方式的颜色（和小程序「练习方式」同一批名称）：和学科色同一个思路，只用页面本身的蓝紫灰色阶（定义在下方非 scoped 样式块的 --type-* 变量里，亮 / 暗各一套）。
// 7 档明度会让相邻两段太像，所以相邻的练习方式一深一浅交错排，图例也分得开
const TYPE_VAR: Record<string, string> = { KNOWLEDGE_POINT: 'kp', UNIT: 'unit', ERROR_QUESTIONS: 'err', FAVORITES: 'fav', SMART: 'smart', RANDOM: 'random', SEMESTER: 'sem' }
const TYPE_FALLBACK: Record<string, string> = { kp: '#e4e7fb', unit: '#7a85c6', err: '#b4bbec', fav: '#4c5489', smart: '#9aa3dc', random: '#626ca6', sem: '#8590cc' }
function typeColor(key: string) {
  const k = TYPE_VAR[key] ?? 'sem'
  return cssVar(`--type-${k}`, TYPE_FALLBACK[k])
}
// ── 知识点 Top5（学习时长 / 训练次数共用）：标题右侧切换科目，列出所选科目在周期内排名前 5 的知识点 ──
function useKpTop<T>(subjects: () => { code: string; name: string }[] | undefined, top: () => Record<string, T[]> | undefined, valueOf: (x: T) => number) {
  const picked = ref('')
  const list = computed(() => (subjects() ?? []).filter(x => SUBJECT_CODES.includes(x.code) || (top()?.[x.code]?.length ?? 0) > 0))
  // 当前科目：点过就用点的；没点过（或换了日期范围后这个科目没了）默认第一个有数据的科目，都没有就第一个
  const code = computed(() => {
    if (list.value.some(x => x.code === picked.value)) return picked.value
    return (list.value.find(x => (top()?.[x.code]?.length ?? 0) > 0) ?? list.value[0])?.code ?? ''
  })
  const items = computed(() => top()?.[code.value] ?? [])
  const max = computed(() => Math.max(1, ...items.value.map(valueOf)))
  return { picked, list, code, items, max }
}
const { picked: kpSubject, list: kpSubjects, code: kpCode, items: kpItems, max: kpMax } =
  useKpTop(() => p.value?.study_time?.subjects, () => p.value?.study_time?.kp_top, x => x.minutes)
// 答题数：答题类型分布 / 难度分布 / 知识点答题数 Top5，各自按科目切换
const { picked: ansTypeSubject, list: ansTypeSubjects, code: ansTypeCode, items: ansTypeItems } =
  useKpTop(() => p.value?.answers?.subjects, () => p.value?.answers?.types_by_subject, x => x.count)
const { picked: ansDiffSubject, list: ansDiffSubjects, code: ansDiffCode, items: ansDiffItems } =
  useKpTop(() => p.value?.answers?.subjects, () => p.value?.answers?.difficulty_by_subject, x => x.count)
const { picked: akpSubject, list: akpSubjects, code: akpCode, items: akpItems, max: akpMax } =
  useKpTop(() => p.value?.answers?.subjects, () => p.value?.answers?.kp_top, x => x.count)
// 正确率：题型正确率 / 难度正确率 / 薄弱知识点 Top 5（表格），各自按科目切换
const { picked: accTypeSubject, list: accTypeSubjects, code: accTypeCode, items: accTypeItems } =
  useKpTop(() => p.value?.accuracy?.subjects, () => p.value?.accuracy?.types_by_subject, x => x.count)
const { picked: accDiffSubject, list: accDiffSubjects, code: accDiffCode, items: accDiffItems } =
  useKpTop(() => p.value?.accuracy?.subjects, () => p.value?.accuracy?.difficulty_by_subject, x => x.count)
const { picked: accKpSubject, list: accKpSubjects, code: accKpCode, items: accKpItems } =
  useKpTop(() => p.value?.accuracy?.subjects, () => p.value?.accuracy?.weak_by_subject, x => x.error_rate ?? 0)
// 练习方式次数分布（训练次数）：同样按科目区分
const { picked: sessTypeSubject, list: sessTypeSubjects, code: sessTypeCode, items: sessTypeItems } =
  useKpTop(() => p.value?.training?.subjects, () => p.value?.training?.types_by_subject, x => x.count)
// 类型时长分布：按科目区分，标题右侧切换科目，环形图显示所选科目各练习方式的时长
const { picked: typeSubject, list: typeSubjects, code: typeCode, items: typeItems } =
  useKpTop(() => p.value?.study_time?.subjects, () => p.value?.study_time?.types_by_subject, x => x.minutes)
const { picked: tkpSubject, list: tkpSubjects, code: tkpCode, items: tkpItems, max: tkpMax } =
  useKpTop(() => p.value?.training?.subjects, () => p.value?.training?.kp_top, x => x.count)
type StatCard = { label: string; value: string; delta: number | null; unit: string; good: 'up' | 'down' | null; viz: 'dial' | 'ridge' | 'bubbles' | 'tide'; hint?: string }
const studyStats = computed(() => {
  const st = p.value?.study_time?.stats
  const bd = st?.best_day
  // 单日最长：较前一段同样长度时间的变化（分钟，和顶部统计卡同口径：各自四舍五入后相减）；前一段没有学习记录则不显示
  const bestDelta = bd && st?.prev_best_minutes != null ? Math.round(bd.minutes) - Math.round(st.prev_best_minutes) : null
  const cards: StatCard[] = [
    { label: '平均每次训练时长', value: fmtMin(st?.avg_per_session), delta: null, unit: '分钟', good: 'up', viz: 'dial' },
    { label: bd ? `单日最长学习时长（${bd.date.slice(5).replace('-', '/')}）` : '单日最长学习时长', value: fmtMin(bd?.minutes), delta: bestDelta, unit: '分钟', good: 'up', viz: 'ridge' },
    { label: '周末日均学习时长', value: fmtMin(st?.weekend_avg), delta: null, unit: '分钟', good: 'up', viz: 'bubbles' },
    { label: '非周末日均学习时长', value: fmtMin(st?.weekday_avg), delta: null, unit: '分钟', good: 'up', viz: 'tide' },
  ]
  return cards
})
// 训练次数的 4 张统计卡。涨跌 = 较前一段同样长度时间的变化；前一段没有数据（或样本太少）则不显示涨跌
//   日均训练次数 = 训练次数 ÷ 所选范围的天数（没训练的天也算）；训练答题完成度 = 作答题数 ÷ 下发题数；平均每次作答题数只算作答了的训练
const diff1 = (a: number | null | undefined, b: number | null | undefined) => (a == null || b == null ? null : Math.round((a - b) * 10) / 10)
const sessionStats = computed<StatCard[]>(() => {
  const st = p.value?.training?.stats
  const bd = st?.best_day
  return [
    { label: '日均训练次数', value: st ? `${st.avg_per_day} 次` : '—', delta: diff1(st?.avg_per_day, st?.prev_avg_per_day), unit: '次', good: 'up', viz: 'tide' },
    { label: bd ? `单日最多训练次数（${bd.date.slice(5).replace('-', '/')}）` : '单日最多训练次数', value: bd ? `${bd.count} 次` : '—', delta: bd && st?.prev_best_count != null ? bd.count - st.prev_best_count : null, unit: '次', good: 'up', viz: 'ridge' },
    { label: '训练答题完成度', value: st?.completion != null ? `${st.completion}%` : '—', delta: diff1(st?.completion, st?.prev_completion), unit: '%', good: 'up', viz: 'dial' },
    { label: '平均每次作答题数', value: st?.avg_answered != null ? `${st.avg_answered} 题` : '—', delta: diff1(st?.avg_answered, st?.prev_avg_answered), unit: '题', good: 'up', viz: 'bubbles' },
  ]
})
// AI 提问的 4 张统计卡：提问次数 = 学生发的消息数；对话次数 = 有消息的会话数；顿悟次数 = 助教回复里被标成顿悟的；场均提问 = 提问数 ÷ 对话次数
const aiStats = computed<StatCard[]>(() => {
  const st = p.value?.ai_asks?.stats
  return [
    { label: '提问次数', value: st ? `${st.total} 次` : '—', delta: st ? st.total - st.prev_total : null, unit: '次', good: 'up', viz: 'bars' },
    { label: '对话次数', value: st ? `${st.sessions} 次` : '—', delta: st ? st.sessions - st.prev_sessions : null, unit: '次', good: 'up', viz: 'bubbles' },
    { label: '顿悟次数', value: st ? `${st.aha} 次` : '—', delta: st ? st.aha - st.prev_aha : null, unit: '次', good: 'up', viz: 'ring' },
    { label: '场均提问数', value: st?.avg_ask != null ? `${st.avg_ask} 问` : '—', delta: diff1(st?.avg_ask, st?.prev_avg_ask), unit: '问', good: 'up', viz: 'ridge' },
  ]
})
const aiStrategyMax = computed(() => Math.max(1, ...(p.value?.ai_asks?.strategies ?? []).map(x => x.uses)))
// 答题数的 4 张统计卡：错题 / 顽固错题 / 收藏都是「当前状态」，不随日期范围变，所以没有涨跌；悬停看各科各是多少
//   待攻克 = 还没攻克的错题；已攻克 = 已经攻克的错题；顽固 = 同一道题错 3 次以上；收藏 = 收藏的题
const answerStats = computed<StatCard[]>(() => {
  const st = p.value?.answers?.stats
  const subs = p.value?.answers?.subjects ?? []
  const hint = (k: 'pending' | 'mastered' | 'stubborn' | 'favorites') =>
    subs.filter(x => SUBJECT_CODES.includes(x.code)).map(x => `${x.name} ${st?.breakdown?.[x.code]?.[k] ?? 0}`).join(' · ')
  const val = (n: number | undefined) => (n == null ? '—' : `${n} 题`)
  return [
    { label: '待攻克错题', value: val(st?.wrong_pending), delta: null, unit: '题', good: 'down', viz: 'ridge', hint: hint('pending') },
    { label: '已攻克错题', value: val(st?.wrong_mastered), delta: null, unit: '题', good: 'up', viz: 'dial', hint: hint('mastered') },
    { label: '顽固错题', value: val(st?.stubborn), delta: null, unit: '题', good: 'down', viz: 'tide', hint: hint('stubborn') },
    { label: '收藏题数', value: val(st?.favorites), delta: null, unit: '题', good: 'up', viz: 'bubbles', hint: hint('favorites') },
  ]
})
// 中间明细区上面那 4 张统计卡：跟着顶部选中的维度走
const detailStats = computed(() => (activeKpi.value === 'ai_asks' ? aiStats.value : activeKpi.value === 'sessions' ? sessionStats.value : activeKpi.value === 'answered' ? answerStats.value : studyStats.value))
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
// 近 N 天：到昨天为止，不含今天（今天还没过完，数据不完整）
const lastDays = (n: number): [string, string] => [ymd(daysAgo(n)), ymd(daysAgo(1))]
const dateRange = ref<[string, string]>(lastDays(7))
const rangeShortcuts = [
  { text: '近一周', value: () => lastDays(7) },
  { text: '近一个月', value: () => lastDays(30) },
]
const disableFuture = (d: Date) => d.getTime() > Date.now()
// 变大是好事的指标：上升绿 / 下降红；变小是好事的（空答率等）反过来；没有好坏的（每题用时）用灰色
function kpiTone(k: { delta: number | null; good: 'up' | 'down' | null }) {
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
const studyRef = ref<HTMLElement>()
const studyTypeRef = ref<HTMLElement>()
const sessTrendRef = ref<HTMLElement>()
const sessTypeRef = ref<HTMLElement>()
const ansSubjRef = ref<HTMLElement>()
const ansTypeRef = ref<HTMLElement>()
const ansDiffRef = ref<HTMLElement>()
const accTrendRef = ref<HTMLElement>()
const aiTrendRef = ref<HTMLElement>()
const aiPeriodRef = ref<HTMLElement>()
const accTypeRef = ref<HTMLElement>()
const accDiffRef = ref<HTMLElement>()
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
// 建议：接口 study_time.highlights 返回的学习时长结论（如「时间分配比较均衡，数学占 62.8%」）
const behaviorTips = computed(() => (p.value?.study_time?.highlights ?? []).map(h => h.text))
const cogInsights = computed(() => p.value?.cognitive.insights)

const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v}%`)

// 图表主色：暗色主题用偏灰的薰衣草蓝紫（和页面强调色一致），亮色主题沿用系统主色
function accent() {
  return document.documentElement.dataset.theme === 'dark' ? '#9aa4ef' : cssVar('--color-primary', '#608df9')
}
function cssVar(name: string, fallback: string) {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim() || fallback
}
function initChart(el?: HTMLElement) {
  if (!el) return null
  const old = echarts.getInstanceByDom(el)
  if (old) {
    old.dispose()
    const i = charts.indexOf(old); if (i >= 0) charts.splice(i, 1)
    dimCharts = dimCharts.filter(x => x !== old)
  }
  const c = echarts.init(el)
  charts.push(c)
  return c
}
// 中间明细区（跟着顶部选中的维度切换）的图表：切维度时整块 DOM 会被换掉，要把旧图表销毁
let dimCharts: echarts.ECharts[] = []
function initDimChart(el?: HTMLElement) {
  const c = initChart(el)
  if (c) dimCharts.push(c)
  return c
}
function disposeDimCharts() {
  dimCharts.forEach(c => { c.dispose(); const i = charts.indexOf(c); if (i >= 0) charts.splice(i, 1) })
  dimCharts = []
}

function renderRadar() {
  const c = initChart(radarRef.value)
  const cog = p.value?.cognitive
  if (!c || !cog?.has_profile) return
  const primary = accent()
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

// 三张学习时长图（趋势 / 学科堆叠 / 时段）。图表一直在页面上，数据加载完就画
function renderStudy() {
  const t = p.value?.study_time
  if (!t?.has_data || !t.series || !t.subjects) return
  const series = t.series
  renderSubjectStack(studyRef.value, {
    subjects: t.subjects, labels: series.map(x => x.label), barWidth: 15, axisName: '分钟', fmt: fmtMin,
    valueOf: (i, code) => series[i].minutes[code] ?? 0, totalOf: i => series[i].total, titleOf: i => `${series[i].label}`,
  })

  renderStudyType()
}

// 类型时长环形图：所选科目各练习方式的时长，圆角分段、段间留缝，中间显示这个科目的总时长
function renderStudyType() {
  const types = typeItems.value
  if (!types.length) return
  const subj = typeSubjects.value.find(x => x.code === typeCode.value)
  renderTypeDonut(studyTypeRef.value, {
    items: types.map(x => ({ key: x.key, name: x.label, value: x.minutes, extra: x })),
    centerText: fmtMin(types.reduce((n, x) => n + x.minutes, 0)), centerSub: `${subj?.name ?? ''}学习时长`,
    legend: x => `${x.name}  ${(x.extra as { share: number | null }).share ?? 0}%`,
    tooltip: x => `${x.name}<br/>${fmtMin(x.value)}（${x.percent}%）<br/>${(x.extra as { sessions: number }).sessions} 次训练`,
  })
}

// 练习方式 / 难度环形图（学习时长 / 训练次数 / 答题数共用；每段颜色默认按练习方式取，也可以自己指定 color）：外圈细线 + 圆角分段，左边是圆环、右边是图例
function renderTypeDonut(el: HTMLElement | undefined, o: {
  items: { key: string; name: string; value: number; extra: unknown; color?: string }[]; centerText: string; centerSub: string
  legend: (x: { name: string; extra: unknown }) => string; tooltip: (x: { name: string; value: number; percent: number; extra: unknown }) => string
}) {
  const c = initDimChart(el)
  const txt3 = cssVar('--text-3', '#999')
  // 外圈细线半径 r（像素）：默认 = 86% × min(宽, 高) / 2，上下各留 7%；盒子窄时缩小，保证右边放得下图例（约 112px + 间距 12px）。
  // 圆环外缘 = 0.875 r，内缘 = 0.7625 r；细线 = 0.9875 r ~ r；细线左缘贴着图表区左边（卡片内边距 15px），所以圆心 = r
  const cw = c?.getWidth() ?? 400, ch = c?.getHeight() ?? 207
  const ringR = Math.max(40, Math.min(0.86 * Math.min(cw, ch) / 2, (cw - 112 - 12) / 2))
  const ringCx = ringR
  const RING_EXTRA = 3   // 圆环在原环宽（= 0.1125 r ≈ 10px）上再加宽 3px：外缘不动，内缘往里收
  c?.setOption({
    title: { text: o.centerText, subtext: o.centerSub, left: ringCx, top: 'middle', textAlign: 'center', itemGap: 4,
      textStyle: { color: cssVar('--text-1', '#fff'), fontSize: 20, fontWeight: 600 }, subtextStyle: { color: txt3, fontSize: 12 } },
    tooltip: { trigger: 'item', formatter: (x: { name: string; value: number; percent: number; data: { extra: unknown } }) => o.tooltip({ name: x.name, value: x.value, percent: x.percent, extra: x.data.extra }) },
    legend: { orient: 'vertical', right: 0, top: 'middle', itemWidth: 9, itemHeight: 9, itemGap: 7, icon: 'circle', textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 },
      formatter: (name: string) => { const x = o.items.find(y => y.name === name); return x ? o.legend({ name, extra: x.extra }) : name } },
    series: [
      { type: 'pie', radius: [ringR * 0.7625 - RING_EXTRA, ringR * 0.875], center: [ringCx, '50%'], padAngle: 3, avoidLabelOverlap: false, label: { show: false }, labelLine: { show: false },
        itemStyle: { borderRadius: 5 }, emphasis: { scale: false },
        data: o.items.map(x => ({ name: x.name, value: x.value, extra: x.extra, itemStyle: { color: x.color ?? typeColor(x.key) } })) },
      // 外圈一条细线，和参考图一样
      { type: 'pie', radius: [ringR * 0.9875, ringR], center: [ringCx, '50%'], silent: true, label: { show: false }, labelLine: { show: false }, tooltip: { show: false },
        data: [{ value: 1, itemStyle: { color: 'rgba(128,128,128,0.22)' } }] },
    ],
  })
}

// 按学科堆叠的柱状图（学科学习时长分布、训练次数分布共用）：学科色 + 学科之间 2px 间隙
function renderSubjectStack(el: HTMLElement | undefined, o: {
  subjects: { code: string; name: string }[]; labels: string[]; barWidth: number; axisName: string; integer?: boolean
  fmt: (v: number) => string; valueOf: (i: number, code: string) => number; totalOf: (i: number) => number; titleOf: (i: number) => string
}) {
  const c = initDimChart(el)
  const txt3 = cssVar('--text-3', '#999')
  const axis = { axisLabel: { color: txt3, fontSize: 11 }, axisLine: { lineStyle: { color: 'rgba(128,128,128,0.25)' } }, axisTick: { show: false } }
  // 学科之间留 2px 间隙：在相邻两段之间插一段不可见的占位。ECharts 堆叠柱没有「段间距」，所以先固定 y 轴上限，
  // 再按绘图区的像素高度把 2px 换算成数据量
  // GRID_BOTTOM 只用来估算绘图区高度（x 轴文字占的高度）；grid.bottom 本身是 0，文字贴着卡片底部 15px 内边距的边
  const GAP_PX = 2, GRID_TOP = 30, GRID_BOTTOM = 24
  const n = o.labels.length
  const totals = Array.from({ length: n }, (_, i) => o.totalOf(i))
  const rawMax = Math.max(1, ...totals) * 1.08
  const stepRaw = rawMax / 3, mag = 10 ** Math.floor(Math.log10(stepRaw))
  // y 轴上限取「3 个整齐刻度」：次数这类整数量用整数刻度，时长用 1 / 2 / 2.5 / 5 的倍数
  const step = o.integer
    ? ([1, 2, 3, 4, 5, 10, 20, 25, 30, 40, 50, 100, 200, 250, 500, 1000].find(m => m >= stepRaw) ?? Math.ceil(stepRaw))
    : ([1, 2, 2.5, 5, 10].find(m => m * mag >= stepRaw) ?? 10) * mag
  const yMax = step * 3
  const plotH = Math.max(60, (c?.getHeight() ?? 210) - GRID_TOP - GRID_BOTTOM)
  const gap = (GAP_PX / plotH) * yMax
  const subs = o.subjects
  const stackSeries: Record<string, unknown>[] = []
  subs.forEach((sj, i, arr) => {
    if (i > 0) {
      // 占位：这个点下面已有学科、且当前学科也有数据时才留缝
      stackSeries.push({
        name: '', type: 'bar', stack: 'sj', barWidth: o.barWidth, silent: true, tooltip: { show: false }, itemStyle: { color: 'transparent' },
        data: Array.from({ length: n }, (_, k) => (subs.slice(0, i).some(x => o.valueOf(k, x.code) > 0) && o.valueOf(k, sj.code) > 0 ? gap : 0)),
      })
    }
    stackSeries.push({
      name: sj.name, type: 'bar', stack: 'sj', barWidth: o.barWidth, data: Array.from({ length: n }, (_, k) => o.valueOf(k, sj.code)),
      itemStyle: { color: subjColor(sj.code), borderRadius: i === arr.length - 1 ? [3, 3, 0, 0] : 0 },
    })
  })
  c?.setOption({
    grid: { left: 0, right: 0, top: GRID_TOP, bottom: 0, containLabel: true },
    legend: { top: 0, data: subs.map(x => x.name), itemWidth: 10, itemHeight: 8, textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
    tooltip: {
      trigger: 'axis', axisPointer: { type: 'shadow' },
      formatter: (ps: { dataIndex: number; seriesName: string; marker: string; value: number }[]) =>
        `${o.titleOf(ps[0].dataIndex)}<br/>` + ps.filter(x => x.seriesName && x.value > 0).map(x => `${x.marker}${x.seriesName}：${o.fmt(x.value)}`).join('<br/>') + `<br/><b>合计：${o.fmt(o.totalOf(ps[0].dataIndex))}</b>`,
    },
    xAxis: { type: 'category', data: o.labels, ...axis },
    yAxis: { type: 'value', splitNumber: 3, max: yMax, ...(o.integer ? { minInterval: 1 } : {}), splitLine: { lineStyle: { color: 'rgba(160,168,220,0.14)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11 }, name: o.axisName, nameTextStyle: { color: txt3, fontSize: 11 } },
    series: stackSeries,
  })
}

// ── 训练次数明细：次数分布（按科目堆叠）、练习方式次数分布 ──
function renderSessions() {
  const t = p.value?.training
  if (!t?.has_data || !t.series || !t.types) return
  const series = t.series

  // ① 训练次数分布：每个点（按天 / 按周）按科目堆叠，学科色和学科学习时长分布一致
  renderSubjectStack(sessTrendRef.value, {
    subjects: t.subjects ?? [], labels: series.map(x => x.label), barWidth: t.unit === 'week' ? 26 : 15, axisName: '次', integer: true,
    fmt: v => `${v} 次`, valueOf: (i, code) => series[i].by_subject?.[code] ?? 0, totalOf: i => series[i].total, titleOf: i => series[i].label,
  })

  renderSessionType()
}

// ② 练习方式次数分布：所选科目各练习方式的训练次数（悬停时带「做完的占多少」：同样的次数，哪种方式更容易中途退出）
function renderSessionType() {
  const types = sessTypeItems.value
  if (!types.length) return
  const subj = sessTypeSubjects.value.find(x => x.code === sessTypeCode.value)
  renderTypeDonut(sessTypeRef.value, {
    items: types.map(x => ({ key: x.key, name: x.label, value: x.count, extra: x })),
    centerText: `${types.reduce((n, x) => n + x.count, 0)} 次`, centerSub: `${subj?.name ?? ''}训练次数`,
    legend: x => { const y = x.extra as { count: number }; return `${x.name}  ${y.count} 次` },
    tooltip: x => { const y = x.extra as { count: number; done_rate: number | null }; return `${x.name}<br/>${y.count} 次（${x.percent}%）<br/>做完的占 ${y.done_rate ?? 0}%` },
  })
}

// 胶囊柱状图（参考设计稿）：柱子两头全圆、上深下浅的渐变，虚线网格，坐标文字很淡；每根柱子可以各用各的颜色
const PILL_BAR_WIDTH = 12   // 胶囊柱的宽度（px），三张图统一
function renderPillBars(el: HTMLElement | undefined, o: { labels: string[]; values: number[]; colors: string[]; tooltip: (i: number) => string; percent?: boolean }) {
  const c = initDimChart(el)
  const txt3 = cssVar('--text-3', '#999')
  // 画布里的颜色要写成 rgba（不认 CSS 的 color-mix）：上端是学科色本身，下端是 50% 透明
  const alpha = (hex: string, a: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${a})` }
  const grad = (clr: string) => ({ type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(clr, 1) }, { offset: 1, color: alpha(clr, 0.5) }] })
  c?.setOption({
    grid: { left: 0, right: 0, top: 14, bottom: 0, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' }, formatter: (ps: { dataIndex: number }[]) => o.tooltip(ps[0].dataIndex) },
    xAxis: { type: 'category', data: o.labels, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: txt3, fontSize: 11, margin: 12 } },
    // 百分比：固定 0~100%、每 25% 一条虚线；次数：整数刻度
    yAxis: { type: 'value', ...(o.percent ? { min: 0, max: 100, interval: 25 } : { minInterval: 1, splitNumber: 3 }), splitLine: { lineStyle: { color: 'rgba(160,168,220,0.16)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11, ...(o.percent ? { formatter: (v: number) => `${v}%` } : {}) } },
    series: [{
      type: 'bar', barWidth: PILL_BAR_WIDTH, showBackground: false,
      data: o.values.map((v, i) => ({ value: v, itemStyle: { color: grad(o.colors[i]), borderRadius: 999 } })),
      emphasis: { itemStyle: { opacity: 0.85 } },
    }],
  })
}

// ── 答题数明细：科目答题数、答题类型分布、难度分布（都是胶囊柱状图）──
const ratePart = (x: { count: number; correct: number; accuracy: number | null }) => `答题 ${x.count} 题，答对 ${x.correct} 题（正确率 ${x.accuracy ?? 0}%）`
function renderAnswers() {
  const a = p.value?.answers
  if (!a?.has_data) return
  // ① 科目答题数：每个科目一根柱子，颜色用学科色
  const subs = a.subjects.filter(x => SUBJECT_CODES.includes(x.code) || x.count > 0)
  renderPillBars(ansSubjRef.value, {
    labels: subs.map(x => x.name), values: subs.map(x => x.count), colors: subs.map(x => subjColor(x.code)),
    tooltip: i => `${subs[i].name}<br/>${ratePart(subs[i])}<br/>占全部答题的 ${subs[i].share ?? 0}%`,
  })
  renderAnswerType()
  renderAnswerDiff()
}
function renderAnswerType() {
  const items = ansTypeItems.value
  if (!items.length) return
  const clr = subjColor(ansTypeCode.value)
  renderPillBars(ansTypeRef.value, {
    labels: items.map(x => x.label), values: items.map(x => x.count), colors: items.map(() => clr),
    tooltip: i => `${items[i].label}<br/>${ratePart(items[i])}`,
  })
}
// 难度分布：环形图。基础 / 进阶 / 挑战三档，颜色是 --diff-* 变量（页面蓝紫灰色阶）
const DIFF_FALLBACK: Record<string, string> = { basic: '#e4e7fb', advanced: '#9aa3dc', challenge: '#5c6499' }
function renderAnswerDiff() {
  const items = ansDiffItems.value
  if (!items.length) return
  const subj = ansDiffSubjects.value.find(x => x.code === ansDiffCode.value)
  renderTypeDonut(ansDiffRef.value, {
    items: items.map(x => ({ key: x.key, name: x.label, value: x.count, extra: x, color: cssVar(`--diff-${x.key}`, DIFF_FALLBACK[x.key] ?? '#8590cc') })),
    centerText: `${items.reduce((n, x) => n + x.count, 0)} 题`, centerSub: `${subj?.name ?? ''}答题数`,
    legend: x => { const y = x.extra as { count: number }; return `${x.name}  ${y.count} 题` },
    tooltip: x => { const y = x.extra as { count: number; correct: number; accuracy: number | null }; return `${x.name}<br/>${y.count} 题（${x.percent}%）<br/>答对 ${y.correct} 题，正确率 ${y.accuracy ?? 0}%` },
  })
}

// ── 正确率趋势（参考设计稿）──
// 合计是粗的圆点虚线，各科是亮度不同的实线；每条线下面一层向下渐隐的半透明面积；悬停时一条细竖线 + 每条线上的小圆圈（平时没有圆点）；
// x 轴文字很小很暗，悬停的那一天最亮、越远越暗，日期之间用小圆点分隔；最低的那条线下面有一团模糊的柔光。
// 暗色用黑白灰（靠亮度和虚实区分）；亮色保留学科色。某个点答题太少（后端给 null）这条线在这里断开不画，用相邻的点连起来；
// 各科的面积画得很淡（有的科目前面几天样本不足，线是从中间开始的，面积浓了起点会有一道竖切边），合计那层最明显
function renderAccuracyTrend() {
  const a = p.value?.accuracy
  const t = a?.trend
  if (!a?.has_data || !t) return
  const dark = document.documentElement.dataset.theme === 'dark'
  const txt3 = cssVar('--text-3', '#999')
  const rgba = (hex: string, al: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${al})` }
  const DARK_SUBJ: Record<string, string> = { MATH: '#5d6597', PHYSICS: '#e6e8f8', CHEMISTRY: '#8f97cf', OTHER: '#6b7186' }
  const lineClr = (code: string) => (dark ? (DARK_SUBJ[code] ?? DARK_SUBJ.OTHER) : subjColor(code))
  const totalClr = dark ? '#8b90ab' : '#475066'
  const hoverFill = dark ? '#0d0f1c' : '#ffffff'
  const fillOf = (hex: string, top: number) => ({ color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: rgba(hex, top) }, { offset: 1, color: rgba(hex, 0) }] } })
  const lineSer = (name: string, data: (number | null)[], clr: string, width: number, o: { dashed?: boolean; top: number; z: number }) => ({
    name, type: 'line', z: o.z, data, smooth: 0.55, smoothMonotone: 'x', symbol: 'none', connectNulls: true,
    lineStyle: { color: clr, width, cap: 'round', type: o.dashed ? [3, 6.5] : 'solid' }, itemStyle: { color: clr }, areaStyle: fillOf(clr, o.top),
  })
  const series = t.series
  const labels = series.map(x => x.label)
  const nPts = labels.length
  const subs = a.subjects.filter(x => SUBJECT_CODES.includes(x.code) || x.count > 0)
  const defs = [{ name: '合计', clr: totalClr, vals: series.map(x => x.accuracy) }, ...subs.map(sj => ({ name: sj.name, clr: lineClr(sj.code), vals: series.map(x => x.by_subject[sj.code]?.accuracy ?? null) }))]
  const hoverPoints = (i: number) => (i < 0 ? [] : defs.filter(d => d.vals[i] != null).map(d => ({ value: [i, d.vals[i]], itemStyle: { color: hoverFill, borderColor: dark ? '#e8eaf8' : d.clr, borderWidth: 1.6 } })))
  // 底部柔光：每个点取最低的那条学科线
  const low = series.map(x => { const v = subs.map(sj => x.by_subject[sj.code]?.accuracy).filter((y): y is number => y != null); return v.length ? Math.min(...v) : x.accuracy })
  const glowClr = dark ? '#aab0e6' : '#5e8df9'
  const glowSer = {
    name: '', type: 'line', z: 0, data: low, smooth: 0.55, smoothMonotone: 'x', symbol: 'none', connectNulls: true, silent: true, legendHoverLink: false, tooltip: { show: false },
    // 光晕：沿最低那条线的一道几乎透明的线，靠它很大的模糊阴影出光（不填充面积——正确率的线都在图的上半部分，铺面积会是一大块）
    lineStyle: { width: 8, cap: 'round', color: rgba(glowClr, dark ? 0.05 : 0.03), shadowBlur: 32, shadowColor: rgba(glowClr, dark ? 0.6 : 0.35) },
  }
  // x 轴文字：悬停那天最亮，相邻的次之，其余很暗（rich 样式按「离悬停位置的距离」取）
  const labelRich = dark
    ? { d0: { color: '#dfe2f4', fontSize: 11, fontWeight: 700 }, d1: { color: '#8b90ab', fontSize: 11 }, d2: { color: '#646a88', fontSize: 11 }, dn: { color: '#474c66', fontSize: 11 } }
    : { d0: { color: '#2d3550', fontSize: 11, fontWeight: 700 }, d1: { color: '#6b7390', fontSize: 11 }, d2: { color: '#9aa1b8', fontSize: 11 }, dn: { color: '#b9bfd0', fontSize: 11 } }
  const labelFmt = (active: number) => (v: string, idx: number) => `{${active < 0 ? 'd2' : ['d0', 'd1', 'd2'][Math.min(2, Math.abs(idx - active))] ?? 'dn'}|${v}}`
  const c = initDimChart(accTrendRef.value)
  c?.setOption({
    grid: { left: 0, right: 0, top: 30, bottom: 0, containLabel: true },
    legend: { top: 0, data: defs.map(d => d.name), itemWidth: 12, itemHeight: 3, icon: 'roundRect', textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: dark ? 'rgba(255, 255, 255, 0.28)' : 'rgba(71, 80, 102, 0.3)', width: 1, type: 'solid' } },
      backgroundColor: dark ? 'rgba(18, 20, 36, 0.92)' : 'rgba(255, 255, 255, 0.96)', borderColor: dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(94, 141, 249, 0.2)',
      textStyle: { color: dark ? '#dfe2f4' : '#2d3550', fontSize: 12 },
      formatter: (ps: { dataIndex: number; seriesName: string; marker: string; value: number | null }[]) =>
        `${labels[ps[0].dataIndex]}<br/>` + ps.filter(x => x.seriesName).map(x => `${x.marker}${x.seriesName}：${x.value == null ? '样本不足' : x.value + '%'}`).join('<br/>'),
    },
    xAxis: [
      { type: 'category', data: labels, boundaryGap: true, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { formatter: labelFmt(-1), rich: labelRich, margin: 10 } },
      { type: 'value', min: 0, max: nPts, show: false },     // 只用来摆「日期之间的小圆点」：整数位置 = 两个日期之间的边界
    ],
    yAxis: { type: 'value', min: 0, max: 100, interval: 25, axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: dark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(128, 128, 128, 0.16)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11, formatter: (v: number) => `${v}%` } },
    series: [
      glowSer,
      lineSer('合计', defs[0].vals, totalClr, 3, { dashed: true, top: dark ? 0.2 : 0.1, z: 1 }),
      ...defs.slice(1).map((d, i) => lineSer(d.name, d.vals, d.clr, d.name === '物理' && dark ? 2.4 : 1.8, { top: dark ? 0.1 : 0.05, z: 2 + i })),
      { type: 'scatter', id: 'hover', name: '', xAxisIndex: 0, yAxisIndex: 0, silent: true, z: 10, legendHoverLink: false, tooltip: { show: false }, symbol: 'circle', symbolSize: 10, data: [] },
      { type: 'scatter', name: '', xAxisIndex: 1, yAxisIndex: 0, silent: true, clip: false, z: 0, legendHoverLink: false, tooltip: { show: false },
        symbol: 'circle', symbolSize: 3, symbolOffset: [0, 17], itemStyle: { color: dark ? '#3d4260' : '#c3c9d8' },
        data: Array.from({ length: Math.max(0, nPts - 1) }, (_, i) => [i + 1, 0]) },
    ],
  })
  // 悬停时：x 轴文字跟着换亮度，每条线上出现小圆圈（updateAxisPointer 给出悬停的是第几个日期）
  let activeIdx = -1
  const setActive = (i: number) => {
    if (i === activeIdx) return
    activeIdx = i
    c?.setOption({ xAxis: [{ axisLabel: { formatter: labelFmt(i), rich: labelRich } }], series: [{ id: 'hover', data: hoverPoints(i) }] })
  }
  c?.on('updateAxisPointer', (e: { axesInfo?: { axisDim: string; axisIndex: number; value: number }[] }) => {
    const info = e.axesInfo?.find(x => x.axisDim === 'x' && x.axisIndex === 0)
    setActive(info ? Math.round(info.value) : -1)
  })
  c?.on('globalout', () => setActive(-1))
}

// ── 正确率明细：题型正确率、难度正确率（0~100% 的胶囊柱状图）──
const accPart = (x: { count: number; correct: number; accuracy: number | null }) => (x.count ? `正确率 ${x.accuracy ?? 0}%（答对 ${x.correct} / ${x.count} 题）` : '还没有答题')
function renderAccuracy() {
  const a = p.value?.accuracy
  if (!a?.has_data) return
  renderAccuracyTrend()
  renderAccuracyType()
  renderAccuracyDiff()
}
function renderAccuracyType() {
  const items = accTypeItems.value
  if (!items.length) return
  const clr = subjColor(accTypeCode.value)
  renderPillBars(accTypeRef.value, { labels: items.map(x => x.label), values: items.map(x => x.accuracy ?? 0), colors: items.map(() => clr), percent: true, tooltip: i => `${items[i].label}<br/>${accPart(items[i])}` })
}
function renderAccuracyDiff() {
  const items = accDiffItems.value
  if (!items.length) return
  const clr = subjColor(accDiffCode.value)
  renderPillBars(accDiffRef.value, { labels: items.map(x => x.label), values: items.map(x => x.accuracy ?? 0), colors: items.map(() => clr), percent: true, tooltip: i => `${items[i].label}<br/>${accPart(items[i])}` })
}

// ── AI 提问明细：提问趋势（提问数柱 + 顿悟数标记）、提问时段分布（环形图）──
function renderAiAsks() {
  const a = p.value?.ai_asks
  if (!a?.has_data) return
  const dark = document.documentElement.dataset.theme === 'dark'
  const barClr = dark ? '#9aa3dc' : '#5e8df9'
  const ahaClr = dark ? '#e6e8f8' : '#475066'
  const txt3 = cssVar('--text-3', '#999')
  const alpha = (hex: string, al: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${al})` }
  const s = a.series
  const c = initDimChart(aiTrendRef.value)
  c?.setOption({
    grid: { left: 0, right: 0, top: 30, bottom: 0, containLabel: true },
    legend: { top: 0, itemWidth: 12, itemHeight: 3, icon: 'roundRect', textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' },
      formatter: (ps: { dataIndex: number }[]) => `${s[ps[0].dataIndex].label}<br/>提问 ${s[ps[0].dataIndex].count} 次<br/>顿悟 ${s[ps[0].dataIndex].aha} 次` },
    xAxis: { type: 'category', data: s.map(x => x.label), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: txt3, fontSize: 11, margin: 12 } },
    yAxis: { type: 'value', min: 0, minInterval: 1, splitNumber: 3, splitLine: { lineStyle: { color: 'rgba(160,168,220,0.16)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11 } },
    series: [
      { name: '提问次数', type: 'bar', barWidth: a.unit === 'week' ? 26 : 15, data: s.map(x => x.count),
        itemStyle: { borderRadius: 999, color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(barClr, 1) }, { offset: 1, color: alpha(barClr, 0.5) }] } } },
      { name: '顿悟次数', type: 'line', data: s.map(x => x.aha), smooth: 0.5, smoothMonotone: 'x', symbol: 'none', lineStyle: { color: ahaClr, width: 2, type: [3, 6] }, itemStyle: { color: ahaClr } },
    ],
  })
  const per = a.periods
  const PERIOD_CLR: Record<string, string> = dark
    ? { night: '#5c6499', morning: '#9aa3dc', afternoon: '#c4caf0', evening: '#e4e7fb' }
    : { night: '#3b4a8a', morning: '#5e8df9', afternoon: '#8fb0fb', evening: '#c3d4fd' }
  renderTypeDonut(aiPeriodRef.value, {
    items: per.map(x => ({ key: x.key, name: x.label, value: x.count, extra: x, color: PERIOD_CLR[x.key] })),
    centerText: `${a.stats.total} 次`, centerSub: '提问次数',
    legend: x => { const y = x.extra as { count: number }; return `${x.name}  ${y.count} 次` },
    tooltip: x => { const y = x.extra as { count: number; range: string }; return `${x.name}（${y.range}）<br/>${y.count} 次（${x.percent}%）` },
  })
}

// 按选中的维度画中间明细区的图表
function renderDetail() {
  disposeDimCharts()
  if (activeKpi.value === 'study_time') renderStudy()
  else if (activeKpi.value === 'sessions') renderSessions()
  else if (activeKpi.value === 'answered') renderAnswers()
  else if (activeKpi.value === 'accuracy') renderAccuracy()
  else if (activeKpi.value === 'ai_asks') renderAiAsks()
}

function renderPowerTrend() {
  const c = initChart(trendPowerRef.value)
  const t = p.value?.cognitive.power_trend
  if (!c || !t?.has_data) return
  c.setOption({
    grid: { left: 0, right: 0, top: 30, bottom: 0, containLabel: true },
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
// 顶部统计卡选中的维度：决定中间明细区显示什么。DETAIL_KEYS 是已经有明细区的维度，其余卡片暂时不可选
const DETAIL_KEYS = ['study_time', 'sessions', 'answered', 'accuracy', 'ai_asks']
const activeKpi = ref('study_time')
function pickKpi(key: string) { if (DETAIL_KEYS.includes(key)) activeKpi.value = key }
// 学习时长明细区里的图表是 v-if 出来的：从别的维度切回来要重新画
watch(activeKpi, async () => { await nextTick(); renderDetail() })
watch(typeCode, async () => { await nextTick(); if (activeKpi.value === 'study_time') renderStudyType() })
watch(sessTypeCode, async () => { await nextTick(); if (activeKpi.value === 'sessions') renderSessionType() })
watch(ansTypeCode, async () => { await nextTick(); if (activeKpi.value === 'answered') renderAnswerType() })
watch(ansDiffCode, async () => { await nextTick(); if (activeKpi.value === 'answered') renderAnswerDiff() })
watch(accTypeCode, async () => { await nextTick(); if (activeKpi.value === 'accuracy') renderAccuracyType() })
watch(accDiffCode, async () => { await nextTick(); if (activeKpi.value === 'accuracy') renderAccuracyDiff() })
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
    renderDetail()
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

.form-topbar { display: flex; align-items: center; gap: 10px; flex-shrink: 0; }
.form-topbar :deep(.el-button + .el-button) { margin-left: 0; }

.section-block {
  padding: 5px 15px 15px;
  flex-shrink: 0;
  border-radius: 4px !important;
  box-shadow: none !important;
  border: 1px solid rgba(96, 141, 248, 0.15) !important;
}
// 学习时长三图：趋势 : 学科分布 : 时段 = 2 : 2.5 : 1.5
.hint-text { font-size: 12px; color: var(--text-3); }

.sub-title { font-size: 13px; font-weight: 600; color: var(--text-1); margin: 10px 0 8px; }
.foot-note { margin-top: 8px; font-size: 12px; color: var(--text-3); }
.empty, .empty-sm { color: var(--text-3); font-size: 13px; }
.empty { padding: 40px 0; text-align: center; }
.empty-sm { padding: 6px 0; }

// 第一列 = 顶部统计条的 2 列宽（5 列、间距 15px），让下面 4 张统计卡与顶部卡片同宽
.chart-row { display: grid; grid-template-columns: calc((100% - 60px) * 2 / 5 + 15px) minmax(0, 1fr); gap: 15px; flex-shrink: 0; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
// 第一列（类型时长分布）= 原来 2.1/8 的宽度再加 20px，其余两列平分剩下的
.detail-row { display: grid; grid-template-columns: calc((100% - 30px) * 2.1 / 8 + 20px) minmax(0, 1fr) minmax(0, 1fr); gap: 15px; flex-shrink: 0; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
// 这一行的图表卡与左边统计卡区（2×118 + 15 = 251px）等高：卡片内边距 + 标题共 48.5px，绘图区取 202.5px
.chart-row .chart-card__body, .chart-row .chart-card__empty { height: 202.5px; }
// 答题数：上面一行右边是两张图（平分剩余宽度）
.chart-row--3 { grid-template-columns: calc((100% - 60px) * 2 / 5 + 15px) minmax(0, 1fr) minmax(0, 1fr); @media (max-width: 1100px) { grid-template-columns: 1fr; } }
// 知识点学习时长 Top5：标题行右侧是科目切换（胶囊分段按钮），下面 5 行「序号 / 知识点名 / 占比条 / 时长」
.chart-card__head { display: flex; align-items: center; justify-content: space-between; gap: 10px; }
// 占两列宽的卡片（薄弱知识点表格）
.chart-card--span2 { grid-column: span 2; @media (max-width: 1100px) { grid-column: auto; }
  // 表头和标题之间留 6px（总高不变：6 + 204 = 210）
  .chart-card__body { margin-top: 6px; height: 204px; } }
.seg { display: inline-flex; gap: 2px; margin: -4px 0; padding: 2px; border-radius: 999px; flex-shrink: 0;
  border: 1px solid color-mix(in srgb, var(--text-3) 28%, transparent); background: color-mix(in srgb, var(--text-3) 8%, transparent); }
.seg__btn { height: 22px; padding: 0 12px; border: none; border-radius: 999px; background: transparent; color: var(--text-3); font-size: 12px; line-height: 22px; cursor: pointer; transition: background 0.2s, color 0.2s;
  &:hover { color: var(--text-1); }
  &.is-active { background: color-mix(in srgb, var(--text-1) 13%, transparent); color: var(--text-1); font-weight: 600; } }
.kp-list { display: flex; flex-direction: column; }      // 固定行高、靠上排：不足 5 个知识点时，下面留白，不把行拉开
.kp-row { height: 40px; display: grid; grid-template-columns: 20px minmax(0, 1.25fr) minmax(0, 1fr) 62px; align-items: center; gap: 10px; font-size: 13px; color: var(--text-1); }
.kp-row__no { width: 20px; height: 20px; border-radius: 50%; text-align: center; line-height: 20px; font-size: 11px; color: var(--text-2); background: color-mix(in srgb, var(--text-3) 16%, transparent); }
.kp-row__name { min-width: 0; overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
.kp-row__val { text-align: right; color: var(--text-2); white-space: nowrap; }
.stat-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); grid-template-rows: repeat(2, auto); align-content: start; gap: 15px; }
.chart-card__body--tips { overflow-y: auto; padding-top: 8px; }
.chart-card { position: relative; padding: 14px 15px 15px; min-width: 0; border-radius: 14px;
  --edge-a: rgba(210, 216, 255, 0.30); --edge-b: rgba(210, 216, 255, 0.035); --edge-c: rgba(210, 216, 255, 0.15);
  background: radial-gradient(240px circle at 0% 0%, rgba(150, 160, 240, 0.11), transparent 70%), linear-gradient(160deg, rgba(26, 30, 56, 0.62), rgba(12, 14, 28, 0.74));
  -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
  box-shadow: 0 10px 28px rgba(3, 5, 16, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  &::before { content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px; pointer-events: none; z-index: 2;
    background: linear-gradient(135deg, var(--edge-a), var(--edge-b) 30%, var(--edge-b) 70%, var(--edge-c, var(--edge-a)));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite: xor; mask-composite: exclude; }
  &__title { font-size: 13px; color: var(--text-3); letter-spacing: 0.02em; }
  &__body { height: 210px; }
  &__empty { height: 210px; display: flex; align-items: center; justify-content: center; font-size: 13px; color: var(--text-3); } }
.subj-dot { display: inline-block; width: 8px; height: 8px; margin-right: 6px; border-radius: 50%; }
.kpi--link { cursor: pointer; }
// 选中的顶部卡：描边提亮（亮色主题的在下面非 scoped 块里）
// 用 .kpi.kpi--active 抬高优先级：.kpi 自己在后面也定义了 --edge-*，同优先级会被它盖掉
.kpi.kpi--active { --edge-a: rgba(255, 255, 255, 0.6); --edge-b: rgba(255, 255, 255, 0.22); --edge-c: rgba(255, 255, 255, 0.42);
  box-shadow: 0 0 20px rgba(200, 205, 235, 0.1), inset 0 1px 0 rgba(255, 255, 255, 0.06); }
.kpi-strip { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 15px; flex-shrink: 0; @media (max-width: 1100px) { grid-template-columns: repeat(3, minmax(0, 1fr)); } }
// 顶部统计小卡片（参考图）：深海军蓝底，左上略亮；1px 渐变描边（四角亮、边中淡）；
// 右侧约一半宽、整卡高的区域铺细方格（向左淡出），迷你图画在方格上；标题灰蓝、数字用等宽字体、较大较细
.kpi { position: relative; display: flex; align-items: stretch; min-width: 0; height: var(--kpi-h, 118px); padding: 14px 16px; border-radius: 14px; overflow: hidden;
  --spark: #a8b0ee; --grid: rgba(190, 200, 255, 0.055); --edge-a: rgba(210, 216, 255, 0.30); --edge-b: rgba(210, 216, 255, 0.035); --edge-c: rgba(210, 216, 255, 0.15);
  background:
    radial-gradient(200px circle at 0% 0%, rgba(150, 160, 240, 0.11), transparent 70%),
    linear-gradient(160deg, rgba(26, 30, 56, 0.62), rgba(12, 14, 28, 0.74));
  -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
  box-shadow: 0 10px 28px rgba(3, 5, 16, 0.38), inset 0 1px 0 rgba(255, 255, 255, 0.04);
  &::before { content: ''; position: absolute; inset: 0; border-radius: inherit; padding: 1px; pointer-events: none; z-index: 2;
    background: linear-gradient(135deg, var(--edge-a), var(--edge-b) 30%, var(--edge-b) 70%, var(--edge-c, var(--edge-a)));
    -webkit-mask: linear-gradient(#fff 0 0) content-box, linear-gradient(#fff 0 0); -webkit-mask-composite: xor; mask-composite: exclude; }
  &__txt { position: relative; z-index: 1; min-width: 0; display: flex; flex-direction: column; }
  &__lbl { display: flex; align-items: center; gap: 4px; font-size: 13px; color: var(--text-3); white-space: nowrap; }
  &__val { margin-top: 8px; font-size: 36px; line-height: 1.1; font-weight: 400; letter-spacing: -0.03em; color: var(--text-1); white-space: nowrap; }
  &__unit { margin-left: 10px; font-size: 16px; font-weight: 400; letter-spacing: 0; color: var(--text-2); }
  &__delta { margin-top: auto; padding-top: 4px; min-height: 22px; font-size: 12px; color: var(--text-3); .delta { font-size: 12px; } }
  // 图案容器：占右侧 46%，内边距上下左右对称，图案在里面居中（左右各 16px、上下各 21px）；整体再往右挪 5px（right: -5px），卡片 overflow: hidden 会裁掉伸出去的方格底纹
  &__viz { position: absolute; z-index: 0; right: -5px; top: 0; bottom: 0; width: 46%; padding: 21px 16px;
    // 方格底纹向左多铺一截（压到数值下面，数值在它上层），再用缓和的多段渐变一路淡出，看起来像被左边的数值挡住
    &::before { content: ''; position: absolute; top: 0; bottom: 0; right: 0; left: -75%; z-index: -1; pointer-events: none;
      background: linear-gradient(var(--grid) 1px, transparent 1px) 0 0 / 100% 22px, linear-gradient(90deg, var(--grid) 1px, transparent 1px) 0 0 / 22px 100%;
      -webkit-mask-image: linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.04) 22%, rgba(0, 0, 0, 0.16) 42%, rgba(0, 0, 0, 0.45) 62%, #000 85%);
      mask-image: linear-gradient(90deg, transparent 0%, rgba(0, 0, 0, 0.04) 22%, rgba(0, 0, 0, 0.16) 42%, rgba(0, 0, 0, 0.45) 62%, #000 85%); } } }
.kpi__viz--ring { right: -10px; padding-top: 17px; padding-bottom: 17px; }   // 圆环稍大一些（上下少留 4px），并比其他图案再往右挪 5px
.kpi__viz--dots { padding-top: 12px; padding-bottom: 12px; }   // 点阵柱的方块更大，上下各少留一点，仍然对称
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
.cog-chip { display: inline-block; white-space: nowrap; padding: 1px 8px; border-radius: 999px; font-size: 12px; font-weight: 600; cursor: default;
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
// ── 暗色主题（参考图）：胶囊标签 / 按钮、小号大写表头、底部区块的深蓝玻璃 ──
</style>

<!-- 不加 scoped：下面的规则要同时带上主题选择器（html[data-theme=...]）和页面里的类名，scoped + :global 写法会把后半截选择器丢掉 -->
<style lang="scss">
// 学科色（数学 / 物理 / 化学）：用页面本身的蓝紫灰色阶，三档明度拉开（和统计卡、图表的灰紫同一个色相），不再引入别的色相
//   暗色：近白 / 中灰紫 / 深灰紫（堆叠柱从下往上由亮到暗）；亮色：深靛 / 中靛 / 浅靛
:root { --diff-basic: #3d4fc4; --diff-advanced: #7c8cf0; --diff-challenge: #b4bdf9; }
html[data-theme="dark"] { --diff-basic: #e4e7fb; --diff-advanced: #9aa3dc; --diff-challenge: #5c6499; }
:root { --subj-math: #3d4fc4; --subj-physics: #7c8cf0; --subj-chemistry: #b4bdf9; --subj-other: #cbd0dd; }
// 练习方式色（类型时长分布）：按小程序「练习方式」的顺序，一深一浅交错
//   暗色：近白 → 深灰紫；亮色：深靛 → 浅靛，其中「按学期」用中性灰
:root { --type-kp: #2f3fa8; --type-unit: #9aa6f5; --type-err: #4a5bd0; --type-fav: #b8c0fa; --type-smart: #6272e6; --type-random: #c9cfe0; --type-sem: #8190ee; }
html[data-theme="dark"] { --type-kp: #e4e7fb; --type-unit: #7a85c6; --type-err: #b4bbec; --type-fav: #4c5489; --type-smart: #9aa3dc; --type-random: #626ca6; --type-sem: #8590cc; }
html[data-theme="dark"] { --subj-math: #e4e7fb; --subj-physics: #9aa3dc; --subj-chemistry: #5c6499; --subj-other: #444a66; }

// 暗色主题（参考图）：更深的蓝黑底 + 右上角淡薰衣草光；强调色偏灰的薰衣草蓝紫；
// 胶囊标签 / 按钮、小号大写表头；亮色主题的统计卡 / 图表卡配色
html[data-theme="dark"] .page-root {
  // 参考图的暗色：更深的蓝黑底，右上角一团淡薰衣草光；强调色是偏灰的薰衣草蓝紫，次要文字带一点蓝紫
  --text-3: #8189aa; --text-2: #b4bbdc; --color-primary: #9aa4ef; --el-color-primary: #9aa4ef;
  background:
    radial-gradient(900px circle at 100% -8%, rgba(120, 132, 214, 0.20), transparent 62%),
    radial-gradient(700px circle at 0% 112%, rgba(80, 90, 170, 0.10), transparent 60%);
}

html[data-theme="light"] .page-root .chart-card {
  --edge-a: rgba(94, 141, 249, 0.42); --edge-b: rgba(94, 141, 249, 0.10); --edge-c: rgba(94, 141, 249, 0.26);
  box-shadow: 0 6px 18px rgba(94, 100, 200, 0.10), inset 0 1px 0 rgba(255, 255, 255, 0.9);
  background: radial-gradient(260px circle at 6% 0%, rgba(124, 112, 255, 0.10), transparent 72%), linear-gradient(165deg, rgba(244, 247, 255, 0.96), rgba(252, 253, 255, 0.92));
  border-color: rgba(94, 141, 249, 0.18); box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9); }

html[data-theme="light"] .page-root .kpi.kpi--active { --edge-a: rgba(94, 141, 249, 0.95); --edge-b: rgba(94, 141, 249, 0.4); --edge-c: rgba(94, 141, 249, 0.7); }
html[data-theme="light"] .page-root .kpi {
  --spark: var(--color-primary); --spark-shadow: #5e8df9; --spark-shadow-o: 0.35; --spark-accent: #4f7cf5; --spark-ln: #9db8ff; --spark-hi: #cdd9ff; --grid: rgba(94, 141, 249, 0.16); --edge-a: rgba(94, 141, 249, 0.42); --edge-b: rgba(94, 141, 249, 0.10);
  background:
    radial-gradient(180px circle at 6% 0%, rgba(124, 112, 255, 0.14), transparent 72%),
    linear-gradient(165deg, rgba(244, 247, 255, 0.96), rgba(252, 253, 255, 0.92));
  box-shadow: inset 0 1px 0 rgba(255, 255, 255, 0.9); }

html[data-theme="dark"] .page-root {
  .section-block.tabs-block {
    border-radius: 14px !important;
    background: radial-gradient(420px circle at 0% 0%, rgba(150, 160, 240, 0.08), transparent 70%), linear-gradient(160deg, rgba(24, 28, 52, 0.52), rgba(12, 14, 28, 0.68)) !important;
    border-color: rgba(210, 216, 255, 0.07) !important;
    -webkit-backdrop-filter: blur(14px); backdrop-filter: blur(14px);
  }
  .section-block.tabs-block::before { border-radius: 14px; }
  // 标签页：整排放在一条胶囊轨道里，选中项是略亮一点的深蓝胶囊
  .tabs-block .el-tabs__nav-wrap::after, .tabs-block .el-tabs__active-bar { display: none; }
  .tabs-block .el-tabs__nav { padding: 4px; border: 1px solid rgba(210, 216, 255, 0.09); border-radius: 999px; background: rgba(255, 255, 255, 0.025); }
  .tabs-block .el-tabs__item { height: 30px; line-height: 30px; padding: 0 16px !important; margin-right: 2px; border-radius: 999px; border: 1px solid transparent; transition: background .2s, color .2s;
    &:hover { color: var(--text-1); }
    &.is-active { background: rgba(120, 132, 214, 0.20); border-color: rgba(210, 216, 255, 0.14); color: #fff; font-weight: 600; } }
  // 顶部按钮用 .btn-back（返回按钮同款玻璃胶囊），避开全局普通按钮的 !important 圆角 / 底色规则
  .form-topbar .el-button, .form-topbar .el-date-editor, .form-topbar .el-date-editor.el-input__wrapper { border-radius: 999px !important; }
  .form-topbar .el-date-editor { padding-left: 14px; padding-right: 14px; }
  .el-table th.el-table__cell { font-size: 11px; font-weight: 500; letter-spacing: 0.08em; text-transform: uppercase; color: var(--text-3); }
}
</style>
