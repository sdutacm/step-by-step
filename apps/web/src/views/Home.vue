<script setup lang="ts">
import { ref, onMounted, computed } from 'vue'
import {
  ElCard,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElTag,
  ElEmpty,
  ElMessage,
} from 'element-plus'
import { getSolutions, type Solution, type PaginatedSolutions } from '../api/auth'
import { useUserStore } from '../stores/user'
import { getToken } from '../api/auth'

const solutions = ref<Solution[]>([])
const isLoading = ref(false)
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

const userStore = useUserStore()

const resultMap: Record<number, { label: string; type: 'success' | 'danger' | 'warning' | 'info' }> = {
  1: { label: 'Accepted', type: 'success' },
  2: { label: 'Wrong Answer', type: 'danger' },
  3: { label: 'Time Limit Exceeded', type: 'warning' },
  4: { label: 'Memory Limit Exceeded', type: 'warning' },
  5: { label: 'Runtime Error', type: 'danger' },
  6: { label: 'Output Limit Exceeded', type: 'warning' },
  7: { label: 'Compile Error', type: 'danger' },
  8: { label: 'Presentation Error', type: 'warning' },
  9: { label: 'System Error', type: 'danger' },
  999: { label: 'Unknown', type: 'danger' },
}

const languageMap: Record<number, string> = {
  1: 'C',
  2: 'C++',
  3: 'Python',
  4: 'Java',
  5: 'Go',
  6: 'Rust',
  7: 'JavaScript',
  8: 'TypeScript',
  9: 'C#',
  10: 'Pascal',
  11: 'Fortran',
  999: 'Unknown',
}

function formatResult(result: number, source?: string) {
  if (result === 999 && source?.toLowerCase() === 'vj') {
    return { label: 'Rejected', type: 'danger' as const }
  }
  return resultMap[result] || resultMap[999]
}

function formatLanguage(language: number) {
  return languageMap[language] || 'Unknown'
}

function formatTime(time: string) {
  const d = new Date(time)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function getProblemUrl(source: string, ojProblemId: string | null): string {
  if (!ojProblemId) return '#'
  switch (source.toLowerCase()) {
    case 'vj':
      return `https://vjudge.net/problem/${ojProblemId}`
    case 'sdut':
      return `https://oj.sdutacm.cn/onlinejudge3/problems/${ojProblemId}`
    default:
      return '#'
  }
}

function getUserUrl(source: string, username: string): string {
  switch (source.toLowerCase()) {
    case 'vj':
      return `https://vjudge.net/user/${username}`
    case 'sdut':
      return `https://oj.sdutacm.cn/onlinejudge3/users/${username}`
    default:
      return '#'
  }
}

async function fetchSolutions() {
  isLoading.value = true
  try {
    const data: PaginatedSolutions = await getSolutions({
      page: pagination.value.page,
      page_size: pagination.value.page_size,
    })
    solutions.value = data.items
    pagination.value.total = data.total
  } catch {
    ElMessage.error('获取提交记录失败')
  } finally {
    isLoading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.value.page = page
  fetchSolutions()
}

function handleSizeChange(size: number) {
  pagination.value.page_size = size
  pagination.value.page = 1
  fetchSolutions()
}

onMounted(async () => {
  if (getToken()) {
    await userStore.fetchUser()
  }
  fetchSolutions()
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto">
    <el-card>
      <template #header>
        <span>提交记录</span>
      </template>
      <el-table v-loading="isLoading" :data="solutions" style="width: 100%"
        :default-sort="{ prop: 'submitted_at', order: 'descending' }">
        <el-table-column prop="submitted_at" label="时间" width="200">
          <template #default="{ row }">
            {{ formatTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="用户" width="160" show-overflow-tooltip>
          <template #default="{ row }">
            <a :href="getUserUrl(row.source, row.username)" target="_blank" rel="noopener noreferrer"
              style="color: #409eff; text-decoration: none">
              {{ row.nickname || row.username }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="problem_title" label="题目" min-width="200" show-overflow-tooltip>
          <template #default="{ row }">
            <a :href="getProblemUrl(row.source, row.oj_problem_id)" target="_blank" rel="noopener noreferrer"
              style="color: #409eff; text-decoration: none">
              {{ row.problem_title || `Problem #${row.oj_problem_id || row.problem_id}` }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" width="140" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag size="small" :type="formatResult(row.result, row.source).type">
              {{ formatResult(row.result, row.source).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100" show-overflow-tooltip>
          <template #default="{ row }">
            <el-tag size="small">{{ formatLanguage(row.language) }}</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!isLoading && !solutions.length" description="暂无提交记录" />
      <div style="margin-top: 20px; display: flex; justify-content: flex-end">
        <el-pagination v-model:current-page="pagination.page" v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]" :total="pagination.total" layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange" @size-change="handleSizeChange" />
      </div>
    </el-card>
  </div>
</template>