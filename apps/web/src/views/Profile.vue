<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { ElCard, ElDescriptions, ElDescriptionsItem, ElAvatar, ElMessage } from 'element-plus'
import { getCurrentUser, type User } from '../api/auth'

const user = ref<User | null>(null)

onMounted(async () => {
  try {
    user.value = await getCurrentUser()
  } catch {
    ElMessage.error('获取用户信息失败')
  }
})
</script>

<template>
  <div style="padding: 20px; max-width: 600px; margin: 0 auto">
    <el-card>
      <template #header>
        <div style="display: flex; align-items: center; gap: 16px">
          <el-avatar :size="64">{{ user?.username?.charAt(0).toUpperCase() }}</el-avatar>
          <div>
            <h2 style="margin: 0">{{ user?.username }}</h2>
            <span style="color: #999">个人信息</span>
          </div>
        </div>
      </template>
      <el-descriptions :column="1" border>
        <el-descriptions-item label="用户ID">{{ user?.id }}</el-descriptions-item>
        <el-descriptions-item label="用户名">{{ user?.username }}</el-descriptions-item>
      </el-descriptions>
    </el-card>
  </div>
</template>
