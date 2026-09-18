import axios from 'axios'
import { ElMessage } from 'element-plus'
import { TOKEN_KEY } from '@/utils/constants'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1/admin',
  timeout: 15000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem(TOKEN_KEY)
  if (token) {
    config.headers['Authorization'] = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => {
    const { data } = response
    if (data.code === 200) {
      return data.data
    }
    ElMessage.error(data.msg || '操作失败')
    return Promise.reject(new Error(data.msg))
  },
  (error) => {
    const status = error.response?.status
    const msg = error.response?.data?.msg
    if (status === 401) {
      localStorage.removeItem(TOKEN_KEY)
      router.push('/login')
      ElMessage.error(msg || '登录已过期，请重新登录')
    } else {
      ElMessage.error(msg || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default request
