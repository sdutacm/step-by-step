<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import {
  ElCard,
  ElButton,
  ElTag,
  ElProgress,
  ElSkeleton,
  ElEmpty,
  ElMessage,
} from 'element-plus'
import {
  getBoard,
  getBoardProgress,
  type Board,
  type BoardProgressResponse,
  type BoardVisibility,
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

function getProgressColor(percent: number): string {
  if (percent >= 100) return '#67c23a'
  if (percent >= 50) return '#e6a23c'
  return '#909399'
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
  await fetchCurrentUser()
  await Promise.all([fetchBoard(), fetchProgress()])
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px">
    <el-card v-if="!isLoading && board">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>{{ board.name }}</span>
          <el-button @click="router.push(`/groups/${board.group_id}`)">返回组织</el-button>
        </div>
      </template>

      <div style="display: flex; flex-direction: column; gap: 16px">
        <div>
          <strong>描述：</strong>
          <span>{{ board.description || '暂无描述' }}</span>
        </div>
        <div>
          <strong>训练计划：</strong>
          <span>{{ board.step_title }}</span>
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
      </div>
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
                  {{ userProgress.solved_problems }}/{{ userProgress.total_problems }} 题
                </span>
              </div>
            </template>
            <div style="margin-bottom: 12px">
              <span style="font-weight: 500; margin-right: 12px">
                {{ progress.step_title }}
                <el-tag :type="getStatusType(userProgress.status)" size="small" style="margin-left: 8px">
                  {{ getStatusLabel(userProgress.status) }}
                </el-tag>
              </span>
              <span style="color: #606266">
                ({{ userProgress.progress_percent.toFixed(1) }}%)
              </span>
            </div>
            <el-progress
              :percentage="userProgress.progress_percent"
              :color="getProgressColor(userProgress.progress_percent)"
              :stroke-width="10"
            />
            <div v-if="userProgress.problems.length" style="margin-top: 12px; padding-left: 12px">
              <div
                v-for="problem in userProgress.problems"
                :key="problem.problem_id"
                style="font-size: 12px; color: #67c23a; margin: 4px 0"
              >
                <span v-if="problem.ac_time">✓ </span>
                <span v-else style="color: #909399">○ </span>
                {{ problem.title }}
                <span v-if="problem.ac_time" style="color: #909399"> ({{ formatTime(problem.ac_time) }})</span>
              </div>
            </div>
          </el-card>
        </div>
      </div>
    </el-card>
  </div>
</template>