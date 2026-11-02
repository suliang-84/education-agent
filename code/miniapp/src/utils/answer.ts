/**
 * 训练答题：按题型的作答状态、提交内容拼装、从已存文本还原
 *
 * 作答模式（AnswerMode）由题型 + 题目数据决定：
 *   single       单选，选项列表 + 单选组件
 *   multi        多选，选项列表 + 复选框
 *   tf           判断，「对 / 错」单选组件
 *   fill         填空，按空数逐行输入
 *   application  应用题，「解题过程」+「最终答案」两栏
 *   text         其它：多行文本框（简答题预留、选项拆分失败的选择题、没有题型的题）
 *
 * 提交内容与后端判题规则一一对应（见接口设计说明书 §5.2）。
 */
import type { TrainingQuestion } from '@/api/training'

export type AnswerMode = 'single' | 'multi' | 'tf' | 'fill' | 'application' | 'text'

export interface AnswerState {
  text: string        // text 模式的作答 / 应用题的「解题过程」
  selected: string[]  // 单选 / 多选 / 判断：选中的 key（判断为「对」「错」）
  blanks: string[]    // 填空：每个空一项
  final: string       // 应用题的「最终答案」
}

export const TF_OPTIONS = ['对', '错'] as const
const BLANK_JOIN = '；'

export function emptyAnswer(blankCount = 0): AnswerState {
  return { text: '', selected: [], blanks: Array.from({ length: blankCount }, () => ''), final: '' }
}

export function answerMode(q: TrainingQuestion | null | undefined): AnswerMode {
  if (!q) return 'text'
  const t = String(q.question_type || '').toUpperCase()
  const hasOptions = Array.isArray(q.options) && q.options.length >= 2
  if (t === 'SINGLE_CHOICE') return hasOptions ? 'single' : 'text'
  if (t === 'MULTIPLE_CHOICE') return hasOptions ? 'multi' : 'text'
  if (t === 'TRUE_FALSE') return 'tf'
  if (t === 'FILL_BLANK') return (q.blank_count ?? 0) >= 1 ? 'fill' : 'text'
  if (t === 'APPLICATION') return 'application'
  return 'text'
}

/** 应用题的展示文本：解题过程 + 最终答案 */
export function composeApplicationText(process: string, final: string): string {
  const parts: string[] = []
  if (process.trim()) parts.push(`解题过程：${process.trim()}`)
  if (final.trim()) parts.push(`最终答案：${final.trim()}`)
  return parts.join('\n')
}

/** 作答的展示文本（也是写入答题记录 / 错题集的 student_answer）；未作答返回空串 */
export function answerText(mode: AnswerMode, s: AnswerState): string {
  switch (mode) {
    case 'single':
    case 'tf':
      return s.selected[0] ?? ''
    case 'multi':
      return [...s.selected].sort().join('')
    case 'fill':
      return s.blanks.some((b) => b.trim()) ? s.blanks.map((b) => b.trim()).join(BLANK_JOIN) : ''
    case 'application':
      return composeApplicationText(s.text, s.final)
    default:
      return s.text.trim()
  }
}

/** 拼装提交接口的请求体里与作答有关的三个字段（student_answer 为空时传 undefined，后端按未作答判错） */
export function buildSubmit(mode: AnswerMode, s: AnswerState): {
  student_answer?: string
  student_answers?: string[]
  final_answer?: string
} {
  const text = answerText(mode, s)
  const out: { student_answer?: string; student_answers?: string[]; final_answer?: string } = {
    student_answer: text || undefined,
  }
  if (mode === 'fill') out.student_answers = s.blanks.map((b) => b.trim())
  if (mode === 'application') out.final_answer = s.final.trim()
  return out
}

/** 从已保存的文本还原作答状态（答题卡跳回已答题目 / 中断恢复时用，只读展示） */
export function restoreAnswer(q: TrainingQuestion | null | undefined, saved: string): AnswerState {
  const mode = answerMode(q)
  const s = emptyAnswer(mode === 'fill' ? q?.blank_count ?? 0 : 0)
  const text = saved || ''
  switch (mode) {
    case 'single':
    case 'tf':
      if (text) s.selected = [text]
      break
    case 'multi':
      s.selected = text.split('')
      break
    case 'fill': {
      const parts = text ? text.split(BLANK_JOIN) : []
      s.blanks = s.blanks.map((_, i) => parts[i] ?? '')
      break
    }
    case 'application': {
      const m = /(?:^|\n)最终答案：([\s\S]*)$/.exec(text)
      s.final = m ? m[1] : ''
      const p = /^解题过程：([\s\S]*?)(?:\n最终答案：|$)/.exec(text)
      s.text = p ? p[1] : m ? '' : text
      break
    }
    default:
      s.text = text
  }
  return s
}

/** 常用数学符号（快捷条）：乘除、角度、根号、圆周率、比较、括号，以及上标数字（手机键盘很难输入） */
export const MATH_SYMBOLS = [
  '×', '÷', '°', '√', 'π', '±', '≤', '≥', '≠', '(', ')', '/',
  '⁰', '¹', '²', '³', '⁴', '⁵', '⁶', '⁷', '⁸', '⁹', '⁻',
]
