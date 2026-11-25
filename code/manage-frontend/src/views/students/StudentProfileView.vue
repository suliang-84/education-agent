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
      <!-- 顶部概览：第一层「是谁 + 现在怎么样」，第二层「能力 | 累计学习」 -->
      <div class="hero chart-card">
        <div class="hero__top">
          <!-- 身份 -->
          <div class="hero__id">
            <div class="hero__avatar"><img v-if="p.basic.avatar_url" :src="p.basic.avatar_url" alt="" /><span v-else>{{ (p.basic.nickname || '?').slice(0, 1) }}</span></div>
            <div class="hero__txt">
              <div class="hero__namerow">
                <span class="hero__name">{{ p.basic.nickname }}</span>
                <span v-if="p.basic.grade" class="hero__grade">{{ GRADES[p.basic.grade] ?? p.basic.grade }}{{ p.basic.semester ? ` · ${SEMESTERS[p.basic.semester] ?? p.basic.semester}` : '' }}</span>
                <span v-if="p.basic.is_minor" class="hero__minor">未成年</span>
                <span v-if="p.basic.is_active === false" class="hero__minor hero__minor--bad">已停用</span>
              </div>
              <div class="hero__meta">
                <span>{{ p.basic.phone_masked || '未留手机号' }}</span>
                <span>加入第 <b class="num">{{ joinDays }}</b> 天</span>
                <span>最近登录 {{ lastLoginText }}</span>
                <span :class="{ 'is-warn': !p.basic.parents.length }">{{ p.basic.parents.length ? `家长 ${p.basic.parents.map(x => x.nickname).join('、')}` : '家长未绑定' }}</span>
              </div>
            </div>
          </div>
          <!-- 当前状态 -->
          <div class="hero__side">
            <div class="ring" :style="{ '--p': p.summary.engagement_score }" title="学习投入度"><b class="num">{{ p.summary.engagement_score }}</b><i>投入度</i></div>
            <div class="hero__status">
              <div class="hero__state">
                <span class="hero__dot" :class="`tone--${statusTone}`" /><span class="hero__tag" :class="`tone--${statusTone}`">{{ p.summary.status }}</span>
                <span class="hero__warn" :class="warnTone">{{ warnText }}</span>
              </div>
              <div class="hero__reason" :title="p.summary.status_reason">{{ p.summary.status_reason }}</div>
            </div>
          </div>
        </div>

        <div class="hero__body">
          <!-- 五力速览 -->
          <section class="hero__power">
            <div class="hero__label">五力速览<span v-if="p.cognitive.has_profile && p.cognitive.tested_at">测试于 {{ formatDate(p.cognitive.tested_at) }}</span></div>
            <template v-if="p.cognitive.has_profile">
              <div class="pw-row">
                <div v-for="k in POWERS" :key="k" class="pw" :class="{ 'is-strong': p.cognitive.primary_strength === k, 'is-weak': p.cognitive.primary_weakness === k }" :style="{ '--pc': POWER_COLORS[k] }">
                  <span class="pw__ico"><SvgIcon :name="`power_${k.toLowerCase()}`" :size="15" /></span>
                  <b class="pw__num num">{{ p.cognitive.final?.[k] ?? '—' }}</b>
                  <span class="pw__name">{{ FivePowerLabels[k] }}</span>
                </div>
              </div>
              <div class="hero__cap">{{ modeText }}</div>
            </template>
            <div v-else class="hero__cap hero__cap--empty">尚未完成五力测试，暂无能力画像</div>
          </section>
          <!-- 累计学习 -->
          <section class="hero__stats">
            <div class="hero__label">累计学习<span>全部历史，不随日期范围变化</span></div>
            <div class="hs-grid">
              <div v-for="x in heroStats" :key="x.label" class="hs">
                <div class="hs__lbl">{{ x.label }}</div>
                <div class="hs__val num">{{ x.value }}<small v-if="x.unit">{{ x.unit }}</small></div>
                <div v-if="x.bar != null" class="bar hs__bar"><div class="bar__fill" :style="{ width: x.bar + '%', '--bar-c': 'var(--color-primary)' }" /></div>
                <div v-else-if="x.sub" class="hs__sub">{{ x.sub }}</div>
              </div>
            </div>
          </section>
        </div>
      </div>

      <div v-if="p.kpis?.length" class="sec-title"><span>学习概览</span><em>{{ rangeLabel }}，涨跌为较前一周期</em></div>
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
      <div class="sec-title"><span>维度明细</span><em>点击上方统计卡切换维度</em></div>
      <div class="chart-row" :class="{ 'chart-row--3': activeKpi === 'answered' || activeKpi === 'accuracy' }">
        <div v-if="activeKpi !== 'accuracy'" class="stat-grid">
          <div v-for="x in detailStats" :key="x.label" class="kpi kpi--plain" :title="x.hint">
            <div class="kpi__txt">
              <div class="kpi__lbl">{{ x.label }}</div>
              <div class="kpi__val num">{{ splitUnit(x.value).num }}<small v-if="splitUnit(x.value).unit" class="kpi__unit">{{ splitUnit(x.value).unit }}</small></div>
              <div class="kpi__delta">
                <span v-if="x.delta != null && x.delta !== 0" class="delta" :class="kpiTone(x)" :title="`${x.deltaLabel ?? '较前一周期'}${x.delta > 0 ? '上升' : '下降'} ${Math.abs(x.delta)}${x.unit}`">
                  <SvgIcon name="arrow_up" :size="11" :class="{ 'delta__down': x.delta < 0 }" />{{ Math.abs(x.delta) }}{{ x.unit }}
                </span>
                <span v-else-if="x.delta === 0" class="delta">持平</span>
                <span v-else>&nbsp;</span>
              </div>
            </div>
            <div class="kpi__viz"><KpiSpark :kind="x.viz" :gid="`st-${x.viz}`" /></div>
          </div>
        </div>
        <!-- 正确率：正确率趋势（总计 / 各科切换，同训练次数分布），占统计卡的位置 -->
        <div v-else class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">正确率趋势</div>
            <div v-if="p.accuracy?.has_data && p.accuracy.trend" class="seg" role="tablist">
              <button v-for="sj in accLineOptions" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': accLineCode === sj.code }" @click="accLinePick = sj.code">{{ sj.name }}</button>
            </div>
          </div>
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
          <div class="chart-card__head">
            <div class="chart-card__title">学科学习时长分布</div>
            <div v-if="p.study_time?.has_data" class="seg" role="tablist">
              <button v-for="sj in studyOptions" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': studyCode === sj.code }" @click="studyPick = sj.code">{{ sj.name }}</button>
            </div>
          </div>
          <div v-if="p.study_time?.has_data" ref="studyRef" class="chart-card__body" />
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无学习记录</div>
        </div>
        <!-- 训练次数：次数分布（按科目堆叠） -->
        <div v-else-if="activeKpi === 'sessions'" class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">训练次数分布</div>
            <div v-if="p.training?.has_data" class="seg" role="tablist">
              <button v-for="sj in sessLineOptions" :key="sj.code" type="button" class="seg__btn" :class="{ 'is-active': sessLineCode === sj.code }" @click="sessLinePick = sj.code">{{ sj.name }}</button>
            </div>
          </div>
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
            <div v-if="ansTypeItems.length" class="chart-card__body kp-list">
              <div v-for="x in ansTypeItems" :key="x.key" class="kp-row kp-row--qt" :title="ratePart(x)">
                <SvgIcon :name="QT_ICONS[x.key] ?? 'qt_single'" :size="16" :color="QT_COLORS[x.key] ?? 'var(--text-3)'" class="qt-ico" />
                <span class="kp-row__name">{{ x.label }}</span>
                <div class="bar"><div class="bar__fill" :style="{ width: (x.count / ansTypeMax * 100) + '%', '--bar-c': QT_COLORS[x.key] ?? 'var(--text-3)' }" /></div>
                <span class="kp-row__val num">{{ x.count }} 题</span>
              </div>
            </div>
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
            <div v-if="accTypeItems.length" class="chart-card__body kp-list">
              <div v-for="x in accTypeItems" :key="x.key" class="kp-row kp-row--qt kp-row--qt-acc" :title="accPart(x)">
                <SvgIcon :name="QT_ICONS[x.key] ?? 'qt_single'" :size="16" :color="QT_COLORS[x.key] ?? 'var(--text-3)'" class="qt-ico" />
                <span class="kp-row__name">{{ x.label }}</span>
                <div class="bar"><div class="bar__fill" :style="{ width: (x.count ? (x.accuracy ?? 0) : 0) + '%', '--bar-c': QT_COLORS[x.key] ?? 'var(--text-3)' }" /></div>
                <span class="kp-row__val num">{{ x.count ? `${x.accuracy ?? 0}%` : '—' }}<small v-if="x.count" class="kp-row__sub">{{ x.correct }}/{{ x.count }}</small></span>
              </div>
            </div>
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
          <div v-if="kpItems.length" class="chart-card__body kp-list kp-list--auto">
            <div v-for="(x, i) in kpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.minutes / kpMax * 100) + '%', '--bar-c': SUBJECT_COLORS[kpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num">{{ fmtMin(x.minutes) }}</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点学习记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="sumOf('study_time').length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in sumOf('study_time')" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
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
          <div v-if="tkpItems.length" class="chart-card__body kp-list kp-list--auto">
            <div v-for="(x, i) in tkpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.count / tkpMax * 100) + '%', '--bar-c': SUBJECT_COLORS[tkpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num" :title="`其中完成 ${x.done} 次`">{{ x.count }} 次</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点训练记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="sumOf('training').length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in sumOf('training')" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
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
          <div v-if="akpItems.length" class="chart-card__body kp-list kp-list--auto">
            <div v-for="(x, i) in akpItems" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.count / akpMax * 100) + '%', '--bar-c': SUBJECT_COLORS[akpCode] ?? SUBJECT_COLORS.OTHER }" /></div>
              <span class="kp-row__val num" :title="`答对 ${x.correct} 题，正确率 ${x.accuracy ?? 0}%`">{{ x.count }} 题</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}该科目暂无知识点答题记录</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="sumOf('answers').length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in sumOf('answers')" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
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
          <div v-if="p.ai_asks?.strategies?.length" class="chart-card__body kp-list kp-list--auto">
            <div v-for="(x, i) in p.ai_asks.strategies" :key="x.id" class="kp-row">
              <span class="kp-row__no num">{{ i + 1 }}</span>
              <span class="kp-row__name" :title="x.name">{{ x.name }}</span>
              <div class="bar"><div class="bar__fill" :style="{ width: (x.uses / aiStrategyMax * 100) + '%', '--bar-c': SUBJECT_COLORS.MATH }" /></div>
              <span class="kp-row__val num" :title="`点赞 ${x.likes} · 点踩 ${x.dislikes}`">{{ x.uses }} 次</span>
            </div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}助教暂未使用启发策略</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__title">总结</div>
          <div v-if="sumOf('ai_asks').length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in sumOf('ai_asks')" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
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
          <div v-if="sumOf('accuracy').length" class="chart-card__body chart-card__body--tips">
            <div v-for="(t, i) in sumOf('accuracy')" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="chart-card__empty">{{ rangeLabel }}暂无答题记录</div>
        </div>
      </div>
      </template>

      <!-- ═══ 下面各模块平铺：认知能力（整行）→ 个人洞察 | 学习信息摘要 → 预警 | 建议 ═══ -->
      <div class="sec-title"><span>能力画像</span><em>五力测试 vs 实战表现</em></div>
      <div class="chart-card cog-card">
        <div class="chart-card__head">
          <div class="chart-card__title">认知能力</div>
          <span class="card-hint">测试得分是五力测试的成绩，实战正确率是所选日期范围内的做题表现</span>
        </div>
        <template v-if="p.cognitive.has_profile">
          <div class="cog-layout">
            <div class="cog-layout__radar"><div ref="radarRef" class="radar-chart" /></div>
            <div class="cog-layout__main">
                <el-table v-if="cogInsights" :data="cogInsights.powers" size="small" class="mini-table cog-table">
                  <el-table-column label="能力" width="104">
                    <template #default="{ row }">
                      <span class="power-cell" :style="{ color: POWER_COLORS[row.key] }">
                        <span class="power-cell__ico" :style="{ background: `color-mix(in srgb, ${POWER_COLORS[row.key]} 16%, transparent)` }"><SvgIcon :name="`power_${String(row.key).toLowerCase()}`" :size="14" /></span>{{ row.label }}
                      </span>
                    </template>
                  </el-table-column>
                  <el-table-column label="测试得分" min-width="170">
                    <template #default="{ row }">
                      <div class="cog-bar"><div class="bar bar--fancy"><div class="bar__fill" :class="{ 'is-zero': !row.test }" :style="{ width: (row.test ?? 0) + '%', '--bar-c': POWER_COLORS[row.key] }" /></div><span class="num">{{ row.test ?? '—' }}</span></div>
                    </template>
                  </el-table-column>
                  <el-table-column label="实战正确率" min-width="170">
                    <template #default="{ row }">
                      <div class="cog-bar" :title="`${row.answered} 题`">
                        <div class="bar bar--fancy bar--scale"><div class="bar__fill" :class="[accLevel(row.accuracy)?.cls, { 'is-zero': !row.accuracy }]" :style="{ width: (row.accuracy ?? 0) + '%' }" /></div>
                        <span class="num">{{ fmtPct(row.accuracy) }}</span>
                      </div>
                    </template>
                  </el-table-column>
                  <el-table-column label="级别" width="76">
                    <template #default="{ row }">
                      <el-tooltip v-if="accLevel(row.accuracy)" content="优秀 90–100 · 良好 80–89 · 一般 60–79 · 不及格 0–59" placement="top">
                        <span class="lv-chip" :class="accLevel(row.accuracy)!.cls">{{ accLevel(row.accuracy)!.label }}</span>
                      </el-tooltip>
                      <span v-else class="cause-mini">—</span>
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
          </div>
          <div v-if="cogInsights?.highlights.length" class="cog-hls">
            <div v-for="(h, i) in cogInsights.highlights" :key="i" class="hl-chip"><span class="hl-item__dot" :class="`tone--${h.tone}`" />{{ h.text }}</div>
          </div>
        </template>
        <div v-else class="chart-card__empty cog-empty">该学生尚未完成五力测试，暂无能力画像</div>
      </div>

      <div class="sec-title"><span>智能洞察</span><em>个人洞察、预警与 AI 建议</em></div>
      <div class="bottom-row">
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">个人洞察</div>
            <span v-if="p.traits.personal_insight_updated_at" class="card-hint">更新于 {{ formatDate(p.traits.personal_insight_updated_at) }}</span>
          </div>
          <div v-if="p.traits.personal_insight" class="quote">{{ p.traits.personal_insight }}</div>
          <div v-else class="card-empty">暂无个人洞察。学生与 AI 助教聊天后会自动生成，也可以在「摘要」页手动填写。</div>
        </div>
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">学习信息摘要</div>
            <span class="card-hint">编辑请前往「摘要」页</span>
          </div>
          <div v-if="p.traits.learning_summary" class="quote">{{ p.traits.learning_summary }}</div>
          <div v-else class="card-empty">暂无</div>
        </div>
      </div>

      <div class="bottom-row">
        <div class="chart-card">
          <div class="chart-card__head">
            <div class="chart-card__title">预警<span v-if="p.warnings.open.length" class="count-badge num">{{ p.warnings.open.length }}</span></div>
            <span class="card-hint">规则和阈值可在「配置管理」里修改</span>
          </div>
            <div v-if="p.warnings.open.length" class="warn-list">
              <div v-for="w in p.warnings.open" :key="w.id" class="warn-item" :class="`warn-item--${w.level}`">
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
            <div v-else class="card-empty">目前没有需要关注的预警</div>
            <template v-if="p.warnings.handled.length">
              <div class="warn-sub">最近处理过的预警</div>
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
        <div class="chart-card advice-card">
          <div class="chart-card__head">
            <div class="chart-card__title">建议<span class="ai-badge"><SvgIcon name="sparkle" :size="12" />AI</span></div>
            <span class="card-hint">
              <template v-if="adviceLoading">AI 正在结合认知能力与学习数据分析…</template>
              <template v-else-if="advice?.source === 'rule'">AI 暂不可用，以下为规则建议</template>
              <template v-else>AI 综合认知能力与学习数据生成</template>
            </span>
            <button v-if="!adviceLoading" type="button" class="advice-refresh" @click="loadAdvice(true)">重新生成</button>
          </div>
          <div v-if="adviceLoading" class="tips tips--card advice-skeleton"><i v-for="n in 5" :key="n" /></div>
          <div v-else-if="advice?.items.length" class="tips tips--card">
            <div v-for="(t, i) in advice.items" :key="i" class="tip"><span class="tip__no num">{{ i + 1 }}</span>{{ t }}</div>
          </div>
          <div v-else class="card-empty">暂无建议</div>
        </div>
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
// 题型颜色：取 --qt-*（与小程序、训练题管理的题目类型一致，随亮 / 暗主题切换）
const QT_COLORS: Record<string, string> = {
  SINGLE_CHOICE: 'var(--qt-single)', MULTIPLE_CHOICE: 'var(--qt-multi)', TRUE_FALSE: 'var(--qt-judge)', FILL_BLANK: 'var(--qt-fill)', APPLICATION: 'var(--qt-application)',
}
const QT_ICONS: Record<string, string> = {
  SINGLE_CHOICE: 'qt_single', MULTIPLE_CHOICE: 'qt_multi', TRUE_FALSE: 'qt_judge', FILL_BLANK: 'qt_fill', APPLICATION: 'qt_application',
}
// 5 张统计卡各用一种固定图案（纯装饰，不随统计数据变化），互不重复：起伏面积（W 形）/ 蜡烛 / 声波 / 圆环 / 点阵柱
const KPI_VIZ: Record<string, 'bars' | 'wave' | 'dots' | 'ring' | 'swing'> = { study_time: 'swing', sessions: 'bars', answered: 'wave', accuracy: 'ring', ai_asks: 'dots' }
// 学科色：定义在下方非 scoped 样式块的 --subj-* 变量里（亮 / 暗各一套，随主题切换）。模板直接用 var()，图表用 subjColor() 取实际色值
const SUBJECT_COLORS: Record<string, string> = { MATH: 'var(--subj-math)', PHYSICS: 'var(--subj-physics)', CHEMISTRY: 'var(--subj-chemistry)', OTHER: 'var(--subj-other)' }
const SUBJECT_CODES = ['MATH', 'PHYSICS', 'CHEMISTRY']
const SUBJECT_FALLBACK: Record<string, string> = { MATH: '#7f9bff', PHYSICS: '#4fd0c4', CHEMISTRY: '#b595ff', OTHER: '#5b617c' }
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
// 练习方式的颜色（和小程序「练习方式」同一批名称）：配色取自题目类型那一套（与答题类型分布一致），定义在下方非 scoped 样式块的 --type-* 变量里，亮 / 暗各一套。
// 7 档明度会让相邻两段太像，所以相邻的练习方式一深一浅交错排，图例也分得开
const TYPE_VAR: Record<string, string> = { KNOWLEDGE_POINT: 'kp', UNIT: 'unit', ERROR_QUESTIONS: 'err', FAVORITES: 'fav', SMART: 'smart', RANDOM: 'random', SEMESTER: 'sem' }
const TYPE_FALLBACK: Record<string, string> = { kp: '#60a5fa', unit: '#22d3ee', err: '#f472b6', fav: '#facc15', smart: '#a78bfa', random: '#94a3b8', sem: '#34d399' }
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
type StatCard = { label: string; value: string; delta: number | null; unit: string; good: 'up' | 'down' | null; viz: 'dial' | 'ridge' | 'bubbles' | 'tide'; hint?: string; deltaLabel?: string }
// 分钟类涨跌：和顶部统计卡同口径（各自四舍五入后相减）；前一周期没有值则不显示
const diffMin = (a: number | null | undefined, b: number | null | undefined) => (a == null || b == null ? null : Math.round(a) - Math.round(b))
const studyStats = computed(() => {
  const st = p.value?.study_time?.stats
  const bd = st?.best_day
  // 单日最长：较前一段同样长度时间的变化（分钟，和顶部统计卡同口径：各自四舍五入后相减）；前一段没有学习记录则不显示
  const bestDelta = bd && st?.prev_best_minutes != null ? Math.round(bd.minutes) - Math.round(st.prev_best_minutes) : null
  const cards: StatCard[] = [
    { label: '平均每次训练时长', value: fmtMin(st?.avg_per_session), delta: diffMin(st?.avg_per_session, st?.prev_avg_per_session), unit: '分钟', good: 'up', viz: 'dial' },
    { label: bd ? `单日最长学习时长（${bd.date.slice(5).replace('-', '/')}）` : '单日最长学习时长', value: fmtMin(bd?.minutes), delta: bestDelta, unit: '分钟', good: 'up', viz: 'ridge' },
    { label: '周末日均学习时长', value: fmtMin(st?.weekend_avg), delta: diffMin(st?.weekend_avg, st?.prev_weekend_avg), unit: '分钟', good: 'up', viz: 'bubbles' },
    { label: '非周末日均学习时长', value: fmtMin(st?.weekday_avg), delta: diffMin(st?.weekday_avg, st?.prev_weekday_avg), unit: '分钟', good: 'up', viz: 'tide' },
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
const ansTypeMax = computed(() => Math.max(1, ...ansTypeItems.value.map(x => x.count)))
const aiStrategyMax = computed(() => Math.max(1, ...(p.value?.ai_asks?.strategies ?? []).map(x => x.uses)))
// 答题数的 4 张统计卡：错题 / 顽固错题 / 收藏都是「当前状态」，不随日期范围变；涨跌 = 较所选范围开始时的净变化；悬停看各科各是多少
//   待攻克 = 还没攻克的错题；已攻克 = 已经攻克的错题；顽固 = 同一道题错 3 次以上；收藏 = 收藏的题
const RANGE_START = '较所选范围开始时'   // 这四项是当前状态，涨跌 = 所选范围内的净变化
const answerStats = computed<StatCard[]>(() => {
  const st = p.value?.answers?.stats
  const subs = p.value?.answers?.subjects ?? []
  const hint = (k: 'pending' | 'mastered' | 'stubborn' | 'favorites') =>
    subs.filter(x => SUBJECT_CODES.includes(x.code)).map(x => `${x.name} ${st?.breakdown?.[x.code]?.[k] ?? 0}`).join(' · ')
  const val = (n: number | undefined) => (n == null ? '—' : `${n} 题`)
  return [
    { label: '待攻克错题', value: val(st?.wrong_pending), delta: diff1(st?.wrong_pending, st?.prev_wrong_pending), deltaLabel: RANGE_START, unit: '题', good: 'down', viz: 'ridge', hint: hint('pending') },
    { label: '已攻克错题', value: val(st?.wrong_mastered), delta: diff1(st?.wrong_mastered, st?.prev_wrong_mastered), deltaLabel: RANGE_START, unit: '题', good: 'up', viz: 'dial', hint: hint('mastered') },
    { label: '顽固错题', value: val(st?.stubborn), delta: diff1(st?.stubborn, st?.prev_stubborn), deltaLabel: RANGE_START, unit: '题', good: 'down', viz: 'tide', hint: hint('stubborn') },
    { label: '收藏题数', value: val(st?.favorites), delta: diff1(st?.favorites, st?.prev_favorites), deltaLabel: RANGE_START, unit: '题', good: 'up', viz: 'bubbles', hint: hint('favorites') },
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
// 学习状态 → 色调：提升绿 / 平稳蓝 / 瓶颈琥珀 / 懈怠红 / 数据不足灰
const statusTone = computed(() => ({ 稳步提升: 'good', 状态平稳: 'calm', 遇到瓶颈: 'warn', 近期懈怠: 'bad' } as Record<string, string>)[p.value?.summary.status ?? ''] ?? 'none')
// ── 顶部概览用到的派生数据 ──
const dayDiff = (iso?: string | null) => (iso ? Math.floor((Date.now() - new Date(iso).getTime()) / 86400000) : null)
const joinDays = computed(() => (dayDiff(p.value?.basic.created_at) ?? 0) + 1)
const lastLoginText = computed(() => {
  const d = dayDiff(p.value?.basic.last_login_at)
  return d == null ? '从未登录' : d <= 0 ? '今天' : `${d} 天前`
})
const MODE_LABELS: Record<string, string> = { TRAIN_WEAKNESS: '补足模式', LEARN_BY_STRENGTH: '一通百通模式' }
const modeText = computed(() => {
  const c = p.value?.cognitive
  if (!c?.has_profile) return ''
  const mode = c.recommended_mode ? MODE_LABELS[c.recommended_mode] ?? c.recommended_mode : ''
  const lbl = (k?: string) => (k ? FivePowerLabels[k as FivePower] ?? k : '')
  const parts = [c.primary_strength && `最强「${lbl(c.primary_strength)}」`, c.primary_weakness && `最需提升「${lbl(c.primary_weakness)}」`].filter(Boolean)
  return `${parts.join('，')}${mode ? `；系统推荐：${mode}` : ''}`
})
// 未处理预警：条数 + 最高级别（严重 > 关注 > 提示）
const warnTone = computed(() => {
  const open = p.value?.warnings.open ?? []
  return open.some(w => w.level === 'critical') ? 'is-critical' : open.some(w => w.level === 'attention') ? 'is-attention' : open.length ? 'is-notice' : 'is-ok'
})
const warnText = computed(() => {
  const n = p.value?.warnings.open.length ?? 0
  return n ? `${n} 条未处理预警` : '暂无预警'
})
// 累计学习数据（整个账号的历史，不随日期范围变）
const heroStats = computed(() => {
  const q = p.value
  if (!q) return []
  const last = q.behavior.last_active_date
  const sp = q.mastery.semester_progress
  return [
    { label: '累计训练', value: String(q.behavior.sessions_total), unit: '次', sub: last ? `最近学习 ${last.slice(5).replace('-', '/')}` : '' },
    { label: '累计答题', value: String(q.cognitive.training_info?.total_question_count ?? q.mastery.answered), unit: '题', sub: `覆盖 ${q.mastery.kp_total_practiced} 个知识点` },
    { label: '连续学习', value: String(q.behavior.streak_days), unit: '天', sub: '' },
    { label: '近 30 天学习', value: String(q.basic.active_days_30), unit: '天', sub: `占 ${Math.round((q.basic.active_days_30 / 30) * 100)}%` },
    { label: '本学期知识点', value: `${sp.practiced}/${sp.total}`, unit: '', bar: sp.rate ?? 0, sub: sp.rate != null ? `已练 ${sp.rate}%` : '' },
    { label: '待攻克错题', value: String(q.mastery.wrong_pending), unit: '题', sub: `已攻克 ${q.mastery.wrong_mastered} 道` },
  ] as { label: string; value: string; unit: string; sub: string; bar?: number }[]
})
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
const ansDiffRef = ref<HTMLElement>()
const accTrendRef = ref<HTMLElement>()
const aiTrendRef = ref<HTMLElement>()
const aiPeriodRef = ref<HTMLElement>()
const accDiffRef = ref<HTMLElement>()
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
// 底部「建议」（≤5 条）+ 各维度「总结」（每个维度 ≤5 条）：大模型结合学生画像 + 认知能力一次生成（接口较慢，画像加载完后单独请求；失败时后端退回规则建议）
const advice = ref<{ items: string[]; summaries: Record<string, string[]>; source: 'ai' | 'rule' }>()
const adviceLoading = ref(false)
let adviceSeq = 0
// 维度「总结」：优先用大模型的结果；还在生成 / 大模型不可用时，用规则生成的事实性小结顶上
function sumOf(key: 'study_time' | 'training' | 'answers' | 'accuracy' | 'ai_asks'): string[] {
  const ai = advice.value?.summaries?.[key]
  if (ai?.length) return ai
  return key === 'study_time' ? behaviorTips.value : (p.value?.[key]?.tips ?? [])
}
async function loadAdvice(refresh = false) {
  const seq = ++adviceSeq
  adviceLoading.value = true
  try {
    const r = await studentApi.getProfileAdvice(studentId, dateRange.value[0], dateRange.value[1], refresh)
    if (seq === adviceSeq) advice.value = r
  } catch { if (seq === adviceSeq) advice.value = undefined }
  finally { if (seq === adviceSeq) adviceLoading.value = false }
}
const behaviorTips = computed(() => (p.value?.study_time?.highlights ?? []).map(h => h.text))
const cogInsights = computed(() => p.value?.cognitive.insights)

// 实战正确率分级：优秀 90–100、良好 80–89、一般 60–79、不及格 0–59（按显示的整数判断）
function accLevel(v: number | null | undefined): { label: string; cls: string } | null {
  if (v === null || v === undefined) return null
  const n = Math.round(v)
  return n >= 90 ? { label: '优秀', cls: 'lv--excellent' } : n >= 80 ? { label: '良好', cls: 'lv--good' } : n >= 60 ? { label: '一般', cls: 'lv--ok' } : { label: '不及格', cls: 'lv--fail' }
}
const fmtPct = (v: number | null | undefined) => (v === null || v === undefined ? '—' : `${v}%`)

// 图表主色：暗色主题用偏灰的薰衣草蓝紫（和页面强调色一致），亮色主题沿用系统主色
function accent() {
  return document.documentElement.dataset.theme === 'dark' ? '#9aa4ef' : cssVar('--color-primary', '#608df9')
}
// 从页面根节点（.page-root）读 CSS 变量：本页在暗色 / 亮色下都单独调整了次要文字色（--text-2 / --text-3），
// 图表里的文字必须读同一份，否则会取到全局偏暗的值（暗色下 --text-3 全局是 #4B5563，在深色底上几乎看不清）
function cssVar(name: string, fallback: string) {
  const el = document.querySelector('.page-root') ?? document.documentElement
  return getComputedStyle(el).getPropertyValue(name).trim() || fallback
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
    const dark = document.documentElement.dataset.theme === 'dark'
    const areaGrad = (hex: string, edge: number) => ({ type: 'radial', x: 0.5, y: 0.5, r: 0.5, colorStops: [{ offset: 0, color: hexAlpha(hex, 0.04) }, { offset: 1, color: hexAlpha(hex, edge) }] })
    const glow = (hex: string) => ({ shadowBlur: 12, shadowColor: hexAlpha(hex, 0.55) })
    const rich = Object.fromEntries(POWERS.map(k => [k, { color: POWER_COLORS[k], fontSize: 12.5, fontWeight: 600 }]))
    const cogColor = (hex: string) => (hex.startsWith('#') ? hex : '#7f9bff')
    c.setOption({
      backgroundColor: 'transparent',
      legend: { bottom: 0, itemWidth: 14, itemHeight: 3, icon: 'roundRect', itemGap: 18, textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
      tooltip: {},
      radar: {
        shape: 'circle', indicator: POWERS.map(k => ({ name: `{${k}|${FivePowerLabels[k]}}`, max: 100 })), radius: 84, center: ['50%', '47%'], axisNameGap: 10,
        axisName: { formatter: (v: string) => v, rich },
        splitNumber: 4,
        splitLine: { lineStyle: { color: dark ? 'rgba(190,200,255,0.16)' : 'rgba(94,141,249,0.22)', type: 'dashed' } },
        splitArea: { areaStyle: { color: dark ? ['rgba(150,160,240,0.05)', 'rgba(150,160,240,0.0)'] : ['rgba(94,141,249,0.06)', 'rgba(94,141,249,0.0)'] } },
        axisLine: { lineStyle: { color: dark ? 'rgba(190,200,255,0.16)' : 'rgba(94,141,249,0.22)' } },
      },
      series: [{
        type: 'radar', symbol: 'circle', symbolSize: 6,
        data: [
          { name: '测试得分', value: POWERS.map(k => cog.final?.[k] ?? 0), lineStyle: { color: cogColor(primary), width: 2.5, ...glow(cogColor(primary)) }, itemStyle: { color: cogColor(primary), borderColor: dark ? '#0d0f1c' : '#fff', borderWidth: 2 }, areaStyle: { color: areaGrad(cogColor(primary), 0.5) } },
          { name: `实战正确率`, value: POWERS.map(k => real[k] ?? 0), lineStyle: { color: green, width: 2, type: 'dashed', ...glow(green) }, itemStyle: { color: green, borderColor: dark ? '#0d0f1c' : '#fff', borderWidth: 2 }, areaStyle: { color: areaGrad(green, 0.34) } },
        ],
      }],
    })
  }
}

// 三张学习时长图（趋势 / 学科堆叠 / 时段）。图表一直在页面上，数据加载完就画
// 学科学习时长分布 / 训练次数分布：总计 + 各科切换（默认总计）；换了日期范围后这个科目没了就回到总计
function useLineView(subjects: () => { code: string; name: string; count?: number }[] | undefined) {
  const picked = ref('ALL')
  const options = computed(() => [{ code: 'ALL', name: '总计' }, ...(subjects() ?? []).filter(x => SUBJECT_CODES.includes(x.code) || (x.count ?? 1) > 0)])
  const code = computed(() => (options.value.some(x => x.code === picked.value) ? picked.value : 'ALL'))
  return { picked, options, code }
}
const { picked: studyPick, options: studyOptions, code: studyCode } = useLineView(() => p.value?.study_time?.subjects)
const { picked: sessLinePick, options: sessLineOptions, code: sessLineCode } = useLineView(() => p.value?.training?.subjects)
const { picked: accLinePick, options: accLineOptions, code: accLineCode } = useLineView(() => p.value?.accuracy?.subjects)

function renderStudy() {
  const t = p.value?.study_time
  if (!t?.has_data || !t.series || !t.subjects) return
  const series = t.series
  renderSubjectLines(studyRef.value, {
    labels: series.map(x => x.label), subjects: t.subjects, totalVals: series.map(x => x.total), valueOf: (i, code) => series[i].minutes[code] ?? 0,
    only: studyCode.value, totalOnly: true, fmt: fmtMin, axisName: '分钟', nullText: '无记录',
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
  // 每一段圆环用斜向渐变：一头是本色（略透明），另一头高亮（暗色偏白，亮色偏深）
  const dark = document.documentElement.dataset.theme === 'dark'
  const ringGrad = (hex: string) => {
    const n = parseInt(hex.replace('#', ''), 16), ch = [n >> 16 & 255, n >> 8 & 255, n & 255]
    const mid = ch.map(v => Math.round(dark ? v + (255 - v) * 0.55 : v * 0.7))
    const rgb = (a: number[], al: number) => `rgba(${a[0]}, ${a[1]}, ${a[2]}, ${al})`
    return { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: rgb(ch, 0.75) }, { offset: 1, color: rgb(mid, 1) }] }
  }
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
        data: o.items.map(x => ({ name: x.name, value: x.value, extra: x.extra, itemStyle: { color: ringGrad(x.color ?? typeColor(x.key)) } })) },
      // 外圈一条细线，和参考图一样
      { type: 'pie', radius: [ringR * 0.9875, ringR], center: [ringCx, '50%'], silent: true, label: { show: false }, labelLine: { show: false }, tooltip: { show: false },
        data: [{ value: 1, itemStyle: { color: 'rgba(128,128,128,0.22)' } }] },
    ],
  })
}

// ── 训练次数明细：次数分布（按科目堆叠）、练习方式次数分布 ──
function renderSessions() {
  const t = p.value?.training
  if (!t?.has_data || !t.series || !t.types) return
  const series = t.series

  // ① 训练次数分布：总计 + 各科的平滑折线，学科色和学科学习时长分布一致
  renderSessionLines()

  renderSessionType()
}

function renderSessionLines() {
  const t = p.value?.training
  if (!t?.has_data || !t.series) return
  const series = t.series
  renderSubjectLines(sessTrendRef.value, {
    labels: series.map(x => x.label), subjects: t.subjects ?? [], totalVals: series.map(x => x.total), valueOf: (i, code) => series[i].by_subject?.[code] ?? 0,
    only: sessLineCode.value, totalOnly: true, fmt: v => `${v} 次`, integer: true, axisName: '次',
  })
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

// 画布里的颜色要写成 rgba（不认 CSS 的 color-mix）
const hexAlpha = (hex: string, a: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${a})` }

// 横向排行条（科目答题数 / 答题类型分布 / 题型正确率）：每项一根圆头的细条，浅色轨道托底，由该科目的颜色渐变为白色 + 柔光；
// 数值统一排在轨道右侧一列，左边是名称，一眼能横向比较。百分比类的轨道固定 0~100%，次数类的轨道以最大值为满格。
function renderRankBars(el: HTMLElement | undefined, o: { labels: string[]; values: number[]; colors: string[]; valueText: (i: number) => string; tooltip: (i: number) => string; percent?: boolean; labelW?: number }) {
  const c = initDimChart(el)
  if (!c) return
  const txt2 = cssVar('--text-2', '#888')
  const txt1 = cssVar('--text-1', '#fff')
  const full = o.percent ? 100 : Math.max(1, ...o.values)
  const BAR = 10   // 与 CSS 变量 --pf-bar-h 保持一致（全页进度条同高）
  c.setOption({
    grid: { left: 0, right: o.labelW ?? 72, top: 6, bottom: 6, containLabel: true },
    tooltip: { trigger: 'axis', axisPointer: { type: 'none' }, formatter: (ps: { dataIndex: number }[]) => o.tooltip(ps[0].dataIndex) },
    xAxis: { type: 'value', min: 0, max: full, show: false },
    yAxis: { type: 'category', inverse: true, data: o.labels, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: txt2, fontSize: 12.5, margin: 10 } },
    series: [
      // 轨道：同时负责把数值文字排在最右一列
      { type: 'bar', silent: true, z: 1, barWidth: BAR, barGap: '-100%', data: o.labels.map(() => full),
        itemStyle: { color: 'rgba(128, 128, 128, 0.14)', borderRadius: 999 },
        label: { show: true, position: 'right', distance: 10, color: txt1, fontSize: 12.5, fontWeight: 500, formatter: (x: { dataIndex: number }) => o.valueText(x.dataIndex) } },
      { type: 'bar', z: 2, barWidth: BAR, data: o.values.map((v, i) => ({ value: v, itemStyle: {
          borderRadius: 999,
          color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: o.colors[i] }, { offset: 1, color: '#ffffff' }] },
          shadowBlur: 10, shadowColor: hexAlpha(o.colors[i], 0.4), shadowOffsetY: 2 } })) },
    ],
  })
}

// 环形进度（难度正确率）：每一项一个圆环，圆头进度 + 渐变，中间是大号百分比和名称，下面一行小字写答对 / 答题数
function renderRingGauges(el: HTMLElement | undefined, o: { items: { name: string; value: number | null; sub: string }[]; color: string; tooltip: (i: number) => string }) {
  const c = initDimChart(el)
  if (!c) return
  const cw = c.getWidth(), ch = c.getHeight(), n = o.items.length
  const r = Math.max(34, Math.min(ch / 2 - 24, cw / n / 2 - 12))
  const cy = ch / 2 - 8
  const W = Math.max(8, Math.round(r * 0.17))
  const txt1 = cssVar('--text-1', '#fff'), txt3 = cssVar('--text-3', '#999')
  c.setOption({
    tooltip: { formatter: (x: { seriesIndex: number }) => o.tooltip(x.seriesIndex) },
    graphic: o.items.map((x, i) => ({ type: 'text', silent: true, style: { x: ((i + 0.5) / n) * cw, y: cy + r + 10, text: x.sub, fill: txt3, fontSize: 12, textAlign: 'center', textVerticalAlign: 'top' } })),
    series: o.items.map((x, i) => ({
      type: 'gauge', center: [`${((i + 0.5) / n) * 100}%`, cy], radius: r, startAngle: 90, endAngle: -270, min: 0, max: 100, pointer: { show: false }, animationDuration: 900,
      axisLine: { lineStyle: { width: W, color: [[1, 'rgba(128, 128, 128, 0.16)']] }, roundCap: true },
      progress: { show: x.value != null, width: W, roundCap: true, itemStyle: { color: { type: 'linear', x: 0, y: 0, x2: 1, y2: 1, colorStops: [{ offset: 0, color: o.color }, { offset: 1, color: '#ffffff' }] }, shadowBlur: 10, shadowColor: hexAlpha(o.color, 0.4) } },
      axisTick: { show: false }, splitLine: { show: false }, axisLabel: { show: false }, anchor: { show: false },
      title: { offsetCenter: [0, '34%'], fontSize: 12, color: txt3 },
      detail: { offsetCenter: [0, '-8%'], fontSize: Math.max(16, Math.round(r * 0.36)), fontWeight: 600, color: txt1, valueAnimation: true, formatter: (v: number) => (x.value == null ? '—' : `${Math.round(v)}%`) },
      data: [{ value: x.value ?? 0, name: x.name }],
    })),
  })
}

// ── 答题数明细：科目答题数、答题类型分布（横向排行条）、难度分布（环形图）──
const ratePart = (x: { count: number; correct: number; accuracy: number | null }) => `答题 ${x.count} 题，答对 ${x.correct} 题（正确率 ${x.accuracy ?? 0}%）`
function renderAnswers() {
  const a = p.value?.answers
  if (!a?.has_data) return
  // ① 科目答题数：每个科目一根条，颜色用学科色；右侧写答题数和正确率
  const subs = a.subjects.filter(x => SUBJECT_CODES.includes(x.code) || x.count > 0)
  renderRankBars(ansSubjRef.value, {
    labels: subs.map(x => x.name), values: subs.map(x => x.count), colors: subs.map(x => subjColor(x.code)), labelW: 104,
    valueText: i => `${subs[i].count} 题 · ${subs[i].accuracy ?? 0}%`,
    tooltip: i => `${subs[i].name}<br/>${ratePart(subs[i])}<br/>占全部答题的 ${subs[i].share ?? 0}%`,
  })
  renderAnswerDiff()
}
// 难度分布：环形图。基础 / 进阶 / 挑战三档，颜色是 --diff-* 变量（页面蓝紫灰色阶）
const DIFF_FALLBACK: Record<string, string> = { basic: '#c4caf0', advanced: '#8f97ea', challenge: '#6a72d0' }
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
// 平滑折线图（学习时长分布 / 训练次数分布 / 正确率趋势共用）：只看某一科时只画这一科的线，「总计」时画合计（虚线）+ 各科
function renderSubjectLines(el: HTMLElement | undefined, o: {
  labels: string[]; subjects: { code: string; name: string }[]; totalVals: (number | null)[]; valueOf: (i: number, code: string) => number | null
  only: string; fmt: (v: number) => string; percent?: boolean; integer?: boolean; axisName?: string; nullText?: string
  totalOnly?: boolean   // 「总计」只画合计一条线（不叠各科）
}) {
  const dark = document.documentElement.dataset.theme === 'dark'
  const txt3 = cssVar('--text-3', '#999')
  const rgba = (hex: string, al: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${al})` }
  const lineClr = (code: string) => subjColor(code)
  const totalClr = dark ? '#8b90ab' : '#475066'
  const totalSoloClr = dark ? '#8f97cf' : '#8fb0fb'   // 「总计」线两端的主色
  const darken = (hex: string, k: number) => { const n = parseInt(hex.replace('#', ''), 16); const f = (v: number) => Math.round(v * k).toString(16).padStart(2, '0'); return `#${f(n >> 16 & 255)}${f(n >> 8 & 255)}${f(n & 255)}` }
  const totalMidClr = dark ? '#ffffff' : '#3d4fc4'      // 中间：暗色是白，亮色白底看不见，改用深靛     // 只画合计时用亮一点的色
  const hoverFill = dark ? '#0d0f1c' : '#ffffff'
  const fillOf = (hex: string, top: number) => ({ color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: rgba(hex, top) }, { offset: 1, color: rgba(hex, 0) }] } })
  // 线两端渐隐、中间最亮：横向渐变描边（两端 14% 透明度 → 中间 100%）
  const fadeClr = (hex: string) => ({ type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: rgba(hex, 0.38) }, { offset: 0.5, color: rgba(hex, 1) }, { offset: 1, color: rgba(hex, 0.38) }] })
  const lineSer = (name: string, data: (number | null)[], clr: string, width: number, o: { dashed?: boolean; top: number; z: number; mid?: string }) => ({
    name, type: 'line', z: o.z, data, smooth: 0.55, smoothMonotone: 'x', symbol: 'none', connectNulls: true,
    lineStyle: { color: o.mid ? { type: 'linear', x: 0, y: 0, x2: 1, y2: 0, colorStops: [{ offset: 0, color: clr }, { offset: 0.5, color: o.mid }, { offset: 1, color: clr }] } : fadeClr(clr), width, cap: 'round', type: o.dashed ? [3, 6.5] : 'solid' }, itemStyle: { color: clr }, areaStyle: fillOf(clr, o.top),
  })
  const labels = o.labels
  const nPts = labels.length
  const subs = o.only === 'ALL' ? (o.totalOnly ? [] : o.subjects) : o.subjects.filter(x => x.code === o.only)
  const defs = [
    ...(o.only === 'ALL' ? [{ name: '合计', clr: totalClr, vals: o.totalVals }] : []),
    ...subs.map(sj => ({ name: sj.name, clr: lineClr(sj.code), vals: labels.map((_, i) => o.valueOf(i, sj.code)) })),
  ]
  const hoverPoints = (i: number) => (i < 0 ? [] : defs.filter(d => d.vals[i] != null).map(d => ({ value: [i, d.vals[i]], itemStyle: { color: hoverFill, borderColor: dark ? '#e8eaf8' : d.clr, borderWidth: 1.6 } })))
  // 底部柔光：每个点取最低的那条学科线
  const low = labels.map((_, i) => { const v = defs.map(d => d.vals[i]).filter((y): y is number => y != null); return v.length ? Math.min(...v) : null })
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
  const c = initDimChart(el)
  c?.setOption({
    grid: { left: 0, right: 0, top: 30, bottom: 0, containLabel: true },
    legend: { show: !o.totalOnly, top: 0, data: defs.map(d => d.name), itemWidth: 12, itemHeight: 3, icon: 'roundRect', textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
    tooltip: {
      trigger: 'axis',
      axisPointer: { type: 'line', lineStyle: { color: dark ? 'rgba(255, 255, 255, 0.28)' : 'rgba(71, 80, 102, 0.3)', width: 1, type: 'solid' } },
      backgroundColor: dark ? 'rgba(18, 20, 36, 0.92)' : 'rgba(255, 255, 255, 0.96)', borderColor: dark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(94, 141, 249, 0.2)',
      textStyle: { color: dark ? '#dfe2f4' : '#2d3550', fontSize: 12 },
      formatter: (ps: { dataIndex: number; seriesName: string; marker: string; value: number | null }[]) =>
        `${labels[ps[0].dataIndex]}<br/>` + ps.filter(x => x.seriesName).map(x => `${x.marker}${x.seriesName}：${x.value == null ? (o.nullText ?? '样本不足') : o.fmt(x.value)}`).join('<br/>'),
    },
    xAxis: [
      { type: 'category', data: labels, boundaryGap: false, axisLine: { show: false }, axisTick: { show: false }, axisLabel: { formatter: labelFmt(-1), rich: labelRich, margin: 10, alignMinLabel: 'left', alignMaxLabel: 'right' } },
      { type: 'value', min: 0, max: Math.max(1, nPts - 1), show: false },     // 只用来摆「日期之间的小圆点」：整数位置 = 两个日期之间的边界
    ],
    yAxis: { type: 'value', min: 0, ...(o.percent ? { max: 100, interval: 25 } : { splitNumber: 3, ...(o.integer ? { minInterval: 1 } : {}) }), name: o.axisName, nameTextStyle: { color: txt3, fontSize: 11, align: 'left' }, axisLine: { show: false }, axisTick: { show: false },
      splitLine: { lineStyle: { color: dark ? 'rgba(255, 255, 255, 0.07)' : 'rgba(128, 128, 128, 0.16)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11, formatter: (v: number) => (o.percent ? `${v}%` : `${v}`) } },
    series: [
      glowSer,
      ...defs.map((d, i) => (d.name === '合计' ? (o.totalOnly ? lineSer('合计', d.vals, totalSoloClr, 3, { top: dark ? 0.5 : 0.3, z: 1, mid: totalMidClr }) : lineSer('合计', d.vals, totalClr, 3, { dashed: true, top: dark ? 0.2 : 0.1, z: 1 })) : lineSer(d.name, d.vals, d.clr, o.only === 'ALL' ? 2 : 3, { top: o.only === 'ALL' ? (dark ? 0.1 : 0.05) : (dark ? 0.5 : 0.3), z: 2 + i, mid: o.only === 'ALL' ? undefined : (dark ? '#ffffff' : darken(d.clr, 0.62)) }))),
      { type: 'scatter', id: 'hover', name: '', xAxisIndex: 0, yAxisIndex: 0, silent: true, z: 10, legendHoverLink: false, tooltip: { show: false }, symbol: 'circle', symbolSize: 10, data: [] },
      { type: 'scatter', name: '', xAxisIndex: 1, yAxisIndex: 0, silent: true, clip: false, z: 0, legendHoverLink: false, tooltip: { show: false },
        symbol: 'circle', symbolSize: 3, symbolOffset: [0, 17], itemStyle: { color: dark ? '#3d4260' : '#c3c9d8' },
        data: Array.from({ length: Math.max(0, nPts - 1) }, (_, i) => [i + 0.5, 0]) },
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

function renderAccuracyTrend() {
  const a = p.value?.accuracy
  const t = a?.trend
  if (!a?.has_data || !t) return
  const subs = a.subjects.filter(x => SUBJECT_CODES.includes(x.code) || x.count > 0)
  // 总计只画整体一条线，选某一科只画这一科（同训练次数分布，不再把整体和各科叠在一起）
  renderSubjectLines(accTrendRef.value, { labels: t.series.map(x => x.label), subjects: subs, totalVals: t.series.map(x => x.accuracy), valueOf: (i, code) => t.series[i].by_subject[code]?.accuracy ?? null, only: accLineCode.value, totalOnly: true, fmt: v => `${v}%`, percent: true })
}

// ── 正确率明细：题型正确率、难度正确率（0~100% 的胶囊柱状图）──
const accPart = (x: { count: number; correct: number; accuracy: number | null }) => (x.count ? `正确率 ${x.accuracy ?? 0}%（答对 ${x.correct} / ${x.count} 题）` : '还没有答题')
function renderAccuracy() {
  const a = p.value?.accuracy
  if (!a?.has_data) return
  renderAccuracyTrend()
  renderAccuracyDiff()
}
// 难度正确率：三个并排的环形进度（基础 / 进阶 / 挑战）
function renderAccuracyDiff() {
  const items = accDiffItems.value
  if (!items.length) return
  renderRingGauges(accDiffRef.value, {
    items: items.map(x => ({ name: x.label, value: x.count ? (x.accuracy ?? 0) : null, sub: x.count ? `答对 ${x.correct} / ${x.count} 题` : '还没有答题' })),
    color: subjColor(accDiffCode.value), tooltip: i => `${items[i].label}<br/>${accPart(items[i])}`,
  })
}

// ── AI 提问明细：提问趋势（提问数柱 + 顿悟数标记）、提问时段分布（环形图）──
function renderAiAsks() {
  const a = p.value?.ai_asks
  if (!a?.has_data) return
  const dark = document.documentElement.dataset.theme === 'dark'
  const barClr = dark ? '#7f9bff' : '#4f6bed'
  const txt3 = cssVar('--text-3', '#999')
  const alpha = (hex: string, al: number) => { const n = parseInt(hex.replace('#', ''), 16); return `rgba(${n >> 16 & 255}, ${n >> 8 & 255}, ${n & 255}, ${al})` }
  const s = a.series
  const c = initDimChart(aiTrendRef.value)
  const ahaLine = dark ? '#fbbf24' : '#f59e0b'
  const area = (clr: string, top: number) => ({ color: { type: 'linear', x: 0, y: 0, x2: 0, y2: 1, colorStops: [{ offset: 0, color: alpha(clr, top) }, { offset: 1, color: alpha(clr, 0) }] } })
  // 提问次数：平滑面积折线（蓝）；顿悟次数：平滑折线（琥珀，像灯泡亮起）。悬停有竖虚线 + 圆点，平时不画点
  c?.setOption({
    grid: { left: 0, right: 8, top: 32, bottom: 0, containLabel: true },
    legend: { top: 0, right: 0, itemWidth: 10, itemHeight: 10, icon: 'circle', itemGap: 16, textStyle: { color: cssVar('--text-2', '#888'), fontSize: 12 } },
    tooltip: { trigger: 'axis', axisPointer: { type: 'line', lineStyle: { color: dark ? 'rgba(255,255,255,0.22)' : 'rgba(71,80,102,0.25)', type: 'dashed' } },
      formatter: (ps: { dataIndex: number }[]) => `${s[ps[0].dataIndex].label}<br/>提问 ${s[ps[0].dataIndex].count} 次<br/>顿悟 ${s[ps[0].dataIndex].aha} 次` },
    xAxis: { type: 'category', boundaryGap: false, data: s.map(x => x.label), axisLine: { show: false }, axisTick: { show: false }, axisLabel: { color: txt3, fontSize: 11, margin: 12 } },
    yAxis: { type: 'value', min: 0, minInterval: 1, splitNumber: 3, splitLine: { lineStyle: { color: 'rgba(160,168,220,0.16)', type: 'dashed' } }, axisLabel: { color: txt3, fontSize: 11 } },
    series: [
      { name: '提问次数', type: 'line', z: 2, data: s.map(x => x.count), smooth: 0.5, smoothMonotone: 'x', symbol: 'circle', symbolSize: 8, showSymbol: false,
        lineStyle: { color: barClr, width: 2.5, cap: 'round', shadowBlur: 10, shadowColor: alpha(barClr, 0.45), shadowOffsetY: 3 }, itemStyle: { color: barClr, borderColor: dark ? '#0d0f1c' : '#fff', borderWidth: 2 }, areaStyle: area(barClr, 0.32) },
      { name: '顿悟次数', type: 'line', z: 3, data: s.map(x => x.aha), smooth: 0.5, smoothMonotone: 'x', symbol: 'circle', symbolSize: 8, showSymbol: false,
        lineStyle: { color: ahaLine, width: 2, cap: 'round' }, itemStyle: { color: ahaLine, borderColor: dark ? '#0d0f1c' : '#fff', borderWidth: 2 }, areaStyle: area(ahaLine, 0.16) },
    ],
  })
  const per = a.periods
  const PERIOD_CLR: Record<string, string> = dark
    ? { night: '#6a72d0', morning: '#c4d4ff', afternoon: '#7ab4f5', evening: '#b3a0f5' }
    : { night: '#3d4fc4', morning: '#a9bdf9', afternoon: '#5fa0e8', evening: '#8a6fe0' }
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

async function drawTab() {
  await nextTick()
  renderRadar()
}
// 顶部统计卡选中的维度：决定中间明细区显示什么。DETAIL_KEYS 是已经有明细区的维度，其余卡片暂时不可选
const DETAIL_KEYS = ['study_time', 'sessions', 'answered', 'accuracy', 'ai_asks']
const activeKpi = ref('study_time')
function pickKpi(key: string) { if (DETAIL_KEYS.includes(key)) activeKpi.value = key }
// 学习时长明细区里的图表是 v-if 出来的：从别的维度切回来要重新画
watch(activeKpi, async () => { await nextTick(); renderDetail() })
watch(studyCode, async () => { await nextTick(); if (activeKpi.value === 'study_time') renderStudy() })
watch(sessLineCode, async () => { await nextTick(); if (activeKpi.value === 'sessions') renderSessionLines() })
watch(accLineCode, async () => { await nextTick(); if (activeKpi.value === 'accuracy') renderAccuracyTrend() })
watch(typeCode, async () => { await nextTick(); if (activeKpi.value === 'study_time') renderStudyType() })
watch(sessTypeCode, async () => { await nextTick(); if (activeKpi.value === 'sessions') renderSessionType() })
watch(ansDiffCode, async () => { await nextTick(); if (activeKpi.value === 'answered') renderAnswerDiff() })
watch(accDiffCode, async () => { await nextTick(); if (activeKpi.value === 'accuracy') renderAccuracyDiff() })
async function load() {
  loading.value = true
  try {
    p.value = await studentApi.getProfile(studentId, dateRange.value[0], dateRange.value[1])
    loadAdvice()
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
.qt-ico { justify-self: center; }
// 答题类型：图标与文字 5px，进度条两端（到题型名、到数值）都是 10px（名称列、数值列定宽，数值左对齐，进度条两端到相邻内容的距离每行一致）
.kp-row--qt { grid-template-columns: 16px 39px minmax(0, 1fr) var(--qt-val-w, 46px); gap: 10px;
  .qt-ico { margin-right: -5px; }
  .kp-row__val { text-align: left; } }
// 题型正确率：数值列放「76%  19/25」（百分比 + 答对 / 答题数小字）
.kp-row--qt-acc { --qt-val-w: 84px; .kp-row__sub { margin-left: 6px; font-size: 11px; color: var(--text-3); } }
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
// 能力列：左侧五力图标（同小程序：洞察 = 靶心、建构 = 尺、推演 = 分支、调适 = 循环、迁移 = 火箭），放在五力色的浅底圆角块里
.power-cell { display: inline-flex; align-items: center; gap: 8px; font-weight: 600; white-space: nowrap; }
.power-cell__ico { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 8px; flex-shrink: 0; }
.cog-bar { display: flex; align-items: center; gap: 10px; width: 100%; font-size: 13px; color: var(--text-1); .bar { flex: 1 1 auto; min-width: 90px; } .num { flex: none; min-width: 26px; text-align: right; } small { font-size: 11px; color: var(--text-3); } }
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

// ── 认知能力 / 个人洞察 / 学习信息摘要 / 预警 / 建议：都是和中间明细区同款的 chart-card ──
.card-hint { font-size: 12px; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; min-width: 0; }
.card-empty { padding: 18px 0 6px; font-size: 13px; color: var(--text-3); }
.bottom-row { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 15px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.bottom-row .chart-card { display: flex; flex-direction: column; }
// 认知能力：左雷达、右表格，下面一排洞察
.cog-layout { display: grid; grid-template-columns: 260px minmax(0, 1fr); gap: 20px; align-items: center; margin-top: 6px; @media (max-width: 1100px) { grid-template-columns: 1fr; } }
.cog-layout .radar-chart { height: 250px; }
.cog-hls { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 10px; margin-top: 12px; }
.hl-chip { position: relative; padding: 9px 12px 9px 26px; border-radius: 10px; font-size: 13px; line-height: 1.6; color: var(--text-1);
  background: color-mix(in srgb, var(--text-3) 8%, transparent); border: 1px solid color-mix(in srgb, var(--text-3) 14%, transparent);
  .hl-item__dot { left: 11px; top: 16px; } }
.cog-empty { height: 120px; }
// 文字段落：不画方框，左侧一条细竖线 + 极淡底色，像引用
.quote { margin-top: 10px; padding: 10px 14px; border-radius: 0 10px 10px 0; font-size: 13px; line-height: 1.85; color: var(--text-1); white-space: pre-wrap; word-break: break-word;
  border-left: 2px solid color-mix(in srgb, var(--color-primary) 55%, transparent); background: color-mix(in srgb, var(--text-3) 7%, transparent); }
.count-badge { display: inline-block; min-width: 18px; height: 18px; margin-left: 8px; padding: 0 6px; border-radius: 999px; vertical-align: 1px; text-align: center; line-height: 18px; font-size: 11px; font-weight: 600;
  color: var(--amber); background: color-mix(in srgb, var(--amber) 18%, transparent); }
// 预警：每条是一行圆角浅底，不再用分隔线
.bottom-row .warn-list { margin-top: 10px; display: flex; flex-direction: column; gap: 8px; }
.bottom-row .warn-item { padding: 9px 12px; border: none; border-radius: 10px; background: color-mix(in srgb, var(--text-3) 8%, transparent); }
// 未处理预警：按紧急程度铺一层向右渐隐的底色（提示 = 主色、关注 = 琥珀、严重 = 红），一眼分出轻重
.bottom-row .warn-item--notice { background: linear-gradient(90deg, color-mix(in srgb, var(--color-primary) 22%, transparent), color-mix(in srgb, var(--color-primary) 2%, transparent) 85%); }
.bottom-row .warn-item--attention { background: linear-gradient(90deg, color-mix(in srgb, var(--amber) 24%, transparent), color-mix(in srgb, var(--amber) 2%, transparent) 85%); }
.bottom-row .warn-item--critical { background: linear-gradient(90deg, color-mix(in srgb, var(--red) 26%, transparent), color-mix(in srgb, var(--red) 2%, transparent) 85%); }
.warn-sub { margin: 14px 0 8px; font-size: 12px; color: var(--text-3); }
.bottom-row .warn-item--done { margin-bottom: 8px; background: transparent; border: 1px dashed color-mix(in srgb, var(--text-3) 22%, transparent); }
.tips--card { margin-top: 10px; .tip { margin-bottom: 9px; } }
.advice-refresh { flex-shrink: 0; border: none; background: transparent; padding: 0; font-size: 12px; color: var(--text-3); cursor: pointer; transition: color 0.2s; &:hover { color: var(--color-primary); } }
.chart-card__head .card-hint { margin-left: auto; }
// 生成中的骨架：5 行淡色条，带流光
.advice-skeleton { display: flex; flex-direction: column; gap: 14px; padding-top: 4px;
  i { display: block; height: 14px; border-radius: 7px; background: linear-gradient(90deg, color-mix(in srgb, var(--text-3) 10%, transparent) 25%, color-mix(in srgb, var(--text-3) 22%, transparent) 50%, color-mix(in srgb, var(--text-3) 10%, transparent) 75%); background-size: 200% 100%; animation: pf-shimmer 1.4s linear infinite;
    &:nth-child(2) { width: 88%; } &:nth-child(3) { width: 94%; } &:nth-child(4) { width: 76%; } &:nth-child(5) { width: 84%; } } }
@keyframes pf-shimmer { to { background-position: -200% 0; } }
// ── 暗色主题（参考图）：胶囊标签 / 按钮、小号大写表头、底部区块的深蓝玻璃 ──
</style>

<!-- 不加 scoped：下面的规则要同时带上主题选择器（html[data-theme=...]）和页面里的类名，scoped + :global 写法会把后半截选择器丢掉 -->
<style lang="scss">
// 图表分类色：以页面主色靛蓝为基准，沿色环取 靛蓝 / 青绿 / 紫 / 琥珀 / 玫红 / 天蓝，饱和度压低（亮色偏深、暗色偏亮），
// 相邻类型一眼能分开，又和页面的蓝紫基调、五力色同一家族。学科、难度、练习方式、时段各用一套，都在这里改
:root { --subj-math: #4f6bed; --subj-physics: #14a39a; --subj-chemistry: #9b6bdf; --subj-other: #aab0c0; }
html[data-theme="dark"] { --subj-math: #7f9bff; --subj-physics: #4fd0c4; --subj-chemistry: #b595ff; --subj-other: #5b617c; }
:root { --diff-basic: #a9bdf9; --diff-advanced: #6272e6; --diff-challenge: #3d4fc4; }
html[data-theme="dark"] { --diff-basic: #c4caf0; --diff-advanced: #8f97ea; --diff-challenge: #6a72d0; }
// 练习方式的圆环配色：取题目类型的那一套色（--qt-*：单选蓝 / 多选紫 / 填空黄 / 判断青 / 应用粉，与「答题类型分布」一致），不够的两种补中性灰和绿
:root { --type-kp: #3b82f6; --type-unit: #06b6d4; --type-err: #ec4899; --type-fav: #ca8a04; --type-smart: #8b5cf6; --type-random: #94a3b8; --type-sem: #10b981; }
html[data-theme="dark"] { --type-kp: #60a5fa; --type-unit: #22d3ee; --type-err: #f472b6; --type-fav: #facc15; --type-smart: #a78bfa; --type-random: #94a3b8; --type-sem: #34d399; }

// 暗色主题（参考图）：更深的蓝黑底 + 右上角淡薰衣草光；强调色偏灰的薰衣草蓝紫；
// 胶囊标签 / 按钮、小号大写表头；亮色主题的统计卡 / 图表卡配色
html[data-theme="dark"] .page-root {
  // 参考图的暗色：更深的蓝黑底，右上角一团淡薰衣草光；强调色是偏灰的薰衣草蓝紫，次要文字带一点蓝紫
  --text-3: #9aa2c4; --text-2: #c3c9e6; --color-primary: #9aa4ef; --el-color-primary: #9aa4ef;
  background:
    radial-gradient(900px circle at 100% -8%, rgba(120, 132, 214, 0.20), transparent 62%),
    radial-gradient(700px circle at 0% 112%, rgba(80, 90, 170, 0.10), transparent 60%);
}

// 亮色：全局次要文字色 --text-3 是 #94A3B8，落在浅色卡片（#F4F7FF）上对比度只有 2.5:1 左右，看不清；本页压深到 WCAG AA（≥ 4.5:1）
html[data-theme="light"] .page-root { --text-3: #64708a; --text-2: #46506b; }

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

// ═══ 质感精修（只增不改：入场动效 / 悬停反馈 / 标题层次 / 进度条 / 选中态）═══
@keyframes pf-rise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
:root { --pf-ease: cubic-bezier(0.22, 1, 0.36, 1); }

// 入场：各行依次上浮淡入；切换顶部统计卡时中间明细区也会重播，形成过渡
.page-root .kpi-strip > .kpi, .page-root .chart-row > *, .page-root .detail-row > *, .page-root > .cog-card, .page-root .bottom-row > * {
  animation: pf-rise 0.5s var(--pf-ease) backwards; }
.page-root .kpi-strip > .kpi:nth-child(2) { animation-delay: 0.04s; } .page-root .kpi-strip > .kpi:nth-child(3) { animation-delay: 0.08s; }
.page-root .kpi-strip > .kpi:nth-child(4) { animation-delay: 0.12s; } .page-root .kpi-strip > .kpi:nth-child(5) { animation-delay: 0.16s; }
.page-root .chart-row > * { animation-delay: 0.08s; } .page-root .detail-row > * { animation-delay: 0.14s; }
.page-root .detail-row > *:nth-child(2) { animation-delay: 0.19s; } .page-root .detail-row > *:nth-child(3) { animation-delay: 0.24s; }
.page-root > .cog-card { animation-delay: 0.1s; }

// 选中的统计卡：描边提亮（上面 scoped 块里的 .kpi--active）+ 底部一条主色光带
.page-root .kpi.kpi--active::after { content: ''; position: absolute; left: 16px; right: 16px; bottom: 0; height: 2px; z-index: 3; border-radius: 2px 2px 0 0;
  background: linear-gradient(90deg, transparent, var(--color-primary), transparent); animation: pf-rise 0.4s var(--pf-ease) backwards; }
html[data-theme="dark"] .page-root .kpi.kpi--active::after { box-shadow: 0 0 12px var(--color-primary); }

// 数字：等宽 + 等宽数字，数值更精致
.page-root .kpi__val { font-variant-numeric: tabular-nums; font-feature-settings: 'tnum' 1; }
.page-root .kpi__lbl { font-weight: 500; letter-spacing: 0.02em; }

// 卡片标题：加一小段主色竖标，层次更清楚
.page-root .chart-card__title { position: relative; padding-left: 10px; font-size: 13.5px; font-weight: 600; letter-spacing: 0.03em; color: var(--text-2);
  &::before { content: ''; position: absolute; left: 0; top: 50%; width: 3px; height: 13px; margin-top: -6.5px; border-radius: 2px;
    background: linear-gradient(180deg, var(--color-primary), color-mix(in srgb, var(--color-primary) 35%, transparent)); } }
.page-root .chart-card__head { margin-bottom: 2px; }

// 科目切换：去掉外框和底色，做成轻量文字标签；选中项文字提亮 + 底部一小段主色下划线（从中间向两侧展开）
.page-root .seg { gap: 16px; margin: -4px 0; padding: 0; border: none; border-radius: 0; background: transparent; }
.page-root .seg__btn { position: relative; height: 24px; padding: 0 1px; border-radius: 0; background: transparent; font-size: 12.5px; line-height: 24px; color: var(--text-3); letter-spacing: 0.02em; transition: color 0.2s;
  &::after { content: ''; position: absolute; left: 0; right: 0; bottom: 0; height: 2px; border-radius: 2px; transform: scaleX(0); transform-origin: center;
    background: linear-gradient(90deg, transparent, var(--color-primary), transparent); transition: transform 0.35s var(--pf-ease); }
  &:hover { color: var(--text-2); background: transparent; }
  &.is-active { background: transparent; box-shadow: none; color: var(--text-1); font-weight: 600; &::after { transform: scaleX(1); } } }
.page-root .seg__btn:focus-visible, .page-root .kpi--link:focus-visible { outline: 2px solid color-mix(in srgb, var(--color-primary) 70%, transparent); outline-offset: 2px; }

// 进度条：更饱满的圆角 + 流畅的宽度动画 + 柔和高光
// 全页进度条统一高度（Top5 榜单、认知能力表；图表里的横向排行条 renderRankBars 的 BAR 也是这个值，改的时候两边一起改）
:root { --pf-bar-h: 10px; }
.page-root .bar { height: var(--pf-bar-h); border-radius: 999px; }
.page-root .bar__fill { position: relative; border-radius: 999px; transition: width 0.7s var(--pf-ease);
  background-image: linear-gradient(90deg, rgba(255, 255, 255, 0.0), rgba(255, 255, 255, 0.22)); background-blend-mode: overlay; }

// 榜单（知识点学习时长 / 训练次数 / 答题数 Top5、启发策略 Top5）：行间距 10px，进度条用渐变
// 颜色与折线图同源（学科色 --bar-c = subjColor），左端学科色 → 右端白色
.page-root .kp-list { gap: 10px; padding-top: 16px; }   // 与标题拉开 16px
.page-root .kp-row { height: 24px; }
// Top5 榜单（学习时长 / 训练次数 / 答题数 / 启发策略）：四列网格，名称列、数值列按本榜单里最宽的一项自适应（名称列最宽占 45%），
// 进度条夹在中间，所以进度条两端到最长的名称、最长的数值恰好都是 10px，每行进度条起点 / 终点对齐
.page-root .kp-list.kp-list--auto { display: grid; grid-template-columns: 20px fit-content(45%) minmax(0, 1fr) max-content; column-gap: 10px; row-gap: 10px; grid-auto-rows: 24px; align-content: start; align-items: center;
  .kp-row { display: contents; }
  .kp-row__val { white-space: nowrap; } }   // 行高收紧；行距 10px，整体靠上排
.page-root .kp-row .bar__fill { background-image: linear-gradient(90deg, var(--bar-c), #fff); background-blend-mode: normal; }
// 知识点榜单：前三名序号用主色
.page-root .kp-row:nth-child(-n+3) .kp-row__no { color: var(--color-primary); background: color-mix(in srgb, var(--color-primary) 18%, transparent); font-weight: 600; }
.page-root .kp-row__val { font-variant-numeric: tabular-nums; }

// 建议 / 总结：条目之间留白更舒展
.page-root .tip { line-height: 1.7; margin-bottom: 8px; }
.page-root .tip__no { font-weight: 600; }
// 总结卡：第一项的位置与同排 Top5 榜单卡对齐（榜单：上方留白 16px，行高 24px、内容垂直居中）
.page-root .chart-card__body--tips { padding-top: 16px; }
.page-root .chart-card__body--tips .tip { line-height: 24px; margin-bottom: 10px; }
.page-root .chart-card__body--tips .tip__no { margin-top: 3px; }
// 底部「建议」卡：同样对齐（标题行自带 2px 下边距，所以这里留 14px，合起来也是 16px）
.page-root .tips--card { margin-top: 14px; }
.page-root .tips--card .tip { line-height: 24px; margin-bottom: 10px; }
.page-root .tips--card .tip__no { margin-top: 3px; }
.page-root .tips--card.advice-skeleton { gap: 10px; padding-top: 0; i { height: 14px; margin: 5px 0; } }

// 引用段落：左侧竖线渐变，更像高级摘录
.page-root .quote { border-left: none; position: relative; padding-left: 18px; background: color-mix(in srgb, var(--text-3) 6%, transparent);
  &::before { content: ''; position: absolute; left: 0; top: 8px; bottom: 8px; width: 3px; border-radius: 2px;
    background: linear-gradient(180deg, var(--color-primary), color-mix(in srgb, var(--color-primary) 20%, transparent)); } }

.page-root .level-tag { letter-spacing: 0.04em; }
.page-root .count-badge { box-shadow: 0 0 0 3px color-mix(in srgb, var(--amber) 10%, transparent); }

// 内部滚动条（建议 / 总结卡）：细、淡
.page-root .chart-card__body--tips { scrollbar-width: thin; scrollbar-color: color-mix(in srgb, var(--text-3) 40%, transparent) transparent; }

// 尊重「减少动态效果」系统设置
@media (prefers-reduced-motion: reduce) {
  .page-root *, .page-root *::before, .page-root *::after { animation: none !important; transition: none !important; }
}


// ── 认知能力进度条（bar--fancy）：粗圆角轨道 + 同色渐变填充 + 顶部高光 + 末端小亮点 + 柔和光晕；正确率条带 60 / 80 / 90 分级刻度 ──
:root { --lv-excellent: #10b981; --lv-good: #3b82f6; --lv-ok: #f59e0b; --lv-fail: #ef4444; }
html[data-theme="dark"] { --lv-excellent: #34d399; --lv-good: #60a5fa; --lv-ok: #fbbf24; --lv-fail: #f87171; }
.lv--excellent { --bar-c: var(--lv-excellent); } .lv--good { --bar-c: var(--lv-good); } .lv--ok { --bar-c: var(--lv-ok); } .lv--fail { --bar-c: var(--lv-fail); }
@keyframes pf-grow { from { transform: scaleX(0); } to { transform: scaleX(1); } }
.page-root .bar--fancy { position: relative; height: var(--pf-bar-h); border-radius: 999px; overflow: visible;
  background: color-mix(in srgb, var(--text-3) 14%, transparent); box-shadow: inset 0 1px 2px rgba(0, 0, 0, 0.12);
  .bar__fill { position: relative; height: 100%; border-radius: 999px; transform-origin: left center; animation: pf-grow 0.9s var(--pf-ease) backwards;
    background-image: linear-gradient(90deg, color-mix(in srgb, var(--bar-c) 45%, transparent), var(--bar-c));
    box-shadow: 0 0 10px -1px color-mix(in srgb, var(--bar-c) 55%, transparent);
    // 顶部高光
    &::before { content: ''; position: absolute; left: 6px; right: 6px; top: 1.5px; height: 3px; border-radius: 3px; background: linear-gradient(180deg, rgba(255, 255, 255, 0.5), rgba(255, 255, 255, 0)); }
    // 末端亮点
    &::after { content: ''; position: absolute; right: 2px; top: 50%; width: 6px; height: 6px; margin-top: -3px; border-radius: 50%; background: #fff; box-shadow: 0 0 6px 1px color-mix(in srgb, var(--bar-c) 70%, transparent); } } }
// 0 分 / 无数据：宽度为 0，不画高光、亮点和光晕
.page-root .bar--fancy .bar__fill.is-zero { box-shadow: none; &::before, &::after { display: none; } }
// 分级刻度：60 / 80 / 90 三条细竖线，压在填充之上
.page-root .bar--scale::after { content: ''; position: absolute; inset: 0; border-radius: inherit; pointer-events: none;
  background:
    linear-gradient(90deg, transparent calc(60% - 0.5px), rgba(255, 255, 255, 0.55) calc(60% - 0.5px) calc(60% + 0.5px), transparent calc(60% + 0.5px)),
    linear-gradient(90deg, transparent calc(80% - 0.5px), rgba(255, 255, 255, 0.55) calc(80% - 0.5px) calc(80% + 0.5px), transparent calc(80% + 0.5px)),
    linear-gradient(90deg, transparent calc(90% - 0.5px), rgba(255, 255, 255, 0.55) calc(90% - 0.5px) calc(90% + 0.5px), transparent calc(90% + 0.5px)); opacity: 0.7; }
// 等级标签
.page-root .lv-chip { flex: none; min-width: 38px; padding: 0 8px; border-radius: 999px; text-align: center; font-size: 11.5px; line-height: 20px; font-weight: 600; white-space: nowrap;
  color: var(--bar-c); background: color-mix(in srgb, var(--bar-c) 15%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--bar-c) 30%, transparent); }

// ═══ 整体质感：顶部概览 Hero / 分区标题 / 学习投入度环 / AI 建议卡 ═══
.page-root > .hero, .page-root > .sec-title { animation: pf-rise 0.5s var(--pf-ease) backwards; }
.page-root > .sec-title { animation-delay: 0.05s; }

// 分区标题：小号字距 + 一条向右渐隐的细线，把页面分成清楚的几块
.page-root .sec-title { display: flex; align-items: center; gap: 12px; margin: 6px 0 -4px; flex-shrink: 0;
  span { font-size: 12px; font-weight: 600; letter-spacing: 0.22em; color: var(--text-2); }
  em { font-style: normal; font-size: 12px; color: var(--text-3); letter-spacing: 0.02em; }
  &::after { content: ''; flex: 1; height: 1px; order: 3; background: linear-gradient(90deg, color-mix(in srgb, var(--text-3) 40%, transparent), transparent); } }

// Hero —— 三层信息：
//   ① 身份（大字昵称 + 一行安静的小字）     ② 当前状态（环 + 状态 + 一句原因）      —— 第一眼
//   ③ 五力速览（五个等宽小方块）            ④ 累计学习（3×2 数据）                  —— 第二眼
// 规则：颜色只给「状态」和「五力」；其余全部用灰阶；所有板块共用同一套间距（外边距 24 / 板块间 20 / 内部 12）和同一种小标题
:root { --st-good: #10b981; --st-calm: #60a5fa; --st-warn: #f59e0b; --st-bad: #ef4444; --st-none: #8b92b0; }
.page-root .hero { overflow: hidden; display: flex; flex-direction: column; gap: 20px; padding: 24px; flex-shrink: 0;
  &::after { content: ''; position: absolute; right: -60px; top: -90px; width: 340px; height: 260px; border-radius: 50%; pointer-events: none; z-index: 0;
    background: radial-gradient(closest-side, color-mix(in srgb, var(--color-primary) 18%, transparent), transparent); }
  > * { position: relative; z-index: 1; } }
.hero__label { display: flex; align-items: baseline; gap: 10px; font-size: 12px; font-weight: 600; letter-spacing: 0.1em; color: var(--text-3);
  span { font-weight: 400; letter-spacing: 0.02em; } }

// 第一层
.hero__top { display: flex; align-items: center; justify-content: space-between; gap: 32px; @media (max-width: 1000px) { flex-direction: column; align-items: flex-start; } }
.hero__id { display: flex; align-items: center; gap: 18px; min-width: 0; }
.hero__avatar { flex: none; width: 60px; height: 60px; border-radius: 50%; display: flex; align-items: center; justify-content: center; overflow: hidden; font-size: 24px; font-weight: 600; color: #fff;
  background: linear-gradient(135deg, var(--color-primary), color-mix(in srgb, var(--color-primary) 40%, #7c3aed)); box-shadow: 0 8px 22px color-mix(in srgb, var(--color-primary) 36%, transparent), inset 0 0 0 2px rgba(255, 255, 255, 0.25);
  img { width: 100%; height: 100%; object-fit: cover; } }
.hero__txt { min-width: 0; }
.hero__namerow { display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }
.hero__name { font-size: 24px; font-weight: 600; line-height: 1.2; letter-spacing: 0.02em; color: var(--text-1); }
.hero__grade { font-size: 13px; font-weight: 600; color: var(--color-primary); }
.hero__minor { padding: 0 8px; border-radius: 999px; font-size: 11.5px; line-height: 20px; color: var(--text-2); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--text-3) 40%, transparent);
  &--bad { color: var(--st-bad); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--st-bad) 50%, transparent); } }
// 一行小字：手机号 · 加入 · 最近登录 · 家长（灰阶，圆点分隔；家长没绑定时用琥珀色轻提醒）
.hero__meta { display: flex; flex-wrap: wrap; margin-top: 8px; font-size: 12.5px; color: var(--text-3);
  span { white-space: nowrap; b { margin: 0 2px; font-weight: 600; color: var(--text-2); } &.is-warn { color: var(--st-warn); } }
  span + span::before { content: '·'; margin: 0 10px; color: var(--text-3); opacity: 0.6; } }

.hero__side { display: flex; align-items: center; gap: 18px; min-width: 0; }
.hero__status { min-width: 0; max-width: 360px; }
.hero__state { display: flex; align-items: center; gap: 8px; }
.hero__tag { font-size: 20px; font-weight: 600; letter-spacing: 0.04em; }
.hero__dot { width: 9px; height: 9px; border-radius: 50%; background: currentColor; box-shadow: 0 0 0 4px color-mix(in srgb, currentColor 18%, transparent), 0 0 10px currentColor; animation: pf-pulse 2.4s ease-in-out infinite; }
@keyframes pf-pulse { 50% { box-shadow: 0 0 0 7px color-mix(in srgb, currentColor 6%, transparent), 0 0 16px currentColor; } }
.hero .tone--good { color: var(--st-good); } .hero .tone--calm { color: var(--st-calm); } .hero .tone--warn { color: var(--st-warn); } .hero .tone--bad { color: var(--st-bad); } .hero .tone--none { color: var(--st-none); }
.hero__reason { margin-top: 6px; font-size: 12.5px; line-height: 1.6; color: var(--text-2); display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
// 预警小标：和状态同一行，颜色跟最高级别
.hero__warn { margin-left: 6px; padding: 0 9px; border-radius: 999px; font-size: 11.5px; line-height: 20px; font-weight: 400; letter-spacing: 0; white-space: nowrap;
  color: var(--wc); background: color-mix(in srgb, var(--wc) 14%, transparent);
  &.is-critical { --wc: var(--st-bad); } &.is-attention { --wc: var(--st-warn); } &.is-notice { --wc: var(--color-primary); } &.is-ok { --wc: var(--st-good); } }
// 投入度环：圆锥渐变进度（主色 → 白）；数字下面一行小字写「投入度」，不再需要单独标题
.page-root .ring { --p: 0; position: relative; flex: none; width: 76px; height: 76px; display: flex; flex-direction: column; align-items: center; justify-content: center;
  &::before { content: ''; position: absolute; inset: 0; border-radius: 50%;
    background: conic-gradient(from 0deg, var(--color-primary) 0, #fff calc(var(--p) * 1%), color-mix(in srgb, var(--text-3) 20%, transparent) 0);
    -webkit-mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px)); mask: radial-gradient(farthest-side, transparent calc(100% - 8px), #000 calc(100% - 7px));
    filter: drop-shadow(0 0 8px color-mix(in srgb, var(--color-primary) 45%, transparent)); }
  b { position: relative; font-size: 24px; font-weight: 500; line-height: 1; color: var(--text-1); }
  i { position: relative; margin-top: 3px; font-style: normal; font-size: 10.5px; color: var(--text-3); } }

// 第二层：左右两块，中间一条细分隔线，顶部与第一层之间也是一条细线
.hero__body { display: grid; grid-template-columns: minmax(0, 1.1fr) minmax(0, 1fr); gap: 0 40px; padding-top: 20px; border-top: 1px solid color-mix(in srgb, var(--text-3) 20%, transparent);
  @media (max-width: 1000px) { grid-template-columns: 1fr; gap: 20px; } }
.hero__power, .hero__stats { min-width: 0; }
.hero__stats { padding-left: 40px; border-left: 1px solid color-mix(in srgb, var(--text-3) 20%, transparent); @media (max-width: 1000px) { padding-left: 0; border-left: none; } }

// 五力：五个等宽小方块，图标 + 得分 + 名称；最强项底色加深，其余样式一致（强弱在下面一行文字里说明）（说明文字在下面一行）
.pw-row { display: grid; grid-template-columns: repeat(5, minmax(0, 1fr)); gap: 10px; margin-top: 12px; }
.pw { display: flex; flex-direction: column; align-items: center; gap: 4px; padding: 12px 4px 10px; border-radius: 12px;
  background: color-mix(in srgb, var(--pc) 7%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--pc) 16%, transparent);
  &.is-strong { background: color-mix(in srgb, var(--pc) 16%, transparent); box-shadow: inset 0 0 0 1px color-mix(in srgb, var(--pc) 50%, transparent); } }
.pw__ico { display: inline-flex; align-items: center; justify-content: center; width: 26px; height: 26px; border-radius: 8px; color: var(--pc); background: color-mix(in srgb, var(--pc) 16%, transparent); }
.pw__num { font-size: 20px; font-weight: 500; line-height: 1.1; color: var(--text-1); }
.pw__name { font-size: 12px; color: var(--text-2); }
.hero__cap { margin-top: 12px; font-size: 12.5px; line-height: 1.6; color: var(--text-2); &--empty { margin-top: 20px; color: var(--text-3); } }

// 累计学习：3 列 × 2 行，每格 = 小标题 / 数字 / 一行补充
.hs-grid { display: grid; grid-template-columns: repeat(3, minmax(0, 1fr)); gap: 16px 24px; margin-top: 12px; }
.hs { min-width: 0; }
.hs__lbl { font-size: 12px; color: var(--text-3); white-space: nowrap; }
.hs__val { margin-top: 3px; font-size: 22px; font-weight: 400; line-height: 1.15; letter-spacing: -0.02em; color: var(--text-1); white-space: nowrap;
  small { margin-left: 4px; font-size: 12px; letter-spacing: 0; color: var(--text-2); } }
.hs__bar { margin-top: 6px; }
.hs__sub { margin-top: 3px; font-size: 12px; color: var(--text-3); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }

// 顶部统计卡数字：暗色下用白 → 淡蓝紫的纵向渐变字，更有质感
html[data-theme="dark"] .page-root .kpi__val { background: linear-gradient(180deg, #ffffff 30%, #aab3ec); -webkit-background-clip: text; background-clip: text; -webkit-text-fill-color: transparent;
  .kpi__unit { -webkit-text-fill-color: var(--text-2); } }

// AI 建议卡：标题旁的 AI 徽章 + 缓慢流动的渐变描边，和别的卡片区分开
.page-root .ai-badge { display: inline-flex; align-items: center; gap: 3px; margin-left: 8px; padding: 0 8px; height: 18px; border-radius: 999px; font-size: 11px; line-height: 1; font-weight: 600; letter-spacing: 0.06em; color: #fff;
  background: linear-gradient(135deg, var(--color-primary), #a78bfa); box-shadow: 0 2px 8px color-mix(in srgb, var(--color-primary) 40%, transparent); }
// 标题和 AI 徽章：之前徽章是行内元素 + vertical-align 微调，和标题文字的基线对不齐；改成弹性布局，两者按中线垂直居中
.page-root .advice-card .chart-card__title { display: flex; align-items: center; line-height: 1.4; }
.page-root .ai-badge svg { flex: none; display: block; }
.page-root .advice-card::before { background: linear-gradient(120deg, var(--color-primary), transparent 30%, transparent 70%, #a78bfa, var(--color-primary)); background-size: 220% 220%; animation: pf-flow 8s linear infinite; opacity: 0.8; }
@keyframes pf-flow { to { background-position: 220% 220%; } }

// ── 表格（.mini-table）：和卡片融成一体，不分层 ──
// 没有表头底色、没有斑马纹、没有外框；表头只是一行小号淡色文字，下面一条细线；行与行之间用极淡的细线，悬停无背景变化。
// el-table 内部会重新定义变量，所以这里直接在 .el-table 作用域里覆盖，并写死颜色
:root { --tbl-line: rgba(96, 141, 248, 0.14); --tbl-head: #66708c; --tbl-text: #2d3550; --tbl-text-2: #4e5877; }
html[data-theme="dark"] { --tbl-line: rgba(210, 216, 255, 0.08); --tbl-head: #9aa2c4; --tbl-text: #e6e9f7; --tbl-text-2: #b8bedb; }
.page-root .mini-table.el-table {
  --el-table-bg-color: transparent; --el-table-tr-bg-color: transparent; --el-table-header-bg-color: transparent;
  --el-table-row-hover-bg-color: transparent; --el-table-border-color: transparent; --el-table-border: none;
  --el-table-text-color: var(--tbl-text); --el-table-header-text-color: var(--tbl-head);
  background: transparent; font-size: 13px;
  &::before, .el-table__inner-wrapper::before { display: none; }
  .el-table__inner-wrapper { border: none !important; border-radius: 0; }
  .el-table__inner-wrapper, .el-table__header-wrapper, .el-table__body-wrapper, thead, tbody, tr { background: transparent !important; }
  th.el-table__cell { background: transparent !important; height: auto; padding: 4px 0 8px; border-bottom: 1px solid var(--tbl-line) !important; color: var(--tbl-head) !important;
    font-size: 11.5px; font-weight: 500; letter-spacing: 0.04em; text-transform: none; }
  td.el-table__cell { height: auto; padding: 10px 0; border-bottom: 1px solid var(--tbl-line) !important; color: var(--tbl-text); background: transparent !important; transition: background .2s; }
  tr:last-child td.el-table__cell { border-bottom: none !important; }
  .cell { padding: 0 !important; color: inherit; line-height: 1.5; }
  th.el-table__cell, td.el-table__cell { padding-left: 8px !important; padding-right: 8px !important; }
  th.el-table__cell:first-child, td.el-table__cell:first-child { padding-left: 0 !important; }
  th .cell { color: inherit; }
  tbody tr > td.el-table__cell:first-child { border-radius: 8px 0 0 8px; }
  tbody tr > td.el-table__cell:last-child { border-radius: 0 8px 8px 0; }
  .el-table__empty-block { background: transparent; }
  .el-table__empty-text { color: var(--tbl-head); }
  .cause-mini { color: var(--tbl-text-2); }
}
</style>
