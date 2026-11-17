<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { apiClient } from '@/services/api'
import type { LeaveRequest } from '@/types'

const rows = ref<LeaveRequest[]>([])
const loading = ref(false)
const error = ref('')
const success = ref('')
const form = ref<{
  leave_type: 'CASUAL' | 'SICK' | 'UNPAID'
  start_date: string
  end_date: string
  reason: string
}>({
  leave_type: 'CASUAL',
  start_date: '',
  end_date: '',
  reason: ''
})

async function load() {
  try {
    rows.value = (await apiClient.getMyLeaveRequests(0, 100)).items
  } catch (e) {
    error.value = apiClient.getErrorMessage(e)
  }
}

async function submit() {
  loading.value = true
  error.value = ''
  success.value = ''
  try {
    await apiClient.createLeaveRequest(form.value)
    success.value = 'Leave request submitted.'
    form.value = { leave_type: 'CASUAL', start_date: '', end_date: '', reason: '' }
    await load()
  } catch (e) {
    error.value = apiClient.getErrorMessage(e)
  } finally {
    loading.value = false
  }
}

onMounted(load)
</script>

<template>
  <main class="space-y-8">
    <h1 class="text-3xl font-bold text-gray-900">My Leave</h1>

    <!-- Form Section -->
    <div class="rounded-lg bg-white p-6 shadow-sm">
      <h2 class="mb-6 text-lg font-semibold text-gray-900">Request New Leave</h2>

      <div v-if="error" class="mb-4 rounded-lg bg-red-50 p-4 text-sm text-red-700">
        {{ error }}
      </div>

      <div v-if="success" class="mb-4 rounded-lg bg-green-50 p-4 text-sm text-green-700">
        {{ success }}
      </div>

      <form @submit.prevent="submit" class="space-y-5">
        <!-- Leave Type -->
        <div>
          <label for="leave_type" class="block text-sm font-medium text-gray-700 mb-1">
            Leave Type
          </label>
          <select
            id="leave_type"
            v-model="form.leave_type"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
          >
            <option value="CASUAL">Casual Leave</option>
            <option value="SICK">Sick Leave</option>
            <option value="UNPAID">Unpaid Leave</option>
          </select>
        </div>

        <!-- Date Range -->
        <div class="grid grid-cols-2 gap-4">
          <div>
            <label for="start_date" class="block text-sm font-medium text-gray-700 mb-1">
              Start Date
            </label>
            <input
              id="start_date"
              v-model="form.start_date"
              required
              type="date"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
          <div>
            <label for="end_date" class="block text-sm font-medium text-gray-700 mb-1">
              End Date
            </label>
            <input
              id="end_date"
              v-model="form.end_date"
              required
              type="date"
              class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500"
            />
          </div>
        </div>

        <!-- Reason -->
        <div>
          <label for="reason" class="block text-sm font-medium text-gray-700 mb-1">
            Reason
          </label>
          <textarea
            id="reason"
            v-model="form.reason"
            required
            placeholder="Please provide a reason for your leave request"
            rows="4"
            class="w-full rounded-lg border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500 resize-none"
          ></textarea>
        </div>

        <!-- Submit Button -->
        <div class="flex justify-start pt-2">
          <button
            type="submit"
            :disabled="loading"
            class="inline-flex items-center rounded-lg bg-blue-600 px-6 py-2 text-sm font-semibold text-white hover:bg-blue-700 disabled:opacity-60 disabled:cursor-not-allowed transition-colors"
          >
            <span v-if="loading" class="mr-2">⏳</span>
            <span v-else class="mr-2">✓</span>
            {{ loading ? 'Submitting...' : 'Submit Request' }}
          </button>
        </div>
      </form>
    </div>

    <!-- Leave Requests Table -->
    <div>
      <h2 class="mb-4 text-lg font-semibold text-gray-900">Leave Requests History</h2>
      <div class="overflow-x-auto rounded-lg border border-gray-200 bg-white shadow-sm">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 bg-gray-50">
              <th class="px-6 py-3 text-left font-semibold text-gray-900">Type</th>
              <th class="px-6 py-3 text-left font-semibold text-gray-900">Dates</th>
              <th class="px-6 py-3 text-left font-semibold text-gray-900">Reason</th>
              <th class="px-6 py-3 text-left font-semibold text-gray-900">Status</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-gray-200">
            <tr v-for="r in rows" :key="r.id" class="hover:bg-gray-50 transition-colors">
              <td class="px-6 py-4">
                <span class="inline-flex items-center rounded-full bg-blue-100 px-3 py-1 text-xs font-medium text-blue-700">
                  {{ r.leave_type }}
                </span>
              </td>
              <td class="px-6 py-4 text-gray-600">
                {{ r.start_date }} to {{ r.end_date }}
              </td>
              <td class="px-6 py-4 text-gray-600">{{ r.reason }}</td>
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
            </tr>
            <tr v-if="rows.length === 0">
              <td colspan="4" class="px-6 py-8 text-center text-gray-500">
                No leave requests yet. Submit one above to get started.
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </main>
</template>
