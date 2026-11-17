/**
 * TypeScript type definitions for the API responses
 */

export interface User {
  id: string;
  email: string;
  role: "ADMIN" | "EMPLOYEE";
  is_active: boolean;
  created_at: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
  user: User;
}

export interface Employee {
  id: string;
  user_id: string;
  email: string;
  role: "ADMIN" | "EMPLOYEE";
  is_active: boolean;
  employee_code: string;
  full_name: string;
  department?: string;
  job_title?: string;
  joining_date: string;
  created_at: string;
  updated_at: string;
}

export interface AttendanceRecord {
  id: string;
  employee_id: string;
  work_date: string;
  check_in_at: string;
  check_out_at: string | null;
  status: "PRESENT" | "INCOMPLETE";
  created_at: string;
  updated_at: string;
}

export interface LeaveRequest {
  id: string;
  employee_id: string;
  leave_type: "CASUAL" | "SICK" | "UNPAID";
  start_date: string;
  end_date: string;
  reason: string;
  status: "PENDING" | "APPROVED" | "REJECTED";
  decision_note?: string;
  decided_by_user_id?: string;
  decided_at?: string;
  created_at: string;
  updated_at: string;
}

export interface ListResponse<T> {
  total: number;
  page: number;
  page_size: number;
  items: T[];
}

export interface AdminDashboard {
  active_employees: number;
  present_today: number;
  incomplete_today: number;
  pending_leave_requests: number;
  recent_attendance: AttendanceRecord[];
  pending_leave_requests_list: LeaveRequest[];
}

export interface EmployeeDashboard {
  today_status: AttendanceRecord | null;
  today_absent: boolean;
  recent_attendance: AttendanceRecord[];
  leave_summary: {
    approved_days: number;
    pending_days: number;
    rejected_days: number;
  };
  recent_leave_requests: LeaveRequest[];
}

export interface ErrorResponse {
  detail: string;
}
