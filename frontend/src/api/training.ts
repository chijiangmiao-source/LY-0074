import request from './request'
import type {
  CompetencyDimensionInfo,
  EmployeeCompetencyAssessment,
  TrainingTask,
  TrainingTaskListResponse,
  CreateTrainingTaskRequest,
  UpdateTrainingTaskRequest,
  HighFrequencyError,
  TrainingStats,
  ErrorTraceLinkRequest,
} from '@/types'

export interface AssessmentQuery {
  start_date?: string
  end_date?: string
  store_id?: string
}

export interface TaskListQuery {
  user_id?: string
  store_id?: string
  position?: string
  status?: string
  task_type?: string
  competency_dimension?: string
  start_date?: string
  end_date?: string
  page?: number
  page_size?: number
}

export interface StatsQuery {
  start_date?: string
  end_date?: string
  store_id?: string
  position?: string
}

export interface HighFreqErrorQuery {
  start_date?: string
  end_date?: string
  store_id?: string
  min_occurrences?: number
}

export const trainingApi = {
  dimensions: () =>
    request.get<unknown, CompetencyDimensionInfo[]>('/training/dimensions'),

  getAssessment: (userId: string, params?: AssessmentQuery) =>
    request.get<unknown, EmployeeCompetencyAssessment>(`/training/assessment/employee/${userId}`, { params }),

  refreshAssessment: (userId: string, params?: AssessmentQuery) =>
    request.get<unknown, EmployeeCompetencyAssessment>(`/training/assessment/refresh/${userId}`, { params }),

  createTask: (data: CreateTrainingTaskRequest) =>
    request.post<unknown, TrainingTask>('/training/tasks', data),

  updateTask: (taskId: string, data: UpdateTrainingTaskRequest) =>
    request.put<unknown, TrainingTask>(`/training/tasks/${taskId}`, data),

  listTasks: (params?: TaskListQuery) =>
    request.get<unknown, TrainingTaskListResponse>('/training/tasks', { params }),

  getStats: (params?: StatsQuery) =>
    request.get<unknown, TrainingStats>('/training/stats', { params }),

  getHighFrequencyErrors: (params?: HighFreqErrorQuery) =>
    request.get<unknown, HighFrequencyError[]>('/training/high-frequency-errors', { params }),

  linkErrorTraces: (data: ErrorTraceLinkRequest) =>
    request.post<unknown, HighFrequencyError>('/training/link-error-traces', data),
}
