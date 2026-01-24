import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authAPI } from '@/api'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref(null)
  
  const isAuthenticated = computed(() => !!token.value)
  const isSuperuser = computed(() => user.value?.is_superuser || false)
  
  function setToken(newToken) {
    token.value = newToken
    localStorage.setItem('token', newToken)
  }
  
  function setUser(newUser) {
    user.value = newUser
  }
  
  async function login(credentials) {
    const response = await authAPI.login(credentials)
    setToken(response.access_token)
    await fetchCurrentUser()
    return response
  }
  
  async function register(userData) {
    const response = await authAPI.register(userData)
    return response
  }
  
  async function fetchCurrentUser() {
    try {
      const currentUser = await authAPI.getCurrentUser()
      setUser(currentUser)
    } catch (error) {
      logout()
    }
  }
  
  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }
  
  return {
    token,
    user,
    isAuthenticated,
    isSuperuser,
    setToken,
    setUser,
    login,
    register,
    fetchCurrentUser,
    logout
  }
})