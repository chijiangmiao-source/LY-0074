import request from './request'
import type { Bucket, PaginatedResponse, BucketStatus } from '@/types'

export interface BucketQuery {
  page?: number
  page_size?: number
  keyword?: string
  store_id?: string
  status?: BucketStatus
}

export interface BucketCreate {
  bucket_code: string
  store_id: string
  capacity: number
  current_quantity?: number
  status?: BucketStatus
  responsible_person?: string
  remark?: string
}

export interface BucketUpdate {
  store_id?: string
  capacity?: number
  current_quantity?: number
  status?: BucketStatus
  responsible_person?: string
  remark?: string
}

export const bucketApi = {
  list: (params?: BucketQuery) =>
    request.get<unknown, PaginatedResponse<Bucket>>('/buckets', { params }),
  listAll: (params?: { store_id?: string; status?: BucketStatus }) =>
    request.get<unknown, Bucket[]>('/buckets/all', { params }),
  get: (id: string) => request.get<unknown, Bucket>(`/buckets/${id}`),
  create: (data: BucketCreate) => request.post<unknown, Bucket>('/buckets', data),
  update: (id: string, data: BucketUpdate) => request.put<unknown, Bucket>(`/buckets/${id}`, data),
  delete: (id: string) => request.delete<unknown, { message: string }>(`/buckets/${id}`),
}
