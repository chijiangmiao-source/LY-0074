import request from './request'
import type {
  BucketInRecord,
  BucketOutRecord,
  PreservationRecord,
  LossRecord,
  PaginatedResponse,
} from '@/types'

export interface RecordQuery {
  page?: number
  page_size?: number
  bucket_id?: string
  flower_id?: string
  store_id?: string
  start_date?: string
  end_date?: string
}

export interface BucketInCreate {
  bucket_id: string
  flower_id: string
  quantity: number
  operator?: string
  remark?: string
}

export interface BucketOutCreate {
  bucket_id: string
  flower_id: string
  quantity: number
  operator?: string
  remark?: string
}

export interface PreservationCreate {
  bucket_id: string
  supplement_quantity: number
  operator?: string
  remark?: string
}

export interface LossCreate {
  flower_id: string
  quantity: number
  reason?: string
  operator?: string
  remark?: string
}

export const recordApi = {
  createInBucket: (data: BucketInCreate) =>
    request.post<unknown, BucketInRecord>('/records/in-bucket', data),
  createOutBucket: (data: BucketOutCreate) =>
    request.post<unknown, BucketOutRecord>('/records/out-bucket', data),
  createPreservation: (data: PreservationCreate) =>
    request.post<unknown, PreservationRecord>('/records/preservation', data),
  createLoss: (data: LossCreate) =>
    request.post<unknown, LossRecord>('/records/loss', data),

  listInBucket: (params?: RecordQuery) =>
    request.get<unknown, PaginatedResponse<BucketInRecord>>('/records/in-bucket', { params }),
  listOutBucket: (params?: RecordQuery) =>
    request.get<unknown, PaginatedResponse<BucketOutRecord>>('/records/out-bucket', { params }),
  listPreservation: (params?: RecordQuery) =>
    request.get<unknown, PaginatedResponse<PreservationRecord>>('/records/preservation', {
      params,
    }),
  listLoss: (params?: RecordQuery) =>
    request.get<unknown, PaginatedResponse<LossRecord>>('/records/loss', { params }),
}
