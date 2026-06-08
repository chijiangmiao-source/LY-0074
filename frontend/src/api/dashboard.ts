import request from './request'

export interface DashboardSummary {
  total_stores: number
  total_buckets: number
  active_buckets: number
  total_flowers: number
  in_bucket_flowers: number
  total_flower_quantity: number
  total_preservation_records: number
  total_loss_records: number
}

export interface BucketTurnover {
  bucket_id: string
  bucket_code: string
  store_name: string
  store_code: string
  capacity: number
  current_quantity: number
  utilization_rate: number
  status: string
  in_count: number
  out_count: number
  turnover_count: number
}

export interface CategoryDistribution {
  category_id: string
  category_code: string
  category_name: string
  flower_count: number
  total_quantity: number
}

export interface StoreLossRanking {
  rank: number
  store_id: string
  store_code: string
  store_name: string
  manager?: string
  total_loss_quantity: number
  total_loss_count: number
  current_flower_quantity: number
}

export interface RecentRecord {
  type: string
  type_key: string
  bucket_code: string
  flower_name: string
  quantity: number
  operator?: string
  created_at: string
}

export const dashboardApi = {
  summary: () => request.get<unknown, DashboardSummary>('/dashboard/summary'),
  bucketTurnover: () => request.get<unknown, BucketTurnover[]>('/dashboard/bucket-turnover'),
  categoryDistribution: () =>
    request.get<unknown, CategoryDistribution[]>('/dashboard/flower-category-distribution'),
  storeLossRanking: () =>
    request.get<unknown, StoreLossRanking[]>('/dashboard/store-loss-ranking'),
  recentRecords: (limit = 10) =>
    request.get<unknown, RecentRecord[]>('/dashboard/recent-records', { params: { limit } }),
}
