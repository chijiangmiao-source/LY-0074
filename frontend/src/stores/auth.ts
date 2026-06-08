import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api/auth'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const user = ref<User | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function setToken(t: string) {
    token.value = t
    localStorage.setItem('token', t)
  }

  function setUser(u: User) {
    user.value = u
    localStorage.setItem('user', JSON.stringify(u))
  }

  function loadUserFromStorage() {
    const stored = localStorage.getItem('user')
    if (stored) {
      try {
        user.value = JSON.parse(stored) as User
      } catch {}
    }
  }

  async function login(username: string, password: string) {
    const res = await authApi.login({ username, password })
    setToken(res.access_token)
    const u = await authApi.getCurrentUser()
    setUser(u)
    return u
  }

  async function fetchCurrentUser() {
    const u = await authApi.getCurrentUser()
    setUser(u)
    return u
  }

  function logout() {
    token.value = null
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('user')
  }

  return {
    token,
    user,
    isLoggedIn,
    setToken,
    setUser,
    loadUserFromStorage,
    login,
    fetchCurrentUser,
    logout,
  }
})
