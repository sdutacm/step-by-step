<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  ElCard,
  ElTable,
  ElTableColumn,
  ElTag,
  ElButton,
  ElMessage,
  ElSwitch,
  ElPagination,
} from 'element-plus'
import { getUsers, updateUserSuperAdmin, type AdminUser } from '../api/admin'

const users = ref<AdminUser[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const loading = ref(false)

async function refreshUsers() {
  loading.value = true
  try {
    const response = await getUsers(page.value, pageSize.value)
    users.value = response.items
    total.value = response.total
  } catch {
    ElMessage.error('获取用户列表失败')
  } finally {
    loading.value = false
  }
}

async function handleToggleSuperAdmin(user: AdminUser) {
  try {
    await updateUserSuperAdmin(user.id, !user.is_super_admin)
    ElMessage.success('更新成功')
    await refreshUsers()
  } catch (e: unknown) {
    ElMessage.error((e as Error).message || '更新失败')
    await refreshUsers()
  }
}

function handlePageChange(newPage: number) {
  page.value = newPage
  refreshUsers()
}

onMounted(() => {
  refreshUsers()
})
</script>

<template>
  <div style="padding: 20px; max-width: 1000px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <span>用户管理</span>
        </div>
      </template>
      <el-table :data="users" v-loading="loading" style="width: 100%">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="username" label="用户名" />
        <el-table-column prop="nickname" label="昵称">
          <template #default="{ row }">
            {{ row.nickname || '-' }}
          </template>
        </el-table-column>
        <el-table-column label="超级管理员" width="150">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_super_admin"
              @change="handleToggleSuperAdmin(row)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-tag v-if="row.is_super_admin" type="danger">超管</el-tag>
          </template>
        </el-table-column>
      </el-table>
      <div style="margin-top: 20px; display: flex; justify-content: flex-end">
        <el-pagination
          v-model:current-page="page"
          :page-size="pageSize"
          :total="total"
          layout="prev, pager, next"
          @current-change="handlePageChange"
        />
      </div>
    </el-card>
  </div>
</template>
