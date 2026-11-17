import { defineStore } from 'pinia'
import { ref, computed, watch } from 'vue'
import type { User } from '@/types'
import { apiClient } from '@/services/api'

export const useAuthStore = defineStore('auth', () => {
  // Initialize from localStorage
  const storedToken = typeof window !== 'undefined' ? localStorage.getItem('auth_token') : null
  const storedUser = typeof window !== 'undefined' ? localStorage.getItem('auth_user') : null

  const user = ref<User | null>(storedUser ? JSON.parse(storedUser) : null)
  const token = ref<string | null>(storedToken)
  const isLoading = ref(false)
  const error = ref<string | null>(null)

  // Persist to localStorage when token or user changes
  watch(() => token.value, (newToken) => {
    if (newToken) {
      localStorage.setItem('auth_token', newToken)
    } else {
      localStorage.removeItem('auth_token')
    }
  })

  watch(() => user.value, (newUser) => {
    if (newUser) {
      localStorage.setItem('auth_user', JSON.stringify(newUser))
    } else {
      localStorage.removeItem('auth_user')
    }
  })

  // Initialize API with stored token on startup
  if (storedToken) {
    apiClient.setToken(storedToken)
  }

  const isAuthenticated = computed(() => !!token.value && !!user.value)
  const isAdmin = computed(() => user.value?.role === 'ADMIN')
  const isEmployee = computed(() => user.value?.role === 'EMPLOYEE')

  async function login(email: string, password: string): Promise<void> {
    isLoading.value = true
    error.value = null

    try {
      const response = await apiClient.login(email, password)
      token.value = response.access_token
      user.value = response.user
      apiClient.setToken(response.access_token)
    } catch (err) {
      error.value = apiClient.getErrorMessage(err)
      throw err
    } finally {
      isLoading.value = false
    }
  }

  async function logout(): Promise<void> {
    token.value = null
    user.value = null
    apiClient.clearToken()
    error.value = null
  }

  async function checkAuth(): Promise<boolean> {
    if (!token.value) {
      return false
    }

    try {
      apiClient.setToken(token.value)
      const currentUser = await apiClient.getMe()
      user.value = currentUser
      return true
    } catch (err) {
      await logout()
      return false
    }
  }

  function clearError(): void {
    error.value = null
  }

  return {
    user,
    token,
    isLoading,
    error,
    isAuthenticated,
    isAdmin,
    isEmployee,
    login,
    logout,
    checkAuth,
    clearError,
  }
})
