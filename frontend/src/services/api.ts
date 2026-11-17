import axios, { AxiosInstance, AxiosError } from 'axios'
import type {
  User,
  AuthResponse,
  Employee,
  AttendanceRecord,
  LeaveRequest,
  ListResponse,
  AdminDashboard,
  EmployeeDashboard,
  ErrorResponse,
} from '@/types'

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000'

class APIClient {
  private api: AxiosInstance
  private token: string | null = null

  constructor() {
    this.api = axios.create({
      baseURL: API_BASE_URL,
      timeout: 10000,
    })

    // Add token to requests if available
    this.api.interceptors.request.use((config) => {
      if (this.token) {
        config.headers.Authorization = `Bearer ${this.token}`
      }
      return config
    })

    // Handle 401 responses
    this.api.interceptors.response.use(
      (response) => response,
      (error) => {
        if (error.response?.status === 401) {
          this.clearToken()
        }
        return Promise.reject(error)
      }
    )
  }

  setToken(token: string): void {
    this.token = token
  }

  clearToken(): void {
    this.token = null
  }

  // Auth endpoints
  async login(email: string, password: string): Promise<AuthResponse> {
    const response = await this.api.post('/api/v1/auth/login', {
      email,
      password,
    })
    return response.data
  }

  async getMe(): Promise<User> {
    const response = await this.api.get('/api/v1/auth/me')
    return response.data
  }

  // Employee endpoints
  async listEmployees(skip = 0, limit = 20): Promise<ListResponse<Employee>> {
    const response = await this.api.get('/api/v1/employees', {
      params: { skip, limit },
    })
    return response.data
  }

  async getEmployee(id: string): Promise<Employee> {
    const response = await this.api.get(`/api/v1/employees/${id}`)
    return response.data
  }

  async createEmployee(data: {
    email: string
    password: string
    employee_code: string
    full_name: string
    department?: string
    job_title?: string
    joining_date: string
  }): Promise<Employee> {
    const response = await this.api.post('/api/v1/employees', data)
    return response.data
  }

  async updateEmployee(
    id: string,
    data: Partial<Employee>
  ): Promise<Employee> {
    const response = await this.api.patch(`/api/v1/employees/${id}`, data)
    return response.data
  }

  async deactivateEmployee(id: string): Promise<Employee> {
    const response = await this.api.post(`/api/v1/employees/${id}/deactivate`)
    return response.data
  }

  // Attendance endpoints
  async checkIn(): Promise<AttendanceRecord> {
    const response = await this.api.post('/api/v1/attendance/check-in')
    return response.data
  }

  async checkOut(): Promise<AttendanceRecord> {
    const response = await this.api.post('/api/v1/attendance/check-out')
    return response.data
  }

  async getMyAttendance(
    skip = 0,
    limit = 20
  ): Promise<ListResponse<AttendanceRecord>> {
    const response = await this.api.get('/api/v1/attendance/me', {
      params: { skip, limit },
    })
    return response.data
  }

  async listAttendance(
    employeeId?: string,
    startDate?: string,
    endDate?: string,
    skip = 0,
    limit = 20
  ): Promise<ListResponse<AttendanceRecord>> {
    const response = await this.api.get('/api/v1/attendance', {
      params: { employee_id: employeeId, start_date: startDate, end_date: endDate, skip, limit },
    })
    return response.data
  }

  async getTodayAttendance(): Promise<{
    total_employees: number
    present_today: number
    incomplete_today: number
    absent_today: number
  }> {
    const response = await this.api.get('/api/v1/attendance/today')
    return response.data
  }

  // Leave endpoints
  async createLeaveRequest(data: {
    leave_type: 'CASUAL' | 'SICK' | 'UNPAID'
    start_date: string
    end_date: string
    reason: string
  }): Promise<LeaveRequest> {
    const response = await this.api.post('/api/v1/leave-requests', data)
    return response.data
  }

  async getMyLeaveRequests(
    skip = 0,
    limit = 20
  ): Promise<ListResponse<LeaveRequest>> {
    const response = await this.api.get('/api/v1/leave-requests/me', {
      params: { skip, limit },
    })
    return response.data
  }

  async listLeaveRequests(
    status?: string,
    skip = 0,
    limit = 20
  ): Promise<ListResponse<LeaveRequest>> {
    const response = await this.api.get('/api/v1/leave-requests', {
      params: { status, skip, limit },
    })
    return response.data
  }

  async approveLeave(
    id: string,
    decisionNote?: string
  ): Promise<LeaveRequest> {
    const response = await this.api.post(`/api/v1/leave-requests/${id}/approve`, {
      decision_note: decisionNote,
    })
    return response.data
  }

  async rejectLeave(
    id: string,
    decisionNote?: string
  ): Promise<LeaveRequest> {
    const response = await this.api.post(`/api/v1/leave-requests/${id}/reject`, {
      decision_note: decisionNote,
    })
    return response.data
  }

  // Dashboard endpoints
  async getAdminDashboard(): Promise<AdminDashboard> {
    const response = await this.api.get('/api/v1/dashboard/admin')
    return response.data
  }

  async getEmployeeDashboard(): Promise<EmployeeDashboard> {
    const response = await this.api.get('/api/v1/dashboard/employee')
    return response.data
  }

  // Reports endpoints
  async getAttendanceReport(
    employeeId?: string,
    startDate?: string,
    endDate?: string,
    skip = 0,
    limit = 20
  ): Promise<ListResponse<AttendanceRecord>> {
    const response = await this.api.get('/api/v1/reports/attendance', {
      params: { employee_id: employeeId, start_date: startDate, end_date: endDate, skip, limit },
    })
    return response.data
  }

  async getLeaveReport(
    status?: string,
    skip = 0,
    limit = 20
  ): Promise<ListResponse<LeaveRequest>> {
    const response = await this.api.get('/api/v1/reports/leave', {
      params: { status, skip, limit },
    })
    return response.data
  }

  async exportAttendanceCSV(
    employeeId?: string,
    startDate?: string,
    endDate?: string
  ): Promise<Blob> {
    const response = await this.api.get('/api/v1/reports/attendance/csv', {
      params: { employee_id: employeeId, start_date: startDate, end_date: endDate },
      responseType: 'blob',
    })
    return response.data
  }

  async exportLeaveCSV(status?: string): Promise<Blob> {
    const response = await this.api.get('/api/v1/reports/leave/csv', {
      params: { status },
      responseType: 'blob',
    })
    return response.data
  }

  getErrorMessage(error: unknown): string {
    if (axios.isAxiosError(error)) {
      const data = error.response?.data as ErrorResponse | undefined
      return data?.detail || error.message || 'An error occurred'
    }
    return 'An unexpected error occurred'
  }
}

export const apiClient = new APIClient()
