import request from './request'
import type { Store, PaginatedResponse } from '@/types'

export interface StoreQuery {
  page?: number
  page_size?: number
  keyword?: string
  is_active?: boolean
}

export interface StoreCreate {
  store_code: string
  store_name: string
  address?: string
  phone?: string
  manager?: string
  is_active?: boolean
}

export interface StoreUpdate {
  store_name?: string
  address?: string
  phone?: string
  manager?: string
  is_active?: boolean
}

export const storeApi = {
  list: (params?: StoreQuery) =>
    request.get<unknown, PaginatedResponse<Store>>('/stores', { params }),
  listAll: () => request.get<unknown, Store[]>('/stores/all'),
  get: (id: string) => request.get<unknown, Store>(`/stores/${id}`),
  create: (data: StoreCreate) => request.post<unknown, Store>('/stores', data),
  update: (id: string, data: StoreUpdate) => request.put<unknown, Store>(`/stores/${id}`, data),
  delete: (id: string) => request.delete<unknown, { message: string }>(`/stores/${id}`),
}
