import request from './request'
import type {
  PositionInfo,
  PerformanceSummary,
  PerformanceRankingResponse,
  EmployeePerformance,
  ResponsibilityTraceResponse,
} from '@/types'

export interface RankingQuery {
  start_date?: string
  end_date?: string
  store_id?: string
  position?: string
  sort_by?: 'score' | 'total_operations' | 'on_time_rate' | 'loss_rate'
  page?: number
  page_size?: number
}

export interface TraceQuery {
  target_type: 'bucket' | 'flower' | 'warning' | 'batch'
  target_id: string
}

export const performanceApi = {
  positions: () => request.get<unknown, PositionInfo[]>('/performance/positions'),

  summary: (params?: { start_date?: string; end_date?: string; store_id?: string }) =>
    request.get<unknown, PerformanceSummary>('/performance/summary', { params }),

  ranking: (params?: RankingQuery) =>
    request.get<unknown, PerformanceRankingResponse>('/performance/ranking', { params }),

  employee: (userId: string, params?: { start_date?: string; end_date?: string }) =>
    request.get<unknown, EmployeePerformance>(`/performance/employee/${userId}`, { params }),

  trace: (params: TraceQuery) =>
    request.get<unknown, ResponsibilityTraceResponse>('/performance/responsibility-trace', { params }),
}
