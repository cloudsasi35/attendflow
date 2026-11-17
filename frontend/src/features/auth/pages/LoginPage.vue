<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
    <div class="w-full max-w-md space-y-8">
      <!-- Header -->
      <div class="text-center">
        <h1 class="text-4xl font-bold text-blue-600">AttendFlow</h1>
        <p class="mt-2 text-gray-600">Employee Attendance & Leave Management</p>
        <h2 class="mt-6 text-2xl font-bold text-gray-900">Sign in to your account</h2>
      </div>

      <!-- Demo Credentials Info -->
      <div class="bg-blue-50 border border-blue-200 rounded-lg p-4">
        <p class="text-sm font-medium text-blue-900">Demo Credentials:</p>
        <p class="text-sm text-blue-800 mt-2">
          <strong>Admin:</strong> admin@attendflow.local / admin123
        </p>
        <p class="text-sm text-blue-800">
          <strong>Employee:</strong> alice.kumar@attendflow.local / employee123
        </p>
      </div>

      <!-- Form -->
      <form @submit.prevent="handleLogin" class="mt-8 space-y-6">
        <div>
          <label for="email" class="form-label">Email address</label>
          <input
            id="email"
            v-model="form.email"
            type="email"
            required
            class="form-input"
            placeholder="you@example.com"
            :disabled="isLoading"
          />
        </div>

        <div>
          <label for="password" class="form-label">Password</label>
          <input
            id="password"
            v-model="form.password"
            type="password"
            required
            class="form-input"
            placeholder="••••••••"
            :disabled="isLoading"
          />
        </div>

        <div v-if="error" class="bg-red-50 border border-red-200 rounded-md p-4 text-red-700 text-sm">
          {{ error }}
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="btn-primary w-full justify-center"
        >
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign in</span>
        </button>
      </form>

      <!-- Footer -->
      <p class="text-center text-xs text-gray-500">
        This is a demo application for testing purposes only.
      </p>
    </div>
  </div>
</template>

<script setup lang="ts">
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({
  email: '',
  password: ''
})

const error = ref('')
const isLoading = ref(false)

const handleLogin = async (): Promise<void> => {
  error.value = ''
  isLoading.value = true

  try {
    await authStore.login(form.email, form.password)
    
    // Redirect based on role
    if (authStore.isAdmin) {
      await router.push('/')
    } else if (authStore.isEmployee) {
      await router.push('/my')
    }
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Login failed. Please try again.'
  } finally {
    isLoading.value = false
  }
}
</script>
