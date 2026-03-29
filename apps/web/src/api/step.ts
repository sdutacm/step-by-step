import { getToken } from './auth'

export interface StepProblemItem {
  problem_id: number
  order: number
  specialty: string | null
  topic: string | null
}

export interface ProblemSimple {
  id: number
  problem_id: string
  source: string
  title: string
  order: number
  specialty: string | null
  topic: string | null
}

export interface Step {
  id: number
  title: string
  description: string | null
  creator_id: number
  creator_username: string
  group_id: number | null
  group_name: string | null
  created_at: string
  updated_at: string
  problems: ProblemSimple[]
  problem_count: number
}

export interface StepListItem {
  id: number
  title: string
  description: string | null
  creator_id: number
  creator_username: string
  group_id: number | null
  group_name: string | null
  created_at: string
  updated_at: string
  problem_count: number
}

export interface StepListResponse {
  total: number
  page: number
  page_size: number
  items: StepListItem[]
}

export interface CreateStepData {
  title: string
  description?: string
  group_id?: number | null
}

export interface UpdateStepData {
  title?: string
  description?: string
}

export interface AddProblemsData {
  problems: StepProblemItem[]
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

export async function getSteps(page: number = 1, pageSize: number = 20): Promise<StepListResponse> {
  const response = await fetch(`/api/steps?page=${page}&page_size=${pageSize}`)
  if (!response.ok) {
    throw new Error('Failed to get steps')
  }
  return await response.json()
}

export async function getStep(id: number): Promise<Step> {
  const response = await fetch(`/api/steps/${id}`)
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error('Step not found')
    }
    throw new Error('Failed to get step')
  }
  return await response.json()
}

export async function createStep(data: CreateStepData): Promise<Step> {
  const response = await fetchWithAuth('/api/steps', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to create step')
  }
  return await response.json()
}

export async function updateStep(id: number, data: UpdateStepData): Promise<Step> {
  const response = await fetchWithAuth(`/api/steps/${id}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to update step')
  }
  return await response.json()
}

export async function deleteStep(id: number): Promise<void> {
  const response = await fetchWithAuth(`/api/steps/${id}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to delete step')
  }
}

export async function addProblemsToStep(stepId: number, data: AddProblemsData): Promise<Step> {
  const response = await fetchWithAuth(`/api/steps/${stepId}/problems`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(data),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to add problems')
  }
  return await response.json()
}

export async function removeProblemFromStep(stepId: number, problemId: number): Promise<void> {
  const response = await fetchWithAuth(`/api/steps/${stepId}/problems/${problemId}`, {
    method: 'DELETE',
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to remove problem')
  }
}

export async function reorderStepProblems(stepId: number, problemIds: number[]): Promise<Step> {
  const response = await fetchWithAuth(`/api/steps/${stepId}/problems/reorder`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ problem_ids: problemIds }),
  })
  if (!response.ok) {
    const error = await response.json()
    throw new Error(error.detail || 'Failed to reorder problems')
  }
  return await response.json()
}

export async function getProblems(
  page: number = 1,
  pageSize: number = 20,
  title?: string,
  source?: string
): Promise<{ items: ProblemSimple[]; total: number }> {
  let url = `/api/problems?page=${page}&page_size=${pageSize}`
  if (title) {
    url += `&title=${encodeURIComponent(title)}`
  }
  if (source) {
    url += `&source=${encodeURIComponent(source)}`
  }
  const response = await fetch(url)
  if (!response.ok) {
    throw new Error('Failed to get problems')
  }
  return await response.json()
}