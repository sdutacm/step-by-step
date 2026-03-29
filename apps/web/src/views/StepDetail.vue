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
  ElPagination,
} from 'element-plus'
import {
  getStep,
  updateStep,
  addProblemsToStep,
  removeProblemFromStep,
  getProblems,
  type Step,
  type StepProblemItem,
  type ProblemSimple,
} from '../api/step'
import { getToken } from '../api/auth'

const router = useRouter()
const route = useRoute()

const step = ref<Step | null>(null)
const isLoading = ref(false)
const isEditing = ref(false)
const isAddingProblems = ref(false)
const isSubmitting = ref(false)
const problemsLoading = ref(false)
const availableProblems = ref<ProblemSimple[]>([])
const selectedProblems = ref<StepProblemItem[]>([])
const problemsPagination = ref({ page: 1, page_size: 20, total: 0 })
const problemsSearch = ref({ title: '', source: '' })

const stepId = computed(() => Number(route.params.id))

const editForm = ref({
  title: '',
  description: '',
})

function isLoggedIn() {
  return !!getToken()
}

function formatTime(time: string) {
  const d = new Date(time)
  const pad = (n: number) => n.toString().padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())} ${pad(d.getHours())}:${pad(d.getMinutes())}:${pad(d.getSeconds())}`
}

function getProblemUrl(source: string, problemId: string): string {
  switch (source.toLowerCase()) {
    case 'vj':
      return `https://vjudge.net/problem/${problemId}`
    case 'sdut':
      return `https://oj.sdutacm.cn/onlinejudde3/problems/${problemId}`
    default:
      return '#'
  }
}

async function fetchStep() {
  isLoading.value = true
  try {
    step.value = await getStep(stepId.value)
    editForm.value.title = step.value.title
    editForm.value.description = step.value.description || ''
  } catch {
    ElMessage.error('获取训练计划详情失败')
    router.push('/steps')
  } finally {
    isLoading.value = false
  }
}

async function fetchAvailableProblems() {
  problemsLoading.value = true
  try {
    const data = await getProblems(
      problemsPagination.value.page,
      problemsPagination.value.page_size,
      problemsSearch.value.title || undefined,
      problemsSearch.value.source || undefined
    )
    availableProblems.value = data.items.filter(
      (p) => !step.value?.problems.some((sp) => sp.id === p.id)
    )
    problemsPagination.value.total = data.total
  } catch {
    ElMessage.error('获取题目列表失败')
  } finally {
    problemsLoading.value = false
  }
}

async function handleProblemsSearch() {
  problemsPagination.value.page = 1
  await fetchAvailableProblems()
}

async function handleProblemsPageChange(page: number) {
  problemsPagination.value.page = page
  await fetchAvailableProblems()
}

async function handleUpdate() {
  if (!editForm.value.title.trim()) {
    ElMessage.error('请输入标题')
    return
  }
  isSubmitting.value = true
  try {
    await updateStep(stepId.value, {
      title: editForm.value.title,
      description: editForm.value.description || undefined,
    })
    ElMessage.success('更新成功')
    isEditing.value = false
    await fetchStep()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
  } finally {
    isSubmitting.value = false
  }
}

async function openAddProblemsDialog() {
  problemsSearch.value = { title: '', source: '' }
  problemsPagination.value = { page: 1, page_size: 20, total: 0 }
  selectedProblems.value = []
  await fetchAvailableProblems()
  isAddingProblems.value = true
}

async function handleAddProblems() {
  if (selectedProblems.value.length === 0) {
    ElMessage.error('请选择至少一道题目')
    return
  }
  isSubmitting.value = true
  try {
    await addProblemsToStep(stepId.value, { problems: selectedProblems.value })
    ElMessage.success('添加成功')
    isAddingProblems.value = false
    await fetchStep()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '添加失败')
  } finally {
    isSubmitting.value = false
  }
}

async function handleRemoveProblem(problemId: number, title: string) {
  try {
    await ElMessageBox.confirm(
      `确定要从训练计划中移除「${title}」吗？`,
      '移除确认',
      {
        confirmButtonText: '确定',
        cancelButtonText: '取消',
        type: 'warning',
      }
    )
    await removeProblemFromStep(stepId.value, problemId)
    ElMessage.success('移除成功')
    await fetchStep()
  } catch (e: unknown) {
    if ((e as Error).message !== 'cancel') {
      ElMessage.error((e as Error).message || '移除失败')
    }
  }
}

onMounted(() => {
  fetchStep()
})
</script>

<template>
  <div style="padding: 20px; max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px">
    <el-card v-loading="isLoading">
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>{{ step?.title || '训练计划详情' }}</span>
          <div style="display: flex; gap: 8px">
            <el-button @click="router.push('/steps')">返回列表</el-button>
            <el-button v-if="!isEditing" type="primary" @click="isEditing = true">
              编辑信息
            </el-button>
          </div>
        </div>
      </template>

      <template v-if="isEditing">
        <el-form label-position="top" :model="editForm">
          <el-form-item label="标题" required>
            <el-input v-model="editForm.title" placeholder="请输入标题" maxlength="200" show-word-limit />
          </el-form-item>
          <el-form-item label="描述">
            <el-input
              v-model="editForm.description"
              type="textarea"
              placeholder="请输入描述"
              :rows="3"
              maxlength="1000"
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
            <span>{{ step?.description || '暂无描述' }}</span>
          </div>
          <div>
            <strong>创建者：</strong>
            <span>{{ step?.creator_username }}</span>
          </div>
          <div>
            <strong>创建时间：</strong>
            <span>{{ step?.created_at ? formatTime(step.created_at) : '-' }}</span>
          </div>
          <div>
            <strong>更新时间：</strong>
            <span>{{ step?.updated_at ? formatTime(step.updated_at) : '-' }}</span>
          </div>
        </div>
      </template>
    </el-card>

    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>题目列表 ({{ step?.problem_count || 0 }})</span>
          <el-button type="primary" @click="openAddProblemsDialog">添加题目</el-button>
        </div>
      </template>
      <el-table v-if="step?.problems.length" :data="step.problems" style="width: 100%">
        <el-table-column prop="order" label="顺序" width="80" align="center" />
        <el-table-column prop="problem_id" label="题目ID" width="120" />
        <el-table-column prop="source" label="平台" width="100">
          <template #default="{ row }">
            <el-tag>{{ row.source.toUpperCase() }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" min-width="200">
          <template #default="{ row }">
            <a
              :href="getProblemUrl(row.source, row.problem_id)"
              target="_blank"
              rel="noopener noreferrer"
              style="color: #409eff; text-decoration: none"
            >
              {{ row.title }}
            </a>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100" fixed="right">
          <template #default="{ row }">
            <el-button type="danger" size="small" @click="handleRemoveProblem(row.id, row.title)">
              移除
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <el-empty v-else description="暂无题目" />
    </el-card>
  </div>

  <el-dialog v-model="isAddingProblems" title="添加题目" width="800px">
    <div style="margin-bottom: 16px; display: flex; gap: 12px">
      <el-input
        v-model="problemsSearch.title"
        placeholder="搜索题目标题"
        style="width: 300px"
        clearable
        @keyup.enter="handleProblemsSearch"
      />
      <el-select
        v-model="problemsSearch.source"
        placeholder="选择平台"
        style="width: 150px"
        clearable
        @change="handleProblemsSearch"
      >
        <el-option label="VJ" value="vj" />
        <el-option label="SDUT" value="sdut" />
      </el-select>
      <el-button type="primary" @click="handleProblemsSearch">搜索</el-button>
    </div>
    <el-table
      v-loading="problemsLoading"
      :data="availableProblems"
      max-height="400"
      @selection-change="(rows: ProblemSimple[]) => selectedProblems = rows.map(p => ({ problem_id: p.id, order: 0 }))"
    >
      <el-table-column type="selection" width="55" />
      <el-table-column prop="problem_id" label="题目ID" width="100" />
      <el-table-column prop="source" label="平台" width="100">
        <template #default="{ row }">
          <el-tag size="small">{{ row.source.toUpperCase() }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="title" label="标题" min-width="200" />
    </el-table>
    <div style="margin-top: 16px; display: flex; justify-content: flex-end">
      <el-pagination
        v-model:current-page="problemsPagination.page"
        :page-size="problemsPagination.page_size"
        :total="problemsPagination.total"
        layout="prev, pager, next, jumper"
        @current-change="handleProblemsPageChange"
      />
    </div>
    <template #footer>
      <el-button @click="isAddingProblems = false">取消</el-button>
      <el-button type="primary" :loading="isSubmitting" @click="handleAddProblems">
        添加 ({{ selectedProblems.length }})
      </el-button>
    </template>
  </el-dialog>
</template>