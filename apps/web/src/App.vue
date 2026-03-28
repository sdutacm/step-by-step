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
  email: '',
  password: '',
})

const isLoggedIn = computed(() => !!user.value)

async function handleLogin() {
  try {
    await login(loginForm.value)
    user.value = await getCurrentUser()
    loginDialogVisible.value = false
    loginForm.value = { username: '', password: '' }
    ElMessage.success('Login successful')
  } catch (error: any) {
    ElMessage.error(error.message || 'Login failed')
  }
}

async function handleRegister() {
  try {
    await register(registerForm.value)
    ElMessage.success('Registration successful, please login')
    registerDialogVisible.value = false
    registerForm.value = { username: '', email: '', password: '' }
    loginDialogVisible.value = true
  } catch (error: any) {
    ElMessage.error(error.message || 'Registration failed')
  }
}

async function handleLogout() {
  await logout()
  user.value = null
  ElMessage.success('Logged out')
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
        <el-button @click="handleLogout">Logout</el-button>
      </el-menu-item>
    </template>
    <template v-else>
      <el-menu-item>
        <el-button @click="loginDialogVisible = true">Login</el-button>
      </el-menu-item>
      <el-menu-item>
        <el-button @click="registerDialogVisible = true">Register</el-button>
      </el-menu-item>
    </template>
  </el-menu>

  <div style="padding: 20px">
    <h1>Welcome</h1>
  </div>

  <el-dialog v-model="loginDialogVisible" title="Login" width="400px">
    <el-form :model="loginForm" @submit.prevent="handleLogin">
      <el-form-item label="Username">
        <el-input v-model="loginForm.username" placeholder="Username" />
      </el-form-item>
      <el-form-item label="Password">
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="Password"
          @keyup.enter="handleLogin"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" style="width: 100%">
          Login
        </el-button>
      </el-form-item>
    </el-form>
  </el-dialog>

  <el-dialog v-model="registerDialogVisible" title="Register" width="400px">
    <el-form :model="registerForm" @submit.prevent="handleRegister">
      <el-form-item label="Username">
        <el-input v-model="registerForm.username" placeholder="Username" />
      </el-form-item>
      <el-form-item label="Email">
        <el-input v-model="registerForm.email" placeholder="Email" type="email" />
      </el-form-item>
      <el-form-item label="Password">
        <el-input
          v-model="registerForm.password"
          type="password"
          placeholder="Password"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" style="width: 100%">
          Register
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
