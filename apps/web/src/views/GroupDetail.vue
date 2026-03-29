<script setup lang="ts">
import { ref, onMounted, computed, watch } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ElCard,
  ElButton,
  ElTable,
  ElTableColumn,
  ElTag,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElDialog,
  ElForm,
  ElFormItem,
  ElInput,
  ElTabs,
  ElTabPane,
  ElSelect,
  ElOption,
  ElProgress,
  ElSkeleton,
} from 'element-plus'
import {
  getGroup,
  updateGroup,
  getGroupMembers,
  addGroupMember,
  updateGroupMember,
  removeGroupMember,
  getGroupProgress,
  type Group,
  type GroupMember,
  type GroupUserProgress,
  type UpdateMemberData,
} from '../api/group'
import {
  getBoards,
  createBoard,
  updateBoard,
  deleteBoard,
  getBoardUsers,
  createBoardUsers,
  deleteBoardUser,
  type Board,
  type BoardListItem,
  type BoardVisibility,
  type CreateBoardData,
  type UpdateBoardData,
  type BoardUser,
} from '../api/board'
import { getSteps, type StepListItem } from '../api/step'
import { getCurrentUser } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const group = ref<Group | null>(null)
const isLoading = ref(false)
const isEditing = ref(false)
const isSubmitting = ref(false)

const members = ref<GroupMember[]>([])
const membersPagination = ref({ page: 1, page_size: 20, total: 0 })
const membersLoading = ref(false)

const addMemberDialogVisible = ref(false)
const addMemberForm = ref({ username: '' })
const isAddingMember = ref(false)

const editMemberDialogVisible = ref(false)
const editMemberForm = ref<UpdateMemberData>({ role: 'member' })
const editingMember = ref<GroupMember | null>(null)

const progress = ref<GroupUserProgress[]>([])
const progressLoading = ref(false)

const boards = ref<BoardListItem[]>([])
const boardsPagination = ref({ page: 1, page_size: 20, total: 0 })
const boardsLoading = ref(false)

const createBoardDialogVisible = ref(false)
const availableSteps = ref<StepListItem[]>([])
const createBoardForm = ref<CreateBoardData & { step_id: number }>({
  name: '',
  description: '',
  visibility: 'board_user',
  step_id: 0,
})
const isCreatingBoard = ref(false)

const editBoardDialogVisible = ref(false)
const editBoardForm = ref<UpdateBoardData & { step_id: number }>({
  name: '',
  description: '',
  visibility: 'board_user',
  step_id: 0,
})
const editingBoard = ref<BoardListItem | null>(null)
const isUpdatingBoard = ref(false)

const manageBoardUsersDialogVisible = ref(false)
const boardUsers = ref<BoardUser[]>([])
const boardUsersLoading = ref(false)
const availableUsers = ref<{ id: number; username: string; nickname: string | null }[]>([])
const selectedUserIds = ref<number[]>([])
const isManagingUsers = ref(false)

const currentUser = ref<{ id: number } | null>(null)
const groupMemberRole = ref<'admin' | 'member' | null>(null)

const groupId = computed(() => Number(route.params.id))

const editForm = ref({
  name: '',
  description: '',
})

function formatTime(time: string) {
  const d = new Date(time)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

async function fetchCurrentUser() {
  try {
    const user = await getCurrentUser()
    currentUser.value = user
    userStore.setUser(user)
  } catch {
    currentUser.value = null
    userStore.clearUser()
  }
}

async function fetchGroup() {
  isLoading.value = true
  try {
    group.value = await getGroup(groupId.value)
    editForm.value.name = group.value.name
    editForm.value.description = group.value.description || ''
  } catch {
    ElMessage.error('获取组织详情失败')
    router.push('/groups')
  } finally {
    isLoading.value = false
  }
}

async function fetchMembers() {
  membersLoading.value = true
  try {
    const data = await getGroupMembers(groupId.value, membersPagination.value.page, membersPagination.value.page_size)
    members.value = data.items
    membersPagination.value.total = data.total
    if (currentUser.value) {
      const myMembership = data.items.find((m) => m.user_id === currentUser.value!.id)
      groupMemberRole.value = myMembership?.role || null
    }
  } catch {
    ElMessage.error('获取成员列表失败')
  } finally {
    membersLoading.value = false
  }
}

async function fetchProgress() {
  progressLoading.value = true
  try {
    const data = await getGroupProgress(groupId.value)
    progress.value = data.members
  } catch {
    ElMessage.error('获取学习进度失败')
  } finally {
    progressLoading.value = false
  }
}

async function fetchBoards() {
  boardsLoading.value = true
  try {
    const data = await getBoards(groupId.value, boardsPagination.value.page, boardsPagination.value.page_size)
    boards.value = data.items
    boardsPagination.value.total = data.total
  } catch {
    ElMessage.error('获取看板列表失败')
  } finally {
    boardsLoading.value = false
  }
}

async function fetchAvailableSteps() {
  try {
    const stepsRes = await getSteps(1, 100)
    availableSteps.value = stepsRes.items
  } catch {
    ElMessage.error('获取训练计划列表失败')
  }
}

function openCreateBoardDialog() {
  fetchAvailableSteps()
  createBoardForm.value = {
    name: '',
    description: '',
    visibility: 'board_user',
    step_id: 0,
  }
  createBoardDialogVisible.value = true
}

async function handleCreateBoard() {
  if (!createBoardForm.value.name.trim()) {
    ElMessage.warning('请输入看板名称')
    return
  }
  if (!createBoardForm.value.step_id) {
    ElMessage.warning('请选择训练计划')
    return
  }
  isCreatingBoard.value = true
  try {
    await createBoard(groupId.value, createBoardForm.value)
    ElMessage.success('创建成功')
    createBoardDialogVisible.value = false
    await fetchBoards()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '创建失败')
  } finally {
    isCreatingBoard.value = false
  }
}

async function openEditBoardDialog(board: BoardListItem) {
  const fullBoard = await getBoards(groupId.value).then(res => res.items.find(b => b.id === board.id))
  if (!fullBoard) return
  await fetchAvailableSteps()
  editingBoard.value = board
  editBoardForm.value = {
    name: board.name,
    description: board.description || '',
    visibility: board.visibility,
    step_id: 0,
  }
  editBoardDialogVisible.value = true
}

async function handleUpdateBoard() {
  if (!editingBoard.value) return
  if (!editBoardForm.value.name?.trim()) {
    ElMessage.warning('请输入看板名称')
    return
  }
  isUpdatingBoard.value = true
  try {
    const updateData: UpdateBoardData = {
      name: editBoardForm.value.name,
      description: editBoardForm.value.description || undefined,
      visibility: editBoardForm.value.visibility,
      step_id: editBoardForm.value.step_id || undefined,
    }
    await updateBoard(editingBoard.value.id, updateData)
    ElMessage.success('更新成功')
    editBoardDialogVisible.value = false
    editingBoard.value = null
    await fetchBoards()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
  } finally {
    isUpdatingBoard.value = false
  }
}

async function handleDeleteBoard(board: BoardListItem) {
  try {
    await ElMessageBox.confirm(
      `确定要删除看板「${board.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteBoard(board.id)
    ElMessage.success('删除成功')
    await fetchBoards()
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '删除失败')
    }
  }
}

async function openManageBoardUsersDialog(board: BoardListItem) {
  editingBoard.value = board
  manageBoardUsersDialogVisible.value = true
  await fetchBoardUsers(board.id)
  const membersRes = await getGroupMembers(groupId.value, 1, 100)
  availableUsers.value = membersRes.items.map(m => ({
    id: m.user_id,
    username: m.username,
    nickname: m.nickname,
  }))
  selectedUserIds.value = []
}

async function fetchBoardUsers(boardId: number) {
  boardUsersLoading.value = true
  try {
    const data = await getBoardUsers(boardId)
    boardUsers.value = data.items
  } catch {
    ElMessage.error('获取成员列表失败')
  } finally {
    boardUsersLoading.value = false
  }
}

async function handleAddBoardUsers() {
  if (!editingBoard.value || !selectedUserIds.value.length) {
    ElMessage.warning('请选择用户')
    return
  }
  isManagingUsers.value = true
  try {
    await createBoardUsers(editingBoard.value.id, selectedUserIds.value)
    ElMessage.success('添加成功')
    selectedUserIds.value = []
    await fetchBoardUsers(editingBoard.value.id)
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '添加失败')
  } finally {
    isManagingUsers.value = false
  }
}

async function handleRemoveBoardUser(userId: number, username: string) {
  if (!editingBoard.value) return
  try {
    await ElMessageBox.confirm(
      `确定要移除「${username}」吗？`,
      '移除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteBoardUser(editingBoard.value.id, userId)
    ElMessage.success('移除成功')
    await fetchBoardUsers(editingBoard.value.id)
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '移除失败')
    }
  }
}

function handleBoardsPageChange(page: number) {
  boardsPagination.value.page = page
  fetchBoards()
}

async function handleUpdate() {
  if (!editForm.value.name.trim()) {
    ElMessage.error('请输入名称')
    return
  }
  isSubmitting.value = true
  try {
    await updateGroup(groupId.value, {
      name: editForm.value.name,
      description: editForm.value.description || undefined,
    })
    ElMessage.success('更新成功')
    isEditing.value = false
    await fetchGroup()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
  } finally {
    isSubmitting.value = false
  }
}

async function handleAddMember() {
  if (!addMemberForm.value.username.trim()) {
    ElMessage.warning('请输入用户名')
    return
  }
  isAddingMember.value = true
  try {
    await addGroupMember(groupId.value, { username: addMemberForm.value.username })
    ElMessage.success('添加成功')
    addMemberDialogVisible.value = false
    addMemberForm.value.username = ''
    await fetchMembers()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '添加失败')
  } finally {
    isAddingMember.value = false
  }
}

function openEditMemberDialog(member: GroupMember) {
  editingMember.value = member
  editMemberForm.value.role = member.role
  editMemberDialogVisible.value = true
}

async function handleUpdateMember() {
  if (!editingMember.value) return
  isSubmitting.value = true
  try {
    await updateGroupMember(groupId.value, editingMember.value.user_id, editMemberForm.value)
    ElMessage.success('更新成功')
    editMemberDialogVisible.value = false
    editingMember.value = null
    await fetchMembers()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
  } finally {
    isSubmitting.value = false
  }
}

async function handleRemoveMember(member: GroupMember) {
  try {
    await ElMessageBox.confirm(
      `确定要将「${member.username}」从组织中移除吗？`,
      '移除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await removeGroupMember(groupId.value, member.user_id)
    ElMessage.success('移除成功')
    await fetchMembers()
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '移除失败')
    }
  }
}

function handleMembersPageChange(page: number) {
  membersPagination.value.page = page
  fetchMembers()
}

function isAdmin() {
  return userStore.isSuperAdmin || groupMemberRole.value === 'admin'
}

function getStepProgressColor(percent: number): string {
  if (percent >= 100) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#909399'
}

function getVisibilityLabel(visibility: BoardVisibility): string {
  const labels: Record<BoardVisibility, string> = {
    public: '公开',
    group_member: '组内可见',
    board_user: '看板内可见',
  }
  return labels[visibility] || visibility
}

function getVisibilityType(visibility: BoardVisibility): string {
  if (visibility === 'public') return 'success'
  if (visibility === 'group_member') return 'warning'
  return 'info'
}

onMounted(async () => {
  await fetchCurrentUser()
  await Promise.all([fetchGroup(), fetchMembers(), fetchBoards()])
})

watch(
  () => userStore.user,
  async (newUser, oldUser) => {
    if (!oldUser && newUser) {
      await fetchCurrentUser()
      await Promise.all([fetchMembers(), fetchBoards()])
    }
  }
)
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px">
    <el-card v-if="!isLoading && group">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>{{ group.name }}</span>
          <div style="display: flex; gap: 8px">
            <el-button @click="router.push('/groups')">返回列表</el-button>
            <el-button v-if="isAdmin() && !isEditing" type="primary" @click="isEditing = true">
              编辑信息
            </el-button>
          </div>
        </div>
      </template>

      <template v-if="isEditing">
        <el-form label-position="top" :model="editForm">
          <el-form-item label="名称" required>
            <el-input v-model="editForm.name" placeholder="请输入名称" maxlength="100" show-word-limit />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="editForm.description"
              type="textarea"
              placeholder="请输入描述"
              :rows="3"
              maxlength="500"
              show-word-limit
            />
          </el-form-item>
          <el-form-item>
            <el-button type="primary" :loading="isSubmitting" @click="handleUpdate">保存</el-button>
            <el-button @click="isEditing = false">取消</el-button>
          </el-form-item>
        </el-form>
      </template>

      <template v-else>
        <div style="display: flex; flex-direction: column; gap: 16px">
          <div>
            <strong>描述：</strong>
            <span>{{ group.description || '暂无描述' }}</span>
          </div>
          <div>
            <strong>成员数：</strong>
            <span>{{ group.member_count }}</span>
          </div>
          <div>
            <strong>训练计划数：</strong>
            <span>{{ group.step_count }}</span>
          </div>
          <div>
            <strong>创建时间：</strong>
            <span>{{ formatTime(group.created_at) }}</span>
          </div>
        </div>
      </template>
    </el-card>
    <el-card v-else>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>组织详情</span>
        </div>
      </template>
      <el-skeleton :rows="4" animated />
    </el-card>

    <el-card>
      <el-tabs>
        <el-tab-pane label="成员管理">
          <template #label>
            <span>成员管理 ({{ membersPagination.total }})</span>
          </template>
          <div style="margin-bottom: 16px; display: flex; justify-content: flex-end">
            <el-button v-if="isAdmin()" type="primary" @click="addMemberDialogVisible = true">
              添加成员
            </el-button>
          </div>
          <el-table v-loading="membersLoading" :data="members" style="width: 100%">
            <el-table-column prop="username" label="用户名" min-width="150">
              <template #default="{ row }">
                <span>{{ row.username }}</span>
                <el-tag v-if="row.role === 'admin'" type="warning" size="small" style="margin-left: 8px">
                  管理员
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="nickname" label="昵称" min-width="150">
              <template #default="{ row }">
                {{ row.nickname || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="role" label="角色" width="100">
              <template #default="{ row }">
                <el-tag :type="row.role === 'admin' ? 'warning' : 'info'" size="small">
                  {{ row.role === 'admin' ? '管理员' : '成员' }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="joined_at" label="加入时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.joined_at) }}
              </template>
            </el-table-column>
            <el-table-column v-if="isAdmin()" label="操作" width="160" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="openEditMemberDialog(row)">
                  编辑
                </el-button>
                <el-button type="danger" size="small" @click="handleRemoveMember(row)">
                  移除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!membersLoading && !members.length" description="暂无成员" />
          <div v-if="membersPagination.total > membersPagination.page_size" style="margin-top: 16px; display: flex; justify-content: flex-end">
            <el-pagination
              v-model:current-page="membersPagination.page"
              :page-size="membersPagination.page_size"
              :total="membersPagination.total"
              layout="prev, pager, next, jumper"
              @current-change="handleMembersPageChange"
            />
          </div>
        </el-tab-pane>

        <el-tab-pane label="学习进度">
          <template #label>
            <span>学习进度</span>
          </template>
          <div v-loading="progressLoading">
            <div v-if="!progressLoading && !progress.length" style="padding: 40px 0">
              <el-empty description="暂无学习进度数据" />
            </div>
            <div v-else style="display: flex; flex-direction: column; gap: 20px">
              <el-card v-for="userProgress in progress" :key="userProgress.user_id" shadow="hover">
                <template #header>
                  <div style="display: flex; align-items: center; justify-content: space-between">
                    <span>
                      {{ userProgress.username }}
                      <el-tag v-if="userProgress.nickname" size="small" style="margin-left: 8px">
                        {{ userProgress.nickname }}
                      </el-tag>
                    </span>
                    <span style="color: #67c23a; font-weight: bold">
                      总计 {{ userProgress.total_solved }} 道
                    </span>
                  </div>
                </template>
                <div v-if="userProgress.steps.length === 0" style="padding: 20px; text-align: center; color: #909399">
                  暂无训练计划进度
                </div>
                <div v-else style="display: flex; flex-direction: column; gap: 16px">
                  <div v-for="stepProgress in userProgress.steps" :key="stepProgress.step_id">
                    <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
                      <span style="font-weight: 500">{{ stepProgress.step_title }}</span>
                      <span style="color: #606266">
                        {{ stepProgress.solved_problems }}/{{ stepProgress.total_problems }}
                        ({{ stepProgress.progress_percent.toFixed(1) }}%)
                      </span>
                    </div>
                    <el-progress
                      :percentage="stepProgress.progress_percent"
                      :color="getStepProgressColor(stepProgress.progress_percent)"
                      :stroke-width="10"
                    />
                    <div v-if="stepProgress.problems.length" style="margin-top: 8px; padding-left: 12px">
                      <div
                        v-for="problem in stepProgress.problems"
                        :key="problem.problem_id"
                        style="font-size: 12px; color: #67c23a; margin: 4px 0"
                      >
                        ✓ {{ problem.title }} ({{ formatTime(problem.ac_time) }})
                      </div>
                    </div>
                  </div>
                </div>
              </el-card>
            </div>
          </div>
        </el-tab-pane>

        <el-tab-pane v-if="isAdmin()" label="看板管理">
          <template #label>
            <span>看板管理 ({{ boardsPagination.total }})</span>
          </template>
          <div style="margin-bottom: 16px; display: flex; justify-content: flex-end">
            <el-button type="primary" @click="openCreateBoardDialog">
              创建看板
            </el-button>
          </div>
          <el-table v-loading="boardsLoading" :data="boards" style="width: 100%">
            <el-table-column prop="name" label="名称" min-width="150" />
            <el-table-column prop="description" label="描述" min-width="200">
              <template #default="{ row }">
                {{ row.description || '-' }}
              </template>
            </el-table-column>
            <el-table-column prop="visibility" label="可见性" width="120">
              <template #default="{ row }">
                <el-tag :type="getVisibilityType(row.visibility)" size="small">
                  {{ getVisibilityLabel(row.visibility) }}
                </el-tag>
              </template>
            </el-table-column>
            <el-table-column prop="creator_username" label="创建者" width="120" />
            <el-table-column prop="created_at" label="创建时间" width="180">
              <template #default="{ row }">
                {{ formatTime(row.created_at) }}
              </template>
            </el-table-column>
            <el-table-column label="操作" width="200" fixed="right">
              <template #default="{ row }">
                <el-button type="primary" size="small" @click="router.push(`/boards/${row.id}`)">
                  查看
                </el-button>
                <el-button type="primary" size="small" @click="openManageBoardUsersDialog(row)">
                  成员
                </el-button>
                <el-button type="warning" size="small" @click="openEditBoardDialog(row)">
                  编辑
                </el-button>
                <el-button type="danger" size="small" @click="handleDeleteBoard(row)">
                  删除
                </el-button>
              </template>
            </el-table-column>
          </el-table>
          <el-empty v-if="!boardsLoading && !boards.length" description="暂无看板" />
          <div v-if="boardsPagination.total > boardsPagination.page_size" style="margin-top: 16px; display: flex; justify-content: flex-end">
            <el-pagination
              v-model:current-page="boardsPagination.page"
              :page-size="boardsPagination.page_size"
              :total="boardsPagination.total"
              layout="prev, pager, next, jumper"
              @current-change="handleBoardsPageChange"
            />
          </div>
        </el-tab-pane>
      </el-tabs>
    </el-card>
  </div>

  <el-dialog v-model="addMemberDialogVisible" title="添加成员" width="400px">
    <el-form :model="addMemberForm" label-width="80px">
      <el-form-item label="用户名" required>
        <el-input v-model="addMemberForm.username" placeholder="请输入要添加的用户名" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="addMemberDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isAddingMember" @click="handleAddMember">添加</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="editMemberDialogVisible" title="编辑成员" width="400px">
    <el-form :model="editMemberForm" label-width="80px">
      <el-form-item label="用户名">
        <span>{{ editingMember?.username }}</span>
      </el-form-item>
      <el-form-item label="角色" required>
        <el-select v-model="editMemberForm.role">
          <el-option label="成员" value="member" />
          <el-option label="管理员" value="admin" />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editMemberDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleUpdateMember">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="createBoardDialogVisible" title="创建看板" width="500px">
    <el-form :model="createBoardForm" label-position="top">
      <el-form-item label="名称" required>
        <el-input v-model="createBoardForm.name" placeholder="请输入看板名称" maxlength="100" show-word-limit />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="createBoardForm.description"
          type="textarea"
          placeholder="请输入描述"
          :rows="3"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="可见性">
        <el-select v-model="createBoardForm.visibility" style="width: 100%">
          <el-option label="公开" value="public" />
          <el-option label="组内可见" value="group_member" />
          <el-option label="看板内可见" value="board_user" />
        </el-select>
      </el-form-item>
      <el-form-item label="训练计划" required>
        <el-select v-model="createBoardForm.step_id" placeholder="请选择训练计划" style="width: 100%">
          <el-option
            v-for="step in availableSteps"
            :key="step.id"
            :label="step.title"
            :value="step.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createBoardDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isCreatingBoard" @click="handleCreateBoard">创建</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="editBoardDialogVisible" title="编辑看板" width="500px">
    <el-form :model="editBoardForm" label-position="top">
      <el-form-item label="名称" required>
        <el-input v-model="editBoardForm.name" placeholder="请输入看板名称" maxlength="100" show-word-limit />
      </el-form-item>
      <el-form-item label="描述">
        <el-input
          v-model="editBoardForm.description"
          type="textarea"
          placeholder="请输入描述"
          :rows="3"
          maxlength="500"
          show-word-limit
        />
      </el-form-item>
      <el-form-item label="可见性">
        <el-select v-model="editBoardForm.visibility" style="width: 100%">
          <el-option label="公开" value="public" />
          <el-option label="组内可见" value="group_member" />
          <el-option label="看板内可见" value="board_user" />
        </el-select>
      </el-form-item>
      <el-form-item label="训练计划">
        <el-select v-model="editBoardForm.step_id" placeholder="请选择训练计划（不修改请留空）" style="width: 100%">
          <el-option :value="0" label="不修改" />
          <el-option
            v-for="step in availableSteps"
            :key="step.id"
            :label="step.title"
            :value="step.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editBoardDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isUpdatingBoard" @click="handleUpdateBoard">保存</el-button>
    </template>
  </el-dialog>

  <el-dialog v-model="manageBoardUsersDialogVisible" :title="`管理看板成员 - ${editingBoard?.name}`" width="600px">
    <div style="margin-bottom: 16px">
      <el-select
        v-model="selectedUserIds"
        multiple
        placeholder="选择要添加的用户"
        style="width: 100%"
      >
        <el-option
          v-for="user in availableUsers"
          :key="user.id"
          :label="user.username + (user.nickname ? ` (${user.nickname})` : '')"
          :value="user.id"
        />
      </el-select>
      <el-button type="primary" style="margin-top: 8px" :loading="isManagingUsers" @click="handleAddBoardUsers">
        添加选中用户
      </el-button>
    </div>
    <el-divider />
    <el-table v-loading="boardUsersLoading" :data="boardUsers" style="width: 100%">
      <el-table-column prop="username" label="用户名" min-width="150" />
      <el-table-column prop="nickname" label="昵称" min-width="150">
        <template #default="{ row }">
          {{ row.nickname || '-' }}
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="添加时间" width="180">
        <template #default="{ row }">
          {{ formatTime(row.created_at) }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="80" fixed="right">
        <template #default="{ row }">
          <el-button type="danger" size="small" @click="handleRemoveBoardUser(row.user_id, row.username)">
            移除
          </el-button>
        </template>
      </el-table-column>
    </el-table>
    <el-empty v-if="!boardUsersLoading && !boardUsers.length" description="暂无成员" />
  </el-dialog>
</template>