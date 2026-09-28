/**
 * 智能助教模块 API — §7
 */
import { http } from '@/utils/request'

export interface ChatMessage {
  message_id: number
  role: 'student' | 'assistant'
  content: string
  is_aha_trigger: boolean
  created_at: string
}

export interface ChatSession {
  session_id: string
  session_mode: string
  status: string
  aha_count: number
  session_summary: string | null
  started_at: string
}

export const assistantApi = {
  /** 创建对话会话 */
  createSession: (data: {
    session_mode?: string
    linked_question_id?: number
    linked_wrong_id?: string
  }) => http.post<{ session_id: string; session_mode: string }>('/assistant/session', data),

  /** 发送消息 */
  sendMessage: (session_id: string, content: string) =>
    http.post<ChatMessage>('/assistant/message', { session_id, content }),

  /** 获取历史消息 */
  getMessages: (session_id: string) =>
    http.get<ChatMessage[]>('/assistant/messages', { session_id }),

  /** 消息评分（like/dislike） */
  rateMessage: (message_id: number, rating: 'like' | 'dislike') =>
    http.patch(`/assistant/message/${message_id}/rating`, { rating }),

  /** 结束会话 */
  endSession: (session_id: string) =>
    http.post(`/assistant/session/${session_id}/end`),

  /** 获取会话列表 */
  getSessions: () => http.get<ChatSession[]>('/assistant/sessions'),
}
