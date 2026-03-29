<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { ElDialog, ElForm, ElFormItem, ElInput, ElMessage } from 'element-plus'
import { login, register, getCurrentUser, logout, type User } from './api/auth'

const route = useRoute()

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
const activeIndex = computed(() => route.path)

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
    ElMessage.success('注册成功')
    registerDialogVisible.value = false
    loginForm.value = { username: registerForm.value.username, password: registerForm.value.password }
    registerForm.value = { username: '', password: '' }
    await handleLogin()
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
  <el-menu mode="horizontal" :router="true" :default-active="activeIndex">
    <el-menu-item index="/">提交记录</el-menu-item>
    <el-menu-item index="/steps">训练计划</el-menu-item>
    <el-menu-item index="/groups">组织</el-menu-item>
    <div style="flex: 1"></div>
    <template v-if="isLoggedIn">
      <el-menu-item index="/steps/create">
        创建训练计划
      </el-menu-item>
      <el-menu-item index="/profile">
        {{ user?.username }}
      </el-menu-item>
      <el-menu-item index="" @click="handleLogout">
        退出登录
      </el-menu-item>
    </template>
    <template v-else>
      <el-menu-item index="" @click="loginDialogVisible = true">
        登录
      </el-menu-item>
      <el-menu-item index="" @click="registerDialogVisible = true">
        注册
      </el-menu-item>
    </template>
  </el-menu>

  <router-view />

  <el-dialog v-model="loginDialogVisible" title="登录" width="320px">
    <el-form label-position="top" :model="loginForm" @submit.prevent="handleLogin">
      <el-form-item label="用户名">
        <el-input v-model="loginForm.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="loginForm.password"
          type="password"
          placeholder="请输入密码"
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

  <el-dialog v-model="registerDialogVisible" title="注册" width="320px">
    <el-form label-position="top" :model="registerForm" @submit.prevent="handleRegister">
      <el-form-item label="用户名">
        <el-input v-model="registerForm.username" placeholder="请输入用户名" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input
          v-model="registerForm.password"
          type="password"
          placeholder="请输入密码"
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
