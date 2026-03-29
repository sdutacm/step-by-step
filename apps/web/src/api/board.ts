import { getToken } from "./auth";

export type BoardVisibility = "public" | "group_member" | "board_user";

export interface Board {
  id: number;
  name: string;
  description: string | null;
  visibility: BoardVisibility;
  group_id: number;
  group_name: string | null;
  created_by: number;
  creator_username: string;
  created_at: string;
  updated_at: string;
  step_id: number;
  step_title: string;
  member_count: number;
}

export interface BoardListItem {
  id: number;
  name: string;
  description: string | null;
  visibility: BoardVisibility;
  group_id: number;
  created_by: number;
  creator_username: string;
  created_at: string;
  updated_at: string;
}

export interface PublicBoardListItem {
  id: number;
  name: string;
  description: string | null;
  visibility: BoardVisibility;
  group_id: number;
  group_name: string | null;
  step_id: number;
  step_title: string;
  created_by: number;
  creator_username: string;
  created_at: string;
  updated_at: string;
}

export interface PublicBoardListResponse {
  total: number;
  page: number;
  page_size: number;
  items: PublicBoardListItem[];
}

export interface BoardListResponse {
  total: number;
  page: number;
  page_size: number;
  items: BoardListItem[];
}

export interface CreateBoardData {
  name: string;
  description?: string;
  visibility: BoardVisibility;
  step_id: number;
}

export interface UpdateBoardData {
  name?: string;
  description?: string;
  visibility?: BoardVisibility;
  step_id?: number;
}

export interface BoardUser {
  id: number;
  board_id: number;
  user_id: number;
  username: string;
  nickname: string | null;
  created_at: string;
}

export interface BoardUserListResponse {
  total: number;
  items: BoardUser[];
}

export interface SubmissionRecord {
  result: number;
  submitted_at: string;
  language: number;
}

export interface ProblemProgress {
  problem_id: number;
  oj_problem_id: string;
  source: string;
  title: string;
  order: number;
  specialty: string | null;
  topic: string | null;
  ac_time: string | null;
  failed_time: string | null;
  result: number | null;
  submissions: SubmissionRecord[];
}

export interface UserBoardProgress {
  user_id: number;
  username: string;
  nickname: string | null;
  solved_problems: number;
  total_problems: number;
  progress_percent: number;
  status: "not_started" | "in_progress" | "completed";
  problems: ProblemProgress[];
}

export interface BoardProgressResponse {
  board_id: number;
  board_name: string;
  step_id: number;
  step_title: string;
  group_id: number;
  users: UserBoardProgress[];
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch(url, {
    ...options,
    headers: {
      ...options.headers,
      Authorization: `Bearer ${token}`,
    },
  });
  return response;
}

export async function getBoards(
  groupId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<BoardListResponse> {
  const response = await fetch(`/api/groups/${groupId}/boards?page=${page}&page_size=${pageSize}`);
  if (!response.ok) {
    throw new Error("Failed to get boards");
  }
  return await response.json();
}

export async function getPublicBoards(
  page: number = 1,
  pageSize: number = 20
): Promise<PublicBoardListResponse> {
  const response = await fetch(`/api/boards/public?page=${page}&page_size=${pageSize}`);
  if (!response.ok) {
    throw new Error("Failed to get public boards");
  }
  return await response.json();
}

export async function getBoard(id: number): Promise<Board> {
  const response = await fetch(`/api/boards/${id}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Board not found");
    }
    throw new Error("Failed to get board");
  }
  return await response.json();
}

export async function createBoard(groupId: number, data: CreateBoardData): Promise<Board> {
  const response = await fetchWithAuth(`/api/groups/${groupId}/boards`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create board");
  }
  return await response.json();
}

export async function updateBoard(id: number, data: UpdateBoardData): Promise<Board> {
  const response = await fetchWithAuth(`/api/boards/${id}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to update board");
  }
  return await response.json();
}

export async function deleteBoard(id: number): Promise<void> {
  const response = await fetchWithAuth(`/api/boards/${id}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete board");
  }
}

export async function getBoardUsers(boardId: number): Promise<BoardUserListResponse> {
  const response = await fetchWithAuth(`/api/boards/${boardId}/users`);
  if (!response.ok) {
    throw new Error("Failed to get board users");
  }
  return await response.json();
}

export async function createBoardUsers(
  boardId: number,
  userIds: number[]
): Promise<BoardUserListResponse> {
  const response = await fetchWithAuth(`/api/boards/${boardId}/users`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(userIds),
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to create board users");
  }
  return await response.json();
}

export async function deleteBoardUser(boardId: number, userId: number): Promise<void> {
  const response = await fetchWithAuth(`/api/boards/${boardId}/users/${userId}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to delete board user");
  }
}

export async function getBoardProgress(boardId: number): Promise<BoardProgressResponse> {
  const response = await fetchWithAuth(`/api/boards/${boardId}/progress`);
  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail || "Failed to get board progress");
  }
  return await response.json();
}
