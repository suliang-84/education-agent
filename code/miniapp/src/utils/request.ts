/**
 * 网络请求封装
 * 统一处理：Token 注入、401 自动刷新、错误提示
 */
import { STORAGE_KEYS } from '@/constants'

const BASE_URL = import.meta.env.VITE_API_BASE_URL as string

// 是否正在刷新 Token（防并发）
let isRefreshing = false
let pendingQueue: Array<(token: string) => void> = []

/** 统一响应结构 */
interface ApiResponse<T = unknown> {
  code: number
  msg: string
  data: T
}

function getToken(): string {
  return uni.getStorageSync(STORAGE_KEYS.ACCESS_TOKEN) || ''
}

function getRefreshToken(): string {
  return uni.getStorageSync(STORAGE_KEYS.REFRESH_TOKEN) || ''
}

function saveTokens(accessToken: string, refreshToken?: string) {
  uni.setStorageSync(STORAGE_KEYS.ACCESS_TOKEN, accessToken)
  if (refreshToken) {
    uni.setStorageSync(STORAGE_KEYS.REFRESH_TOKEN, refreshToken)
  }
}

async function doRefreshToken(): Promise<string> {
  const refreshToken = getRefreshToken()
  if (!refreshToken) throw new Error('无 refresh_token')

  const res = await new Promise<UniApp.RequestSuccessCallbackResult>((resolve, reject) => {
    uni.request({
      url: `${BASE_URL}/auth/token/refresh`,
      method: 'POST',
      data: { refresh_token: refreshToken },
      success: resolve,
      fail: reject,
    })
  })

  const body = res.data as ApiResponse<{ access_token: string; refresh_token?: string }>
  if (body.code !== 200) throw new Error(body.msg)

  const { access_token, refresh_token } = body.data
  saveTokens(access_token, refresh_token)
  return access_token
}

function redirectToLogin() {
  uni.removeStorageSync(STORAGE_KEYS.ACCESS_TOKEN)
  uni.removeStorageSync(STORAGE_KEYS.REFRESH_TOKEN)
  uni.removeStorageSync(STORAGE_KEYS.USER_INFO)
  uni.reLaunch({ url: '/pages/auth/login' })
}

/**
 * 核心请求函数
 */
export function request<T = unknown>(
  options: UniApp.RequestOptions & { skipAuth?: boolean }
): Promise<T> {
  return new Promise((resolve, reject) => {
    const { skipAuth = false, ...restOptions } = options

    const doRequest = (token?: string) => {
      uni.request({
        ...restOptions,
        url: `${BASE_URL}${restOptions.url}`,
        header: {
          'Content-Type': 'application/json',
          ...(token ? { Authorization: `Bearer ${token}` } : {}),
          ...restOptions.header,
        },
        success(res) {
          const body = res.data as ApiResponse<T>

          if (res.statusCode === 401) {
            // Token 过期，尝试刷新
            if (isRefreshing) {
              pendingQueue.push((newToken) => doRequest(newToken))
              return
            }
            isRefreshing = true
            doRefreshToken()
              .then((newToken) => {
                pendingQueue.forEach((cb) => cb(newToken))
                pendingQueue = []
                doRequest(newToken)
              })
              .catch(() => {
                pendingQueue = []
                redirectToLogin()
                reject(new Error('登录已过期，请重新登录'))
              })
              .finally(() => {
                isRefreshing = false
              })
            return
          }

          if (body.code !== 200) {
            uni.showToast({ title: body.msg || '请求失败', icon: 'none', duration: 2000 })
            reject(new Error(body.msg))
            return
          }

          resolve(body.data)
        },
        fail(err) {
          uni.showToast({ title: '网络异常，请检查连接', icon: 'none', duration: 2000 })
          reject(err)
        },
      })
    }

    doRequest(skipAuth ? undefined : getToken())
  })
}

// 快捷方法
export const http = {
  get<T = unknown>(url: string, data?: Record<string, unknown>, options?: Partial<UniApp.RequestOptions>) {
    return request<T>({ ...options, url, method: 'GET', data })
  },
  post<T = unknown>(url: string, data?: unknown, options?: Partial<UniApp.RequestOptions>) {
    return request<T>({ ...options, url, method: 'POST', data })
  },
  patch<T = unknown>(url: string, data?: unknown, options?: Partial<UniApp.RequestOptions>) {
    return request<T>({ ...options, url, method: 'PUT', data })
  },
  delete<T = unknown>(url: string, data?: unknown, options?: Partial<UniApp.RequestOptions>) {
    return request<T>({ ...options, url, method: 'DELETE', data })
  },
}
