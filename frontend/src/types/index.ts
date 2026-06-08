export interface User {
  _id: string
  username: string
  email?: string
  full_name?: string
  is_active: boolean
  is_admin: boolean
  created_at: string
}

export interface Store {
  _id: string
  store_code: string
  store_name: string
  address?: string
  phone?: string
  manager?: string
  is_active: boolean
  created_at: string
}

export interface FlowerCategory {
  _id: string
  category_code: string
  category_name: string
  description?: string
  created_at: string
}

export interface BucketStoreInfo {
  id: string
  store_name: string
  store_code: string
}

export type BucketStatus = 'active' | 'inactive' | 'maintenance'

export interface Bucket {
  _id: string
  bucket_code: string
  store: BucketStoreInfo
  capacity: number
  current_quantity: number
  status: BucketStatus
  responsible_person?: string
  remark?: string
  created_at: string
  updated_at: string
}

export interface CategoryInfo {
  id: string
  category_name: string
  category_code: string
}

export interface BucketInfo {
  id: string
  bucket_code: string
}

export interface StoreInfo {
  id: string
  store_name: string
}

export type PreservationStatus = 'fresh' | 'normal' | 'wilted'

export interface Flower {
  _id: string
  flower_code: string
  flower_name: string
  category: CategoryInfo
  bucket?: BucketInfo
  store?: StoreInfo
  current_quantity: number
  preservation_status: PreservationStatus
  in_bucket_date?: string
  remark?: string
  created_at: string
  updated_at: string
}

export interface FlowerInfo {
  id: string
  flower_name: string
  flower_code: string
}

export interface BucketInRecord {
  _id: string
  bucket: BucketInfo
  flower: FlowerInfo
  quantity: number
  operator?: string
  remark?: string
  created_at: string
}

export interface BucketOutRecord extends BucketInRecord {}

export interface PreservationRecord {
  _id: string
  bucket: BucketInfo
  store?: StoreInfo
  supplement_quantity: number
  previous_quantity: number
  after_quantity: number
  operator?: string
  remark?: string
  created_at: string
}

export interface LossRecord {
  _id: string
  flower: FlowerInfo
  store?: StoreInfo
  quantity: number
  reason?: string
  operator?: string
  remark?: string
  created_at: string
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
  total_pages: number
}
