<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ElCard,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElEmpty,
  ElMessage,
  ElTag,
} from 'element-plus'
import { getPublicBoards, type PublicBoardListItem, type PublicBoardListResponse } from '../api/board'

const router = useRouter()

const boards = ref<PublicBoardListItem[]>([])
const isLoading = ref(false)
const pagination = ref({
  page: 1,
  page_size: 20,
  total: 0,
})

function formatTime(time: string) {
  const d = new Date(time)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function getVisibilityLabel(visibility: string): string {
  if (visibility === 'public') return '公开'
  if (visibility === 'group_member') return '组内可见'
  return '看板内可见'
}

function getVisibilityType(visibility: string): string {
  if (visibility === 'public') return 'success'
  if (visibility === 'group_member') return 'warning'
  return 'info'
}

async function fetchBoards() {
  isLoading.value = true
  try {
    const data: PublicBoardListResponse = await getPublicBoards(
      pagination.value.page,
      pagination.value.page_size
    )
    boards.value = data.items
    pagination.value.total = data.total
  } catch {
    ElMessage.error('获取公开看板列表失败')
  } finally {
    isLoading.value = false
  }
}

function handlePageChange(page: number) {
  pagination.value.page = page
  fetchBoards()
}

function handleSizeChange(size: number) {
  pagination.value.page_size = size
  pagination.value.page = 1
  fetchBoards()
}

function goToBoardDetail(id: number) {
  router.push(`/boards/${id}`)
}

onMounted(() => {
  fetchBoards()
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>公开看板</span>
        </div>
      </template>
      <el-table
        v-loading="isLoading"
        :data="boards"
        style="width: 100%"
        @row-click="(row: PublicBoardListItem) => goToBoardDetail(row.id)"
      >
        <el-table-column prop="name" label="名称" min-width="150">
          <template #default="{ row }">
            <span style="color: #409eff; cursor: pointer">{{ row.name }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="group_name" label="所属组织" width="150">
          <template #default="{ row }">
            {{ row.group_name || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="step_title" label="训练计划" width="150">
          <template #default="{ row }">
            {{ row.step_title || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="creator_username" label="创建者" width="120" />
        <el-table-column prop="created_at" label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatTime(row.created_at) }}
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!isLoading && !boards.length" description="暂无公开看板" />
      <div style="margin-top: 20px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="pagination.page"
          v-model:page-size="pagination.page_size"
          :page-sizes="[10, 20, 50, 100]"
          :total="pagination.total"
          layout="total, sizes, prev, pager, next, jumper"
          @current-change="handlePageChange"
          @size-change="handleSizeChange"
        />
      </div>
    </el-card>
  </div>
</template>
