<template>
  <div class="flex h-screen bg-gray-100">
    <!-- Sidebar -->
    <div class="flex flex-col w-64 bg-slate-900 text-white">
      <!-- Header -->
      <div class="p-6 border-b border-slate-700">
        <h1 class="text-2xl font-bold">AttendFlow</h1>
        <p class="text-xs text-slate-400 mt-1">Admin Portal</p>
      </div>

      <!-- Navigation -->
      <nav class="flex-1 mt-8 space-y-1 px-3 overflow-y-auto">
        <RouterLink
          to="/"
          class="block px-4 py-3 rounded-lg transition-colors text-sm font-medium"
          :class="route.path === '/' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'"
        >
          📊 Overview
        </RouterLink>
        <RouterLink
          to="/employees"
          class="block px-4 py-3 rounded-lg transition-colors text-sm font-medium"
          :class="route.path === '/employees' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'"
        >
          👥 Employees
        </RouterLink>
        <RouterLink
          to="/attendance"
          class="block px-4 py-3 rounded-lg transition-colors text-sm font-medium"
          :class="route.path === '/attendance' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'"
        >
          ⏰ Attendance
        </RouterLink>
        <RouterLink
          to="/leave"
          class="block px-4 py-3 rounded-lg transition-colors text-sm font-medium"
          :class="route.path === '/leave' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'"
        >
          📋 Leave Requests
        </RouterLink>
        <RouterLink
          to="/reports"
          class="block px-4 py-3 rounded-lg transition-colors text-sm font-medium"
          :class="route.path === '/reports' ? 'bg-blue-600 text-white' : 'text-slate-300 hover:bg-slate-800'"
        >
          📈 Reports
        </RouterLink>
      </nav>

      <!-- Footer -->
      <div class="border-t border-slate-700 p-4 space-y-3">
        <p v-if="authStore.user" class="text-xs text-slate-400 text-center truncate px-2">
          {{ authStore.user.email }}
        </p>
        <button
          @click="handleLogout"
          class="w-full bg-red-600 hover:bg-red-700 text-white font-medium px-4 py-2 rounded-lg transition-colors text-sm"
        >
          🚪 Logout
        </button>
      </div>
    </div>

    <!-- Main Content -->
    <div class="flex-1 flex flex-col overflow-hidden">
      <div class="flex-1 overflow-auto p-8">
        <RouterView />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { RouterLink, RouterView, useRoute, useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()

const handleLogout = async (): Promise<void> => {
  await authStore.logout()
  await router.push('/login')
}
</script>
