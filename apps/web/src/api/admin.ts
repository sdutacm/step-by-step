import { getToken } from './auth'

export interface AdminUser {
  id: number
  username: string
  nickname: string | null
  avatar_url: string | null
  is_super_admin: boolean
}

export interface AdminUserListResponse {
  total: number
  page: number
  page_size: number
  items: AdminUser[]
}

export interface UpdateSuperAdminData {
  is_super_admin: boolean
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken()
  if (!token) {
    throw new Error('No token found')
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  })
  return response
}

export async function getUsers(page: number = 1, pageSize: number = 20): Promise<AdminUserListResponse> {
  const response = await fetchWithAuth(`/api/admin/users?page=${page}&page_size=${pageSize}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get users')
  }
  return await response.json()
}

export async function updateUserSuperAdmin(userId: number, isSuperAdmin: boolean): Promise<AdminUser> {
  const response = await fetchWithAuth(`/api/admin/users/${userId}/super-admin`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ is_super_admin: isSuperAdmin }),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update user')
  }
  return await response.json()
}
