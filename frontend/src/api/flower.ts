import request from './request'
import type { Flower, PaginatedResponse, PreservationStatus } from '@/types'

export interface FlowerQuery {
  page?: number
  page_size?: number
  keyword?: string
  category_id?: string
  bucket_id?: string
  store_id?: string
  preservation_status?: PreservationStatus
}

export interface FlowerCreate {
  flower_code: string
  flower_name: string
  category_id: string
  bucket_id?: string
  store_id?: string
  current_quantity?: number
  preservation_status?: PreservationStatus
  in_bucket_date?: string
  remark?: string
}

export interface FlowerUpdate {
  flower_name?: string
  category_id?: string
  bucket_id?: string
  store_id?: string
  current_quantity?: number
  preservation_status?: PreservationStatus
  in_bucket_date?: string
  remark?: string
}

export const flowerApi = {
  list: (params?: FlowerQuery) =>
    request.get<unknown, PaginatedResponse<Flower>>('/flowers', { params }),
  listAll: (params?: { store_id?: string }) =>
    request.get<unknown, Flower[]>('/flowers/all', { params }),
  get: (id: string) => request.get<unknown, Flower>(`/flowers/${id}`),
  create: (data: FlowerCreate) => request.post<unknown, Flower>('/flowers', data),
  update: (id: string, data: FlowerUpdate) => request.put<unknown, Flower>(`/flowers/${id}`, data),
  delete: (id: string) => request.delete<unknown, { message: string }>(`/flowers/${id}`),
}
