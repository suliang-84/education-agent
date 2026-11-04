/**
 * AI 助教模块 API — §7
 *
 * 单一永久会话：进入助教页就是同一个会话，历史自动加载；没有「新对话 / 结束对话 / 历史记录」。
 */
import { http } from '@/utils/request'

export interface ChatMessage {
  message_id: number
  role: 'student' | 'assistant'
  content: string
  image_url?: string | null        // 学生随消息发送的图片（服务端相对路径，用 assetUrl() 补全）
  is_aha_trigger: boolean          // 理解突破的成就感反馈消息（特殊样式）
  rating?: 'like' | 'dislike' | null
  created_at: string
}

export interface SendResult extends ChatMessage {
  student_message_id: number       // 刚发出的学生消息在服务端的 id（用于替换本地临时消息）
  silence: boolean                 // 是否处于沉默模式（AI 暂停主动引导）
}

export const assistantApi = {
  /** 获取或创建永久会话（新会话会带一条个性化开场白） */
  getSession: () =>
    http.post<{ session_id: string; is_new: boolean; silence: boolean }>('/assistant/session'),

  /** 历史消息（分页，向上翻页）：不传 before_id 取最新一页 */
  getMessages: (session_id: string, before_id?: number, limit = 30) =>
    http.get<{ messages: ChatMessage[]; has_more: boolean }>(
      '/assistant/messages',
      before_id ? { session_id, before_id, limit } : { session_id, limit },
    ),

  /** 发送消息。大模型较慢，请求超时放宽到 90 秒；失败原因（内容安全 / 过长 / AI 不可用）由请求层弹出提示 */
  sendMessage: (session_id: string, content: string, image_url?: string) =>
    http.post<SendResult>('/assistant/message', { session_id, content, image_url }, { timeout: 90000 } as never),

  /** 重新生成这条回复（换一种启发策略），原消息被替换 */
  regenerate: (session_id: string, message_id: number) =>
    http.post<ChatMessage>(`/assistant/message/${message_id}/regenerate?session_id=${encodeURIComponent(session_id)}`, undefined, { timeout: 90000 } as never),

  /** 消息评分（点赞 / 点踩），用于优化之后的启发策略选择 */
  rateMessage: (message_id: number, rating: 'like' | 'dislike') =>
    http.patch(`/assistant/message/${message_id}/rating`, { rating }),

  /** 解除沉默模式，恢复 AI 引导 */
  resumeSilence: (session_id: string) =>
    http.post(`/assistant/silence/resume?session_id=${encodeURIComponent(session_id)}`),

  /** 退出助教页 / 小程序退到后台时调用：通知服务端按需更新摘要和个人洞察（立即返回，静默） */
  digest: () => http.post<{ scheduled: boolean }>('/assistant/digest', undefined, { silent: true } as never),

  /** 快捷提问（按学生的薄弱知识点、错题、五力生成） */
  getSuggestions: () => http.get<{ suggestions: string[] }>('/assistant/suggestions'),

  /** 图片提问：先上传图片（只保存，不解析），拿到 image_url 后随消息一起发给 AI 助教，由助教回答 */
  uploadImage: (image_base64: string, media_type: string) =>
    http.post<{ image_url: string }>('/assistant/image', { image_base64, media_type }, { timeout: 60000 } as never),
}
