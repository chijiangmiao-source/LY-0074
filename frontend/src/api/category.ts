import request from './request'
import type { FlowerCategory, PaginatedResponse } from '@/types'

export interface CategoryQuery {
  page?: number
  page_size?: number
  keyword?: string
}

export interface CategoryCreate {
  category_code: string
  category_name: string
  description?: string
}

export interface CategoryUpdate {
  category_name?: string
  description?: string
}

export const categoryApi = {
  list: (params?: CategoryQuery) =>
    request.get<unknown, PaginatedResponse<FlowerCategory>>('/categories', { params }),
  listAll: () => request.get<unknown, FlowerCategory[]>('/categories/all'),
  get: (id: string) => request.get<unknown, FlowerCategory>(`/categories/${id}`),
  create: (data: CategoryCreate) => request.post<unknown, FlowerCategory>('/categories', data),
  update: (id: string, data: CategoryUpdate) =>
    request.put<unknown, FlowerCategory>(`/categories/${id}`, data),
  delete: (id: string) => request.delete<unknown, { message: string }>(`/categories/${id}`),
}
