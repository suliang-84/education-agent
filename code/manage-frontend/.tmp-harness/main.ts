import { createApp } from 'vue'
import ElementPlus from 'element-plus'
import 'element-plus/dist/index.css'
import zhCn from 'element-plus/es/locale/lang/zh-cn'
import '../src/style.scss'
import 'virtual:svg-icons-register'
import SvgIcon from '@/components/SvgIcon.vue'
import View from '../src/views/students/StudentProfileView.vue'
document.documentElement.setAttribute('data-theme', new URLSearchParams(location.search).get('theme') || 'dark')
const log: string[] = []
const push = (s: string) => { log.push(s); document.title = 'ERR ' + JSON.stringify(log).slice(0, 1500) }
window.addEventListener('error', (e) => push('onerror ' + e.message))
window.addEventListener('unhandledrejection', (e) => push('rejection ' + String((e.reason && e.reason.stack) || e.reason)))
const app = createApp(View)
app.config.errorHandler = (err: any, _i, info) => push('vue ' + info + ' ' + String(err && err.stack || err))
app.config.warnHandler = (msg) => push('warn ' + msg)
app.component('SvgIcon', SvgIcon)
app.config.globalProperties.$router = { push() {} }
app.use(ElementPlus, { locale: zhCn })
app.mount('#app')
setTimeout(() => { const r = document.querySelector('.page-root') as HTMLElement | null; document.body.setAttribute('data-done', JSON.stringify({ has: !!r, h: r?.getBoundingClientRect().height, kids: r?.children.length, text: (r?.innerText || '').slice(0, 200) })) }, 2500)
