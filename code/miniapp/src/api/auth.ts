/**
 * 认证与账户模块 API — §2
 */
import { http } from '@/utils/request'

export interface WxLoginReq {
  code: string
  nickname?: string
  avatar_url?: string
}

export interface UserInfo {
  student_id: number
  nickname: string
  grade: string | null
  semester: string | null
  has_five_power_profile: boolean
}

export interface TokenResp {
  access_token: string
  refresh_token: string
  access_expires_in: number
  user_info: UserInfo
}

export interface NewUserResp {
  temp_token: string
  is_new_user: true
  nickname: string
  avatar_url: string
}

export const authApi = {
  /** 微信登录 */
  wxLogin: (data: WxLoginReq) =>
    http.post<TokenResp | NewUserResp>('/auth/wx-login', data, { skipAuth: true } as never),

  /** 发送短信验证码（开发固定 123456） */
  sendSms: (phone: string, purpose: string) =>
    http.post('/auth/sms/send', { phone, purpose }, { skipAuth: true } as never),

  /** 绑定手机号完成注册（携带 temp_token） */
  bindPhone: (data: { phone: string; sms_code: string; grade?: string; semester?: string }, tempToken: string) =>
    http.post<TokenResp>('/auth/bind-phone-with-token', data, {
      header: { Authorization: `Bearer ${tempToken}` },
      skipAuth: true,
    } as never),

  /** 刷新 Token */
  refreshToken: (refreshToken: string) =>
    http.post<{ access_token: string; refresh_token: string; access_expires_in: number }>(
      '/auth/token/refresh',
      { refresh_token: refreshToken },
      { skipAuth: true } as never
    ),

  /** 退出登录 */
  logout: () => http.post('/auth/logout'),

  /** 生成家长邀请码 */
  generateInviteCode: () =>
    http.post<{ code: string; expire_at: string; expire_hours: number }>('/auth/invite-code'),
}
