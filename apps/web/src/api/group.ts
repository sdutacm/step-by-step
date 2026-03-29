import { getToken } from "./auth";

export interface Group {
  id: number;
  name: string;
  description: string | null;
  creator_id: number | null;
  creator_username: string | null;
  created_at: string;
  updated_at: string;
  member_count: number;
  step_count: number;
}

export interface GroupListItem {
  id: number;
  name: string;
  description: string | null;
  creator_id: number | null;
  creator_username: string | null;
  created_at: string;
  updated_at: string;
  member_count: number;
  step_count: number;
}

export interface GroupListResponse {
  total: number;
  page: number;
  page_size: number;
  items: GroupListItem[];
}

export interface CreateGroupData {
  name: string;
  description?: string;
}

export interface UpdateGroupData {
  name?: string;
  description?: string;
}

export interface GroupMember {
  id: number;
  user_id: number;
  username: string;
  nickname: string | null;
  role: "member" | "admin";
  joined_at: string;
}

export interface GroupMemberListResponse {
  total: number;
  page: number;
  page_size: number;
  items: GroupMember[];
}

export interface AddMemberData {
  username: string;
}

export interface UpdateMemberData {
  role: "member" | "admin";
}

async function fetchWithAuth(url: string, options: RequestInit = {}): Promise<Response> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const headers = new Headers(options.headers as HeadersInit);
  headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(url, {
    ...options,
    headers,
  });
  return response;
}

export async function getGroups(
  page: number = 1,
  pageSize: number = 20
): Promise<GroupListResponse> {
  const response = await fetch(`/api/groups?page=${String(page)}&page_size=${String(pageSize)}`);
  if (!response.ok) {
    throw new Error("Failed to get groups");
  }
  return (await response.json()) as GroupListResponse;
}

export async function getGroup(id: number): Promise<Group> {
  const response = await fetch(`/api/groups/${String(id)}`);
  if (!response.ok) {
    if (response.status === 404) {
      throw new Error("Group not found");
    }
    throw new Error("Failed to get group");
  }
  return (await response.json()) as Group;
}

export async function createGroup(data: CreateGroupData): Promise<Group> {
  const response = await fetchWithAuth("/api/groups", {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to create group");
  }
  return (await response.json()) as Group;
}

export async function updateGroup(id: number, data: UpdateGroupData): Promise<Group> {
  const response = await fetchWithAuth(`/api/groups/${String(id)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to update group");
  }
  return (await response.json()) as Group;
}

export async function deleteGroup(id: number): Promise<void> {
  const response = await fetchWithAuth(`/api/groups/${String(id)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to delete group");
  }
}

export async function getGroupMembers(
  groupId: number,
  page: number = 1,
  pageSize: number = 20
): Promise<GroupMemberListResponse> {
  const response = await fetch(
    `/api/groups/${String(groupId)}/members?page=${String(page)}&page_size=${String(pageSize)}`
  );
  if (!response.ok) {
    throw new Error("Failed to get members");
  }
  return (await response.json()) as GroupMemberListResponse;
}

export async function addGroupMember(groupId: number, data: AddMemberData): Promise<GroupMember> {
  const response = await fetchWithAuth(`/api/groups/${String(groupId)}/members`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to add member");
  }
  return (await response.json()) as GroupMember;
}

export async function updateGroupMember(
  groupId: number,
  userId: number,
  data: UpdateMemberData
): Promise<GroupMember> {
  const response = await fetchWithAuth(`/api/groups/${String(groupId)}/members/${String(userId)}`, {
    method: "PATCH",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(data),
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to update member");
  }
  return (await response.json()) as GroupMember;
}

export async function removeGroupMember(groupId: number, userId: number): Promise<void> {
  const response = await fetchWithAuth(`/api/groups/${String(groupId)}/members/${String(userId)}`, {
    method: "DELETE",
  });
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to remove member");
  }
}

export interface ImportRecord {
  id: number;
  group_id: number;
  imported_by: number | null;
  source: string;
  total_count: number;
  success_count: number;
  skip_count: number;
  error_detail: string | null;
  created_at: string;
}

export interface ImportRecordListResponse {
  items: ImportRecord[];
}

export interface ImportResult {
  total: number;
  success: number;
  skipped: number;
  success_list: Array<{ source: string; username: string; nickname: string | null }>;
  skipped_list: Array<{
    source: string;
    username: string;
    nickname: string | null;
    reason: string;
  }>;
  errors: Array<{ row: number; source: string; username: string; error: string }>;
}

export async function getImportRecords(groupId: number): Promise<ImportRecordListResponse> {
  const response = await fetchWithAuth(`/api/groups/${String(groupId)}/import-records`);
  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to get import records");
  }
  return (await response.json()) as ImportRecordListResponse;
}

export async function downloadImportTemplate(groupId: number): Promise<void> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const response = await fetch(`/api/groups/${String(groupId)}/import-templates`, {
    headers: {
      Authorization: `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Failed to download template");
  }

  const blob = await response.blob();
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = "import_template.xlsx";
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  window.URL.revokeObjectURL(url);
}

export async function importOjAccounts(groupId: number, file: File): Promise<ImportResult> {
  const token = getToken();
  if (!token) {
    throw new Error("No token found");
  }

  const formData = new FormData();
  formData.append("file", file);

  const response = await fetch(`/api/groups/${String(groupId)}/import`, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
    },
    body: formData,
  });

  if (!response.ok) {
    const error = (await response.json()) as { detail?: string };
    throw new Error(error.detail ?? "Import failed");
  }
  return (await response.json()) as ImportResult;
}
