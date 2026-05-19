/** API 服务层 — 封装与后端的 HTTP 通信 */
import axios from 'axios'
import type { TripPlanRequest, TripPlan } from '../types'

// 开发环境走 Vite proxy，生产环境用环境变量指定的后端地址
const API_BASE = import.meta.env.VITE_API_BASE_URL || '/api'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 600000, // 10分钟超时(Agent调用耗时较长)
  headers: {
    'Content-Type': 'application/json',
  },
})

// 请求拦截器 — 日志记录
api.interceptors.request.use(
  (config) => {
    console.log(`[API] ${config.method?.toUpperCase()} ${config.url}`)
    return config
  },
  (error) => Promise.reject(error)
)

// 响应拦截器 — 错误统一处理
api.interceptors.response.use(
  (response) => {
    console.log(`[API] 响应 ${response.status}`)
    return response
  },
  (error) => {
    const msg = error.response?.data?.detail || error.message || '网络请求失败'
    console.error('[API] 错误:', msg)
    return Promise.reject(new Error(msg))
  }
)

/**
 * 生成旅行计划
 * @param request 旅行需求参数
 * @returns 完整的旅行计划
 */
export const generateTripPlan = async (
  request: TripPlanRequest
): Promise<TripPlan> => {
  const response = await api.post<TripPlan>('/trip/plan', request)
  return response.data
}

/**
 * 健康检查
 */
export const healthCheck = async (): Promise<{
  status: string
  llm_configured: boolean
  amap_configured: boolean
  unsplash_configured: boolean
}> => {
  const response = await api.get('/trip/health')
  return response.data
}

export default api
