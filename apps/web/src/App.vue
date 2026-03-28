<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { ElButton, ElDialog, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import { login, register, getCurrentUser, logout, type User } from './api/auth'

const user = ref<User | null>(null)
const loginDialogVisible = ref(false)
const registerDialogVisible = ref(false)

const loginForm = ref({
  username: '',
  password: '',
})

const registerForm = ref({
  username: '',
  password: '',
})

const isLoggedIn = computed(() => !!user.value)

async function handleLogin() {
  try {
    await login(loginForm.value)
    user.value = await getCurrentUser()
    loginDialogVisible.value = false
    loginForm.value = { username: '', password: '' }
    ElMessage.success('登录成功')
  } catch (error: any) {
    ElMessage.error(error.message || '登录失败')
  }
}

async function handleRegister() {
  try {
    await register(registerForm.value)
    ElMessage.success('注册成功，请登录')
    registerDialogVisible.value = false
    registerForm.value = { username: '', password: '' }
    loginDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.message || '注册失败')
  }
}

async function handleLogout() {
  await logout()
  user.value = null
  ElMessage.success('已退出登录')
}

onMounted(async () => {
  try {
    user.value = await getCurrentUser()
  } catch {
    user.value = null
  }
})
</script>

<template>
  <el-menu mode="horizontal" :router="false">
    <el-menu-item index="/">Step By Step</el-menu-item>
    <div style="flex: 1"></div>
    <template v-if="isLoggedIn">
      <el-menu-item disabled style="cursor: default">
        {{ user?.username }}
      </el-menu-item>
      <el-menu-item>
        <el-button @click="handleLogout">退出登录</el-button>
      </el-menu-item>
    </template>
    <template v-else>
      <el-menu-item>
        <el-button @click="loginDialogVisible = true">登录</el-button>
      </el-menu-item>
      <el-menu-item>
        <el-button @click="registerDialogVisible = true">注册</el-button>
      </el-menu-item>
    </template>
  </el-menu>

  <div style="padding: 20px">
    <h1>欢迎</h1>
  </div>

  <el-dialog v-model="loginDialogVisible" title="登录" width="400px">
    <el-form :model="loginForm" @submit.prevent="handleLogin">
      <el-form-item label="用户名">
        <el-input v-model="loginForm.username" placeholder="用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="密码"
          @keyup.enter="handleLogin"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" style="width: 100%">
          登录
        </el-button>
      </el-form-item>
    </el-form>
  </el-dialog>

  <el-dialog v-model="registerDialogVisible" title="注册" width="400px">
    <el-form :model="registerForm" @submit.prevent="handleRegister">
      <el-form-item label="用户名">
        <el-input v-model="registerForm.username" placeholder="用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="registerForm.password"
          type="password"
          placeholder="密码"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" style="width: 100%">
          注册
        </el-button>
      </el-form-item>
    </el-form>
  </el-dialog>
</template>

<style scoped>
.el-menu {
  display: flex;
  align-items: center;
}
</style>
