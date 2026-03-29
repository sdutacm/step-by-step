export interface LoginData {
  username: string;
  password: string;
}

export interface RegisterData {
  username: string;
  password: string;
}

export interface AuthResponse {
  access_token: string;
  token_type: string;
}

export interface SourceUser {
  id: number;
  source: string;
  username: string;
}

export interface User {
  id: number;
  username: string;
  nickname: string | null;
  avatar_url: string | null;
  source_users: SourceUser[];
  is_super_admin?: boolean;
}

export interface UserUpdateData {
  nickname?: string;
  avatar_url?: string;
}

export interface SourceBindingData {
  source: string;
  username: string;
  password: string;
}

const TOKEN_KEY = "access_token";

export function getToken(): string | null {
  return localStorage.getItem(TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(TOKEN_KEY, token);
}

export function removeToken(): void {
  localStorage.removeItem(TOKEN_KEY);
}

export async function login(data: LoginData): Promise<AuthResponse> {
  const formData = new URLSearchParams();
  formData.append("username", data.username);
  formData.append("password", data.password);

  const response = await fetch("/api/auth/login", {
    method: "POST",
    headers: {
      "Content-Type": "application/x-www-form-urlencoded",
    },
    body: formData,
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "登录失败");
  }

  const result = (await response.json()) as AuthResponse;
  setToken(result.access_token);
  return result;
}

export async function register(data: RegisterData): Promise<User> {
  const response = await fetch("/api/auth/register", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "注册失败");
  }

  return (await response.json()) as User;
}

export async function getCurrentUser(): Promise<User> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch("/api/auth/me", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    removeToken();
    throw new Error("Failed to get current user");
  }

  return (await response.json()) as User;
}

export async function updateCurrentUser(data: UserUpdateData): Promise<User> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch("/api/auth/me", {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    throw new Error("Failed to update user");
  }

  return (await response.json()) as User;
}

export function logout(): void {
  removeToken();
}

export interface Source {
  source: string;
}

export async function getSources(): Promise<Source[]> {
  const response = await fetch("/api/sources");
  if (!response.ok) {
    throw new Error("Failed to get sources");
  }
  return (await response.json()) as Source[];
}

export async function bindSource(data: SourceBindingData): Promise<SourceUser> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch("/api/sources/bind", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "绑定失败");
  }

  return (await response.json()) as SourceUser;
}

export async function unbindSource(bindingId: number): Promise<void> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch(`/api/sources/unbind/${String(bindingId)}`, {
    method: "DELETE",
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "解绑失败");
  }
}

export interface Solution {
  id: number;
  username: string;
  nickname: string | null;
  source: string;
  result: number;
  language: number;
  submitted_at: string;
  solution_id: number;
  problem_id: number | null;
  oj_problem_id: string | null;
  problem_title: string | null;
}

export interface PaginatedSolutions {
  total: number;
  page: number;
  page_size: number;
  items: Solution[];
}

export interface GetSolutionsParams {
  page?: number;
  page_size?: number;
}

export async function getSolutions(params: GetSolutionsParams = {}): Promise<PaginatedSolutions> {
  const { page = 1, page_size = 20 } = params;
  const response = await fetch(
    `/api/solutions/?page=${String(page)}&page_size=${String(page_size)}`
  );
  if (!response.ok) {
    throw new Error("Failed to get solutions");
  }
  return (await response.json()) as PaginatedSolutions;
}

export interface ClaimGhostData {
  source: string;
  username: string;
  password: string;
}

export interface ClaimGhostResult {
  success: boolean;
  message: string;
}

export interface GhostAccount {
  source: string;
  username: string;
  nickname: string | null;
  bound: boolean;
}

export interface GhostAccountListResponse {
  ghosts: GhostAccount[];
}

export async function claimGhostAccount(data: ClaimGhostData): Promise<ClaimGhostResult> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch("/api/auth/claim-ghost", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Authorization: `Bearer ${token}`,
    },
    body: JSON.stringify(data),
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Claim failed");
  }
  return (await response.json()) as ClaimGhostResult;
}

export async function getGhostAccounts(): Promise<GhostAccountListResponse> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch("/api/auth/ghost-accounts", {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    throw new Error("Failed to get ghost accounts");
  }
  return (await response.json()) as GhostAccountListResponse;
}
