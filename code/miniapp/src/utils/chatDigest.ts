/**
 * AI 助教「退出时更新摘要」
 *
 * 学生退出助教页（切到别的 Tab / 进入别的页面）或小程序退到后台时，通知服务端按需更新对话摘要、个人洞察和聊天困惑信号。
 * 接口立即返回、更新在服务端后台做，所以小程序随后被系统挂起也不影响；没有新聊天内容时服务端什么都不做。
 * 只在这次启动里聊过天（dirty）才调用，避免无谓的请求；退出时那次请求丢了也没关系——下次进入助教页服务端会补一次。
 */
import { assistantApi } from '@/api'

let dirty = false

/** 聊过天（发出了新消息）后调用 */
export function markChatDirty() {
  dirty = true
}

/** 退出助教页 / 小程序退到后台时调用 */
export function flushChatDigest() {
  if (!dirty) return
  dirty = false
  assistantApi.digest().catch(() => { dirty = true })   // 失败（比如网络断了）保留标记，下次退出再试
}
