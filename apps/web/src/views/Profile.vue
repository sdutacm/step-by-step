<script setup lang="ts">
import { ref, onMounted } from 'vue'
import {
  ElCard,
  ElDescriptions,
  ElDescriptionsItem,
  ElAvatar,
  ElMessage,
  ElButton,
  ElInput,
  ElDialog,
  ElForm,
  ElFormItem,
} from 'element-plus'
import { getCurrentUser, updateCurrentUser, type User } from '../api/auth'

const user = ref<User | null>(null)
const editDialogVisible = ref(false)
const isEditing = ref(false)

const editForm = ref({
  nickname: '',
  avatar_url: '',
})

async function refreshUser() {
  try {
    user.value = await getCurrentUser()
  } catch {
    ElMessage.error('获取用户信息失败')
  }
}

function openEditDialog() {
  editForm.value = {
    nickname: user.value?.nickname || '',
    avatar_url: user.value?.avatar_url || '',
  }
  editDialogVisible.value = true
}

async function handleUpdate() {
  try {
    await updateCurrentUser({
      nickname: editForm.value.nickname || undefined,
      avatar_url: editForm.value.avatar_url || undefined,
    })
    ElMessage.success('更新成功')
    editDialogVisible.value = false
    await refreshUser()
  } catch {
    ElMessage.error('更新失败')
  }
}

onMounted(async () => {
  await refreshUser()
})
</script>

<template>
  <div style="padding: 20px; max-width: 600px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; justify-content: space-between">
          <div style="display: flex; align-items: center; gap: 16px">
            <el-avatar v-if="user?.avatar_url" :size="64" :src="user.avatar_url" />
            <el-avatar v-else :size="64">
              {{ user?.username?.charAt(0).toUpperCase() }}
            </el-avatar>
            <div>
              <h2 style="margin: 0">{{ user?.nickname || user?.username }}</h2>
              <span style="color: #999">个人信息</span>
            </div>
          </div>
          <el-button @click="openEditDialog">编辑资料</el-button>
        </div>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
        <el-descriptions-item label="昵称">{{ user?.nickname || '未设置' }}</el-descriptions-item>
        <el-descriptions-item label="头像">
          <el-image
            v-if="user?.avatar_url"
            style="width: 80px; height: 80px"
            :src="user.avatar_url"
            fit="cover"
          />
          <span v-else>未设置</span>
        </el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>

  <el-dialog v-model="editDialogVisible" title="编辑资料" width="400px">
    <el-form label-position="top" :model="editForm">
      <el-form-item label="昵称">
        <el-input v-model="editForm.nickname" placeholder="请输入昵称" />
      </el-form-item>
      <el-form-item label="头像URL">
        <el-input v-model="editForm.avatar_url" placeholder="请输入头像URL" />
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button @click="editDialogVisible = false">取消</el-button>
      <el-button type="primary" @click="handleUpdate">保存</el-button>
    </template>
  </el-dialog>
</template>
