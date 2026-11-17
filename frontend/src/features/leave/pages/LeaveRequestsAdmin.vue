<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '@/services/api'
import type { LeaveRequest } from '@/types'

const rows = ref<LeaveRequest[]>([])
const status = ref('')
const loading = ref(false)
const error = ref('')
const success = ref('')
const note = ref('')
const expandedRow = ref<string | null>(null)

async function load() {
  loading.value = true
  try {
    rows.value = (await apiClient.listLeaveRequests(status.value || undefined, 0, 100)).items
  } catch (e) {
    error.value = apiClient.getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

async function decide(row: LeaveRequest, approved: boolean) {
  try {
    if (approved) await apiClient.approveLeave(row.id, note.value || undefined)
    else await apiClient.rejectLeave(row.id, note.value || undefined)
    success.value = 'Request updated.'
    note.value = ''
    expandedRow.value = null
    await load()
  } catch (e) {
    error.value = apiClient.getErrorMessage(e)
  }
}

onMounted(load)
</script>

<template>
  <main class="space-y-6">
    <!-- Header & Filter -->
    <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
      <h1 class="text-3xl font-bold text-gray-900">Leave Requests</h1>
      <select
        v-model="status"
        @change="load"
        class="rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
      >
        <option value="">All statuses</option>
        <option value="PENDING">Pending</option>
        <option value="APPROVED">Approved</option>
        <option value="REJECTED">Rejected</option>
      </select>
    </div>

    <!-- Messages -->
    <div v-if="error" class="rounded-lg bg-red-50 p-4 text-sm text-red-700">
      {{ error }}
    </div>

    <div v-if="success" class="rounded-lg bg-green-50 p-4 text-sm text-green-700">
      {{ success }}
    </div>

    <!-- Decision Note Input -->
    <div v-if="expandedRow" class="rounded-lg bg-blue-50 border border-blue-200 p-4">
      <label class="block text-sm font-medium text-gray-700 mb-2">
        Decision Note (optional)
      </label>
      <textarea
        v-model="note"
        placeholder="Add a note for the employee (e.g., reason for rejection)"
        rows="3"
        class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
      ></textarea>
    </div>

    <!-- Table -->
    <div class="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
      <table class="w-full text-sm">
        <thead>
          <tr class="border-b border-gray-200 bg-gray-50">
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Employee</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Type</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Dates</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Reason</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Status</th>
            <th class="px-6 py-3 text-left font-semibold text-gray-900">Action</th>
          </tr>
        </thead>
        <tbody class="divide-y divide-gray-200">
          <tr v-for="r in rows" :key="r.id" class="hover:bg-gray-50 transition-colors">
            <td class="px-6 py-4 text-gray-900 font-medium">
              {{ r.employee_id }}
            </td>
            <td class="px-6 py-4">
              <span class="inline-flex items-center rounded-full bg-indigo-100 px-3 py-1 text-xs font-medium text-indigo-700">
                {{ r.leave_type }}
              </span>
            </td>
            <td class="px-6 py-4 text-gray-600">
              {{ r.start_date }} to {{ r.end_date }}
            </td>
            <td class="px-6 py-4 text-gray-600 max-w-xs truncate">
              {{ r.reason }}
            </td>
            <td class="px-6 py-4">
              <span
                :class="{
                  'bg-yellow-100 text-yellow-700': r.status === 'PENDING',
                  'bg-green-100 text-green-700': r.status === 'APPROVED',
                  'bg-red-100 text-red-700': r.status === 'REJECTED'
                }"
                class="inline-flex items-center rounded-full px-3 py-1 text-xs font-medium"
              >
                {{ r.status }}
              </span>
            </td>
            <td class="px-6 py-4">
              <div v-if="r.status === 'PENDING'" class="flex gap-2">
                <button
                  v-if="expandedRow === r.id"
                  @click="decide(r, true)"
                  class="inline-flex items-center rounded-lg bg-green-600 px-3 py-1 text-xs font-semibold text-white hover:bg-green-700 transition-colors"
                >
                  ✓ Approve
                </button>
                <button
                  v-if="expandedRow === r.id"
                  @click="decide(r, false)"
                  class="inline-flex items-center rounded-lg bg-red-600 px-3 py-1 text-xs font-semibold text-white hover:bg-red-700 transition-colors"
                >
                  ✗ Reject
                </button>
                <button
                  v-if="expandedRow !== r.id"
                  @click="expandedRow = r.id"
                  class="inline-flex items-center rounded-lg bg-blue-600 px-3 py-1 text-xs font-semibold text-white hover:bg-blue-700 transition-colors"
                >
                  ⋯ Decide
                </button>
              </div>
              <span v-else class="text-gray-500 text-xs">—</span>
            </td>
          </tr>
          <tr v-if="rows.length === 0">
            <td colspan="6" class="px-6 py-8 text-center text-gray-500">
              {{ status ? `No ${status.toLowerCase()} leave requests.` : 'No leave requests found.' }}
            </td>
          </tr>
        </tbody>
      </table>
    </div>
  </main>
</template>
