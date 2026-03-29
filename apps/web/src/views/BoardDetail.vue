<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
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
  ElSelect,
  ElOption,
  ElProgress,
  ElSkeleton,
  ElBadge,
} from 'element-plus'
import {
  getBoard,
  updateBoard,
  deleteBoard,
  getBoardAssignments,
  createAssignments,
  deleteAssignment,
  getBoardProgress,
  type Board,
  type BoardProgressResponse,
  type Assignment,
  type UpdateBoardData,
  type CreateAssignmentData,
  type BoardVisibility,
} from '../api/board'
import { getGroup, getGroupMembers, type Group, type GroupMember } from '../api/group'
import { getSteps, type StepListItem } from '../api/step'
import { getCurrentUser } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const board = ref<Board | null>(null)
const group = ref<Group | null>(null)
const isLoading = ref(false)
const isEditing = ref(false)
const isSubmitting = ref(false)

const assignments = ref<Assignment[]>([])
const assignmentsLoading = ref(false)

const progress = ref<BoardProgressResponse | null>(null)
const progressLoading = ref(false)

const currentUser = ref<{ id: number } | null>(null)
const groupMemberRole = ref<'admin' | 'member' | null>(null)

const boardId = computed(() => Number(route.params.id))

const editForm = ref<UpdateBoardData>({
  name: '',
  description: '',
  visibility: 'board_user',
})

const createAssignmentDialogVisible = ref(false)
const availableSteps = ref<StepListItem[]>([])
const availableUsers = ref<{ id: number; username: string; nickname: string | null }[]>([])
const selectedStepId = ref<number | null>(null)
const selectedUserId = ref<number | null>(null)
const isCreatingAssignment = ref(false)

function formatTime(time: string) {
  const d = new Date(time)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
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

function getStatusType(status: string): string {
  if (status === 'completed') return 'success'
  if (status === 'in_progress') return 'warning'
  return 'info'
}

function getStatusLabel(status: string): string {
  if (status === 'completed') return '已完成'
  if (status === 'in_progress') return '进行中'
  return '未开始'
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

async function fetchBoard() {
  isLoading.value = true
  try {
    board.value = await getBoard(boardId.value)
    editForm.value.name = board.value.name
    editForm.value.description = board.value.description || ''
    editForm.value.visibility = board.value.visibility
    if (board.value.group_id) {
      group.value = await getGroup(board.value.group_id)
      const membersRes = await getGroupMembers(board.value.group_id, 1, 100)
      const myMembership = membersRes.items.find(m => m.user_id === currentUser.value?.id)
      if (myMembership) {
        groupMemberRole.value = myMembership.role
      }
    }
  } catch {
    ElMessage.error('获取看板详情失败')
    router.push('/groups')
  } finally {
    isLoading.value = false
  }
}

async function fetchAssignments() {
  assignmentsLoading.value = true
  try {
    const data = await getBoardAssignments(boardId.value)
    assignments.value = data.items
  } catch {
    ElMessage.error('获取分配列表失败')
  } finally {
    assignmentsLoading.value = false
  }
}

async function fetchProgress() {
  progressLoading.value = true
  try {
    progress.value = await getBoardProgress(boardId.value)
  } catch {
    ElMessage.error('获取学习进度失败')
  } finally {
    progressLoading.value = false
  }
}

async function fetchAvailableData() {
  if (!board.value) {
    ElMessage.error('看板信息未加载')
    return
  }
  try {
    const stepsRes = await getSteps(1, 100)
    availableSteps.value = stepsRes.items
    const membersRes = await getGroupMembers(board.value.group_id, 1, 100)
    availableUsers.value = membersRes.items.map(m => ({
      id: m.user_id,
      username: m.username,
      nickname: m.nickname,
    }))
  } catch (e: unknown) {
    ElMessage.error('获取可选数据失败: ' + (e instanceof Error ? e.message : '未知错误'))
  }
}

async function handleUpdate() {
  if (!editForm.value.name?.trim()) {
    ElMessage.error('请输入名称')
    return
  }
  isSubmitting.value = true
  try {
    await updateBoard(boardId.value, editForm.value)
    ElMessage.success('更新成功')
    isEditing.value = false
    await fetchBoard()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
  } finally {
    isSubmitting.value = false
  }
}

async function handleDelete() {
  try {
    await ElMessageBox.confirm(
      `确定要删除看板「${board.value?.name}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteBoard(boardId.value)
    ElMessage.success('删除成功')
    router.push(`/groups/${board.value?.group_id}`)
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '删除失败')
    }
  }
}

async function handleCreateAssignments() {
  if (!selectedStepId.value || !selectedUserId.value) {
    ElMessage.warning('请选择训练计划和用户')
    return
  }
  isCreatingAssignment.value = true
  try {
    await createAssignments(boardId.value, [{ step_id: selectedStepId.value, user_id: selectedUserId.value }])
    ElMessage.success('分配成功')
    createAssignmentDialogVisible.value = false
    selectedStepId.value = null
    selectedUserId.value = null
    await Promise.all([fetchAssignments(), fetchProgress()])
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '分配失败')
  } finally {
    isCreatingAssignment.value = false
  }
}

async function handleRemoveAssignment(assignment: Assignment) {
  try {
    await ElMessageBox.confirm(
      `确定要移除「${assignment.username}」的「${assignment.step_title}」分配吗？`,
      '移除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteAssignment(boardId.value, assignment.id)
    ElMessage.success('移除成功')
    await Promise.all([fetchAssignments(), fetchProgress()])
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '移除失败')
    }
  }
}

function openCreateAssignmentDialog() {
  fetchAvailableData()
  createAssignmentDialogVisible.value = true
}

function isAdmin() {
  return userStore.isSuperAdmin || groupMemberRole.value === 'admin'
}

function getStepProgressColor(percent: number): string {
  if (percent >= 100) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#909399'
}

onMounted(async () => {
  await fetchCurrentUser()
  await Promise.all([fetchBoard(), fetchAssignments(), fetchProgress()])
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px">
    <el-card v-if="!isLoading && board">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>{{ board.name }}</span>
          <div style="display: flex; gap: 8px">
            <el-button @click="router.push(`/groups/${board.group_id}`)">返回组织</el-button>
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
          <el-form-item label="可见性">
            <el-select v-model="editForm.visibility">
              <el-option label="公开" value="public" />
              <el-option label="组内可见" value="group_member" />
              <el-option label="看板内可见" value="board_user" />
            </el-select>
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
            <span>{{ board.description || '暂无描述' }}</span>
          </div>
          <div>
            <strong>可见性：</strong>
            <el-tag :type="getVisibilityType(board.visibility)" size="small">
              {{ getVisibilityLabel(board.visibility) }}
            </el-tag>
          </div>
          <div>
            <strong>所属组织：</strong>
            <span>{{ board.group_name || '-' }}</span>
          </div>
          <div>
            <strong>创建者：</strong>
            <span>{{ board.creator_username }}</span>
          </div>
          <div>
            <strong>创建时间：</strong>
            <span>{{ formatTime(board.created_at) }}</span>
          </div>
          <div v-if="isAdmin()">
            <el-button type="danger" size="small" @click="handleDelete">删除看板</el-button>
          </div>
        </div>
      </template>
    </el-card>
    <el-card v-else>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>看板详情</span>
        </div>
      </template>
      <el-skeleton :rows="4" animated />
    </el-card>

    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>分配管理</span>
          <el-button v-if="isAdmin()" type="primary" size="small" @click="openCreateAssignmentDialog">
            添加分配
          </el-button>
        </div>
      </template>
      <div v-loading="assignmentsLoading">
        <el-table v-loading="assignmentsLoading" :data="assignments" style="width: 100%">
          <el-table-column prop="username" label="用户" min-width="150" />
          <el-table-column prop="step_title" label="训练计划" min-width="200" />
          <el-table-column prop="created_at" label="分配时间" width="180">
            <template #default="{ row }">
              {{ formatTime(row.created_at) }}
            </template>
          </el-table-column>
          <el-table-column v-if="isAdmin()" label="操作" width="100" fixed="right">
            <template #default="{ row }">
              <el-button type="danger" size="small" @click="handleRemoveAssignment(row)">
                移除
              </el-button>
            </template>
          </el-table-column>
        </el-table>
        <el-empty v-if="!assignmentsLoading && !assignments.length" description="暂无分配" />
      </div>
    </el-card>

    <el-card>
      <template #header>
        <span>学习进度</span>
      </template>
      <div v-loading="progressLoading">
        <div v-if="!progressLoading && (!progress || !progress.users.length)" style="padding: 40px 0">
          <el-empty description="暂无学习进度数据" />
        </div>
        <div v-else style="display: flex; flex-direction: column; gap: 20px">
          <el-card v-for="userProgress in progress?.users" :key="userProgress.user_id" shadow="hover">
            <template #header>
              <div style="display: flex; align-items: center; justify-content: space-between">
                <span>
                  {{ userProgress.username }}
                  <el-tag v-if="userProgress.nickname" size="small" style="margin-left: 8px">
                    {{ userProgress.nickname }}
                  </el-tag>
                </span>
                <span style="color: #606266">
                  {{ userProgress.total_solved }}/{{ userProgress.total_problems }} 题
                </span>
              </div>
            </template>
            <div v-if="userProgress.steps.length === 0" style="padding: 20px; text-align: center; color: #909399">
              暂无训练计划进度
            </div>
            <div v-else style="display: flex; flex-direction: column; gap: 16px">
              <div v-for="stepProgress in userProgress.steps" :key="stepProgress.step_id">
                <div style="display: flex; align-items: center; justify-content: space-between; margin-bottom: 8px">
                  <span style="font-weight: 500">
                    {{ stepProgress.step_title }}
                    <el-tag :type="getStatusType(stepProgress.status)" size="small" style="margin-left: 8px">
                      {{ getStatusLabel(stepProgress.status) }}
                    </el-tag>
                  </span>
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
                    <span v-if="problem.ac_time">✓ </span>
                    <span v-else style="color: #909399">○ </span>
                    {{ problem.title }}
                    <span v-if="problem.ac_time" style="color: #909399"> ({{ formatTime(problem.ac_time) }})</span>
                  </div>
                </div>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>

  <el-dialog v-model="createAssignmentDialogVisible" title="添加分配" width="500px">
    <el-form label-position="top">
      <el-form-item label="训练计划" required>
        <el-select v-model="selectedStepId" placeholder="请选择训练计划" style="width: 100%">
          <el-option
            v-for="step in availableSteps"
            :key="step.id"
            :label="step.title"
            :value="step.id"
          />
        </el-select>
      </el-form-item>
      <el-form-item label="用户" required>
        <el-select v-model="selectedUserId" placeholder="请选择用户" style="width: 100%">
          <el-option
            v-for="user in availableUsers"
            :key="user.id"
            :label="user.username + (user.nickname ? ` (${user.nickname})` : '')"
            :value="user.id"
          />
        </el-select>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="createAssignmentDialogVisible = false">取消</el-button>
      <el-button type="primary" :loading="isCreatingAssignment" @click="handleCreateAssignments">
        添加
      </el-button>
    </template>
  </el-dialog>
</template>