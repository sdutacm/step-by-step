<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ElCard,
  ElButton,
  ElTag,
  ElSkeleton,
  ElEmpty,
  ElMessage,
  ElLink,
  ElTable,
  ElTableColumn,
  ElDialog,
} from 'element-plus'
import {
  getBoard,
  getBoardProgress,
  type Board,
  type BoardProgressResponse,
  type BoardVisibility,
  type ProblemProgress,
} from '../api/board'
import { getGroup, type Group } from '../api/group'
import { getCurrentUser } from '../api/auth'
import { useUserStore } from '../stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()

const board = ref<Board | null>(null)
const group = ref<Group | null>(null)
const isLoading = ref(false)

const progress = ref<BoardProgressResponse | null>(null)
const progressLoading = ref(false)

const currentUser = ref<{ id: number } | null>(null)

const boardId = computed(() => Number(route.params.id))

interface TableUser {
  user_id: number
  username: string
  nickname: string | null
}

interface CellData {
  solved: boolean
  ac_time: string | null
  failed_time: string | null
  result: number | null
}

const dialogVisible = ref(false)
const dialogData = ref<{
  problem: ProblemProgress | null
  user: TableUser | null
  cell: CellData | null
}>({
  problem: null,
  user: null,
  cell: null,
})

const users = computed<TableUser[]>(() => {
  if (!progress.value) return []
  return progress.value.users.map(u => ({
    user_id: u.user_id,
    username: u.username,
    nickname: u.nickname,
  }))
})

const problems = computed<ProblemProgress[]>(() => {
  if (!progress.value || progress.value.users.length === 0) return []
  return [...progress.value.users[0].problems].sort((a, b) => a.order - b.order)
})

const cellMap = computed(() => {
  const map = new Map<number, Map<number, CellData>>()
  if (!progress.value) return map

  for (const user of progress.value.users) {
    const userMap = new Map<number, CellData>()
    for (const problem of user.problems) {
      userMap.set(problem.problem_id, {
        solved: problem.ac_time !== null,
        ac_time: problem.ac_time,
        failed_time: problem.failed_time,
        result: problem.result,
      })
    }
    map.set(user.user_id, userMap)
  }
  return map
})

function isWithin7Days(dateStr: string | null): boolean {
  if (!dateStr) return false
  const date = new Date(dateStr)
  const now = new Date()
  const diffTime = now.getTime() - date.getTime()
  const diffDays = diffTime / (1000 * 60 * 60 * 24)
  return diffDays <= 7
}

const tableHeight = ref(window.innerHeight - 220)

function updateTableHeight() {
  tableHeight.value = window.innerHeight - 220
}

function getCellData(problemId: number, userId: number): CellData | null {
  const userMap = cellMap.value.get(userId)
  if (!userMap) return null
  return userMap.get(problemId) || null
}

function getCellStyle(problemId: number, userId: number): string {
  const cell = getCellData(problemId, userId)
  if (!cell || cell.result === null) return ''
  const timeToCheck = cell.result === 1 ? cell.ac_time : cell.failed_time
  const within7Days = isWithin7Days(timeToCheck)
  if (cell.result === 1) {
    return within7Days
      ? 'background-color: #67c23a; color: #fff; text-align: center; line-height: inherit;'
      : 'background-color: #e1f3d8; color: #67c23a; text-align: center; line-height: inherit;'
  } else {
    return within7Days
      ? 'background-color: #f56c6c; color: #fff; text-align: center; line-height: inherit;'
      : 'background-color: #fde2e2; color: #f56c6c; text-align: center; line-height: inherit;'
  }
}

function getCellTimeText(problemId: number, userId: number): string {
  const cell = getCellData(problemId, userId)
  if (!cell || cell.result === null) return ''
  const time = cell.result === 1 ? cell.ac_time : cell.failed_time
  return formatTime(time || '')
}

function openCellDialog(problemId: number, userId: number) {
  const problem = problems.value.find(p => p.problem_id === problemId)
  const user = users.value.find(u => u.user_id === userId)
  const cell = getCellData(problemId, userId)

  dialogData.value = {
    problem: problem || null,
    user: user || null,
    cell: cell || null,
  }
  dialogVisible.value = true
}

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

function getResultLabel(result: number | null): string {
  if (result === null) return '未提交'
  const results: Record<number, string> = {
    1: 'Accepted',
    2: 'Wrong Answer',
    3: 'Time Limit Exceeded',
    4: 'Memory Limit Exceeded',
    5: 'Runtime Error',
    6: 'Output Limit Exceeded',
    7: 'Compile Error',
    8: 'Presentation Error',
    9: 'System Error',
    999: 'Unknown',
  }
  return results[result] || 'Unknown'
}

function getResultType(result: number | null): string {
  if (result === 1) return 'success'
  if (result === null) return 'info'
  return 'danger'
}

function getProblemUrl(source: string, problemId: string): string {
  if (source === 'vj') return `https://vjudge.net/problem/${problemId}`
  if (source === 'sdut') return `https://oj.sdutacm.cn/onlinejudge3/problems/${problemId}`
  return '#'
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
    if (board.value.group_id) {
      group.value = await getGroup(board.value.group_id)
    }
  } catch {
    ElMessage.error('获取看板详情失败')
    router.push('/groups')
  } finally {
    isLoading.value = false
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

onMounted(async () => {
  window.addEventListener('resize', updateTableHeight)
  await fetchCurrentUser()
  await Promise.all([fetchBoard(), fetchProgress()])
})

onUnmounted(() => {
  window.removeEventListener('resize', updateTableHeight)
})
</script>

<template>
  <div style="padding: 20px; max-width: 1400px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>学习进度</span>
          <span v-if="progress" style="color: #606266; font-size: 14px">
            {{ progress.step_title }} - {{ users.length }} 位用户，{{ problems.length }} 道题目
          </span>
        </div>
      </template>
      <div v-loading="progressLoading">
        <div v-if="!progressLoading && (!progress || !progress.users.length)" style="padding: 40px 0">
          <el-empty description="暂无学习进度数据" />
        </div>
        <div v-else class="table-wrapper">
          <el-table
            :data="problems"
            border
            :scrollbar-always-on="true"
            :height="tableHeight"
            class="board-table"
          >
            <el-table-column prop="specialty" label="专项" width="120" align="center" fixed show-overflow-tooltip />
            <el-table-column prop="topic" label="专题" width="120" align="center" fixed show-overflow-tooltip />
            <el-table-column prop="title" label="题目" width="180" fixed show-overflow-tooltip>
              <template #default="{ row }">
                <el-link type="primary" :href="getProblemUrl(row.source, row.oj_problem_id)" target="_blank">{{ row.title }}</el-link>
              </template>
            </el-table-column>
            <el-table-column
              v-for="user in users"
              :key="user.user_id"
              :label="user.nickname ? `${user.username} (${user.nickname})` : user.username"
              width="220"
              align="center"
            >
              <template #default="{ row }">
                <div
                  v-if="getCellData(row.problem_id, user.user_id)?.result !== null"
                  :style="getCellStyle(row.problem_id, user.user_id)"
                  class="cell-bg"
                  @click="openCellDialog(row.problem_id, user.user_id)"
                >
                  {{ getCellTimeText(row.problem_id, user.user_id) }}
                </div>
              </template>
            </el-table-column>
          </el-table>
        </div>
      </div>
    </el-card>

    <el-dialog
      v-model="dialogVisible"
      :title="dialogData.problem?.title || '题目详情'"
      width="500px"
    >
      <div v-if="dialogData.problem" style="display: flex; flex-direction: column; gap: 16px">
        <div>
          <strong>OJ题目ID：</strong>
          <span>{{ dialogData.problem.oj_problem_id }}</span>
        </div>
        <div>
          <strong>提交时间：</strong>
          <span v-if="dialogData.cell?.ac_time">{{ formatTime(dialogData.cell.ac_time) }}</span>
          <span v-else>-</span>
        </div>
        <div>
          <strong>提交结果：</strong>
          <el-tag
            :type="getResultType(dialogData.cell?.result ?? null)"
            size="small"
          >
            {{ getResultLabel(dialogData.cell?.result ?? null) }}
          </el-tag>
        </div>
        <div v-if="dialogData.problem.specialty">
          <strong>专项：</strong>
          <span>{{ dialogData.problem.specialty }}</span>
        </div>
        <div v-if="dialogData.problem.topic">
          <strong>主题：</strong>
          <span>{{ dialogData.problem.topic }}</span>
        </div>
      </div>
      <template #footer>
        <div style="display: flex; justify-content: space-between">
          <a
            v-if="dialogData.problem"
            :href="getProblemUrl(dialogData.problem.source || '', dialogData.problem.oj_problem_id)"
            target="_blank"
            rel="noopener noreferrer"
          >
            <el-button type="primary">在 OJ 查看</el-button>
          </a>
          <span v-else></span>
          <el-button @click="dialogVisible = false">关闭</el-button>
        </div>
      </template>
    </el-dialog>
  </div>
</template>

<style scoped>
.table-wrapper {
  overflow-x: auto;
  max-width: 100%;
}

.board-table :deep(.el-table__body-wrapper) {
  overflow-x: auto;
}

.board-table :deep(.el-table__body .el-table-cell) {
  position: relative;
}

.cell-bg {
  position: absolute;
  top: 0;
  left: 0;
  right: 0;
  bottom: 0;
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>