<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '@/services/api'
import type { AdminDashboard } from '@/types'

const data = ref<AdminDashboard | null>(null)
const loading = ref(true)
const error = ref('')

const formatDate = (dateStr: string): string => {
  return new Date(dateStr).toLocaleDateString(undefined, {
    month: 'short',
    day: 'numeric'
  })
}

const loadData = async (): Promise<void> => {
  loading.value = true
  error.value = ''

  try {
    data.value = await apiClient.getAdminDashboard()
  } catch (err) {
    error.value = 'Failed to load dashboard. Please try again.'
    console.error(err)
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
</script>
<template><section><div class="mb-8 flex flex-wrap items-end justify-between gap-4"><div><p class="text-sm font-medium text-blue-600">Admin workspace</p><h1 class="mt-1 text-3xl font-bold tracking-tight">Overview</h1><p class="mt-2 text-slate-500">Here’s what’s happening today.</p></div><button class="rounded-lg border bg-white px-4 py-2 text-sm font-medium hover:bg-slate-50" @click="loadData">↻ Refresh</button></div><div v-if="error" class="mb-6 rounded-lg bg-red-50 p-4 text-red-700">{{ error }}</div><div v-if="loading" class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div v-for="n in 4" :key="n" class="h-28 animate-pulse rounded-xl bg-slate-200" /></div><template v-else-if="data"><div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4"><div v-for="card in [{label:'Active employees',value:data.active_employees,color:'blue'},{label:'Present today',value:data.present_today,color:'green'},{label:'Incomplete',value:data.incomplete_today,color:'amber'},{label:'Pending leave',value:data.pending_leave_requests,color:'violet'}]" :key="card.label" class="rounded-xl border bg-white p-5 shadow-sm"><p class="text-sm text-slate-500">{{ card.label }}</p><p class="mt-3 text-3xl font-bold">{{ card.value }}</p></div></div><div class="mt-8 grid gap-6 lg:grid-cols-2"><div class="rounded-xl border bg-white shadow-sm"><div class="border-b p-5"><h2 class="font-semibold">Recent attendance</h2></div><div v-if="!data.recent_attendance.length" class="p-5 text-sm text-slate-500">No attendance records yet.</div><div v-for="item in data.recent_attendance.slice(0, 5)" :key="item.id" class="flex items-center justify-between border-b px-5 py-4 last:border-0"><div><p class="font-medium">{{ item.employee_id }}</p><p class="text-sm text-slate-500">{{ formatDate(item.work_date) }}</p></div><span :class="item.status === 'PRESENT' ? 'bg-green-100 text-green-700' : 'bg-amber-100 text-amber-700'" class="rounded-full px-3 py-1 text-xs font-semibold">{{ item.status }}</span></div></div><div class="rounded-xl border bg-white shadow-sm"><div class="border-b p-5"><h2 class="font-semibold">Pending leave requests</h2></div><div v-if="!data.pending_leave_requests_list.length" class="p-5 text-sm text-slate-500">No pending requests.</div><div v-for="item in data.pending_leave_requests_list.slice(0, 5)" :key="item.id" class="flex items-center justify-between border-b px-5 py-4 last:border-0"><div><p class="font-medium">{{ item.leave_type }} leave</p><p class="text-sm text-slate-500">{{ formatDate(item.start_date) }} – {{ formatDate(item.end_date) }}</p></div><span class="rounded-full bg-amber-100 px-3 py-1 text-xs font-semibold text-amber-700">Pending</span></div></div></div></template></section></template>
