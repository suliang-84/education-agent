import { createApp, h, ref, nextTick } from 'vue'
import ElementPlus, { ElDatePicker } from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import '../src/style.scss'

const app = createApp({
  setup() {
    const v = ref<[string, string]>(['2026-11-10', '2026-11-16'])
    return () => h('main', { class: 'content-area' }, [h('div', { class: 'page-root' }, [h('div', { class: 'form-topbar', style: 'display:flex;gap:10px;align-items:center' }, [
      h('div', { style: 'flex:1' }),
      h(ElDatePicker, { id: 'dp', modelValue: v.value, 'onUpdate:modelValue': (x: any) => (v.value = x), type: 'daterange', clearable: false, editable: false,
        rangeSeparator: '–', format: 'YYYY-MM-DD', valueFormat: 'YYYY-MM-DD', style: 'width:300px;flex:none' }),
      h('button', { id: 'btn' }, '摘要'),
    ])])])
  },
})
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
setTimeout(() => {
  const el = document.querySelector('.el-date-editor') as HTMLElement
  const cs = getComputedStyle(el)
  const kids = [...el.children].map((c) => `${c.className}:${(c as HTMLElement).getBoundingClientRect().width.toFixed(0)}`)
  const hits: string[] = []
  const walk = (rules: CSSRuleList) => { for (const r of Array.from(rules)) {
    const any = r as any
    if (any.cssRules && !any.selectorText) { walk(any.cssRules); continue }
    if (!any.selectorText) continue
    try { if (el.matches(any.selectorText) && /(flex|width|grow|basis|inline-size|zoom|scale|transform)/.test(any.style.cssText)) hits.push(any.selectorText + ' => ' + any.style.cssText.split(';').filter((x: string) => /(flex|width|grow|basis|inline-size|zoom|scale|transform)/.test(x)).join(';')) } catch (e) {}
  } }
  for (const sh of Array.from(document.styleSheets)) { try { walk(sh.cssRules) } catch (e) {} }
  document.title = 'HITS ' + JSON.stringify(hits)
  document.body.setAttribute('data-hits', '1')
  void 0
  const _t = 'RESULT '
  document.title += ' ' + _t + JSON.stringify({ rect: el.getBoundingClientRect().width, cssWidth: cs.width, inline: el.getAttribute('style'), cls: el.className, boxSizing: cs.boxSizing, minW: cs.minWidth, kids, zoom: (cs as any).zoom, root: document.getElementById('app')!.firstElementChild!.getBoundingClientRect().width })
  document.body.setAttribute('data-done', '1')
}, 800)
