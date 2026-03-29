<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import {
  ElCard,
  ElTable,
  ElTableColumn,
  ElPagination,
  ElButton,
  ElEmpty,
  ElMessage,
  ElMessageBox,
  ElTag,
} from 'element-plus'
import { getSteps, deleteStep, type StepListItem, type StepListResponse } from '../api/step'
import { getToken, getCurrentUser } from '../api/auth'

const router = useRouter()

const steps = ref<StepListItem[]>([])
const isLoading = ref(false)
const currentUserId = ref<number | null>(null)
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

function isLoggedIn() {
  return !!getToken()
}

async function fetchSteps() {
  isLoading.value = true
  try {
    const data: StepListResponse = await getSteps(pagination.value.page, pagination.value.page_size)
    steps.value = data.items
    pagination.value.total = data.total
  } catch {
    ElMessage.error('获取训练计划列表失败')
  } finally {
    isLoading.value = false
  }
}

async function fetchCurrentUser() {
  try {
    const user = await getCurrentUser()
    currentUserId.value = user.id
  } catch {
    currentUserId.value = null
  }
}

function handlePageChange(page: number) {
  pagination.value.page = page
  fetchSteps()
}

function handleSizeChange(size: number) {
  pagination.value.page_size = size
  pagination.value.page = 1
  fetchSteps()
}

function goToStepDetail(id: number) {
  router.push(`/steps/${id}`)
}

function goToCreate() {
  router.push('/steps/create')
}

async function handleDelete(id: number, title: string) {
  try {
    await ElMessageBox.confirm(
      `确定要删除训练计划「${title}」吗？`,
      '删除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await deleteStep(id)
    ElMessage.success('删除成功')
    await fetchSteps()
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '删除失败')
    }
  }
}

onMounted(async () => {
  await Promise.all([fetchSteps(), fetchCurrentUser()])
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>训练计划</span>
          <el-button v-if="isLoggedIn()" type="primary" @click="goToCreate">
            创建训练计划
          </el-button>
        </div>
      </template>
      <el-table
        v-loading="isLoading"
        :data="steps"
        style="width: 100%"
        :default-sort="{ prop: 'updated_at', order: 'descending' }"
        @row-click="(row: StepListItem) => goToStepDetail(row.id)"
      >
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <span style="color: #409eff; cursor: pointer">{{ row.title }}</span>
          </template>
        </el-table-column>
        <el-table-column prop="description" label="描述" min-width="200">
          <template #default="{ row }">
            {{ row.description || '-' }}
          </template>
        </el-table-column>
        <el-table-column prop="group_name" label="组织" width="120">
          <template #default="{ row }">
            <el-tag v-if="row.group_name" type="success" size="small">{{ row.group_name }}</el-tag>
            <span v-else style="color: #909399">-</span>
          </template>
        </el-table-column>
        <el-table-column prop="creator_username" label="创建者" width="120" />
        <el-table-column prop="problem_count" label="题目数" width="100" align="center">
          <template #default="{ row }">
            {{ row.problem_count }}
          </template>
        </el-table-column>
        <el-table-column prop="updated_at" label="更新时间" width="180" sortable>
          <template #default="{ row }">
            {{ formatTime(row.updated_at) }}
          </template>
        </el-table-column>
        <el-table-column v-if="isLoggedIn() && currentUserId" label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button
              v-if="row.creator_id === currentUserId"
              type="danger"
              size="small"
              @click.stop="handleDelete(row.id, row.title)"
            >
              删除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-if="!isLoading && !steps.length" description="暂无训练计划" />
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