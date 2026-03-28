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

const solutions = ref<Solution[]>([])
const isLoading = ref(false)
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

const resultMap: Record<number, { label: string; type: string }> = {
  1: { label: 'Accepted', type: 'success' },
  2: { label: 'Wrong Answer', type: 'danger' },
  3: { label: 'Time Limit Exceeded', type: 'warning' },
  4: { label: 'Memory Limit Exceeded', type: 'warning' },
  5: { label: 'Runtime Error', type: 'danger' },
  6: { label: 'Output Limit Exceeded', type: 'warning' },
  7: { label: 'Compile Error', type: 'danger' },
  8: { label: 'Presentation Error', type: 'warning' },
  9: { label: 'System Error', type: 'danger' },
  999: { label: 'Unknown', type: 'info' },
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

function formatResult(result: number) {
  return resultMap[result] || resultMap[999]
}

function formatLanguage(language: number) {
  return languageMap[language] || 'Unknown'
}

function formatTime(time: string) {
  return new Date(time).toLocaleString('zh-CN')
}

function getProblemUrl(source: string, ojProblemId: string | null): string {
  if (!ojProblemId) return '#'
  switch (source.toLowerCase()) {
    case 'vj':
      return `https://vjudge.net/problem/${ojProblemId}`
    case 'sdut':
      return `https://oj.sdutacm.cn/onlinejudde3/problems/${ojProblemId}`
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

onMounted(() => {
  fetchSolutions()
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto">
    <el-card>
      <template #header>
        <span>提交记录</span>
      </template>
      <el-table
        v-loading="isLoading"
        :data="solutions"
        style="width: 100%"
        :default-sort="{ prop: 'submitted_at', order: 'descending' }"
      >
        <el-table-column prop="submitted_at" label="时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.submitted_at) }}
          </template>
        </el-table-column>
        <el-table-column prop="source" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="username" label="用户" width="120" />
        <el-table-column prop="problem_title" label="题目" min-width="200">
          <template #default="{ row }">
            <a
              :href="getProblemUrl(row.source, row.oj_problem_id)"
              target="_blank"
              rel="noopener noreferrer"
              style="color: #409eff; text-decoration: none"
            >
              {{ row.problem_title || `Problem #${row.oj_problem_id || row.problem_id}` }}
            </a>
          </template>
        </el-table-column>
        <el-table-column prop="result" label="结果" width="140">
          <template #default="{ row }">
            <el-tag :type="formatResult(row.result).type">
              {{ formatResult(row.result).label }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="language" label="语言" width="100">
          <template #default="{ row }">
            {{ formatLanguage(row.language) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!isLoading && !solutions.length" description="暂无提交记录" />
      <div style="margin-top: 20px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>