import request from './request'
import type { User } from '@/types'

export interface LoginData {
  username: string
  password: string
}

export interface TokenResponse {
  access_token: string
  token_type: string
}

export const authApi = {
  login: (data: LoginData) => {
    const form = new FormData()
    form.append('username', data.username)
    form.append('password', data.password)
    return request.post<unknown, TokenResponse>('/auth/login', form)
  },
  getCurrentUser: () => request.get<unknown, User>('/auth/me'),
  initAdmin: () => request.post<unknown, { message: string }>('/auth/init-admin'),
}
