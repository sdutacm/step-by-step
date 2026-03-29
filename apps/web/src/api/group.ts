import { getToken } from './auth'

export interface Group {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  member_count: number
  step_count: number
}

export interface GroupListItem {
  id: number
  name: string
  description: string | null
  created_at: string
  updated_at: string
  member_count: number
  step_count: number
}

export interface GroupListResponse {
  total: number
  page: number
  page_size: number
  items: GroupListItem[]
}

export interface CreateGroupData {
  name: string
  description?: string
}

export interface UpdateGroupData {
  name?: string
  description?: string
}

export interface GroupMember {
  id: number
  user_id: number
  username: string
  nickname: string | null
  role: 'member' | 'admin'
  joined_at: string
}

export interface GroupMemberListResponse {
  total: number
  page: number
  page_size: number
  items: GroupMember[]
}

export interface AddMemberData {
  username: string
}

export interface UpdateMemberData {
  role: 'member' | 'admin'
}

export interface GroupProblemProgress {
  problem_id: number
  oj_problem_id: string
  title: string
  ac_time: string
  order: number
}

export interface GroupStepProgress {
  step_id: number
  step_title: string
  total_problems: number
  solved_problems: number
  progress_percent: number
  problems: GroupProblemProgress[]
}

export interface GroupUserProgress {
  user_id: number
  username: string
  nickname: string | null
  steps: GroupStepProgress[]
  total_solved: number
}

export interface GroupProgressResponse {
  group_id: number
  group_name: string
  members: GroupUserProgress[]
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

export async function getGroups(page: number = 1, pageSize: number = 20): Promise<GroupListResponse> {
  const response = await fetch(`/api/groups?page=${page}&page_size=${pageSize}`)
  if (!response.ok) {
    throw new Error('Failed to get groups')
  }
  return await response.json()
}

export async function getGroup(id: number): Promise<Group> {
  const response = await fetch(`/api/groups/${id}`)
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Group not found')
    }
    throw new Error('Failed to get group')
  }
  return await response.json()
}

export async function createGroup(data: CreateGroupData): Promise<Group> {
  const response = await fetchWithAuth('/api/groups', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create group')
  }
  return await response.json()
}

export async function updateGroup(id: number, data: UpdateGroupData): Promise<Group> {
  const response = await fetchWithAuth(`/api/groups/${id}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update group')
  }
  return await response.json()
}

export async function deleteGroup(id: number): Promise<void> {
  const response = await fetchWithAuth(`/api/groups/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete group')
  }
}

export async function getGroupMembers(
  groupId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<GroupMemberListResponse> {
  const response = await fetch(`/api/groups/${groupId}/members?page=${page}&page_size=${pageSize}`)
  if (!response.ok) {
    throw new Error('Failed to get members')
  }
  return await response.json()
}

export async function addGroupMember(groupId: number, data: AddMemberData): Promise<GroupMember> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/members`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to add member')
  }
  return await response.json()
}

export async function updateGroupMember(
  groupId: number,
  userId: number,
  data: UpdateMemberData
): Promise<GroupMember> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/members/${userId}`, {
    method: 'PATCH',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update member')
  }
  return await response.json()
}

export async function removeGroupMember(groupId: number, userId: number): Promise<void> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/members/${userId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to remove member')
  }
}

export async function getGroupProgress(groupId: number): Promise<GroupProgressResponse> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/progress`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get progress')
  }
  return await response.json()
}

export async function getUserProgress(groupId: number, userId: number): Promise<GroupUserProgress> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/progress/${userId}`)
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to get user progress')
  }
  return await response.json()
}
