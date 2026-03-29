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
        result: problem.ac_time !== null ? 1 : null,
      })
    }
    map.set(user.user_id, userMap)
  }
  return map
})

const tableHeight = ref(window.innerHeight - 220)

function updateTableHeight() {
  tableHeight.value = window.innerHeight - 220
}

function getCellData(problemId: number, userId: number): CellData | null {
  const userMap = cellMap.value.get(userId)
  if (!userMap) return null
  return userMap.get(problemId) || null
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

interface SpanMethodProps {
  row: ProblemProgress
  column: { property: string }
  rowIndex: number
  columnIndex: number
}

const specialtyMergeMap = computed(() => {
  const map: number[] = []
  if (!problems.value.length) return map

  for (let i = 0; i < problems.value.length; i++) {
    if (i === 0) {
      map.push(1)
    } else {
      const current = problems.value[i]
      const prev = problems.value[i - 1]
      if (current.specialty === prev.specialty && current.specialty !== null) {
        map.push(0)
      } else {
        map.push(1)
      }
    }
  }
  return map
})

const topicMergeMap = computed(() => {
  const map: number[] = []
  if (!problems.value.length) return map

  for (let i = 0; i < problems.value.length; i++) {
    if (i === 0) {
      map.push(1)
    } else {
      const current = problems.value[i]
      const prev = problems.value[i - 1]
      if (current.topic === prev.topic && current.topic !== null) {
        map.push(0)
      } else {
        map.push(1)
      }
    }
  }
  return map
})

function spanMethod({ row, column, rowIndex, columnIndex }: SpanMethodProps) {
  if (column.property === 'specialty') {
    const rowspan = specialtyMergeMap.value[rowIndex]
    if (rowspan === 0) {
      return { rowspan: 0, colspan: 1 }
    }
    return { rowspan: rowspan, colspan: 1 }
  }
  if (column.property === 'topic') {
    const rowspan = topicMergeMap.value[rowIndex]
    if (rowspan === 0) {
      return { rowspan: 0, colspan: 1 }
    }
    return { rowspan: rowspan, colspan: 1 }
  }
  return { rowspan: 1, colspan: 1 }
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
            :span-method="spanMethod"
            :scrollbar-always-on="true"
            :height="tableHeight"
            class="board-table"
          >
            <el-table-column prop="specialty" label="专项" min-width="120" align="center" fixed />
            <el-table-column prop="topic" label="专题" min-width="120" align="center" fixed />
            <el-table-column prop="title" label="题目" min-width="200" fixed />
            <el-table-column
              v-for="user in users"
              :key="user.user_id"
              :label="user.nickname ? `${user.username} (${user.nickname})` : user.username"
              min-width="150"
              align="center"
            >
              <template #default="{ row }">
                <span
                  v-if="getCellData(row.problem_id, user.user_id)?.solved"
                  style="color: #67c23a; cursor: pointer"
                  @click="openCellDialog(row.problem_id, user.user_id)"
                >
                  ✓ {{ formatTime(getCellData(row.problem_id, user.user_id)?.ac_time || '') }}
                </span>
                <span
                  v-else
                  style="color: #c0c4cc; cursor: pointer"
                  @click="openCellDialog(row.problem_id, user.user_id)"
                >
                  ✗
                </span>
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

.board-table :deep(.el-table__body) {
  width: auto !important;
}
</style>