export interface User {
  _id: string
  username: string
  email?: string
  full_name?: string
  position?: string
  position_label?: string
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

export type WarningType = 'low_liquid' | 'wilted' | 'long_in_bucket' | 'high_loss'
export type WarningSeverity = 'high' | 'medium' | 'low'
export type WarningStatusType = 'pending' | 'handling' | 'resolved'

export interface Warning {
  warning_id: string
  warning_type: WarningType
  warning_type_label: string
  severity: WarningSeverity
  store_id?: string
  store_name: string
  bucket_id?: string
  bucket_code?: string
  flower_id?: string
  flower_name?: string
  flower_code?: string
  message: string
  current_value: string | number
  threshold: string | number
  unit: string
  status: WarningStatusType
  status_label: string
  handler: string
  handled_at?: string
  handle_note?: string
  created_at: string
  updated_at: string
}

export type OperationType = 'in_bucket' | 'out_bucket' | 'preservation' | 'loss' | 'status_change'

export interface OperationTrace {
  trace_id: string
  operation_type: OperationType
  operation_type_label: string
  store_name: string
  store_id: string
  bucket_id: string
  bucket_code: string
  flower_id: string
  flower_name: string
  flower_code: string
  quantity: number
  quantity_unit: string
  operator: string
  remark: string
  detail: string
  created_at: string
}

export interface PositionInfo {
  code: string
  label: string
}

export interface UserSimpleInfo {
  id: string
  username: string
  full_name?: string
  position?: string
  position_label?: string
}

export interface StoreSimpleInfo {
  id: string
  store_name: string
  store_code?: string
}

export interface WorkloadStats {
  in_bucket_count: number
  out_bucket_count: number
  preservation_count: number
  loss_count: number
  warning_handled_count: number
  inspection_count: number
  total_operations: number
}

export interface TimelinessStats {
  on_time_count: number
  overdue_count: number
  on_time_rate: number
  avg_warning_handle_hours: number
}

export interface LossStats {
  total_loss_quantity: number
  responsible_loss_quantity: number
  loss_rate: number
}

export interface EmployeePerformance {
  user: UserSimpleInfo
  store?: StoreSimpleInfo
  workload: WorkloadStats
  timeliness: TimelinessStats
  loss: LossStats
  score: number
  rank?: number
}

export interface PerformanceRankingResponse {
  items: EmployeePerformance[]
  total: number
  period_start: string
  period_end: string
}

export interface ResponsibilityTraceItem {
  _id: string
  target_type: string
  target_type_label: string
  target_id: string
  batch_no?: string
  action: string
  action_label: string
  operator?: UserSimpleInfo
  operator_name?: string
  operator_position?: string
  operator_position_label?: string
  store?: StoreSimpleInfo
  bucket?: { id: string; bucket_code: string }
  flower?: { id: string; flower_name: string; flower_code: string }
  warning?: { id: string; warning_type: string; message: string }
  remark?: string
  created_at: string
}

export interface ResponsibilityTraceResponse {
  target_type: string
  target_type_label: string
  target_id: string
  batch_no?: string
  target_info: Record<string, any>
  traces: ResponsibilityTraceItem[]
  total: number
}

export interface PerformanceSummary {
  period_start: string
  period_end: string
  total_employees: number
  total_operations: number
  avg_on_time_rate: number
  total_loss_quantity: number
}

export interface CompetencyDimensionInfo {
  code: string
  label: string
}

export interface CompetencyScoreItem {
  dimension: string
  dimension_label: string
  score: number
  max_score: number
  level: string
  level_label: string
  operations_count: number
  error_count: number
  details: Record<string, any>
}

export interface EmployeeCompetencyAssessment {
  _id: string
  user_id: string
  user_name: string
  position?: string
  position_label?: string
  store_id?: string
  store_name?: string
  period_start: string
  period_end: string
  overall_score: number
  overall_level: string
  overall_level_label: string
  competency_scores: CompetencyScoreItem[]
  weak_dimensions: string[]
  strong_dimensions: string[]
  training_suggestions: string[]
  created_at: string
}

export interface TrainingTask {
  _id: string
  user_id: string
  user_name: string
  position?: string
  position_label?: string
  store_id?: string
  store_name?: string
  course_id?: string
  course_name: string
  competency_dimension: string
  competency_dimension_label: string
  task_type: string
  task_type_label: string
  status: string
  status_label: string
  assigned_at: string
  deadline?: string
  started_at?: string
  completed_at?: string
  score?: number
  passed?: boolean
  attempts: number
  remark?: string
  related_error_ids: string[]
  related_trace_ids: string[]
}

export interface TrainingTaskListResponse {
  items: TrainingTask[]
  total: number
}

export interface CreateTrainingTaskRequest {
  user_id: string
  course_id?: string
  course_name: string
  competency_dimension: string
  task_type?: string
  deadline?: string
  remark?: string
  related_error_ids?: string[]
  related_trace_ids?: string[]
}

export interface UpdateTrainingTaskRequest {
  status?: string
  score?: number
  passed?: boolean
  remark?: string
}

export interface HighFrequencyError {
  _id: string
  error_type: string
  error_type_label: string
  competency_dimension: string
  competency_dimension_label: string
  description: string
  occurrence_count: number
  affected_employee_count: number
  affected_store_count: number
  period_start: string
  period_end: string
  related_trace_ids: string[]
  sample_traces: Array<{
    trace_id: string
    operator_name: string
    created_at: string
    remark?: string
    batch_no?: string
  }>
  created_at: string
  updated_at: string
}

export interface DimensionScoreItem {
  dimension: string
  dimension_label: string
  avg_score: number
  employee_count: number
}

export interface TrendDataItem {
  period: string
  total_tasks: number
  completed_tasks: number
  completion_rate: number
}

export interface TrainingStats {
  period_start: string
  period_end: string
  store_id?: string
  store_name?: string
  total_employees: number
  total_tasks: number
  pending_tasks: number
  in_progress_tasks: number
  completed_tasks: number
  failed_tasks: number
  training_completion_rate: number
  refresher_tasks: number
  refresher_passed: number
  refresher_pass_rate: number
  exam_tasks: number
  exam_passed: number
  exam_pass_rate: number
  problem_recurrence_rate: number
  avg_overall_score: number
  dimension_scores: DimensionScoreItem[]
  trend_data: TrendDataItem[]
}

export interface ErrorTraceLinkRequest {
  error_type: string
  error_type_label: string
  competency_dimension: string
  description: string
  trace_ids: string[]
}
